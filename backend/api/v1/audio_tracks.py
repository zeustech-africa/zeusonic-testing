from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import secrets

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.core.auth import get_current_verified_user
from backend.db.database import get_db
from backend.db import models
from backend.core.config import settings
from backend.services.audio_processor import analyze_audio, mix_audio, master_audio
from backend.core.observability import log_job_event, log_audit_event
from backend.core.logging import get_logger
import time

logger = get_logger(__name__)
router = APIRouter(tags=["audio-tracks"])

MAX_AUDIO_SIZE = 100 * 1024 * 1024  # 100 MB
ALLOWED_AUDIO_TYPES = {".wav", ".mp3"}


class TrackUploadResponse(BaseModel):
    id: int
    project_id: int
    filename: str
    original_filename: str
    file_size: int
    status: str
    created_at: datetime


class AnalysisResponse(BaseModel):
    track_id: int
    bpm: Optional[float]
    musical_key: Optional[str]
    duration_seconds: float
    loudness_lufs: Optional[float]
    sample_rate: Optional[int]
    channels: Optional[int]


class ProcessingResponse(BaseModel):
    id: int
    track_id: int
    process_type: str
    status: str
    output_filename: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]


class TrackListResponse(BaseModel):
    tracks: List[Dict[str, Any]]


def _get_project_audio_dir(project_id: int) -> Path:
    """Get or create audio storage directory for a project."""
    path = Path(settings.storage_path) / "projects" / str(project_id) / "audio"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _analyze_track_bg(track_id: int):
    """Background task to analyze an audio track."""
    db = None
    start_time = time.time()
    try:
        from backend.db.database import SessionLocal
        db = SessionLocal()
        
        track = db.query(models.AudioTrack).filter(models.AudioTrack.id == track_id).first()
        if not track:
            return
        
        track.status = "analyzing"
        db.commit()
        
        audio_dir = _get_project_audio_dir(track.project_id)
        file_path = audio_dir / track.filename
        
        if not file_path.exists():
            track.status = "failed"
            db.commit()
            duration_ms = int((time.time() - start_time) * 1000)
            log_job_event(
                job_type='audio_analysis',
                job_id=track_id,
                user_id=track.user_id,
                project_id=track.project_id,
                status='failed',
                duration_ms=duration_ms,
                error_message='Audio file not found'
            )
            return
        
        analysis_data = analyze_audio(file_path)
        
        # Update track duration
        track.duration_seconds = analysis_data["duration_seconds"]
        track.status = "analyzed"
        
        # Save analysis
        analysis = models.AudioAnalysis(
            track_id=track.id,
            bpm=analysis_data.get("bpm"),
            musical_key=analysis_data.get("musical_key"),
            duration_seconds=analysis_data["duration_seconds"],
            loudness_lufs=analysis_data.get("loudness_lufs"),
            sample_rate=analysis_data.get("sample_rate"),
            channels=analysis_data.get("channels"),
            bit_depth=analysis_data.get("bit_depth"),
        )
        db.add(analysis)
        db.commit()
        
        duration_ms = int((time.time() - start_time) * 1000)
        log_job_event(
            job_type='audio_analysis',
            job_id=track_id,
            user_id=track.user_id,
            project_id=track.project_id,
            status='completed',
            duration_ms=duration_ms,
            metadata={'bpm': analysis_data.get('bpm'), 'key': analysis_data.get('musical_key')}
        )
        
    except Exception as e:
        if db and track:
            track.status = "failed"
            db.commit()
            duration_ms = int((time.time() - start_time) * 1000)
            log_job_event(
                job_type='audio_analysis',
                job_id=track_id,
                user_id=track.user_id,
                project_id=track.project_id,
                status='failed',
                duration_ms=duration_ms,
                error_message=str(e)
            )
        logger.exception(f"Failed to analyze track {track_id}: {e}")
    finally:
        if db:
            db.close()


