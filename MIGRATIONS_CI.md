# CI: migrations & tests

This repository enforces migrations and backend tests in CI via `.github/workflows/backend.yml`.

Quick summary:
- On pushes and pull requests touching `backend/` or migration files, CI performs a clean test run that:
  1. Installs backend dependencies from `backend/requirements.txt`.
  2. Ensures a clean SQLite DB file (removes `backend/storage/zeusonic.db` if present).
  3. Applies migrations: `alembic -c backend/alembic.ini upgrade head` (this will apply revisions including `0001_add_tier_and_owner` and `0002_add_plans_and_subscriptions`).
  4. Runs the full backend test suite: `pytest` (including migration tests).
- Failures in applying migrations or running tests will fail the CI job.

Notes:
- This workflow is intentionally lightweight and uses SQLite to keep run-time short. For integration testing on other DBs, add a separate workflow with the appropriate service containers.
- CI uses Python 3.11 to match the project's language features (PEP 604 `|` type unions are used in annotations). If you encounter local import errors related to annotations, ensure you run tests with Python >= 3.11.
