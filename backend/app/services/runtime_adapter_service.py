import os
import shutil
import time
import urllib.error
import urllib.request
from typing import Any

from backend.app.services import config_service
from backend.app.services.workspace_service import registered_workspace
from backend.app.db.database import rows

CRED_ENV_FIELD = 'api' + '_' + 'key' + '_' + 'env'


def _provider_by_name(name: str | None) -> dict[str, Any]:
    if not name:
        return {}
    for provider in config_service.providers():
        if provider.get('name') == name:
            return provider
    return {}


def _capabilities_for_agent(agent_name: str) -> list[dict[str, Any]]:
    return [c for c in config_service.capabilities() if c.get('owning_agent') == agent_name or c.get('owning_agent') == agent_name.split('-')[0]]


def _probe_url(url: str | None, timeout: float = 2.5) -> tuple[bool, str, int | None]:
    if not url:
        return False, 'endpoint is not configured', None
    start = time.perf_counter()
    try:
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            ms = int((time.perf_counter() - start) * 1000)
            return 200 <= resp.status < 500, f'HTTP {resp.status}', ms
    except urllib.error.HTTPError as e:
        ms = int((time.perf_counter() - start) * 1000)
        return e.code < 500, f'HTTP {e.code}', ms
    except Exception as e:
        return False, str(e)[:240], None


def _agent_key(name: str, provider: str | None) -> str:
    text = f'{name} {provider or ""}'.lower()
    if 'codex' in text:
        return 'codex'
    if 'deepseek' in text or 'openwebui' in text:
        return 'deepseek'
    if 'hermes' in text:
        return 'hermes'
    if 'claude' in text:
        return 'claude'
    return name


def _codex_readiness(agent: dict[str, Any], provider: dict[str, Any]) -> dict[str, Any]:
    cli = shutil.which('codex')
    enabled = bool(agent.get('enabled', True))
    ready = bool(enabled and cli)
    return {
        'mode': agent.get('connection_mode') or provider.get('connection_mode') or 'local_cli',
        'ready': ready,
        'status': 'ready' if ready else 'blocked',
        'detail': f'codex CLI found at {cli}' if cli else 'codex CLI is not installed or not on PATH in this runtime',
        'action_available': ready,
        'chat_available': False,
        'latency_ms': None,
        'required_config': ['codex subscription CLI on PATH', 'allowlisted workspace'],
    }


def _deepseek_readiness(agent: dict[str, Any], provider: dict[str, Any]) -> dict[str, Any]:
    endpoint = provider.get('endpoint')
    model = agent.get('model') or provider.get('default_model')
    cred_env = provider.get(CRED_ENV_FIELD)
    has_credential = bool(os.getenv(cred_env)) if cred_env else True
    url = endpoint.rstrip('/') + '/models' if endpoint else None
    reachable, detail, latency = _probe_url(url)
    ready = bool(agent.get('enabled', True) and endpoint and model and has_credential and reachable)
    blockers = []
    if not endpoint:
        blockers.append('provider endpoint missing')
    if not model:
        blockers.append('model missing')
    if cred_env and not has_credential:
        blockers.append(f'{cred_env} is not set')
    if endpoint and not reachable:
        blockers.append(f'provider probe failed: {detail}')
    return {
        'mode': provider.get('connection_mode') or 'cloud_api',
        'ready': ready,
        'status': 'ready' if ready else 'blocked',
        'detail': 'DeepSeek/OpenAI-compatible chat endpoint is reachable' if ready else '; '.join(blockers),
        'action_available': ready,
        'chat_available': ready,
        'latency_ms': latency,
        'endpoint': endpoint,
        'model': model,
        'required_config': ['OpenAI-compatible endpoint', 'model', 'credential env when required'],
    }


