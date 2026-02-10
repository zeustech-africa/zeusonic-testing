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
from backend.services.audio_transformer import SUPPORTED_STYLES
from backend.api.v1.audio_transform import _transform_bg
from backend.api.v1.audio_tracks import _analyze_track_bg, _process_audio_bg

router = APIRouter(tags=["ai-commands"])


class AICommandResponse(BaseModel):
    job_id: str
    status: str
    ai_engine_pending: bool = False
    detail: Optional[str] = None
    download_url: Optional[str] = None
    stems: Optional[dict[str, str]] = None


class AIAnalyzeTrackRequest(BaseModel):
    project_id: int
    track_id: int


class AISplitStemsRequest(BaseModel):
    project_id: int
    track_id: int


class AITransformStyleRequest(BaseModel):
    project_id: int
    track_id: int
    style: str
    intensity: int = Field(ge=0, le=100)
    preserve_rhythm: bool = True


class AIAddInstrumentRequest(BaseModel):
    project_id: Optional[int] = None
    track_id: int
    instrument: str
    mood: Optional[str] = None
    blend: Optional[int] = Field(default=None, ge=0, le=100)
    intensity: Optional[float] = Field(default=None, ge=0, le=100)


class AIMixAdjustRequest(BaseModel):
    project_id: Optional[int] = None
    track_id: int
    bass: int = Field(ge=0, le=100)
    treble: int = Field(ge=0, le=100)
    vocal_presence: Optional[int] = Field(default=None, ge=0, le=100)
    vocals: Optional[float] = Field(default=None, ge=0, le=100)
    stereo_width: Optional[int] = Field(default=None, ge=0, le=100)


class AIExportTrackRequest(BaseModel):
    project_id: int
    track_id: int


class AISimpleAnalyzeRequest(BaseModel):
    track_id: int


class AISimpleSeparateRequest(BaseModel):
    track_id: int


class AISimpleStyleTransferRequest(BaseModel):
    track_id: int
    style: str
    reference_audio: Optional[int] = None


class AISimpleAddInstrumentRequest(BaseModel):
    track_id: int
    instrument: str
    intensity: float = Field(ge=0, le=100)


class AISimpleMixAdjustRequest(BaseModel):
    track_id: int
    bass: float = Field(ge=0, le=100)
    treble: float = Field(ge=0, le=100)
    vocals: float = Field(ge=0, le=100)


class AISimpleExportRequest(BaseModel):
    track_id: int


def _get_track(db: Session, user: models.User, project_id: int, track_id: int) -> models.AudioTrack:
    track = db.query(models.AudioTrack).filter(
        models.AudioTrack.id == track_id,
        models.AudioTrack.project_id == project_id,
        models.AudioTrack.user_id == user.id,
    ).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    return track


def _get_track_by_id(db: Session, user: models.User, track_id: int) -> models.AudioTrack:
    track = db.query(models.AudioTrack).filter(
        models.AudioTrack.id == track_id,
        models.AudioTrack.user_id == user.id,
    ).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    return track


