from fastapi.testclient import TestClient
from backend.main import app
from backend.core.auth import create_api_key
from backend.core.features import FEATURE_MATRIX
from backend.db.database import SessionLocal
from backend.db import models

client = TestClient(app)


def test_subscription_endpoint_public_data_matches_features():
    ak = create_api_key(owner='visible', tier='CREATOR')

    r = client.get('/api/v1/subscription', headers={'X-API-Key': ak.key})
    assert r.status_code == 200
    data = r.json()
    assert data['tier'] == 'CREATOR'
    assert data['features'] == FEATURE_MATRIX['CREATOR']
    assert 'jobs_used_last_30_days' in data['usage']
    assert data['usage']['jobs_limit'] == FEATURE_MATRIX['CREATOR']['max_jobs_per_month']
