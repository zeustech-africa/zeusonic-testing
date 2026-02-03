from typing import Dict, Any, Optional
from datetime import datetime

from db import models
from db.database import SessionLocal

# Centralized feature gate matrix (tier -> feature values)
# Values can be booleans or numeric limits
FEATURE_MATRIX: Dict[str, Dict[str, Any]] = {
    'FREE': {
        'can_download_audio': False,
        'can_export_stems': False,
        'max_job_duration_seconds': 30,  # simulated limit
        'max_jobs_per_month': 10,
        'max_projects_total': 2,
        'can_use_creator_voice': False,
        'can_change_vocal_tone': False,
        'can_use_advanced_beats': False,
    },
    'CREATOR': {
        'can_download_audio': True,
        'can_export_stems': True,
        'max_job_duration_seconds': 120,
        'max_jobs_per_month': 500,
        'max_projects_total': None,
        'can_use_creator_voice': True,
        'can_change_vocal_tone': True,
        'can_use_advanced_beats': True,
    },
    'PRO': {
        'can_download_audio': True,
        'can_export_stems': True,
        'max_job_duration_seconds': 600,
        'max_jobs_per_month': 5000,
        'max_projects_total': None,
        'can_use_creator_voice': True,
        'can_change_vocal_tone': True,
        'can_use_advanced_beats': True,
    },
}


def tier_has(feature: str, tier: str) -> bool:
    # Deprecated helper: use get_entitlements instead for authoritative checks
    return bool(FEATURE_MATRIX.get(tier, FEATURE_MATRIX['FREE']).get(feature, False))


def tier_limit(feature: str, tier: str) -> Any:
    # Deprecated helper: use get_entitlements instead for authoritative checks
    return FEATURE_MATRIX.get(tier, FEATURE_MATRIX['FREE']).get(feature)


def get_entitlements(owner: str, api_key_tier: str, user_id: Optional[int] = None) -> Dict[str, Any]:
    """Resolve the final entitlements for an owner.

    Precedence:
    1. If the owner has an active/trialing subscription (and not expired), return the Plan.features (authoritative) along with plan metadata and status.
    2. Else, fall back to the `api_key_tier` using `FEATURE_MATRIX`.
    """
    db = SessionLocal()
    try:
        query = db.query(models.Subscription).order_by(models.Subscription.created_at.desc())
        if user_id is not None:
            sub = query.filter(models.Subscription.user_id == user_id).first()
        else:
            sub = query.filter(models.Subscription.owner == owner).first()

        if sub:
            now = datetime.utcnow()
            period_end = sub.current_period_end or sub.ends_at
            status = (sub.status or "").lower()

            active_status = status in ("active", "trialing", "past_due")
            canceled_but_active = status == "canceled" and period_end and period_end > now

            if active_status or canceled_but_active:
                plan = None
                if sub.plan_id:
                    plan = db.query(models.Plan).filter(models.Plan.id == sub.plan_id).first()
                if not plan and sub.plan_code:
                    plan = db.query(models.Plan).filter(models.Plan.code == sub.plan_code).first()

                if plan:
                    return {
                        'plan_id': plan.id,
                        'plan_code': plan.code,
                        'plan_name': plan.name,
                        'status': sub.status,
                        'entitlements': plan.features,
                    }
    finally:
        db.close()

    # Fallback to API key tier
    features = FEATURE_MATRIX.get(api_key_tier, FEATURE_MATRIX['FREE'])
    return {
        'plan_code': None,
        'plan_name': None,
        'status': 'fallback',
        'entitlements': features,
    }
