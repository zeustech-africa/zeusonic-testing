import importlib
import time
from fastapi.testclient import TestClient

import backend.main as main_module
from backend.main import app


def test_imports_cleanly():
    # Ensure the main module imports without raising
    importlib.reload(main_module)


def test_app_startup_and_health_endpoint():
    client = TestClient(app)
    # Startup should run without error; health endpoint should be available
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert "status" in r.json()


def test_audio_routes_registered_no_404():
    client = TestClient(app)

    # /api/v1/audio/upload is a POST endpoint; a GET should return 405 if registered
    r_upload = client.get("/api/v1/audio/upload")
    assert r_upload.status_code != 404

    # /api/v1/audio/jobs is a GET-protected endpoint; we expect at worst 401 Unauthorized but not 404
    r_jobs = client.get("/api/v1/audio/jobs")
    assert r_jobs.status_code != 404


def test_static_import_sweep():
    # Lightweight import sweep to catch obvious missing import-time errors
    import backend.api.v1.audio as audio_mod
    import backend.core.auth as auth_mod
    import backend.db.database as db_mod
    assert hasattr(audio_mod, "router")
    assert hasattr(auth_mod, "get_api_key")
    assert hasattr(db_mod, "create_tables")
