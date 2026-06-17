from fastapi.testclient import TestClient
from backend.app.main import app

def test_health(monkeypatch, tmp_path):
    monkeypatch.setenv('AGENTIC_OS_ENVIRONMENT','development')
    monkeypatch.setenv('AGENTIC_OS_DATA_DIR', str(tmp_path))
    c=TestClient(app)
    r=c.get('/api/health')
    assert r.status_code == 200
    assert r.json()['status'] == 'healthy'
