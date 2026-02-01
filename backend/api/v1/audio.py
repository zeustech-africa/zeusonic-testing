from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Depends, Security
from pathlib import Path
from uuid import uuid4, UUID
from typing import Iterable, Dict, List
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


def _create_job_entry(filename: str, owner: str | None = None) -> str:
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



from backend.core.auth import get_api_key
from backend.core.features import get_entitlements


@router.post("/audio/upload", response_model=UploadResponse, status_code=201)
async def upload_audio(background_tasks: BackgroundTasks, file: UploadFile = File(...), api_key = Security(get_api_key)):
    """Upload a single audio file (wav, mp3, m4a). Max 20 MB.

    The file is saved locally and a background job is queued for processing.
    Returns an immediate response with a job_id.

    Authentication: requires header `X-API-Key`.
    """
    # Operational counter: attempted
    from backend.core.ops import increment
    increment('uploads_attempted')

    # Server-authoritative maintenance switch
    if settings.disable_uploads:
        increment('uploads_failed')
        raise HTTPException(status_code=503, detail='Uploads temporarily paused for maintenance.')

    if not file.filename:
        increment('uploads_failed')
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = _get_extension(file.filename)
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(f"Unsupported file extension: .{ext}. Supported: {', '.join(sorted(ALLOWED_EXTENSIONS))}"),
        )

    # Basic content type sanity check
    if not (file.content_type and file.content_type.startswith("audio/")):
        raise HTTPException(status_code=400, detail=f"Unsupported content type: {file.content_type}")

    # Create a safe, unique filename and avoid overwriting
    for _ in range(10):
        unique_name = f"{uuid4().hex}.{ext}"
        dest = STORAGE_DIR / unique_name
        if not dest.exists():
            break
    else:
        raise HTTPException(status_code=500, detail="Failed to generate unique filename")

    size = await _save_stream(file, dest, MAX_FILE_SIZE)

    # Resolve entitlements (Subscription > ApiKey.tier fallback)
    ent = get_entitlements(api_key.owner, api_key.tier)
    limit = ent.get('entitlements', {}).get('max_jobs_per_month')

    if limit:
        # Count jobs by this owner in last 30 days
        from datetime import datetime, timedelta

        cutoff = datetime.utcnow() - timedelta(days=30)
        db = SessionLocal()
        try:
            count = db.query(models.AudioJob).filter(models.AudioJob.owner == api_key.owner, models.AudioJob.created_at >= cutoff).count()
        finally:
            db.close()
        if count >= limit:
            increment('uploads_failed')
            raise HTTPException(status_code=403, detail="Monthly job limit reached for your subscription tier")

    # Create job entry (queued). Background worker will pick it up.
    job_id = _create_job_entry(dest.name, owner=api_key.owner)
    increment('uploads_queued')

    return UploadResponse(
        job_id=UUID(job_id),
        filename=dest.name,
        content_type=file.content_type,
        size_bytes=size,
        status="queued",
    )


from backend.db.database import get_db
from sqlalchemy.orm import Session


@router.get("/audio/jobs/{job_id}", response_model=JobModel)
async def get_job(job_id: str, api_key = Depends(get_api_key), db: Session = Depends(get_db)):
    """Return job metadata and status for a given job_id."""
    row = db.query(models.AudioJob).filter(models.AudioJob.job_id == job_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobModel(**{
        "job_id": row.job_id,
        "filename": row.filename,
        "status": row.status,
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    })


from fastapi.responses import FileResponse


@router.get('/audio/download/{job_id}')
async def download_audio(job_id: str, api_key = Depends(get_api_key), db: Session = Depends(get_db)):
    """Download the processed audio for a job if the subscription tier allows it."""
    row = db.query(models.AudioJob).filter(models.AudioJob.job_id == job_id).first()
    if not row:
        raise HTTPException(status_code=404, detail='Job not found')

    ent = get_entitlements(api_key.owner, api_key.tier)
    if not ent.get('entitlements', {}).get('can_download_audio'):
        raise HTTPException(status_code=403, detail='Downloads are available for paid plans. Upgrade to unlock.')

    file_path = STORAGE_DIR / row.filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail='Output file not found')

    return FileResponse(path=str(file_path), filename=row.filename, media_type='application/octet-stream')


@router.get("/audio/jobs", response_model=JobListResponse)
async def list_jobs(limit: int = 20, api_key = Depends(get_api_key), db: Session = Depends(get_db)):
    """List recent jobs, newest first. Limit defaults to 20."""
    rows = db.query(models.AudioJob).order_by(models.AudioJob.created_at.desc()).limit(max(0, limit)).all()
    job_models = [
        JobModel(
            job_id=r.job_id,
            filename=r.filename,
            status=r.status,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in rows
    ]
    return JobListResponse(jobs=job_models)
