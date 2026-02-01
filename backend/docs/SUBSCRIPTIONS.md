# Subscription & Feature Gating (Foundational)

This module introduces a minimal subscription tier and centralized feature gate system for Zeusonic.

Tiers
- FREE (default)
- CREATOR
- PRO

Feature matrix (see `backend/core/features.py`):
- can_download_audio (bool)
- can_export_stems (bool)
- max_job_duration_seconds (number)
- max_jobs_per_month (number)
- can_use_creator_voice (bool)
- can_change_vocal_tone (bool)
- can_use_advanced_beats (bool)

Enforcement points
- Download endpoint `/api/v1/audio/download/{job_id}` denies downloads for FREE with 403 and a clear message.
- Job creation (`/api/v1/audio/upload`) enforces `max_jobs_per_month` per API key owner (past 30 days).

Endpoints added in Phase 10B
- `GET /api/v1/subscription` — returns current tier, enabled features, numeric limits, and usage summary (jobs used in last 30 days).
- `POST /api/v1/admin/set-tier` — development-only endpoint to set the tier of an existing API key. Requires `settings.app_env == 'development'` and an authenticated API key to call. This endpoint is intended for testing and simulation only (no billing).
Storage & DB
- ApiKey model now stores `tier` (DEFAULT FREE)
- AudioJob model now stores `owner` (nullable) to attribute jobs to API key owners

Notes
- All checks are server-authoritative.
- Free users may still create jobs and have them processed, but some features (downloads) are gated.
- This is foundational and does not include payment or billing logic yet (Phase 10B).
