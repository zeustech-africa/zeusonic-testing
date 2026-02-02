from fastapi import FastAPI
from pathlib import Path

from backend.api.v1.health import router as health_router
from backend.api.v1.meta import router as meta_router
from backend.api.v1.audio import router as audio_router
from backend.api.v1.projects import router as projects_router
from backend.api.v1.audio_tracks import router as audio_tracks_router
from backend.api.v1.audio_transform import router as audio_transform_router
from backend.api.v1.billing import router as billing_router
from backend.api.auth import router as auth_router

from backend.core.auth import create_api_key, list_api_keys
from backend.db.database import create_tables
from backend.core.config import settings

app = FastAPI(
    title="Zeusonic API",
    version="0.1.0",
)

# Install calm, non-leaky exception handlers so production responses never include stack traces
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException as FastAPIHTTPException
from backend.core.logging import get_logger

logger = get_logger(__name__)


@app.exception_handler(FastAPIHTTPException)
async def http_exception_handler(request: Request, exc: FastAPIHTTPException):
    # Return a calm, user-friendly message while preserving status code
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc.detail)})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Don't return raw validation errors to clients; provide a simple message
    logger.warning("Validation error: %s", exc)
    return JSONResponse(status_code=422, content={"detail": "Invalid request"})


@app.exception_handler(Exception)
async def internal_exception_handler(request: Request, exc: Exception):
    # Log details server-side but return a safe message to clients
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "An internal server error occurred. Please try again later."})

# CORS - enable only in development to allow local frontend dev to call the API
if settings.app_env == "development":
    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.on_event("startup")
async def startup_event():
    """Ensure DB tables exist, validate JWT_SECRET, create a demo API key on startup, and start the job worker (dev only)."""
    
    # CRITICAL: Enforce JWT_SECRET is configured (fail fast if missing)
    if not settings.jwt_secret:
        from backend.core.logging import get_logger as _get_logger
        logger = _get_logger(__name__)
        logger.critical("❌ FATAL: JWT_SECRET is not configured. Set JWT_SECRET in .env or environment variables.")
        raise RuntimeError("JWT_SECRET is required but not configured. Cannot start application.")
    
    create_tables()

    keys = list_api_keys()
    if keys:
        demo = keys[0]
    else:
        demo = create_api_key()
    # Development-only: log API key and write it to disk for convenience when running locally
    if settings.app_env == "development":
        from backend.core.logging import get_logger

        logger = get_logger(__name__)
        logger.info("✅ Application startup: JWT_SECRET configured")
        logger.info("✅ Application startup: initializing database and demo API key")
        logger.info("Demo API key (development only): %s owner=%s", demo.key, demo.owner)
        try:
            # Also write the key to the configured api_key_path for convenience in local development
            api_key_path = Path(settings.api_key_path)
            api_key_path.parent.mkdir(parents=True, exist_ok=True)
            api_key_path.write_text(demo.key)
            logger.info("Wrote demo API key to %s", str(api_key_path))
        except Exception as exc:
            logger.warning("Failed to write demo API key file: %s", exc)
    else:
        # In non-development environments we still log startup but never print or persist API keys
        from backend.core.logging import get_logger as _get_logger

        _get_logger(__name__).info("✅ Application startup: JWT_SECRET configured")
        _get_logger(__name__).info("✅ Application startup: initializing database")

    # Start background job worker (non-blocking)
    try:
        from backend.jobs import worker

        worker.start_worker()
        logger.info("✅ Background job worker started")
    except Exception as exc:
        logger.warning("Failed to start background job worker: %s", exc)


# Register API v1 routers
app.include_router(health_router, prefix="/api/v1")
app.include_router(meta_router, prefix="/api/v1")
app.include_router(audio_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")
app.include_router(audio_tracks_router, prefix="/api/v1")
app.include_router(audio_transform_router, prefix="/api/v1")
app.include_router(billing_router, prefix="/api/v1")
app.include_router(auth_router)


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint used for quick checks."""
    return {"message": "Zeusonic API"}


@app.on_event("shutdown")
async def shutdown_event():
    """Attempt to cleanly stop background workers on shutdown."""
    try:
        from backend.jobs import worker

        worker.stop_worker()
    except Exception:
        pass
