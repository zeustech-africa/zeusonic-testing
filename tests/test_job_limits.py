import io
from fastapi.testclient import TestClient
from backend.main import app
from backend.core.auth import create_api_key
from backend.db import models
from backend.db.database import SessionLocal

client = TestClient(app)


def test_free_user_monthly_limit_blocks_upload(tmp_path):
    # create a free api key
    ak = create_api_key(owner='limiter', tier='FREE')

    # create max allowed jobs in last 30 days
    db = SessionLocal()
    try:
        for i in range(10):
            job = models.AudioJob(job_id=f'limit-{i}', filename=f'file-{i}.wav', status='completed', owner='limiter')
            db.add(job)
        db.commit()
    finally:
        db.close()

    # attempt to upload a small file
    data = {'file': ('small.wav', io.BytesIO(b'data'), 'audio/wav')}
    r = client.post('/api/v1/audio/upload', files=data, headers={'X-API-Key': ak.key})
    assert r.status_code == 403
    assert 'Monthly job limit' in r.json().get('detail', '')
