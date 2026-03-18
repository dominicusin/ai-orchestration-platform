"""Health checks for DAG execution"""

import time
import logging
from typing import Dict, Any, List, Callable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("orchestration.health")


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheck:
    """Health check result"""
    name: str
    status: HealthStatus
    message: str = ""
    duration_ms: float = 0


class HealthChecker:
    """Health checker"""
    
    def __init__(self):
        self.checks: Dict[str, Callable] = {}
    
    def register(self, name: str, check: Callable):
        """Register health check"""
        self.checks[name] = check
    
    def check_all(self) -> List[HealthCheck]:
        """Run all health checks"""
        results = []
        
        for name, check in self.checks.items():
            start = time.time()
            try:
                result = check()
                results.append(HealthCheck(
                    name=name,
                    status=HealthStatus.HEALTHY if result else HealthStatus.DEGRADED,
                    duration_ms=(time.time() - start) * 1000,
                ))
            except Exception as e:
                results.append(HealthCheck(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=str(e),
                    duration_ms=(time.time() - start) * 1000,
                ))
        
        return results
    
    def is_healthy(self) -> bool:
        """Check if system is healthy"""
        checks = self.check_all()
        return all(c.status == HealthStatus.HEALTHY for c in checks)


# Built-in health checks
def check_workers(agent_pool) -> bool:
    """Check if workers available"""
    return len(agent_pool.agents) > 0


def check_memory() -> bool:
    """Check memory usage"""
    import psutil
    return psutil.virtual_memory().percent < 90


def check_disk() -> bool:
    """Check disk space"""
    import psutil
    return psutil.disk_usage('/').percent < 90


# Global health checker
_health_checker: HealthChecker = None


def get_health_checker() -> HealthChecker:
    """Get health checker"""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker