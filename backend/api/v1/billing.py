from datetime import datetime
from typing import Literal, Optional

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.auth import get_current_verified_user
from core.config import settings
from core.features import get_entitlements
from db import models
from db.database import get_db
from core.observability import log_audit_event
from core.logging import get_logger

router = APIRouter(tags=["billing"])
logger = get_logger(__name__)


class CheckoutRequest(BaseModel):
    plan: Literal["monthly", "yearly"]


class CheckoutResponse(BaseModel):
    url: str


class BillingStatusResponse(BaseModel):
    tier: str
    subscription_status: Optional[str]
    current_period_end: Optional[datetime]
    entitlements: dict


def _get_stripe_price_id(plan: str) -> str:
    if plan == "monthly":
        if not settings.stripe_monthly_price_id:
            raise HTTPException(status_code=500, detail="Stripe monthly price ID not configured")
        return settings.stripe_monthly_price_id
    if plan == "yearly":
        if not settings.stripe_yearly_price_id:
            raise HTTPException(status_code=500, detail="Stripe yearly price ID not configured")
        return settings.stripe_yearly_price_id
    raise HTTPException(status_code=400, detail="Invalid plan")


@router.post("/billing/checkout", response_model=CheckoutResponse)
def create_checkout_session(
    payload: CheckoutRequest,
    user: models.User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=500, detail="Stripe secret key not configured")

    stripe.api_key = settings.stripe_secret_key
    price_id = _get_stripe_price_id(payload.plan)

    plan = db.query(models.Plan).filter(models.Plan.code == "PRO").first()
    if not plan:
        raise HTTPException(status_code=500, detail="Pro plan not configured")

    existing_sub = (
        db.query(models.Subscription)
        .filter(models.Subscription.user_id == user.id)
        .order_by(models.Subscription.created_at.desc())
        .first()
    )
    customer_id = existing_sub.stripe_customer_id if existing_sub else None

    success_url = f"{settings.frontend_base_url}/billing/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{settings.frontend_base_url}/billing/cancel"

    session_params = {
        "mode": "subscription",
        "payment_method_types": ["card"],
        "line_items": [{"price": price_id, "quantity": 1}],
        "success_url": success_url,
        "cancel_url": cancel_url,
        "client_reference_id": str(user.id),
        "metadata": {
            "user_id": str(user.id),
            "plan_code": plan.code,
            "interval": payload.plan,
        },
    }

    if customer_id:
        session_params["customer"] = customer_id
    else:
        session_params["customer_email"] = user.email

    session = stripe.checkout.Session.create(**session_params)
    return CheckoutResponse(url=session.url)


