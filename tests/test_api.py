from pathlib import Path
from time import sleep

import pytest
from fastapi.testclient import TestClient

from backend.main import app


def test_health():
    with TestClient(app) as client:
        r = client.get("/api/v1/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}


def test_upload_unauthorized():
    with TestClient(app) as client:
        files = {"file": ("test.wav", b"RIFF....", "audio/wav")}
        r = client.post("/api/v1/audio/upload", files=files)
        assert r.status_code == 401


def test_upload_and_job_lifecycle():
    with TestClient(app) as client:
        # read demo API key created on startup
        key_path = Path(".demo_api_key")
        assert key_path.exists(), ".demo_api_key must exist (created on app startup)"
        api_key = key_path.read_text().strip()

        headers = {"X-API-Key": api_key}
        files = {"file": ("test.wav", b"RIFF....", "audio/wav")}

        r = client.post("/api/v1/audio/upload", headers=headers, files=files)
        assert r.status_code == 201
        payload = r.json()
        assert "job_id" in payload
        job_id = payload["job_id"]

        # Verify job is persisted and retrievable
        r2 = client.get(f"/api/v1/audio/jobs/{job_id}", headers=headers)
        assert r2.status_code == 200
        job = r2.json()
        assert job["job_id"] == job_id
        assert job["filename"] == payload["filename"]
        assert job["status"] in {"queued", "processing", "completed", "failed"}
