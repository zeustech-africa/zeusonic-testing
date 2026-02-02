from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.core.auth import get_current_verified_user
from backend.core.features import get_entitlements
from backend.db.database import get_db
from backend.db import models
from backend.core.observability import log_audit_event
from backend.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["projects"])


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    metadata: Optional[Dict[str, Any]] = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(BaseModel):
    projects: List[ProjectResponse]


def _enforce_project_limit(db: Session, user: models.User) -> None:
    ent = get_entitlements(user.email, user.tier, user_id=user.id)
    status = ent.get("status")
    paid = ent.get("plan_code") is not None and status in ("active", "trialing", "past_due", "canceled")

    limit = None
    if not paid:
        limit = 2
    else:
        limit = ent.get("entitlements", {}).get("max_projects_total")

    if limit is None:
        return

    count = db.query(models.Project).filter(models.Project.user_id == user.id).count()
    if count >= limit:
        raise HTTPException(
            status_code=403,
            detail="Free plan allows up to 2 projects. Upgrade to Pro to add more.",
        )


@router.post("/projects", response_model=ProjectResponse, status_code=201)
def create_project(payload: ProjectCreate, user: models.User = Depends(get_current_verified_user), db: Session = Depends(get_db)):
    _enforce_project_limit(db, user)

    project = models.Project(
        user_id=user.id,
        name=payload.name.strip(),
        meta=payload.metadata,
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    log_audit_event(
        event_type='project',
        user_id=user.id,
        project_id=project.id,
        resource_type='project',
        resource_id=project.id,
        action='created',
        details={'name': project.name}
    )

    return ProjectResponse(
        id=project.id,
        name=project.name,
        metadata=project.meta,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.get("/projects", response_model=ProjectListResponse)
def list_projects(user: models.User = Depends(get_current_verified_user), db: Session = Depends(get_db)):
    rows = db.query(models.Project).filter(models.Project.user_id == user.id).order_by(models.Project.created_at.desc()).all()
    return ProjectListResponse(
        projects=[
            ProjectResponse(
                id=row.id,
                name=row.name,
                metadata=row.meta,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
            for row in rows
        ]
    )
