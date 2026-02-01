from fastapi.testclient import TestClient
from backend.main import app
from backend.core.auth import create_api_key
from backend.db.database import SessionLocal
from backend.db import models
from datetime import datetime


def test_e2e_upload_and_quota_gating():
    client = TestClient(app)

    # Create a fresh API key for the test
    ak = create_api_key(owner="e2e-test-user", tier="FREE")
    headers = {"X-API-Key": ak.key}

    # First, a successful small upload should return 201
    files = {"file": ("test.wav", b"RIFFTESTDATA", "audio/wav")}
    r = client.post("/api/v1/audio/upload", headers=headers, files=files)
    assert r.status_code == 201
    jr = r.json()
    assert jr.get("status") == "queued"
    assert "job_id" in jr

    # Now exhaust the FREE tier limit by inserting jobs directly into DB
    db = SessionLocal()
    try:
        # Determine limit from FEATURE_MATRIX via entitlements; FREE default is 10
        for i in range(10):
            aj = models.AudioJob(job_id=f"e2e-{i}-{datetime.utcnow().timestamp()}", filename=f"f{i}.wav", status="completed", owner=ak.owner)
            db.add(aj)
        db.commit()
    finally:
        db.close()

    # Attempt another upload should be gated with 403
    r2 = client.post("/api/v1/audio/upload", headers=headers, files=files)
    assert r2.status_code == 403
    assert "Monthly job limit" in r2.text or "Upgrade" in r2.text
    # Ensure response does not leak stack traces
    assert "Traceback" not in r2.text
    assert "Exception" not in r2.text
