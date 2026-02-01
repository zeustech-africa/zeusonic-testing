import os
import shutil
from fastapi.testclient import TestClient
from backend.main import app
from backend.db.database import SessionLocal
from backend.db import models
from backend.core.auth import create_api_key
from pathlib import Path

client = TestClient(app)


def setup_file(filename: str):
    storage = Path('backend/storage/audio_uploads')
    storage.mkdir(parents=True, exist_ok=True)
    p = storage / filename
    p.write_bytes(b'data')
    return p


def test_free_user_cannot_download():
    # create free api key
    ak = create_api_key(owner='free-user', tier='FREE')

    # create job by hand
    job_id = 'job-free-1'
    db = SessionLocal()
    try:
        job = models.AudioJob(job_id=job_id, filename='free.wav', status='completed', owner='free-user')
        db.add(job)
        db.commit()
    finally:
        db.close()

    p = setup_file('free.wav')

    r = client.get(f'/api/v1/audio/download/{job_id}', headers={'X-API-Key': ak.key})
    assert r.status_code == 403
    assert 'Upgrade' in r.json().get('detail', '')


def test_paid_user_can_download():
    ak = create_api_key(owner='pro-user', tier='PRO')
    job_id = 'job-pro-1'
    db = SessionLocal()
    try:
        job = models.AudioJob(job_id=job_id, filename='pro.wav', status='completed', owner='pro-user')
        db.add(job)
        db.commit()
    finally:
        db.close()

    p = setup_file('pro.wav')

    r = client.get(f'/api/v1/audio/download/{job_id}', headers={'X-API-Key': ak.key})
    assert r.status_code == 200
    assert r.content == b'data'
