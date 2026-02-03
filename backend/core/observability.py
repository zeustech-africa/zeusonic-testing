import json
import logging
from typing import Any, Dict, Optional
from datetime import datetime

from core.logging import get_logger

logger = get_logger(__name__)


def log_job_event(
    job_type: str,
    job_id: int,
    user_id: Optional[int],
    project_id: Optional[int],
    status: str,
    duration_ms: Optional[int] = None,
    error_message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log a structured job event for observability.
    
    job_type: 'audio_analysis' | 'beat_transform' | 'mix' | 'master'
    status: 'pending' | 'processing' | 'completed' | 'failed'
    """
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": "job",
        "job_type": job_type,
        "job_id": job_id,
        "user_id": user_id,
        "project_id": project_id,
        "status": status,
    }
    
    if duration_ms is not None:
        event["duration_ms"] = duration_ms
    
    if error_message:
        event["error_message"] = error_message
    
    if metadata:
        event["metadata"] = metadata
    
    logger.info(json.dumps(event))


def log_audit_event(
    event_type: str,
    user_id: Optional[int],
    project_id: Optional[int],
    resource_type: str,
    resource_id: Optional[int],
    action: str,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log an audit event for compliance and support.
    
    event_type: 'project' | 'audio' | 'subscription' | 'transform'
    action: 'created' | 'updated' | 'deleted' | 'uploaded' | 'failed'
    """
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": "audit",
        "audit_type": event_type,
        "user_id": user_id,
        "project_id": project_id,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "action": action,
    }
    
    if details:
        event["details"] = details
    
    logger.info(json.dumps(event))