@router.post("/ai/analyze-track", response_model=AICommandResponse, status_code=202)
def analyze_track(
    payload: AIAnalyzeTrackRequest,
    background_tasks: BackgroundTasks,
    user: models.User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    track = _get_track(db, user, payload.project_id, payload.track_id)
    job_id = str(uuid4())

    background_tasks.add_task(_analyze_track_bg, track.id)

    log_audit_event(
        event_type="ai_command",
        user_id=user.id,
        project_id=payload.project_id,
        resource_type="track",
        resource_id=track.id,
        action="analyze",
        details={"job_id": job_id},
    )

    return AICommandResponse(job_id=job_id, status="queued", detail="Analysis queued")


@router.post("/ai/split-stems", response_model=AICommandResponse, status_code=202)
def split_stems(
    payload: AISplitStemsRequest,
    user: models.User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    track = _get_track(db, user, payload.project_id, payload.track_id)
    job_id = str(uuid4())

    log_audit_event(
        event_type="ai_command",
        user_id=user.id,
        project_id=payload.project_id,
        resource_type="track",
        resource_id=track.id,
        action="split_stems",
        details={"job_id": job_id},
    )

    return AICommandResponse(
        job_id=job_id,
        status="queued",
        ai_engine_pending=True,
        detail="AI Engine connected — execution coming next",
    )


@router.post("/ai/transform-style", response_model=AICommandResponse, status_code=202)
def transform_style(
    payload: AITransformStyleRequest,
    background_tasks: BackgroundTasks,
    user: models.User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    target_style = payload.style.strip().lower()
    if target_style not in SUPPORTED_STYLES:
        raise HTTPException(status_code=400, detail="Unsupported target style")

    track = _get_track(db, user, payload.project_id, payload.track_id)

    job = models.BeatTransformJob(
        track_id=track.id,
        source_style="unknown",
        target_style=target_style,
        status="pending",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(_transform_bg, job.id)

    log_audit_event(
        event_type="ai_command",
        user_id=user.id,
        project_id=payload.project_id,
        resource_type="track",
        resource_id=track.id,
        action="transform_style",
        details={
            "job_id": str(job.id),
            "style": target_style,
            "intensity": payload.intensity,
            "preserve_rhythm": payload.preserve_rhythm,
        },
    )

    return AICommandResponse(job_id=str(job.id), status="queued", detail="Style transform queued")


@router.post("/ai/add-instrument", response_model=AICommandResponse, status_code=202)
def add_instrument(
    payload: AIAddInstrumentRequest,
    user: models.User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    if payload.project_id is not None:
        track = _get_track(db, user, payload.project_id, payload.track_id)
    else:
        track = _get_track_by_id(db, user, payload.track_id)
    job_id = str(uuid4())
    intensity_value = payload.blend if payload.blend is not None else (payload.intensity or 50)

    log_audit_event(
        event_type="ai_command",
        user_id=user.id,
        project_id=track.project_id,
        resource_type="track",
        resource_id=track.id,
        action="add_instrument",
        details={
            "job_id": job_id,
            "instrument": payload.instrument,
            "mood": payload.mood,
            "intensity": intensity_value,
        },
    )

    return AICommandResponse(
        job_id=job_id,
        status="completed",
        detail="Instrument blend mocked (passthrough)",
        download_url=f"/api/v1/audio/{track.id}/source/download",
    )


@router.post("/ai/mix-adjust", response_model=AICommandResponse, status_code=202)
def mix_adjust(
    payload: AIMixAdjustRequest,
    background_tasks: BackgroundTasks,
    user: models.User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    if payload.project_id is not None:
        track = _get_track(db, user, payload.project_id, payload.track_id)
    else:
        track = _get_track_by_id(db, user, payload.track_id)
    job_id = str(uuid4())
    vocal_value = payload.vocal_presence if payload.vocal_presence is not None else (payload.vocals or 50)

    processing = models.AudioProcessing(
        track_id=track.id,
        process_type="mix",
        status="pending",
    )
    db.add(processing)
    db.commit()
    db.refresh(processing)

    background_tasks.add_task(_process_audio_bg, processing.id)

    log_audit_event(
        event_type="ai_command",
        user_id=user.id,
        project_id=payload.project_id,
        resource_type="track",
        resource_id=track.id,
        action="mix_adjust",
        details={
            "job_id": job_id,
            "bass": payload.bass,
            "treble": payload.treble,
            "vocal_presence": vocal_value,
            "stereo_width": payload.stereo_width,
        },
    )

    return AICommandResponse(job_id=job_id, status="queued", detail="Mix adjustment queued")


@router.post("/ai/export-track", response_model=AICommandResponse, status_code=202)
def export_track(
    payload: AIExportTrackRequest,
    background_tasks: BackgroundTasks,
    user: models.User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    track = _get_track(db, user, payload.project_id, payload.track_id)
    job_id = str(uuid4())

    if track.status == "mastered":
        return AICommandResponse(
            job_id=job_id,
            status="completed",
            detail="Master ready",
            download_url=f"/api/v1/audio/download/{track.id}/master",
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

    return AICommandResponse(job_id=job_id, status="queued", detail="Export queued")


@router.post("/ai/analyze", response_model=AICommandResponse, status_code=202)
def analyze_track_simple(
    payload: AISimpleAnalyzeRequest,
    background_tasks: BackgroundTasks,
    user: models.User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    track = _get_track_by_id(db, user, payload.track_id)
    job_id = str(uuid4())

    background_tasks.add_task(_analyze_track_bg, track.id)

    log_audit_event(
        event_type="ai_command",
        user_id=user.id,
        project_id=track.project_id,
        resource_type="track",
        resource_id=track.id,
        action="analyze",
        details={"job_id": job_id},
    )

    return AICommandResponse(job_id=job_id, status="queued", detail="Analysis queued")


@router.post("/ai/separate", response_model=AICommandResponse, status_code=202)
def separate_stems_simple(
    payload: AISimpleSeparateRequest,
    user: models.User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    track = _get_track_by_id(db, user, payload.track_id)
    job_id = str(uuid4())

    stems_payload = {
        "vocals": f"/api/v1/audio/{track.id}/source/download",
        "drums": f"/api/v1/audio/{track.id}/source/download",
        "bass": f"/api/v1/audio/{track.id}/source/download",
        "instruments": f"/api/v1/audio/{track.id}/source/download",
    }

    log_audit_event(
        event_type="ai_command",
        user_id=user.id,
        project_id=track.project_id,
        resource_type="track",
        resource_id=track.id,
        action="separate_stems",
        details={"job_id": job_id},
    )

    return AICommandResponse(
        job_id=job_id,
        status="completed",
        detail="Stem separation mocked (passthrough)",
        download_url=f"/api/v1/audio/{track.id}/source/download",
        stems=stems_payload,
    )


@router.post("/ai/style-transfer", response_model=AICommandResponse, status_code=202)
def style_transfer_simple(
    payload: AISimpleStyleTransferRequest,
    background_tasks: BackgroundTasks,
    user: models.User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    track = _get_track_by_id(db, user, payload.track_id)
    job_id = str(uuid4())
    target_style = payload.style.strip().lower()

    if target_style in SUPPORTED_STYLES:
        job = models.BeatTransformJob(
            track_id=track.id,
            source_style="unknown",
            target_style=target_style,
            status="pending",
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        background_tasks.add_task(_transform_bg, job.id)

        log_audit_event(
            event_type="ai_command",
            user_id=user.id,
            project_id=track.project_id,
            resource_type="track",
            resource_id=track.id,
            action="style_transfer",
            details={
                "job_id": str(job.id),
                "style": target_style,
                "reference_audio": payload.reference_audio,
            },
        )

        return AICommandResponse(job_id=str(job.id), status="queued", detail="Style transfer queued")

    log_audit_event(
        event_type="ai_command",
        user_id=user.id,
        project_id=track.project_id,
        resource_type="track",
        resource_id=track.id,
        action="style_transfer",
        details={
            "job_id": job_id,
            "style": target_style,
            "reference_audio": payload.reference_audio,
            "mocked": True,
        },
    )

    return AICommandResponse(
        job_id=job_id,
        status="completed",
        detail="Style transfer mocked (passthrough)",
        download_url=f"/api/v1/audio/{track.id}/source/download",
    )




@router.post("/ai/export", response_model=AICommandResponse, status_code=202)
def export_track_simple(
    payload: AISimpleExportRequest,
    background_tasks: BackgroundTasks,
    user: models.User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    track = _get_track_by_id(db, user, payload.track_id)
    job_id = str(uuid4())

    if track.status == "mastered":
        return AICommandResponse(
            job_id=job_id,
            status="completed",
            detail="Master ready",
            download_url=f"/api/v1/audio/download/{track.id}/master",
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

    return AICommandResponse(job_id=job_id, status="queued", detail="Export queued")
