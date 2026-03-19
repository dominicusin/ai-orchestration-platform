"""Audit logging"""

import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger("orchestration.audit")


class AuditLogger:
    """Audit log events"""
    
    def __init__(self):
        self.events = []
    
    def log(self, action: str, user: str, details: Dict = None):
        event = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "user": user,
            "details": details or {},
        }
        self.events.append(event)
        logger.info(f"Audit: {action} by {user}")
    
    def get_events(self, limit: int = 100):
        return self.events[-limit:]


_audit_logger = None


def get_audit_logger() -> AuditLogger:
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger