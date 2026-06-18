from pathlib import Path
import os
import yaml
from backend.app.core.settings import get_settings
from backend.app.core.security import redact

SECRET_FIELDS = {'api_key', 'token', 'password', 'secret', 'credential'}

def _read_yaml(name: str, default):
    path = get_settings().config_dir / name
    if not path.exists():
        return default
    with path.open('r', encoding='utf-8') as f:
        return yaml.safe_load(f) or default

def _walk(obj, prefix=''):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _walk(v, str(k))
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk(v, prefix)
    else:
        yield prefix, obj

def _write_yaml(name: str, payload: dict):
    for key, value in _walk(payload):
        if any(s in key.lower() for s in SECRET_FIELDS) and key != 'api_key_env' and value:
            raise ValueError('secret values must be stored in .env, not YAML/UI config')
    path = get_settings().config_dir / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding='utf-8')

def providers():
    data = _read_yaml('providers.yaml', {'providers': []})
    for p in data.get('providers', []):
        if isinstance(p.get('api_key_env'), str):
            p['has_api_key'] = bool(os.getenv(p['api_key_env']))
        if p.get('url_env') and os.getenv(p['url_env']):
            p['endpoint'] = os.getenv(p['url_env'])
    return data.get('providers', [])

def agents(): return _read_yaml('agents.yaml', {'agents': []}).get('agents', [])
def workspaces(): return _read_yaml('workspaces.yaml', {'workspaces': []}).get('workspaces', [])
def skills(): return _read_yaml('skills.yaml', {'skills': []}).get('skills', [])
def capabilities(): return _read_yaml('capabilities.yaml', {'capabilities': []}).get('capabilities', [])
def spaces(): return _read_yaml('spaces.yaml', {'spaces': []}).get('spaces', [])

def update_registry(kind: str, payload: dict):
    mapping = {'providers':'providers.yaml','agents':'agents.yaml','workspaces':'workspaces.yaml','skills':'skills.yaml','capabilities':'capabilities.yaml','spaces':'spaces.yaml'}
    if kind not in mapping:
        raise ValueError('unknown registry')
    _write_yaml(mapping[kind], payload)
    return effective_settings()

def set_provider(name: str, patch: dict):
    data = _read_yaml('providers.yaml', {'providers': []})
    providers_list = data.setdefault('providers', [])
    current = None
    for provider in providers_list:
        if provider.get('name') == name:
            current = provider
            break
    if current is None:
        current = {'name': name}
        providers_list.append(current)
    for key, value in patch.items():
        if value is not None:
            current[key] = value
    _write_yaml('providers.yaml', data)
    return current

def set_agent(name: str, patch: dict):
    data = _read_yaml('agents.yaml', {'agents': []})
    agents_list = data.setdefault('agents', [])
    current = None
    for agent in agents_list:
        if agent.get('name') == name:
            current = agent
            break
    if current is None:
        current = {'name': name}
        agents_list.append(current)
    for key, value in patch.items():
        if value is not None:
            current[key] = value
    _write_yaml('agents.yaml', data)
    return current

def add_workspace(payload: dict):
    data = _read_yaml('workspaces.yaml', {'workspaces': []})
    items = data.setdefault('workspaces', [])
    name = payload.get('name')
    if not name:
        raise ValueError('workspace name is required')
    if not payload.get('path'):
        raise ValueError('workspace path is required')
    if not payload.get('allowed_commands'):
        payload['allowed_commands'] = ['npm test', 'npm run build', 'pytest', 'python -m pytest']
    for i, workspace in enumerate(items):
        if workspace.get('name') == name:
            items[i] = {**workspace, **payload}
            _write_yaml('workspaces.yaml', data)
            return items[i]
    items.append(payload)
    _write_yaml('workspaces.yaml', data)
    return payload

def missing_config():
    missing=[]
    for p in providers():
        if p.get('enabled', True) and not p.get('endpoint') and p.get('type') != 'placeholder':
            missing.append({'type':'provider','name':p.get('name'),'field':'endpoint'})
    return missing

def effective_settings():
    s = get_settings()
    return {'app': {'url': s.public_url, 'bind_host': s.app_host, 'port': s.app_port, 'environment': s.environment, 'data_dir': str(s.data_dir), 'sqlite_path': str(s.db_path)}, 'providers': redact(providers()), 'agents': agents(), 'workspaces': workspaces(), 'skills': skills(), 'capabilities': capabilities(), 'spaces': spaces(), 'missing': missing_config()}
