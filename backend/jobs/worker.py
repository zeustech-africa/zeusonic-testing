import asyncio
from typing import Optional
from backend.db import models
from backend.db.database import SessionLocal
from backend.core.logging import get_logger
from sqlalchemy import select

logger = get_logger(__name__)

_worker_task: Optional[asyncio.Task] = None


def _pick_queued_job(db):
    # Pick the oldest queued job
    return db.query(models.AudioJob).filter(models.AudioJob.status == "queued").order_by(models.AudioJob.created_at.asc()).first()


async def _process_job_logic(job_id: str):
    """Process a single job: mark processing, simulate work, then mark completed/failed."""
    db = SessionLocal()
    try:
        row = db.query(models.AudioJob).filter(models.AudioJob.job_id == job_id).first()
        if not row:
            logger.warning("Job %s not found when attempting to process", job_id)
            return

        logger.info("Job %s picked up for processing", job_id)
        row.status = "processing"
        db.add(row)
        db.commit()

        # Simulated processing time (non-blocking sleep)
        await asyncio.sleep(3)

        # Deterministic failure rule for development: fail if sum of bytes mod 7 == 0
        checksum = sum(bytearray(job_id.encode("utf-8")))
        if checksum % 7 == 0:
            row.status = "failed"
            logger.info("Job %s marked as failed (deterministic rule)", job_id)
        else:
            row.status = "completed"
            logger.info("Job %s completed successfully", job_id)
        db.add(row)
        db.commit()
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Error processing job %s: %s", job_id, exc)
        try:
            if row:
                row.status = "failed"
                db.add(row)
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


async def _worker_loop(poll_interval: float = 2.0):
    logger.info("Job worker loop started (interval=%s sec)", poll_interval)
    try:
        while True:
            db = SessionLocal()
            try:
                job = _pick_queued_job(db)
                if job:
                    job_id = job.job_id
                    db.close()
                    await _process_job_logic(job_id)
                else:
                    db.close()
                    await asyncio.sleep(poll_interval)
            except Exception as exc:  # pragma: no cover - defensive
                logger.exception("Worker loop encountered an error: %s", exc)
                try:
                    db.close()
                except Exception:
                    pass
                await asyncio.sleep(poll_interval)
    except asyncio.CancelledError:
        logger.info("Job worker loop cancelled")
        raise


def start_worker(loop: Optional[asyncio.AbstractEventLoop] = None, poll_interval: float = 2.0):
    global _worker_task
    if _worker_task and not _worker_task.done():
        logger.info("Worker already running")
        return
    if loop is None:
        loop = asyncio.get_event_loop()
    _worker_task = loop.create_task(_worker_loop(poll_interval=poll_interval))
    logger.info("Started job worker task: %s", _worker_task)


def stop_worker():
    global _worker_task
    if _worker_task:
        logger.info("Stopping job worker task")
        _worker_task.cancel()
        _worker_task = None
