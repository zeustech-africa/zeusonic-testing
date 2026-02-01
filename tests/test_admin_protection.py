from fastapi.testclient import TestClient
from backend.main import app
from backend.core.auth import create_api_key
from backend.core import config


def test_admin_endpoints_blocked_in_production(monkeypatch):
    client = TestClient(app)
    ak = create_api_key(owner="admin-test", tier="FREE")
    headers = {"X-API-Key": ak.key}

    # Temporarily set app_env to production
    original = config.settings.app_env
    monkeypatch.setattr(config.settings, "app_env", "production")

    payload = {"owner": "someone", "plan_code": "FREE", "status": "active"}
    r = client.post("/api/v1/admin/set-subscription", json=payload, headers=headers)
    assert r.status_code == 403

    # restore done by monkeypatch automatically