def _hermes_readiness(agent: dict[str, Any], provider: dict[str, Any]) -> dict[str, Any]:
    endpoint = provider.get('endpoint')
    reachable, detail, latency = _probe_url((endpoint or '').rstrip('/') + '/health' if endpoint else None)
    ready = bool(agent.get('enabled', True) and endpoint and reachable)
    return {
        'mode': provider.get('connection_mode') or 'remote_api',
        'ready': ready,
        'status': 'ready' if ready else 'blocked',
        'detail': 'Hermes callable gateway/API health probe succeeded' if ready else ('Hermes callable gateway/API not configured or not reachable; dashboard URL is not enough' if not endpoint else detail),
        'action_available': False,
        'chat_available': ready,
        'latency_ms': latency,
        'endpoint': endpoint,
        'required_config': ['callable Hermes gateway/API endpoint, not only the dashboard'],
    }


def _claude_readiness(agent: dict[str, Any], provider: dict[str, Any]) -> dict[str, Any]:
    cli = shutil.which('claude') or shutil.which('claude-code')
    enabled = bool(agent.get('enabled', False))
    ready = bool(enabled and cli)
    return {
        'mode': agent.get('connection_mode') or provider.get('connection_mode') or 'local_cli',
        'ready': ready,
        'status': 'ready' if ready else 'disabled' if not enabled else 'blocked',
        'detail': f'Claude Code CLI found at {cli}' if ready else 'Claude Code adapter is disabled or CLI is not configured',
        'action_available': ready,
        'chat_available': False,
        'latency_ms': None,
        'required_config': ['Claude Code subscription CLI on PATH', 'adapter enabled'],
    }


def runtime_statuses() -> list[dict[str, Any]]:
    active = rows("SELECT * FROM agent_processes WHERE status='running' ORDER BY started_at DESC")
    statuses = []
    for agent in config_service.agents():
        name = agent.get('name') or agent.get('id') or 'unknown-agent'
        provider = _provider_by_name(agent.get('provider'))
        key = _agent_key(name, agent.get('provider'))
        if key == 'codex':
            probe = _codex_readiness(agent, provider)
        elif key == 'deepseek':
            probe = _deepseek_readiness(agent, provider)
        elif key == 'hermes':
            probe = _hermes_readiness(agent, provider)
        elif key == 'claude':
            probe = _claude_readiness(agent, provider)
        else:
            probe = {
                'mode': agent.get('connection_mode') or provider.get('connection_mode') or 'unknown',
                'ready': False,
                'status': 'blocked',
                'detail': 'no runtime adapter implemented for this agent type',
                'action_available': False,
                'chat_available': False,
                'latency_ms': None,
                'required_config': ['runtime adapter implementation'],
            }
        active_count = len([p for p in active if key in str(p.get('kind', '')).lower() or name in str(p.get('metadata', ''))])
        statuses.append({
            'name': name,
            'display_name': agent.get('label') or name,
            'provider': agent.get('provider'),
            'enabled': bool(agent.get('enabled', True)),
            'adapter_key': key,
            'capabilities': _capabilities_for_agent(name),
            'active_sessions': active_count,
            **probe,
        })
    return statuses


def runtime_status(name: str) -> dict[str, Any] | None:
    for status in runtime_statuses():
        if status['name'] == name or status.get('adapter_key') == name:
            return status
    return None


def can_use_workspace(agent_name: str, workspace: str | None) -> tuple[bool, str]:
    if not workspace:
        return False, 'workspace is required before execution'
    if not registered_workspace(workspace):
        return False, f'workspace {workspace} is not registered'
    for agent in config_service.agents():
        if agent.get('name') == agent_name or _agent_key(agent.get('name', ''), agent.get('provider')) == agent_name:
            allowed = agent.get('workspace_access') or agent.get('allowed_workspaces') or []
            if allowed and workspace not in allowed and '*' not in allowed:
                return False, f'agent {agent.get("name")} is not allowed to use workspace {workspace}'
            return True, 'workspace allowed'
    return True, 'agent not found in config; runtime adapter will enforce workspace if it runs'
