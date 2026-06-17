import importlib
from fastapi.testclient import TestClient

def make_client(monkeypatch, tmp_path):
    monkeypatch.setenv('AGENTIC_OS_ENVIRONMENT','development')
    monkeypatch.setenv('AGENTIC_OS_DATA_DIR', str(tmp_path))
    monkeypatch.setenv('AGENTIC_OS_CONFIG_DIR', 'config')
    from backend.app.core.settings import get_settings
    get_settings.cache_clear()
    from backend.app.db.migrations import run_migrations
    run_migrations()
    from backend.app.main import app
    return TestClient(app)

def test_health(monkeypatch, tmp_path):
    c=make_client(monkeypatch,tmp_path)
    r=c.get('/api/health')
    assert r.status_code == 200
    assert r.json()['status'] == 'healthy'
    assert r.json()['bind_host'] == '0.0.0.0'

def test_kanban_memory_and_audit(monkeypatch, tmp_path):
    c=make_client(monkeypatch,tmp_path)
    r=c.post('/api/kanban/tasks', json={'title':'Test task','status':'Ready'})
    assert r.status_code == 200
    assert r.json()['title'] == 'Test task'
    r=c.post('/api/memory', json={'title':'Memory','content':'Content','scope':'global','tags':['x']})
    assert r.status_code == 200
    assert c.get('/api/memory').json()[0]['title'] == 'Memory'
    audit=c.get('/api/audit').json()
    assert any(a['action'] == 'kanban.create' for a in audit)
    assert any(a['action'] == 'memory.create' for a in audit)

def test_production_requires_token(monkeypatch, tmp_path):
    monkeypatch.setenv('AGENTIC_OS_ENVIRONMENT','production')
    monkeypatch.delenv('AGENTIC_OS_ADMIN_TOKEN', raising=False)
    monkeypatch.setenv('AGENTIC_OS_DATA_DIR', str(tmp_path))
    from backend.app.core.settings import get_settings
    get_settings.cache_clear()
    from backend.app.main import app
    c=TestClient(app)
    assert c.get('/api/health').status_code == 503
