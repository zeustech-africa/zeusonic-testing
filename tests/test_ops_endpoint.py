from fastapi.testclient import TestClient
from backend.main import app
import backend.core.config as config
from backend.core.ops import reset_counters, increment


def test_ops_endpoint_dev_returns_counters(monkeypatch):
    client = TestClient(app)

    # ensure dev env
    monkeypatch.setattr(config.settings, "app_env", "development")

    # reset and increment a few counters
    reset_counters()
    increment('uploads_attempted', 2)
    increment('uploads_queued', 1)
    increment('uploads_failed', 1)

    r = client.get('/api/v1/admin/ops')
    assert r.status_code == 200
    j = r.json()
    assert j['uploads_attempted'] == 2
    assert j['uploads_queued'] == 1
    assert j['uploads_failed'] == 1


def test_ops_endpoint_blocked_in_production(monkeypatch):
    client = TestClient(app)
    monkeypatch.setattr(config.settings, "app_env", "production")
    r = client.get('/api/v1/admin/ops')
    assert r.status_code == 403
