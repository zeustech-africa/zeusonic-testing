from fastapi.testclient import TestClient
from backend.main import app
from backend.core.auth import create_api_key
import backend.api.v1.audio as audio_mod


def test_internal_error_returns_calm_message(monkeypatch):
    client = TestClient(app)
    ak = create_api_key(owner="err-test", tier="FREE")
    headers = {"X-API-Key": ak.key}

    # Monkeypatch get_entitlements to raise to simulate an internal error during upload
    def _boom(owner, tier):
        raise RuntimeError("simulated boom")

    monkeypatch.setattr(audio_mod, "get_entitlements", _boom)

    files = {"file": ("test.wav", b"RIFFTESTDATA", "audio/wav")}
    r = client.post("/api/v1/audio/upload", headers=headers, files=files)
    assert r.status_code == 500
    assert "internal server error" in r.json().get("detail", "").lower()
    assert "Traceback" not in r.text
    assert "simulated boom" not in r.text