@router.post("/projects/{project_id}/audio", response_model=TrackUploadResponse, status_code=201)
async def upload_audio_to_project(
    project_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user: models.User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Upload an audio file to a project and trigger analysis."""
    
    # Verify project ownership
    project = db.query(models.Project).filter(
        models.Project.id == project_id,
        models.Project.user_id == user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")
    
    # Read and validate size
    content = await file.read()
    if len(content) > MAX_AUDIO_SIZE:
        raise HTTPException(status_code=413, detail="File exceeds 100 MB limit")
    
    # Generate unique filename
    unique_name = f"{secrets.token_hex(8)}{ext}"
    audio_dir = _get_project_audio_dir(project_id)
    file_path = audio_dir / unique_name
    
    # Save file
    file_path.write_bytes(content)
    
    # Create track record
    track = models.AudioTrack(
        project_id=project_id,
        user_id=user.id,
        filename=unique_name,
        original_filename=file.filename,
        file_size=len(content),
        status="uploaded"
    )
    db.add(track)
    db.commit()
    db.refresh(track)
    
    # Trigger analysis in background
    background_tasks.add_task(_analyze_track_bg, track.id)
    
    log_audit_event(
        event_type='audio',
        user_id=user.id,
        project_id=project_id,
        resource_type='track',
        resource_id=track.id,
        action='uploaded',
        details={'filename': file.filename, 'size_bytes': len(content)}
    )
    
    return TrackUploadResponse(
        id=track.id,
        project_id=track.project_id,
        filename=track.filename,
        original_filename=track.original_filename,
        file_size=track.file_size,
        status=track.status,
        created_at=track.created_at
    )


@router.get("/projects/{project_id}/audio", response_model=TrackListResponse)
def list_project_audio(
    project_id: int,
    user: models.User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """List all audio tracks for a project."""
    
    # Verify project ownership
    project = db.query(models.Project).filter(
        models.Project.id == project_id,
        models.Project.user_id == user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    tracks = db.query(models.AudioTrack).filter(
        models.AudioTrack.project_id == project_id
    ).order_by(models.AudioTrack.created_at.desc()).all()
    
    result = []
    for track in tracks:
        track_data = {
            "id": track.id,
            "filename": track.filename,
            "original_filename": track.original_filename,
            "file_size": track.file_size,
            "duration_seconds": track.duration_seconds,
            "status": track.status,
            "created_at": track.created_at,
        }

        stems = db.query(models.AudioStem).filter(
            models.AudioStem.source_track_id == track.id,
            models.AudioStem.project_id == project_id,
        ).order_by(models.AudioStem.created_at.asc()).all()
        if stems:
            track_data["stems"] = [
                {
                    "id": stem.id,
                    "stem_type": stem.stem_type,
                }
                for stem in stems
            ]
        
        # Include analysis if available
        analysis = db.query(models.AudioAnalysis).filter(
            models.AudioAnalysis.track_id == track.id
        ).first()
        if analysis:
            track_data["analysis"] = {
                "bpm": analysis.bpm,
                "musical_key": analysis.musical_key,
                "loudness_lufs": analysis.loudness_lufs,
                "sample_rate": analysis.sample_rate,
                "channels": analysis.channels,
            }
        
        result.append(track_data)
    
    return TrackListResponse(tracks=result)


def _process_audio_bg(processing_id: int):
    """Background task to process audio (mix or master)."""
    db = None
    start_time = time.time()
    try:
        from backend.db.database import SessionLocal
        db = SessionLocal()
        
        processing = db.query(models.AudioProcessing).filter(
            models.AudioProcessing.id == processing_id
        ).first()
        if not processing:
            return
        
        processing.status = "processing"
        db.commit()
        
        track = db.query(models.AudioTrack).filter(
            models.AudioTrack.id == processing.track_id
        ).first()
        if not track:
            processing.status = "failed"
            processing.error_message = "Track not found"
            db.commit()
            duration_ms = int((time.time() - start_time) * 1000)
            log_job_event(
                job_type=processing.process_type,
                job_id=processing_id,
                user_id=None,
                project_id=None,
                status='failed',
                duration_ms=duration_ms,
                error_message='Track not found'
            )
            return
        
        audio_dir = _get_project_audio_dir(track.project_id)
        input_path = audio_dir / track.filename
        
        if not input_path.exists():
            processing.status = "failed"
            processing.error_message = "Input file not found"
            db.commit()
            duration_ms = int((time.time() - start_time) * 1000)
            log_job_event(
                job_type=processing.process_type,
                job_id=processing_id,
                user_id=track.user_id,
                project_id=track.project_id,
                status='failed',
                duration_ms=duration_ms,
                error_message='Input file not found'
            )
            return
        
        # Generate output filename
        output_name = f"{secrets.token_hex(8)}_{processing.process_type}.wav"
        output_path = audio_dir / output_name
        
        # Process based on type
        if processing.process_type == "mix":
            mix_audio(input_path, output_path)
            track.status = "mixed"
        elif processing.process_type == "master":
            mp3_name = output_name.replace(".wav", ".mp3")
            mp3_path = audio_dir / mp3_name
            master_audio(input_path, output_path, mp3_path)
            track.status = "mastered"
        
        processing.output_filename = output_name
        processing.status = "completed"
        processing.completed_at = datetime.utcnow()
        
        db.add(track)
        db.commit()
        
        duration_ms = int((time.time() - start_time) * 1000)
        log_job_event(
            job_type=processing.process_type,
            job_id=processing_id,
            user_id=track.user_id,
            project_id=track.project_id,
            status='completed',
            duration_ms=duration_ms,
            metadata={'output_file': output_name}
        )
        
    except Exception as e:
        if db and processing:
            processing.status = "failed"
            processing.error_message = str(e)[:500]
            db.commit()
            duration_ms = int((time.time() - start_time) * 1000)
            log_job_event(
                job_type=processing.process_type,
                job_id=processing_id,
                user_id=track.user_id if track else None,
                project_id=track.project_id if track else None,
                status='failed',
                duration_ms=duration_ms,
                error_message=str(e)
            )
        logger.exception(f"Failed to process audio {processing_id}: {e}")
    finally:
        if db:
            db.close()


@router.post("/audio/{track_id}/mix", response_model=ProcessingResponse, status_code=202)
def trigger_mix(
    track_id: int,
    background_tasks: BackgroundTasks,
    user: models.User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Trigger automated mixing for an audio track."""
    
    track = db.query(models.AudioTrack).filter(
        models.AudioTrack.id == track_id,
        models.AudioTrack.user_id == user.id
    ).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    if track.status not in ["analyzed", "mixed", "mastered"]:
        raise HTTPException(status_code=400, detail="Track must be analyzed first")
    
    # Create processing job
    processing = models.AudioProcessing(
        track_id=track.id,
        process_type="mix",
        status="pending"
    )
    db.add(processing)
    db.commit()
    db.refresh(processing)
    
    # Trigger processing
    background_tasks.add_task(_process_audio_bg, processing.id)
    
    return ProcessingResponse(
        id=processing.id,
        track_id=processing.track_id,
        process_type=processing.process_type,
        status=processing.status,
        output_filename=processing.output_filename,
        created_at=processing.created_at,
        completed_at=processing.completed_at
    )


@router.post("/audio/{track_id}/master", response_model=ProcessingResponse, status_code=202)
def trigger_master(
    track_id: int,
    background_tasks: BackgroundTasks,
    user: models.User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Trigger automated mastering for an audio track."""
    
    track = db.query(models.AudioTrack).filter(
        models.AudioTrack.id == track_id,
        models.AudioTrack.user_id == user.id
    ).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    if track.status not in ["analyzed", "mixed", "mastered"]:
        raise HTTPException(status_code=400, detail="Track must be analyzed first")
    
    # Create processing job
    processing = models.AudioProcessing(
        track_id=track.id,
        process_type="master",
        status="pending"
    )
    db.add(processing)
    db.commit()
    db.refresh(processing)
    
    # Trigger processing
    background_tasks.add_task(_process_audio_bg, processing.id)
    
    return ProcessingResponse(
        id=processing.id,
        track_id=processing.track_id,
        process_type=processing.process_type,
        status=processing.status,
        output_filename=processing.output_filename,
        created_at=processing.created_at,
        completed_at=processing.completed_at
    )


from fastapi.responses import FileResponse


@router.get("/audio/download/{track_id}/{process_type}")
def download_processed_audio(
    track_id: int,
    process_type: str,
    user: models.User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Download processed audio file."""
    
    track = db.query(models.AudioTrack).filter(
        models.AudioTrack.id == track_id,
        models.AudioTrack.user_id == user.id
    ).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    processing = db.query(models.AudioProcessing).filter(
        models.AudioProcessing.track_id == track_id,
        models.AudioProcessing.process_type == process_type,
        models.AudioProcessing.status == "completed"
    ).order_by(models.AudioProcessing.completed_at.desc()).first()
    
    if not processing or not processing.output_filename:
        raise HTTPException(status_code=404, detail="Processed file not found")
    
    audio_dir = _get_project_audio_dir(track.project_id)
    file_path = audio_dir / processing.output_filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(
        path=str(file_path),
        filename=f"{track.original_filename}_{process_type}{file_path.suffix}",
        media_type="application/octet-stream"
    )


@router.get("/audio/{track_id}/source/download")
def download_source_audio(
    track_id: int,
    user: models.User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Download the original source audio for a track (JWT-only)."""

    track = db.query(models.AudioTrack).filter(
        models.AudioTrack.id == track_id,
        models.AudioTrack.user_id == user.id
    ).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")

    audio_dir = _get_project_audio_dir(track.project_id)
    file_path = audio_dir / track.filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        path=str(file_path),
        filename=track.original_filename,
        media_type="application/octet-stream"
    )
