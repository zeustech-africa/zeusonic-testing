from datetime import datetime
from pathlib import Path
from typing import Optional
import secrets
import time

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.auth import get_current_verified_user
from core.config import settings
from db import models
from db.database import get_db, SessionLocal
from services.audio_transformer import SUPPORTED_STYLES, analyze_rhythm, extract_stems, transform_beat
from core.logging import get_logger
from services.audio_processor import analyze_audio
from core.observability import log_job_event, log_audit_event

router = APIRouter(tags=["audio-transform"])
logger = get_logger(__name__)


class TransformRequest(BaseModel):
    target_style: str


class TransformStatusResponse(BaseModel):
    id: int
    track_id: int
    source_style: str
    target_style: str
    status: str
    output_path: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]


def _get_project_audio_dir(project_id: int) -> Path:
    path = Path(settings.storage_path) / "projects" / str(project_id) / "audio"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _transform_bg(job_id: int) -> None:
    db = None
    start_time = time.time()
    try:
        db = SessionLocal()
        job = db.query(models.BeatTransformJob).filter(models.BeatTransformJob.id == job_id).first()
        if not job:
            return

        logger.info("Beat transform job %s started", job.id)

        job.status = "processing"
        db.commit()

        track = db.query(models.AudioTrack).filter(models.AudioTrack.id == job.track_id).first()
        if not track:
            job.status = "failed"
            db.commit()
            duration_ms = int((time.time() - start_time) * 1000)
            log_job_event(
                job_type='beat_transform',
                job_id=job_id,
                user_id=track.user_id if track else None,
                project_id=track.project_id if track else None,
                status='failed',
                duration_ms=duration_ms,
                error_message='Source track not found'
            )
            return

        audio_dir = _get_project_audio_dir(track.project_id)
        input_path = audio_dir / track.filename
        if not input_path.exists():
            job.status = "failed"
            db.commit()
            duration_ms = int((time.time() - start_time) * 1000)
            log_job_event(
                job_type='beat_transform',
                job_id=job_id,
                user_id=track.user_id,
                project_id=track.project_id,
                status='failed',
                duration_ms=duration_ms,
                error_message='Source audio file not found'
            )
            return

        stems_dir = audio_dir / "stems" / f"track_{track.id}"
        stems = extract_stems(input_path, stems_dir)

        # Persist stems metadata
        for stem_type, path in stems.items():
            db.add(models.AudioStem(
                project_id=track.project_id,
                source_track_id=track.id,
                stem_type=stem_type,
                file_path=str(path),
            ))
        db.commit()

        output_name = f"{secrets.token_hex(8)}_transform_{job.target_style}.wav"
        output_path = audio_dir / "transforms" / output_name

        transform_beat(input_path, job.target_style, output_path)

        job.output_path = str(output_path)
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        db.commit()

        logger.info("Beat transform job %s completed", job.id)

        # Create a new track for the transformed output to enable mix/master
        file_size = output_path.stat().st_size
        transformed_track = models.AudioTrack(
            project_id=track.project_id,
            user_id=track.user_id,
            filename=str(output_path.relative_to(audio_dir)),
            original_filename=f"{Path(track.original_filename).stem}_transform_{job.target_style}.wav",
            file_size=file_size,
            status="uploaded",
        )
        db.add(transformed_track)
        db.commit()
        db.refresh(transformed_track)

        # Analyze transformed track to allow immediate mix/master
        analysis_data = analyze_audio(output_path)
        transformed_track.duration_seconds = analysis_data.get("duration_seconds")
        transformed_track.status = "analyzed"
        db.add(models.AudioAnalysis(
            track_id=transformed_track.id,
            bpm=analysis_data.get("bpm"),
            musical_key=analysis_data.get("musical_key"),
            duration_seconds=analysis_data.get("duration_seconds") or 0.0,
            loudness_lufs=analysis_data.get("loudness_lufs"),
            sample_rate=analysis_data.get("sample_rate"),
            channels=analysis_data.get("channels"),
            bit_depth=analysis_data.get("bit_depth"),
        ))
        db.commit()

        duration_ms = int((time.time() - start_time) * 1000)
        log_job_event(
            job_type='beat_transform',
            job_id=job_id,
            user_id=track.user_id,
            project_id=track.project_id,
            status='completed',
            duration_ms=duration_ms,
            metadata={'style': job.target_style, 'output_track_id': transformed_track.id}
        )
        
        log_audit_event(
            event_type='transform',
            user_id=track.user_id,
            project_id=track.project_id,
            resource_type='track',
            resource_id=transformed_track.id,
            action='created',
            details={'source_track_id': track.id, 'style': job.target_style}
        )

    except Exception as e:
        if db:
            try:
                job = db.query(models.BeatTransformJob).filter(models.BeatTransformJob.id == job_id).first()
                if job:
                    job.status = "failed"
                    db.commit()
                    duration_ms = int((time.time() - start_time) * 1000)
                    log_job_event(
                        job_type='beat_transform',
                        job_id=job_id,
                        user_id=track.user_id if track else None,
                        project_id=track.project_id if track else None,
                        status='failed',
                        duration_ms=duration_ms,
                        error_message=str(e)
                    )
                    logger.warning("Beat transform job %s failed", job.id)
            except Exception:
                pass
        logger.exception(f"Beat transform job {job_id} failed with exception: {e}")
    finally:
        if db:
            db.close()