@router.post("/billing/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    if not settings.stripe_webhook_secret or not settings.stripe_secret_key:
        raise HTTPException(status_code=500, detail="Stripe webhook not configured")

    stripe.api_key = settings.stripe_secret_key
    payload = await request.body()
    signature = request.headers.get("stripe-signature")
    if not signature:
        raise HTTPException(status_code=400, detail="Missing Stripe signature")

    try:
        event = stripe.Webhook.construct_event(payload, signature, settings.stripe_webhook_secret)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")

    # Idempotency check
    existing = db.query(models.StripeEvent).filter(models.StripeEvent.event_id == event.id).first()
    if existing:
        return {"received": True}

    db.add(models.StripeEvent(event_id=event.id, event_type=event.type))
    db.commit()

    if event.type == "checkout.session.completed":
        session = event.data.object
        _handle_checkout_completed(session, db)
    elif event.type == "invoice.payment_succeeded":
        invoice = event.data.object
        _handle_payment_succeeded(invoice, db)
    elif event.type == "customer.subscription.deleted":
        subscription = event.data.object
        _handle_subscription_deleted(subscription, db)

    return {"received": True}


@router.get("/billing/status", response_model=BillingStatusResponse)
def billing_status(user: models.User = Depends(get_current_verified_user), db: Session = Depends(get_db)):
    ent = get_entitlements(user.email, user.tier, user_id=user.id)
    tier = ent.get("plan_code") or user.tier or "FREE"

    sub = (
        db.query(models.Subscription)
        .filter(models.Subscription.user_id == user.id)
        .order_by(models.Subscription.created_at.desc())
        .first()
    )

    return BillingStatusResponse(
        tier=tier,
        subscription_status=sub.status if sub else None,
        current_period_end=sub.current_period_end if sub else None,
        entitlements=ent.get("entitlements") or {},
    )


def _handle_checkout_completed(session, db: Session) -> None:
    subscription_id = session.get("subscription")
    customer_id = session.get("customer")
    user_id = session.get("client_reference_id") or session.get("metadata", {}).get("user_id")
    if not user_id or not subscription_id:
        return

    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if not user:
        return

    stripe_sub = stripe.Subscription.retrieve(subscription_id)
    plan = db.query(models.Plan).filter(models.Plan.code == "PRO").first()
    if not plan:
        return

    current_period_end = datetime.utcfromtimestamp(stripe_sub["current_period_end"]) if stripe_sub.get("current_period_end") else None

    sub = (
        db.query(models.Subscription)
        .filter(models.Subscription.stripe_subscription_id == subscription_id)
        .first()
    )
    if not sub:
        sub = models.Subscription(
            owner=user.email,
            user_id=user.id,
            stripe_customer_id=customer_id,
            stripe_subscription_id=subscription_id,
            plan_id=plan.id,
            plan_code=plan.code,
            status=stripe_sub.get("status", "active"),
            current_period_end=current_period_end,
        )
        db.add(sub)
    else:
        sub.owner = user.email
        sub.user_id = user.id
        sub.stripe_customer_id = customer_id
        sub.plan_id = plan.id
        sub.plan_code = plan.code
        sub.status = stripe_sub.get("status", sub.status)
        sub.current_period_end = current_period_end
        db.add(sub)

    if sub.status in ("active", "trialing", "past_due"):
        user.tier = "PRO"
        db.add(user)

    db.commit()

    log_audit_event(
        event_type='subscription',
        user_id=user.id,
        project_id=None,
        resource_type='subscription',
        resource_id=sub.id,
        action='created',
        details={'plan_code': plan.code, 'stripe_subscription_id': subscription_id}
    )


def _handle_payment_succeeded(invoice, db: Session) -> None:
    subscription_id = invoice.get("subscription")
    if not subscription_id:
        return

    stripe_sub = stripe.Subscription.retrieve(subscription_id)
    current_period_end = datetime.utcfromtimestamp(stripe_sub["current_period_end"]) if stripe_sub.get("current_period_end") else None

    sub = db.query(models.Subscription).filter(models.Subscription.stripe_subscription_id == subscription_id).first()
    if not sub:
        return

    sub.status = stripe_sub.get("status", "active")
    sub.current_period_end = current_period_end
    db.add(sub)

    user = db.query(models.User).filter(models.User.id == sub.user_id).first()
    if user and sub.status in ("active", "trialing", "past_due"):
        user.tier = "PRO"
        db.add(user)

    db.commit()


def _handle_subscription_deleted(subscription, db: Session) -> None:
    subscription_id = subscription.get("id")
    if not subscription_id:
        return

    current_period_end = datetime.utcfromtimestamp(subscription["current_period_end"]) if subscription.get("current_period_end") else None

    sub = db.query(models.Subscription).filter(models.Subscription.stripe_subscription_id == subscription_id).first()
    if not sub:
        return

    sub.status = "canceled"
    sub.current_period_end = current_period_end
    db.add(sub)

    user = db.query(models.User).filter(models.User.id == sub.user_id).first()
    if user and current_period_end and current_period_end <= datetime.utcnow():
        user.tier = "FREE"
        db.add(user)

    db.commit()
