from fastapi.testclient import TestClient
from backend.main import app
import backend.core.config as config


def test_uploads_disabled_returns_503(monkeypatch):
    client = TestClient(app)
    # ensure uploads are disabled
    monkeypatch.setattr(config.settings, "disable_uploads", True)

    files = {"file": ("test.wav", b"RIFFTESTDATA", "audio/wav")}
    # Create an API key by importing helper
    from backend.core.auth import create_api_key
    ak = create_api_key(owner="tmp-uploader", tier="FREE")
    headers = {"X-API-Key": ak.key}

    r = client.post('/api/v1/audio/upload', headers=headers, files=files)
    assert r.status_code == 503
    assert 'Uploads temporarily paused for maintenance' in r.json().get('detail', '')
    # reset flag
    monkeypatch.setattr(config.settings, "disable_uploads", False)
