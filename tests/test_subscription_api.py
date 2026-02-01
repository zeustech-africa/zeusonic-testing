from fastapi.testclient import TestClient
from backend.main import app
from backend.core.auth import create_api_key
from backend.core.features import FEATURE_MATRIX
from backend.db.database import SessionLocal
from backend.db import models
from datetime import datetime, timedelta

client = TestClient(app)


def test_subscription_endpoint_and_admin_set_tier():
    # create target api key (FREE)
    target = create_api_key(owner='subscriber', tier='FREE')

    # create some jobs for usage
    db = SessionLocal()
    try:
        for i in range(3):
            job = models.AudioJob(job_id=f'sub-{i}', filename=f'f-{i}.wav', status='completed', owner='subscriber')
            db.add(job)
        db.commit()
    finally:
        db.close()

    # call subscription endpoint as target
    r = client.get('/api/v1/subscription', headers={'X-API-Key': target.key})
    assert r.status_code == 200
    data = r.json()
    # No subscription: fallback to API key tier
    assert data['plan_code'] is None
    assert data['status'] == 'fallback'
    assert data['entitlements'] == FEATURE_MATRIX['FREE']
    assert data['usage']['jobs_used_last_30_days'] >= 3
    assert data['usage']['jobs_limit'] == FEATURE_MATRIX['FREE']['max_jobs_per_month']

    # create admin api key (dev) to change tier
    admin = create_api_key(owner='admin-user', tier='PRO')
    # change target tier to CREATOR
    r2 = client.post('/api/v1/admin/set-tier', json={'target_api_key': target.key, 'tier': 'CREATOR'}, headers={'X-API-Key': admin.key})
    assert r2.status_code == 200
    assert r2.json()['new_tier'] == 'CREATOR'

    # subscription endpoint should reflect new tier (fallback still uses ApiKey.tier)
    r3 = client.get('/api/v1/subscription', headers={'X-API-Key': target.key})
    assert r3.status_code == 200
    assert r3.json()['status'] == 'fallback'
    assert r3.json()['entitlements'] == FEATURE_MATRIX['CREATOR']
