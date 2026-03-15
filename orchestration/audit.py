```python
"""Audit logging for compliance and security"""

import os
import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
import uuid

logger = logging.getLogger("orchestration.audit")


@dataclass
class AuditEvent:
    """Audit event"""
    id: str
    timestamp: str
    event_type: str
    user: str
    action: str
    resource: str
    result: str
    details: Dict[str, Any]
    ip_address: str = ""
    user_agent: str = ""


class AuditLogger:
    """Audit logger with file and remote output"""
    
    def __init__(self, audit_dir: str = "./audit"):
        self.audit_dir = Path(audit_dir)
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_file = self.audit_dir / f"audit_{datetime.now().strftime('%Y%m%d')}.jsonl"
        self.events: List[AuditEvent] = []
    
    def log(
        self,
        event_type: str,
        action: str,
        resource: str,
        result: str = "success",
        details: Dict[str, Any] = None,
        user: str = None,
    ):
        """Log audit event"""
        event = AuditEvent(
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            event_type=event_type,
            user=user or os.getenv("USER", "unknown"),
            action=action,
            resource=resource,
            result=result,
            details=details or {},
        )
        
        self.events.append(event)
        
        # Write to file
        self._write_event(event)
        
        # Also log to regular logger
        logger.info(f"AUDIT: {action} {resource} -> {result}")
    
    def _write_event(self, event: AuditEvent):
        """Write event to file"""
        try:
            with open(self.current_file, "a") as f:
                f.write(json.dumps(asdict(event)) + "\n")
        except Exception as e:
            logger.error(f"Failed to write audit event: {e}")
    
    def log_ai_call(self, provider: str, model: str, prompt_hash: str, tokens: int):
        """Log AI API call"""
        self.log(
            event_type="ai.call",
            action="ai_call",
            resource=f"{provider}/{model}",
            details={
                "prompt_hash": prompt_hash,
                "tokens": tokens,
            }
        )
    
    def log_file_access(self, file_path: str, operation: str):
        """Log file access"""
        self.log(
            event_type="file.access",
            action=operation,
            resource=file_path,
        )
    
    def log_conversion(self, from_format: str, to_format: str, file_path: str, success: bool):
        """Log file conversion"""
        self.log(
            event_type="conversion",
            action=f"{from_format}_to_{to_format}",
            resource=file_path,
            result="success" if success else "failed",
        )
    
    def log_config_change(self, key: str, old_value: Any, new_value: Any):
        """Log configuration change"""
        self.log(
            event_type="config.change",
            action="update_config",
            resource=f"config.{key}",
            details={
                "old_value": str(old_value),
                "new_value": str(new_value),
            }
        )
    
    def get_events(
        self,
        event_type: str = None,
        user: str = None,
        start_date: str = None,
        end_date: str = None,
    ) -> List[AuditEvent]:
        """Query audit events"""
        events = []
        
        for log_file in sorted(self.audit_dir.glob("audit_*.jsonl")):
            if start_date and log_file.stem < f"audit_{start_date[:8]}":
                continue
            if end_date and log_file.stem > f"audit_{end_date[:8]}":
                continue
                
            try:
                for line in log_file.read_text().splitlines():
                    event = json.loads(line)
                    
                    if event_type and event.get("event_type") != event_type:
                        continue
                    if user and event.get("user") != user:
                        continue
                    
                    events.append(event)
            except Exception:
                continue
        
        return events
    
    def generate_report(self, output_path: str = None) -> Dict[str, Any]:
        """Generate audit report"""
        events = self.get_events()
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "total_events": len(events),
            "by_type": {},
            "by_user": {},
            "by_result": {},
            "failed_actions": [],
        }
        
        for event in events:
            # By type
            et = event.get("event_type", "unknown")
            report["by_type"][et] = report["by_type"].get(et, 0) + 1
            
            # By user
            user = event.get("user", "unknown")
            report["by_user"][user] = report["by_user"].get(user, 0) + 1
            
            # By result
            result = event.get("result", "unknown")
            report["by_result"][result] = report["by_result"].get(result, 0) + 1
            
            # Failed actions
            if result == "failed":
                report["failed_actions"].append({
                    "action": event.get("action"),
                    "resource": event.get("resource"),
                    "timestamp": event.get("timestamp"),
                })
        
        if output_path:
            Path(output_path).write_text(json.dumps(report, indent=2))
        
        return report


# Global audit logger
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get global audit logger"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