@router.post("/audio/{track_id}/transform", response_model=TransformStatusResponse, status_code=202)
def transform_track(
    track_id: int,
    payload: TransformRequest,
    background_tasks: BackgroundTasks,
    user: models.User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    target_style = payload.target_style.strip().lower()
    if target_style not in SUPPORTED_STYLES:
        raise HTTPException(status_code=400, detail="Unsupported target style")

    track = db.query(models.AudioTrack).filter(
        models.AudioTrack.id == track_id,
        models.AudioTrack.user_id == user.id,
    ).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")

    # Infer source style from rhythm analysis (best-effort)
    audio_dir = _get_project_audio_dir(track.project_id)
    input_path = audio_dir / track.filename
    source_style = "unknown"
    try:
        rhythm = analyze_rhythm(input_path)
        source_style = f"{rhythm.bpm:.1f}bpm"
    except Exception:
        pass

    job = models.BeatTransformJob(
        track_id=track.id,
        source_style=source_style,
        target_style=target_style,
        status="pending",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    logger.info("Beat transform job %s queued for track %s", job.id, track.id)

    background_tasks.add_task(_transform_bg, job.id)

    return TransformStatusResponse(
        id=job.id,
        track_id=job.track_id,
        source_style=job.source_style,
        target_style=job.target_style,
        status=job.status,
        output_path=job.output_path,
        created_at=job.created_at,
        completed_at=job.completed_at,
    )


@router.get("/audio/{track_id}/transform/status", response_model=TransformStatusResponse)
def transform_status(
    track_id: int,
    user: models.User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    track = db.query(models.AudioTrack).filter(
        models.AudioTrack.id == track_id,
        models.AudioTrack.user_id == user.id,
    ).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")

    job = db.query(models.BeatTransformJob).filter(
        models.BeatTransformJob.track_id == track.id,
    ).order_by(models.BeatTransformJob.created_at.desc()).first()

    if not job:
        raise HTTPException(status_code=404, detail="Transform job not found")

    return TransformStatusResponse(
        id=job.id,
        track_id=job.track_id,
        source_style=job.source_style,
        target_style=job.target_style,
        status=job.status,
        output_path=job.output_path,
        created_at=job.created_at,
        completed_at=job.completed_at,
    )


@router.get("/audio/{track_id}/transform/download")
def download_transform(
    track_id: int,
    user: models.User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    track = db.query(models.AudioTrack).filter(
        models.AudioTrack.id == track_id,
        models.AudioTrack.user_id == user.id,
    ).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")

    job = db.query(models.BeatTransformJob).filter(
        models.BeatTransformJob.track_id == track.id,
        models.BeatTransformJob.status == "completed",
    ).order_by(models.BeatTransformJob.completed_at.desc()).first()

    if not job or not job.output_path:
        raise HTTPException(status_code=404, detail="Transform output not found")

    output_path = Path(job.output_path)
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        path=str(output_path),
        filename=f"{Path(track.original_filename).stem}_transform_{job.target_style}.wav",
        media_type="application/octet-stream",
    )
