from fastapi import APIRouter, Depends, HTTPException
from core.config import settings
from core.auth import get_api_key
from db.database import SessionLocal
from db import models
from core.features import FEATURE_MATRIX, get_entitlements
from datetime import datetime, timedelta
from pydantic import BaseModel

router = APIRouter()


@router.get("/meta", tags=["meta"])
async def get_meta():
    """Return application metadata from settings."""
    return {
        "app_name": settings.app_name,
        "version": settings.version,
        "company": settings.company,
        "beta_mode": settings.beta_mode,
        "disable_uploads": settings.disable_uploads,
    }


@router.get('/subscription', tags=['subscription'])
async def get_subscription(api_key = Depends(get_api_key)):
    """Return the subscription info for the calling API key. This includes authoritative entitlements and usage summary."""
    tier = api_key.tier

    ent = get_entitlements(api_key.owner, tier)

    # Usage: jobs in past 30 days
    cutoff = datetime.utcnow() - timedelta(days=30)
    db = SessionLocal()
    try:
        used = db.query(models.AudioJob).filter(models.AudioJob.owner == api_key.owner, models.AudioJob.created_at >= cutoff).count()
    finally:
        db.close()

    return {
        'tier': tier,
        'plan_code': ent.get('plan_code'),
        'plan_name': ent.get('plan_name'),
        'status': ent.get('status'),
        'entitlements': ent.get('entitlements'),
        'usage': {
            'jobs_used_last_30_days': used,
            'jobs_limit': ent.get('entitlements', {}).get('max_jobs_per_month')
        }
    }


@router.get('/admin/ops', tags=['admin'])
async def admin_ops(api_key = Depends(get_api_key)):
    """Dev-only: Return current operational counters (in-memory)."""
    if settings.app_env != 'development':
        raise HTTPException(status_code=403, detail='Ops endpoint allowed only in development')

    from backend.core.ops import get_counters

    return get_counters()


class SetSubscriptionPayload(BaseModel):
    owner: str
    plan_code: str
    status: str = 'active'


@router.post('/admin/set-subscription', tags=['admin'])
async def admin_set_subscription(payload: SetSubscriptionPayload, api_key = Depends(get_api_key)):
    """Dev-only: Create or update a Subscription for an owner. Affects entitlements immediately."""
    if settings.app_env != 'development':
        raise HTTPException(status_code=403, detail='Admin subscription changes are allowed only in development')

    db = SessionLocal()
    try:
        plan = db.query(models.Plan).filter(models.Plan.code == payload.plan_code).first()
        if not plan:
            raise HTTPException(status_code=400, detail='Invalid plan code')

        sub = db.query(models.Subscription).filter(models.Subscription.owner == payload.owner).first()
        if not sub:
            sub = models.Subscription(owner=payload.owner, plan_code=payload.plan_code, status=payload.status)
            db.add(sub)
        else:
            sub.plan_code = payload.plan_code
            sub.status = payload.status
            db.add(sub)
        db.commit()
        db.refresh(sub)
    finally:
        db.close()

    return {
        'owner': payload.owner,
        'plan_code': payload.plan_code,
        'status': payload.status,
    }


@router.post('/admin/set-tier', tags=['admin'])
async def admin_set_tier(target_api_key: str, tier: str, api_key = Depends(get_api_key)):
    """Dev-only: Set the tier on another API key. Only allowed in development environment."""
    if settings.app_env != 'development':
        raise HTTPException(status_code=403, detail='Admin tier changes are allowed only in development')

    if tier not in FEATURE_MATRIX:
        raise HTTPException(status_code=400, detail='Invalid tier')

    db = SessionLocal()
    try:
        row = db.query(models.ApiKey).filter(models.ApiKey.key == target_api_key).first()
        if not row:
            raise HTTPException(status_code=404, detail='API key not found')
        old = row.tier
        row.tier = tier
        db.add(row)
        db.commit()
    finally:
        db.close()

    return {'key': target_api_key, 'old_tier': old, 'new_tier': tier}
