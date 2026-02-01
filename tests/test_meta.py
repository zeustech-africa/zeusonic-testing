from fastapi.testclient import TestClient
import backend.main as main_module
from backend.main import app


def test_meta_includes_beta_mode_default_false():
    client = TestClient(app)
    r = client.get("/api/v1/meta")
    assert r.status_code == 200
    j = r.json()
    assert "beta_mode" in j
    # Default in Settings should be False unless overridden by env
    assert j["beta_mode"] is False
