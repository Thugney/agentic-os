import os
import shutil
import subprocess
import time
from typing import Any

import httpx

from backend.app.services import config_service


def _agent_enabled(name: str) -> bool:
    for agent in config_service.agents():
        if agent.get('name') == name:
            return bool(agent.get('enabled', True))
    return False


def _provider_by_name(name: str) -> dict[str, Any] | None:
    for provider in config_service.providers():
        if provider.get('name') == name:
            return provider
    return None


async def _probe_openai_compatible(provider: dict[str, Any]) -> dict[str, Any]:
    endpoint = provider.get('endpoint')
    model = provider.get('default_model')
    if not endpoint:
        return {'status': 'misconfigured', 'ready': False, 'detail': 'provider endpoint missing', 'chat_available': False}
    headers: dict[str, str] = {}
    if provider.get('api_key_env'):
        api_key = os.getenv(provider['api_key_env'])
        if not api_key and provider.get('connection_mode') == 'cloud_api':
            return {'status': 'needs_api_key', 'ready': False, 'detail': f"set {provider['api_key_env']} in .env, then rebuild/restart Agentic OS", 'chat_available': False}
        if api_key:
            headers['Authorization'] = f"Bearer {api_key}"
    started = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            response = await client.get(endpoint.rstrip('/') + '/v1/models', headers=headers)
        latency = round((time.perf_counter() - started) * 1000)
        if response.status_code >= 400:
            return {'status': 'error', 'ready': False, 'detail': f'/v1/models returned HTTP {response.status_code}', 'latency_ms': latency, 'chat_available': False}
        models = []
        try:
            payload = response.json()
            models = [item.get('id') for item in payload.get('data', []) if isinstance(item, dict)]
        except Exception:
            models = []
        model_required = bool(model) and not str(model).startswith('selected-')
        model_known = (model in models) if (model_required and models) else True
        ready = bool(models) and model_known
        detail = 'OpenAI-compatible endpoint reachable; choose a model from the dropdown' if ready and not model_required else ('OpenAI-compatible endpoint reachable' if ready else f'endpoint reachable but configured model {model!r} was not listed')
        return {'status': 'ready' if ready else 'warning', 'ready': ready, 'detail': detail, 'latency_ms': latency, 'models': models[:50], 'chat_available': ready}
    except Exception as exc:
        return {'status': 'offline', 'ready': False, 'detail': f'cannot reach {endpoint}: {exc}', 'chat_available': False}


def _probe_cli(binary: str) -> dict[str, Any]:
    path = shutil.which(binary)
    if not path:
        return {'status': 'missing', 'ready': False, 'detail': f'{binary} CLI not found in container PATH', 'path': None}
    try:
        result = subprocess.run([path, '--version'], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=5)
        version = (result.stdout or '').strip().splitlines()[0] if result.stdout else 'version unavailable'
        return {'status': 'ready' if result.returncode == 0 else 'warning', 'ready': result.returncode == 0, 'detail': version, 'path': path}
    except Exception as exc:
        return {'status': 'error', 'ready': False, 'detail': str(exc), 'path': path}


async def _probe_hermes_gateway(endpoint: str | None) -> dict[str, Any]:
    if not endpoint:
        return {'status': 'misconfigured', 'ready': False, 'detail': 'Hermes gateway/API endpoint is missing', 'endpoint': endpoint, 'chat_available': False, 'action_available': False}
    base = str(endpoint).rstrip('/')
    candidates = ['/health', '/api/health', '/openapi.json', '/docs']
    observations: list[str] = []
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            for path in candidates:
                response = await client.get(base + path)
                observations.append(f'{path} -> HTTP {response.status_code}')
                if response.status_code < 400:
                    detail = f'Hermes gateway reachable via {base + path}. Remote chat is routed through Agentic OS POST /api/hermes/chat -> {base}/v1/chat/completions. Kanban/cron/tools still need dedicated Hermes route mapping.'
                    return {'status': 'ready', 'ready': True, 'detail': detail, 'endpoint': endpoint, 'probe_path': path, 'observations': observations, 'chat_available': True, 'action_available': False, 'remote_chat_route': base + '/v1/chat/completions'}
        return {'status': 'reachable_no_known_api', 'ready': False, 'detail': f'Hermes host responded but no known Agentic OS health/discovery route worked: {"; ".join(observations)}.', 'endpoint': endpoint, 'observations': observations, 'chat_available': False, 'action_available': False}
    except Exception as exc:
        return {'status': 'offline', 'ready': False, 'detail': f'Cannot reach Hermes gateway/API endpoint {endpoint}: {exc}', 'endpoint': endpoint, 'observations': observations, 'chat_available': False, 'action_available': False}


