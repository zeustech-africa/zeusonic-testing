# Database Migrations (Alembic)

This project uses Alembic to manage schema changes in a formal, reversible way.

Location
- Alembic config: `backend/alembic.ini`
- Alembic env: `backend/alembic/env.py`
- Migration versions: `backend/alembic/versions/`

How to run migrations locally
1. Install requirements (including Alembic):
   - cd backend
   - pip install -r requirements.txt

2. Initialize (not required; repo already includes baseline migration):
   - alembic -c backend/alembic.ini current

3. Apply migrations:
   - alembic -c backend/alembic.ini upgrade head

4. Rollback (downgrade):
   - alembic -c backend/alembic.ini downgrade -1

Adding new schema changes
- Workflow:
  1. Update your SQLAlchemy models under `backend/db/models.py`.
  2. Generate a new revision:
     - alembic -c backend/alembic.ini revision --autogenerate -m "describe change"
  3. Review and edit the generated script in `backend/alembic/versions/` to ensure safe operations, especially for SQLite.
  4. Apply locally with `alembic -c backend/alembic.ini upgrade head` and run tests.

Notes for SQLite development
- The codebase still supports a fallback ALTER TABLE logic in `backend/db/database.py` for dev convenience when Alembic is not available. When Alembic migrations are present (i.e., `alembic_version` table exists), the fallback ALTER is skipped and migrations are authoritative.
- For production deployments using other databases, Alembic provides a proper migration path and reversible changes.
