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
    # Internal AI disabled for external Mureka pivot.
    raise HTTPException(status_code=503, detail="Internal AI commands are disabled.")


@router.post("/ai/transform", response_model=AITransformResponse, status_code=202)
def ai_transform(
    payload: AITransformRequest,
    background_tasks: BackgroundTasks,
    user: models.User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    # Internal AI disabled for external Mureka pivot.
    raise HTTPException(status_code=503, detail="Internal AI commands are disabled.")


@router.post("/ai/mix-adjust", response_model=AICommandResponse, status_code=202)
def ai_mix_adjust(
    payload: AIMixAdjustRequest,
    background_tasks: BackgroundTasks,
    user: models.User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    # Internal AI disabled for external Mureka pivot.
    raise HTTPException(status_code=503, detail="Internal AI commands are disabled.")


@router.post("/ai/instrument-add", response_model=AICommandResponse, status_code=202)
def ai_instrument_add(
    payload: AIInstrumentAddRequest,
    user: models.User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    # Internal AI disabled for external Mureka pivot.
    raise HTTPException(status_code=503, detail="Internal AI commands are disabled.")


@router.post("/ai/export", response_model=AICommandResponse, status_code=202)
def ai_export(
    payload: AIExportRequest,
    background_tasks: BackgroundTasks,
    user: models.User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    # Internal AI disabled for external Mureka pivot.
    raise HTTPException(status_code=503, detail="Internal AI commands are disabled.")
