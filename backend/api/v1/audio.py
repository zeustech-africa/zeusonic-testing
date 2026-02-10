from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends, Security
from pathlib import Path
from uuid import uuid4, UUID
from typing import Iterable, Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime
import time

router = APIRouter(tags=["audio"])

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB
ALLOWED_EXTENSIONS: Iterable[str] = {"wav", "mp3", "m4a"}

# Storage directory: configurable via settings.storage_path
from backend.core.config import settings

STORAGE_DIR = Path(settings.storage_path) / "audio_uploads"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# NOTE: Jobs are persisted to database now; no in-memory store required


class JobModel(BaseModel):
    job_id: UUID
    filename: str
    status: str  # queued | processing | completed | failed
    created_at: datetime
    updated_at: datetime


class UploadResponse(BaseModel):
    job_id: UUID
    filename: str
    content_type: str
    size_bytes: int
    status: str


class JobListResponse(BaseModel):
    jobs: List[JobModel]


def _get_extension(filename: str) -> str:
    """Return the lowercase file extension without leading dot."""
    return Path(filename).suffix.lower().lstrip(".")


async def _save_stream(upload_file: UploadFile, destination: Path, max_size: int) -> int:
    """Save an UploadFile to disk streaming in chunks and enforce max size.

    Raises HTTPException(413) if the size limit is exceeded and ensures partial
    files are removed.
    """
    total = 0
    try:
        with destination.open("wb") as out:
            while True:
                chunk = await upload_file.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_size:
                    out.close()
                    try:
                        destination.unlink(missing_ok=True)
                    except Exception:
                        pass
                    raise HTTPException(status_code=413, detail="File exceeds maximum allowed size of 20 MB")
                out.write(chunk)
    finally:
        # Close the upload to release resources
        try:
            await upload_file.close()
        except Exception:
            pass
    return total


from backend.db.database import SessionLocal
from backend.db import models


def _create_job_entry(filename: str, owner: Optional[str] = None) -> str:
    """Persist a new AudioJob and return job_id (UUID string)."""
    job_id = str(uuid4())
    db = SessionLocal()
    try:
        aj = models.AudioJob(job_id=job_id, filename=filename, status="queued", owner=owner)
        db.add(aj)
        db.commit()
        db.refresh(aj)
        return job_id
    finally:
        db.close()



from backend.core.logging import get_logger

logger = get_logger(__name__)


def _process_audio_job_bg(job_id: str, filename: str, owner: Optional[str] = None):
    """Background task to process uploaded audio file.
    
    This simulates audio processing. Replace with actual processing logic.
    Updates job status in database upon completion or failure.
    """
    import time
    logger.info(f"Starting background processing for job {job_id}, file: {filename}")
    
    db = SessionLocal()
    try:
        # Simulate processing (replace with actual audio processing)
        time.sleep(2)  # Simulate work
        
        # Update job status to completed
        job = db.query(models.AudioJob).filter(models.AudioJob.job_id == job_id).first()
        if job:
            job.status = "completed"
            db.commit()
            logger.info(f"Job {job_id} processing completed successfully")
    except Exception as e:
        # Mark job as failed
        try:
            job = db.query(models.AudioJob).filter(models.AudioJob.job_id == job_id).first()
            if job:
                job.status = "failed"
                db.commit()
        except Exception:
            pass
        logger.error(f"Job {job_id} processing failed: {str(e)}")
    finally:
        db.close()


def _legacy_upload_disabled():
    raise HTTPException(
        status_code=410,
        detail="Legacy API-key uploads are disabled. Use JWT project upload: POST /api/v1/projects/{project_id}/audio.",
    )


@router.post("/audio/upload", response_model=UploadResponse, status_code=201)
async def upload_audio(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Legacy upload disabled. Use JWT project upload instead."""
    _legacy_upload_disabled()


from backend.db.database import get_db
from sqlalchemy.orm import Session


@router.get("/audio/jobs/{job_id}", response_model=JobModel)
async def get_job(job_id: str, db: Session = Depends(get_db)):
    """Legacy job endpoint disabled. Use project-scoped track endpoints."""
    _legacy_upload_disabled()


from fastapi.responses import FileResponse


@router.get('/audio/download/{job_id}')
async def download_audio(job_id: str, db: Session = Depends(get_db)):
    """Legacy download endpoint disabled. Use project-scoped track endpoints."""
    _legacy_upload_disabled()


@router.get("/audio/jobs", response_model=JobListResponse)
async def list_jobs(limit: int = 20, db: Session = Depends(get_db)):
    """Legacy job listing disabled. Use project-scoped track endpoints."""
    _legacy_upload_disabled()
