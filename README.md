# Zeusonic 🚀

AI-powered audio & voice platform by ZeusTech.

## Backend smoke tests
Run the lightweight smoke tests to validate backend startup and routing:

1. Create a virtualenv and install dev deps (your environment may already have these):

   python -m venv .venv
   source .venv/bin/activate
   pip install -U pip
   pip install -r backend/requirements.txt  # ensure pytest and testclient are available

2. Run tests:

   cd zeusonic
   pytest -q tests/test_smoke.py

What these tests verify:
- `backend.main` imports cleanly and startup hooks run
- `/api/v1/health` returns 200
- Audio routes `/api/v1/audio/upload` and `/api/v1/audio/jobs` are registered (no 404)

Subscription & feature gating tests:
- `tests/test_features.py` — unit tests for feature gate matrix
- `tests/test_download_access.py` — asserts free users cannot download; paid users can
- `tests/test_job_limits.py` — asserts free user monthly limit enforcement

Subscription endpoints (dev):
- `GET /api/v1/subscription` — returns tier, features, and usage summary for the calling API key
- `POST /api/v1/admin/set-tier` — change another API key's tier (development-only; requires `settings.app_env == 'development'`)

Dev example: change a key's tier (development only)

1. Create or get an API key (e.g., demo key created at startup)
2. Call:
   POST /api/v1/admin/set-tier
   {
     "target_api_key": "<key-to-change>",
     "tier": "CREATOR"
   }
   Include `X-API-Key` header with a valid dev API key (server must be in development mode)

Note: These tests are fast, run locally, and do not require Docker.
