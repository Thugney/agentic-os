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
        model_known = bool(model) and (not models or model in models)
        return {'status': 'ready' if model_known else 'warning', 'ready': model_known, 'detail': 'OpenAI-compatible endpoint reachable' if model_known else f'endpoint reachable but configured model {model!r} was not listed', 'latency_ms': latency, 'models': models[:25], 'chat_available': model_known}
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
        result = _probe_cli(provider.get('cli_binary') or 'codex') if provider.get('connection_mode') == 'local_cli' else {'status': 'not_implemented', 'ready': False, 'detail': f"{provider.get('connection_mode')} adapter is configured but not implemented yet"}
        result['provider'] = name
        result['connection_mode'] = provider.get('connection_mode')
        return result
    if provider.get('type') == 'hermes':
        endpoint = provider.get('endpoint')
        if provider.get('connection_mode') == 'local_cli':
            result = _probe_cli(provider.get('cli_binary') or 'hermes')
        elif endpoint:
            try:
                async with httpx.AsyncClient(timeout=3) as client:
                    r = await client.get(str(endpoint).rstrip('/') + '/api/health')
                result = {'status': 'reachable' if r.status_code < 500 else 'error', 'ready': r.status_code < 500, 'detail': f'Hermes API health returned HTTP {r.status_code}', 'endpoint': endpoint}
            except Exception as exc:
                result = {'status': 'offline', 'ready': False, 'detail': f'Cannot reach Hermes API endpoint {endpoint}: {exc}', 'endpoint': endpoint}
        else:
            result = {'status': 'misconfigured', 'ready': False, 'detail': 'Hermes endpoint is missing'}
        result['provider'] = name
        result['connection_mode'] = provider.get('connection_mode')
        return result
    return {'provider': name, 'status': 'not_implemented', 'ready': False, 'detail': f"provider type {provider.get('type')} is not implemented"}


async def runtime_status() -> dict[str, Any]:
    deepseek_provider = _provider_by_name('deepseek') or _provider_by_name('openwebui') or {}
    hermes = _provider_by_name('hermes') or {}
    codex_provider = _provider_by_name('codex') or {}
    deepseek = await _probe_openai_compatible(deepseek_provider) if _agent_enabled('deepseek-chat') else {'status': 'disabled', 'ready': False, 'detail': 'deepseek-chat agent disabled', 'chat_available': False}
    codex = (_probe_cli(codex_provider.get('cli_binary') or 'codex') if codex_provider.get('connection_mode','local_cli') == 'local_cli' else {'status': 'adapter_not_implemented', 'ready': False, 'detail': f"{codex_provider.get('connection_mode')} adapter selected; implement or configure local_cli before running"}) if _agent_enabled('codex-worker') else {'status': 'disabled', 'ready': False, 'detail': 'codex-worker agent disabled'}
    hermes_cli = _probe_cli(os.getenv('HERMES_CLI', 'hermes')) if _agent_enabled('hermes-control') else {'status': 'disabled', 'ready': False, 'detail': 'hermes-control agent disabled'}
    hermes_endpoint = hermes.get('endpoint')
    hermes_ready = False
    hermes_detail = hermes_cli.get('detail')
    if hermes_cli.get('ready'):
        hermes_ready = True
        hermes_detail = f"Hermes CLI available: {hermes_cli.get('detail')}"
    elif hermes_endpoint:
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                r = await client.get(str(hermes_endpoint).rstrip('/') + '/api/health')
            hermes_ready = r.status_code < 500
            hermes_detail = f'Hermes API endpoint {hermes_endpoint}/api/health returned HTTP {r.status_code}; CLI bridge is {hermes_cli.get("status")}'
        except Exception as exc:
            hermes_detail = f'Hermes CLI missing and API endpoint {hermes_endpoint} unreachable: {exc}'
    else:
        hermes_detail = 'Hermes endpoint missing and Hermes CLI not available'
    return {
        'heartbeat': 'online',
        'systems': [
            {'name': 'codex-worker', 'provider': 'codex', 'connection_mode': codex_provider.get('connection_mode'), 'enabled': _agent_enabled('codex-worker'), 'status': codex.get('status'), 'ready': codex.get('ready'), 'detail': codex.get('detail'), 'path': codex.get('path'), 'action_available': bool(codex.get('ready')), 'chat_available': False},
            {'name': 'deepseek-chat', 'provider': deepseek_provider.get('name','deepseek'), 'connection_mode': deepseek_provider.get('connection_mode'), 'enabled': _agent_enabled('deepseek-chat'), 'status': deepseek.get('status'), 'ready': deepseek.get('ready'), 'detail': deepseek.get('detail'), 'latency_ms': deepseek.get('latency_ms'), 'models': deepseek.get('models', []), 'chat_available': bool(deepseek.get('chat_available'))},
            {'name': 'hermes-control', 'provider': 'hermes', 'connection_mode': hermes.get('connection_mode'), 'enabled': _agent_enabled('hermes-control'), 'status': 'ready' if hermes_ready else 'not_connected', 'ready': hermes_ready, 'detail': hermes_detail, 'path': hermes_cli.get('path'), 'endpoint': hermes_endpoint, 'chat_available': hermes_ready, 'action_available': hermes_ready},
            {'name': 'claude-code', 'provider': 'claude', 'enabled': _agent_enabled('claude-code'), 'status': 'disabled', 'ready': False, 'detail': 'Claude Code agent is disabled until configured', 'chat_available': False},
        ]
    }
