from pathlib import Path
import os
import yaml
from backend.app.core.settings import get_settings

def _read_yaml(name: str, default):
    path = get_settings().config_dir / name
    if not path.exists():
        return default
    with path.open('r', encoding='utf-8') as f:
        return yaml.safe_load(f) or default

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

def missing_config():
    missing=[]
    for p in providers():
        if p.get('enabled', True) and not p.get('endpoint') and p.get('type') != 'placeholder':
            missing.append({'type':'provider','name':p.get('name'),'field':'endpoint'})
    return missing

def effective_settings():
    s = get_settings()
    return {'app': {'url':'http://127.0.0.1:3737','environment': s.environment, 'data_dir': str(s.data_dir), 'sqlite_path': str(s.db_path)}, 'providers': providers(), 'agents': agents(), 'workspaces': workspaces(), 'skills': skills(), 'missing': missing_config()}