async def test_provider(name: str) -> dict[str, Any]:
    provider = _provider_by_name(name) or {}
    if not provider:
        return {'status': 'missing', 'ready': False, 'detail': f'provider {name} is not configured'}
    if provider.get('type') == 'openai_compatible':
        result = await _probe_openai_compatible(provider)
        result['provider'] = name
        result['connection_mode'] = provider.get('connection_mode')
        return result
    if provider.get('type') == 'codex':
        result = _probe_cli(provider.get('cli_binary') or 'codex') if provider.get('connection_mode') in {'local_cli','subscription_cli'} else {'status': 'not_implemented', 'ready': False, 'detail': f"{provider.get('connection_mode')} adapter is configured but not implemented yet"}
        result['provider'] = name
        result['connection_mode'] = provider.get('connection_mode')
        return result
    if provider.get('type') == 'hermes':
        if provider.get('connection_mode') == 'local_cli':
            result = _probe_cli(provider.get('cli_binary') or 'hermes')
            result['chat_available'] = bool(result.get('ready'))
            result['action_available'] = bool(result.get('ready'))
        else:
            result = await _probe_hermes_gateway(provider.get('endpoint'))
        result['provider'] = name
        result['connection_mode'] = provider.get('connection_mode')
        return result
    return {'provider': name, 'status': 'not_implemented', 'ready': False, 'detail': f"provider type {provider.get('type')} is not implemented"}


async def runtime_status() -> dict[str, Any]:
    deepseek_provider = _provider_by_name('deepseek') or _provider_by_name('openwebui') or {}
    hermes = _provider_by_name('hermes') or {}
    codex_provider = _provider_by_name('codex') or {}
    deepseek = await _probe_openai_compatible(deepseek_provider) if _agent_enabled('deepseek-chat') else {'status': 'disabled', 'ready': False, 'detail': 'deepseek-chat agent disabled', 'chat_available': False}
    codex = (_probe_cli(codex_provider.get('cli_binary') or 'codex') if codex_provider.get('connection_mode','subscription_cli') in {'local_cli','subscription_cli'} else {'status': 'adapter_not_implemented', 'ready': False, 'detail': f"{codex_provider.get('connection_mode')} adapter selected; implement or configure subscription_cli before running"}) if _agent_enabled('codex-worker') else {'status': 'disabled', 'ready': False, 'detail': 'codex-worker agent disabled'}
    hermes_endpoint = hermes.get('endpoint') or os.getenv('HERMES_URL')
    if _agent_enabled('hermes-control') and hermes.get('connection_mode') == 'local_cli':
        hermes_cli = _probe_cli(os.getenv('HERMES_CLI', 'hermes'))
        hermes_status = {'status': 'ready' if hermes_cli.get('ready') else 'missing_cli', 'ready': bool(hermes_cli.get('ready')), 'detail': f"Hermes CLI bridge available: {hermes_cli.get('detail')}" if hermes_cli.get('ready') else hermes_cli.get('detail'), 'chat_available': bool(hermes_cli.get('ready')), 'action_available': bool(hermes_cli.get('ready')), 'path': hermes_cli.get('path')}
    else:
        hermes_status = await _probe_hermes_gateway(hermes_endpoint) if _agent_enabled('hermes-control') else {'status': 'disabled', 'ready': False, 'detail': 'hermes-control agent disabled', 'chat_available': False, 'action_available': False}
    return {
        'heartbeat': 'online',
        'systems': [
            {'name': 'codex-worker', 'provider': 'codex', 'connection_mode': codex_provider.get('connection_mode'), 'enabled': _agent_enabled('codex-worker'), 'status': codex.get('status'), 'ready': codex.get('ready'), 'detail': codex.get('detail'), 'path': codex.get('path'), 'action_available': bool(codex.get('ready')), 'chat_available': False},
            {'name': 'deepseek-chat', 'provider': deepseek_provider.get('name','deepseek'), 'connection_mode': deepseek_provider.get('connection_mode'), 'enabled': _agent_enabled('deepseek-chat'), 'status': deepseek.get('status'), 'ready': deepseek.get('ready'), 'detail': deepseek.get('detail'), 'latency_ms': deepseek.get('latency_ms'), 'models': deepseek.get('models', []), 'chat_available': bool(deepseek.get('chat_available'))},
            {'name': 'hermes-control', 'provider': 'hermes', 'connection_mode': hermes.get('connection_mode'), 'enabled': _agent_enabled('hermes-control'), 'status': hermes_status.get('status'), 'ready': hermes_status.get('ready'), 'detail': hermes_status.get('detail'), 'path': hermes_status.get('path'), 'endpoint': hermes_endpoint, 'chat_available': bool(hermes_status.get('chat_available')), 'action_available': bool(hermes_status.get('action_available')), 'remote_chat_route': hermes_status.get('remote_chat_route')},
            {'name': 'claude-code', 'provider': 'claude', 'enabled': _agent_enabled('claude-code'), 'status': 'disabled', 'ready': False, 'detail': 'Claude Code agent is disabled until configured', 'chat_available': False},
        ]
    }
