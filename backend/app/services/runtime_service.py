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
    if provider.get('api_key_env') and os.getenv(provider['api_key_env']):
        headers['Authorization'] = f"Bearer {os.getenv(provider['api_key_env'])}"
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


async def runtime_status() -> dict[str, Any]:
    openwebui = _provider_by_name('openwebui') or {}
    hermes = _provider_by_name('hermes') or {}
    deepseek = await _probe_openai_compatible(openwebui) if _agent_enabled('deepseek-chat') else {'status': 'disabled', 'ready': False, 'detail': 'deepseek-chat agent disabled', 'chat_available': False}
    codex = _probe_cli('codex') if _agent_enabled('codex-worker') else {'status': 'disabled', 'ready': False, 'detail': 'codex-worker agent disabled'}
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
                r = await client.get(str(hermes_endpoint).rstrip('/') + '/health')
            hermes_ready = r.status_code < 500
            hermes_detail = f'Hermes endpoint {hermes_endpoint}/health returned HTTP {r.status_code}; CLI chat bridge is {hermes_cli.get("status")}'
        except Exception as exc:
            hermes_detail = f'Hermes CLI missing and endpoint {hermes_endpoint} unreachable: {exc}'
    else:
        hermes_detail = 'Hermes endpoint missing and Hermes CLI not available'
    return {
        'heartbeat': 'online',
        'systems': [
            {'name': 'codex-worker', 'provider': 'codex', 'enabled': _agent_enabled('codex-worker'), 'status': codex.get('status'), 'ready': codex.get('ready'), 'detail': codex.get('detail'), 'path': codex.get('path'), 'action_available': bool(codex.get('ready')), 'chat_available': False},
            {'name': 'deepseek-chat', 'provider': 'openwebui', 'enabled': _agent_enabled('deepseek-chat'), 'status': deepseek.get('status'), 'ready': deepseek.get('ready'), 'detail': deepseek.get('detail'), 'latency_ms': deepseek.get('latency_ms'), 'models': deepseek.get('models', []), 'chat_available': bool(deepseek.get('chat_available'))},
            {'name': 'hermes-control', 'provider': 'hermes', 'enabled': _agent_enabled('hermes-control'), 'status': 'ready' if hermes_ready else 'not_connected', 'ready': hermes_ready, 'detail': hermes_detail, 'path': hermes_cli.get('path'), 'endpoint': hermes_endpoint, 'chat_available': hermes_ready, 'action_available': hermes_ready},
            {'name': 'claude-code', 'provider': 'claude', 'enabled': _agent_enabled('claude-code'), 'status': 'disabled', 'ready': False, 'detail': 'Claude Code agent is disabled until configured', 'chat_available': False},
        ]
    }
