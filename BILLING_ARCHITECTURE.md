# Billing Architecture (Billing-Ready Data Models)

This document describes the new database-backed billing/entitlements model. This change enables server-authoritative entitlements without integrating payments yet.

Key Concepts
- Plan: Represents a published plan (FREE, CREATOR, PRO). Stores authoritative `features` as JSON and pricing fields for future billing integration.
- Subscription: Represents an account subscription to a Plan for an `owner` (matching `ApiKey.owner`). Tracks `status` (active, trialing, canceled, expired), start and end dates.
- Entitlements Resolution: The system resolves entitlements in the following order:
  1. If the `owner` has an active or trialing `Subscription` and it has not expired, entitlements are taken from the Plan.features (authoritative).
  2. Otherwise, fallback to the API key's `tier` and the in-memory `FEATURE_MATRIX` for backward compatibility.

Why no payments yet
- This initial iteration focuses on data modeling and server-authoritative entitlements to support QA, demos, and gating.
- Payment providers (Stripe, Apple/Google subscriptions) will integrate with the `Subscription` model in a future step.

How this enables future billing integrations
- Plans include `price_monthly` and `price_yearly` so a future payment system can map provider product IDs to plans.
- Subscriptions are owner-scoped and include `status` and `ends_at` so webhook-driven updates from payment providers can update the `Subscription` row and immediately affect entitlements.

Safety & Migration
- An Alembic migration is included that creates `plans` and `subscriptions` and seeds default plans. The migration is reversible and idempotent-safe for SQLite and similar databases.

Developer notes
- Admin tools exist (dev-only) to create/update subscriptions: `POST /api/v1/admin/set-subscription`.
- The public subscription introspection endpoint `GET /api/v1/subscription` now returns resolved entitlements and plan metadata so clients can rely on a single response shape.
