from fastapi.testclient import TestClient
from backend.main import app
from backend.core.auth import create_api_key
from backend.db.database import SessionLocal
from backend.db import models
from backend.core.features import FEATURE_MATRIX
from datetime import datetime, timedelta

client = TestClient(app)


def test_entitlement_precedence_and_admin_set_subscription():
    # create owner and api key with FREE tier
    owner = 'ent-owner'
    ak = create_api_key(owner=owner, tier='FREE')

    # ensure no subscription: fallback to FREE
    r = client.get('/api/v1/subscription', headers={'X-API-Key': ak.key})
    assert r.status_code == 200
    data = r.json()
    assert data['status'] == 'fallback'
    assert data['entitlements'] == FEATURE_MATRIX['FREE']

    # create admin and set a PRO subscription for owner
    admin = create_api_key(owner='admin', tier='PRO')
    payload = {'owner': owner, 'plan_code': 'PRO', 'status': 'active'}
    r2 = client.post('/api/v1/admin/set-subscription', json=payload, headers={'X-API-Key': admin.key})
    assert r2.status_code == 200

    # subscription endpoint should now reflect authoritative plan entitlements
    r3 = client.get('/api/v1/subscription', headers={'X-API-Key': ak.key})
    assert r3.status_code == 200
    data3 = r3.json()
    assert data3['plan_code'] == 'PRO'
    assert data3['status'] == 'active'
    assert data3['entitlements']['can_download_audio'] is True


def test_upload_blocked_when_subscription_limit_exceeded():
    owner = 'limit-owner'
    ak = create_api_key(owner=owner, tier='FREE')

    # Create a PRO subscription with low limit for testing
    admin = create_api_key(owner='admin2', tier='PRO')
    r = client.post('/api/v1/admin/set-subscription', json={'owner': owner, 'plan_code': 'PRO', 'status': 'active'}, headers={'X-API-Key': admin.key})
    assert r.status_code == 200

    # Modify plan to have very low limit so we can exceed it
    db = SessionLocal()
    try:
        plan = db.query(models.Plan).filter(models.Plan.code == 'PRO').first()
        assert plan is not None
        feats = plan.features
        feats['max_jobs_per_month'] = 2
        plan.features = feats
        db.add(plan)
        db.commit()
    finally:
        db.close()

    # Add 2 jobs in the last 30 days
    db = SessionLocal()
    try:
        for i in range(2):
            job = models.AudioJob(job_id=f'l-{i}', filename=f'file-{i}.wav', status='completed', owner=owner, created_at=datetime.utcnow())
            db.add(job)
        db.commit()
    finally:
        db.close()

    # Try uploading (simulate multipart upload minimal fields)
    files = {'file': ('a.wav', b'RIFFDATA', 'audio/wav')}
    r2 = client.post('/api/v1/audio/upload', files=files, headers={'X-API-Key': ak.key})
    assert r2.status_code == 403


def test_download_allowed_with_subscription_even_if_tier_free():
    owner = 'download-owner'
    ak = create_api_key(owner=owner, tier='FREE')

    admin = create_api_key(owner='admin3', tier='PRO')
    r = client.post('/api/v1/admin/set-subscription', json={'owner': owner, 'plan_code': 'PRO', 'status': 'active'}, headers={'X-API-Key': admin.key})
    assert r.status_code == 200

    # Create a job and a file in storage
    db = SessionLocal()
    try:
        job = models.AudioJob(job_id='dl-1', filename='dl-file.wav', status='completed', owner=owner)
        db.add(job)
        db.commit()
    finally:
        db.close()

    # Create dummy file
    from pathlib import Path
    from backend.core.config import settings
    storage = Path(settings.storage_path) / 'audio_uploads'
    storage.mkdir(parents=True, exist_ok=True)
    fpath = storage / 'dl-file.wav'
    fpath.write_bytes(b'DUMMY')

    r2 = client.get('/api/v1/audio/download/dl-1', headers={'X-API-Key': ak.key})
    assert r2.status_code == 200


def test_admin_set_subscription_updates_entitlements_immediately():
    owner = 'immediate-owner'
    ak = create_api_key(owner=owner, tier='FREE')
    admin = create_api_key(owner='admin4', tier='PRO')

    # create subscription
    r = client.post('/api/v1/admin/set-subscription', json={'owner': owner, 'plan_code': 'CREATOR', 'status': 'active'}, headers={'X-API-Key': admin.key})
    assert r.status_code == 200

    # entitlements should show CREATOR features
    r2 = client.get('/api/v1/subscription', headers={'X-API-Key': ak.key})
    assert r2.status_code == 200
    assert r2.json()['plan_code'] == 'CREATOR'
    assert r2.json()['entitlements']['can_export_stems'] is True
