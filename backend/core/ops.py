"""Simple in-memory operational counters for basic visibility.

This is intentionally lightweight and in-memory only (no external analytics SDKs).
Counters are process-local and useful for quick dev inspection.
"""
from threading import Lock
from typing import Dict

_lock = Lock()
_counters: Dict[str, int] = {
    "uploads_attempted": 0,
    "uploads_queued": 0,
    "uploads_failed": 0,
}


def increment(counter: str, amount: int = 1) -> None:
    with _lock:
        if counter not in _counters:
            _counters[counter] = 0
        _counters[counter] += amount


def get_counters() -> Dict[str, int]:
    with _lock:
        return dict(_counters)


def reset_counters() -> None:
    with _lock:
        for k in _counters:
            _counters[k] = 0
