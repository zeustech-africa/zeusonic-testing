import logging

"""
Minimal, centralized logger configuration for Zeusonic backend.
Uses stdlib logging only; intentionally lightweight for smoke tests and local dev.
"""

LOGGER_NAME = "zeusonic"

logger = logging.getLogger(LOGGER_NAME)

if not logger.handlers:
    # Basic console handler with a concise format
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

logger.setLevel(logging.INFO)

def get_logger(name: str | None = None) -> logging.Logger:
    """Return the module logger; if name is provided, get a child logger."""
    if name:
        return logger.getChild(name)
    return logger
