from __future__ import annotations

from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.core.auth import get_current_verified_user
from backend.core.observability import log_audit_event
from backend.db import models
from backend.db.database import get_db
from backend.api.v1.audio_tracks import _analyze_track_bg, _process_audio_bg, _get_project_audio_dir
from backend.api.v1.audio_transform import SUPPORTED_STYLES, analyze_rhythm, _transform_bg

router = APIRouter(tags=["ai-commands"])


class AIAnalyzeRequest(BaseModel):
    project_id: int
    track_id: int


class AITransformRequest(BaseModel):
    project_id: int
    track_id: int
    style: str
    mood: str
    tempo_bias: int = Field(ge=-20, le=20)
    energy: int = Field(ge=0, le=100)


class AIMixAdjustRequest(BaseModel):
    project_id: int
    track_id: int
    bass: int = Field(ge=0, le=100)
    treble: int = Field(ge=0, le=100)
    presence: int = Field(ge=0, le=100)
    width: int = Field(ge=0, le=100)


class AIInstrumentAddRequest(BaseModel):
    project_id: int
    track_id: int
    instrument_type: str
    intensity: int = Field(ge=0, le=100)
    placement: str = "auto"


class AIExportRequest(BaseModel):
    project_id: int
    track_id: int


class AICommandResponse(BaseModel):
    command_id: str
    status: str
    detail: Optional[str] = None
    job_id: Optional[int] = None
    download_url: Optional[str] = None


class AITransformResponse(AICommandResponse):
    transform_job_id: Optional[int] = None


def _get_track(db: Session, user: models.User, project_id: int, track_id: int) -> models.AudioTrack:
    track = db.query(models.AudioTrack).filter(
        models.AudioTrack.id == track_id,
        models.AudioTrack.project_id == project_id,
        models.AudioTrack.user_id == user.id,
    ).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    return track


@router.post("/ai/analyze", response_model=AICommandResponse, status_code=202)
def ai_analyze(
    payload: AIAnalyzeRequest,
    background_tasks: BackgroundTasks,
    user: models.User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    track = _get_track(db, user, payload.project_id, payload.track_id)
    command_id = str(uuid4())

    if track.status != "analyzing":
        track.status = "analyzing"
        db.add(track)
        db.commit()

    background_tasks.add_task(_analyze_track_bg, track.id)

    log_audit_event(
        event_type="ai_command",
        user_id=user.id,
        project_id=payload.project_id,
        resource_type="track",
        resource_id=track.id,
        action="analyze",
        details={"command_id": command_id},
    )

    return AICommandResponse(
        command_id=command_id,
        status="queued",
        detail="Analysis queued",
        job_id=track.id,
    )


@router.post("/ai/transform", response_model=AITransformResponse, status_code=202)
def ai_transform(
    payload: AITransformRequest,
    background_tasks: BackgroundTasks,
    user: models.User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    target_style = payload.style.strip().lower()
    if target_style not in SUPPORTED_STYLES:
        raise HTTPException(status_code=400, detail="Unsupported target style")

    track = _get_track(db, user, payload.project_id, payload.track_id)

    source_style = "unknown"
    try:
        audio_dir = _get_project_audio_dir(track.project_id)
        input_path = audio_dir / track.filename
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

    background_tasks.add_task(_transform_bg, job.id)

    command_id = str(uuid4())
    log_audit_event(
        event_type="ai_command",
        user_id=user.id,
        project_id=payload.project_id,
        resource_type="track",
        resource_id=track.id,
        action="transform",
        details={
            "command_id": command_id,
            "style": target_style,
            "mood": payload.mood,
            "tempo_bias": payload.tempo_bias,
            "energy": payload.energy,
        },
    )

    return AITransformResponse(
        command_id=command_id,
        status="queued",
        detail="Transform queued",
        job_id=job.id,
        transform_job_id=job.id,
    )


@router.post("/ai/mix-adjust", response_model=AICommandResponse, status_code=202)
def ai_mix_adjust(
    payload: AIMixAdjustRequest,
    background_tasks: BackgroundTasks,
    user: models.User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    track = _get_track(db, user, payload.project_id, payload.track_id)

    processing = models.AudioProcessing(
        track_id=track.id,
        process_type="mix",
        status="pending",
    )
    db.add(processing)
    db.commit()
    db.refresh(processing)

    background_tasks.add_task(_process_audio_bg, processing.id)

    command_id = str(uuid4())
    log_audit_event(
        event_type="ai_command",
        user_id=user.id,
        project_id=payload.project_id,
        resource_type="track",
        resource_id=track.id,
        action="mix_adjust",
        details={
            "command_id": command_id,
            "bass": payload.bass,
            "treble": payload.treble,
            "presence": payload.presence,
            "width": payload.width,
        },
    )

    return AICommandResponse(
        command_id=command_id,
        status="queued",
        detail="Mix adjustment queued",
        job_id=processing.id,
    )


@router.post("/ai/instrument-add", response_model=AICommandResponse, status_code=202)
def ai_instrument_add(
    payload: AIInstrumentAddRequest,
    user: models.User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    _get_track(db, user, payload.project_id, payload.track_id)
    command_id = str(uuid4())

    log_audit_event(
        event_type="ai_command",
        user_id=user.id,
        project_id=payload.project_id,
        resource_type="track",
        resource_id=payload.track_id,
        action="instrument_add",
        details={
            "command_id": command_id,
            "instrument_type": payload.instrument_type,
            "intensity": payload.intensity,
            "placement": payload.placement,
        },
    )

    return AICommandResponse(
        command_id=command_id,
        status="queued",
        detail="Instrument layer queued",
    )


@router.post("/ai/export", response_model=AICommandResponse, status_code=202)
def ai_export(
    payload: AIExportRequest,
    background_tasks: BackgroundTasks,
    user: models.User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    track = _get_track(db, user, payload.project_id, payload.track_id)

    if track.status == "mastered":
        return AICommandResponse(
            command_id=str(uuid4()),
            status="completed",
            detail="Master export ready",
            download_url=f"/api/v1/audio/download/{track.id}/master",
        )

    if track.status == "mixed":
        return AICommandResponse(
            command_id=str(uuid4()),
            status="completed",
            detail="Mix export ready",
            download_url=f"/api/v1/audio/download/{track.id}/mix",
        )

    processing = models.AudioProcessing(
        track_id=track.id,
        process_type="master",
        status="pending",
    )
    db.add(processing)
    db.commit()
    db.refresh(processing)

    background_tasks.add_task(_process_audio_bg, processing.id)

    return AICommandResponse(
        command_id=str(uuid4()),
        status="queued",
        detail="Export queued",
        job_id=processing.id,
    )
