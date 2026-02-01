import time
import uuid
from fastapi.testclient import TestClient

from backend.main import app
from backend.db.database import SessionLocal
from backend.db import models


def test_background_worker_processes_queued_job():
    client = TestClient(app)

    # create a queued job directly in DB
    job_id = str(uuid.uuid4())
    db = SessionLocal()
    try:
        job = models.AudioJob(job_id=job_id, filename="job-test.wav", status="queued")
        db.add(job)
        db.commit()
    finally:
        db.close()

    # poll DB for status change (should move off 'queued' within a few seconds)
    db = SessionLocal()
    try:
        status = None
        for _ in range(10):
            row = db.query(models.AudioJob).filter(models.AudioJob.job_id == job_id).first()
            status = row.status if row else None
            if status and status != "queued":
                break
            time.sleep(1)
        assert status in {"processing", "completed", "failed"}
    finally:
        db.close()
