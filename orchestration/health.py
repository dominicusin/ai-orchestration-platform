"""Health check system for all components"""

import os
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("orchestration.health")


class HealthStatus(Enum):
    """Health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Health check result"""
    component: str
    status: HealthStatus
    message: str = ""
    details: Dict[str, Any] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        if self.details is None:
            self.details = {}


class HealthChecker:
    """Check health of all components"""
    
    def __init__(self):
        self.checks: Dict[str, callable] = {}
        self._register_default_checks()
    
    def _register_default_checks(self):
        """Register default health checks"""
        self.register_check("python", self._check_python)
        self.register_check("disk", self._check_disk)
        self.register_check("memory", self._check_memory)
        self.register_check("ai_client", self._check_ai_client)
        self.register_check("cache", self._check_cache)
        self.register_check("config", self._check_config)
    
    def register_check(self, name: str, check_func: callable):
        """Register a health check"""
        self.checks[name] = check_func
    
    async def check_all(self) -> Dict[str, HealthCheck]:
        """Run all health checks"""
        results = {}
        
        for name, check_func in self.checks.items():
            try:
                if asyncio.iscoroutinefunction(check_func):
                    result = await check_func()
                else:
                    result = check_func()
                
                results[name] = result
                
            except Exception as e:
                logger.error(f"Health check failed for {name}: {e}")
                results[name] = HealthCheck(
                    component=name,
                    status=HealthStatus.UNHEALTHY,
                    message=str(e),
                )
        
        return results
    
    async def get_overall_status(self) -> HealthStatus:
        """Get overall system health"""
        checks = await self.check_all()
        
        statuses = [c.status for c in checks.values()]
        
        if all(s == HealthStatus.HEALTHY for s in statuses):
            return HealthStatus.HEALTHY
        elif any(s == HealthStatus.UNHEALTHY for s in statuses):
            return HealthStatus.UNHEALTHY
        else:
            return HealthStatus.DEGRADED
    
    def _check_python(self) -> HealthCheck:
        """Check Python version"""
        import sys
        
        version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        
        if sys.version_info >= (3, 11):
            return HealthCheck(
                component="python",
                status=HealthStatus.HEALTHY,
                message=f"Python {version}",
                details={"version": version},
            )
        else:
            return HealthCheck(
                component="python",
                status=HealthStatus.DEGRADED,
                message=f"Python {version} (recommended 3.11+)",
                details={"version": version},
            )
    
    def _check_disk(self) -> HealthCheck:
        """Check disk space"""
        import shutil
        
        try:
            total, used, free = shutil.disk_usage("/")
            
            free_gb = free // (2**30)
            percent_used = (used / total) * 100
            
            if percent_used < 80:
                status = HealthStatus.HEALTHY
            elif percent_used < 90:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.UNHEALTHY
            
            return HealthCheck(
                component="disk",
                status=status,
                message=f"Free: {free_gb}GB ({percent_used:.1f}% used)",
                details={
                    "total_gb": total // (2**30),
                    "used_gb": used // (2**30),
                    "free_gb": free_gb,
                    "percent_used": percent_used,
                },
            )
        except Exception as e:
            return HealthCheck(
                component="disk",
                status=HealthStatus.UNKNOWN,
                message=str(e),
            )
    
    def _check_memory(self) -> HealthCheck:
        """Check memory"""
        try:
            import psutil
            
            mem = psutil.virtual_memory()
            
            if mem.percent < 70:
                status = HealthStatus.HEALTHY
            elif mem.percent < 85:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.UNHEALTHY
            
            return HealthCheck(
                component="memory",
                status=status,
                message=f"Used: {mem.percent:.1f}%",
                details={
                    "total_gb": mem.total // (2**30),
                    "available_gb": mem.available // (2**30),
                    "percent": mem.percent,
                },
            )
        except ImportError:
            return HealthCheck(
                component="memory",
                status=HealthStatus.UNKNOWN,
                message="psutil not available",
            )
        except Exception as e:
            return HealthCheck(
                component="memory",
                status=HealthStatus.UNKNOWN,
                message=str(e),
            )
    
    def _check_ai_client(self) -> HealthCheck:
        """Check AI client"""
        try:
            from orchestration.ai.client import AsyncAIClient
            
            # Just check if client can be created
            client = AsyncAIClient(None)
            
            return HealthCheck(
                component="ai_client",
                status=HealthStatus.HEALTHY,
                message="AI client ready",
            )
        except Exception as e:
            return HealthCheck(
                component="ai_client",
                status=HealthStatus.DEGRADED,
                message=str(e),
            )
    
    def _check_cache(self) -> HealthCheck:
        """Check cache"""
        try:
            from orchestration.cache.cache import FileCache
            
            cache_dir = "./Surypus2/.cache"
            
            if os.path.exists(cache_dir):
                import shutil
                size = sum(f.stat().st_size for f in Path(cache_dir).rglob("*") if f.is_file())
                
                return HealthCheck(
                    component="cache",
                    status=HealthStatus.HEALTHY,
                    message=f"Cache size: {size / 1024:.1f}KB",
                    details={"size_kb": size / 1024},
                )
            else:
                return HealthCheck(
                    component="cache",
                    status=HealthStatus.HEALTHY,
                    message="Cache directory not created yet",
                )
        except Exception as e:
            return HealthCheck(
                component="cache",
                status=HealthStatus.UNKNOWN,
                message=str(e),
            )
    
    def _check_config(self) -> HealthCheck:
        """Check configuration"""
        try:
            from orchestration.config import get_config
            
            config = get_config()
            
            # Check if paths exist
            project_exists = os.path.exists(config.project_path)
            
            if project_exists:
                status = HealthStatus.HEALTHY
            else:
                status = HealthStatus.DEGRADED
            
            return HealthCheck(
                component="config",
                status=status,
                message=f"Project path: {config.project_path}",
                details={
                    "project_path": config.project_path,
                    "project_exists": project_exists,
                    "provider": config.default_provider,
                },
            )
        except Exception as e:
            return HealthCheck(
                component="config",
                status=HealthStatus.UNKNOWN,
                message=str(e),
            )


class ReadinessChecker:
    """Check if system is ready to handle requests"""
    
    def __init__(self):
        self.health_checker = HealthChecker()
    
    async def is_ready(self) -> bool:
        """Check if system is ready"""
        status = await self.health_checker.get_overall_status()
        return status == HealthStatus.HEALTHY
    
    async def get_readiness_info(self) -> Dict[str, Any]:
        """Get detailed readiness info"""
        checks = await self.health_checker.check_all()
        
        ready = all(
            c.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]
            for c in checks.values()
        )
        
        return {
            "ready": ready,
            "checks": {
                name: {
                    "status": c.status.value,
                    "message": c.message,
                }
                for name, c in checks.items()
            },
            "timestamp": datetime.now().isoformat(),
        }


# Global instances
_health_checker: Optional[HealthChecker] = None
_readiness_checker: Optional[ReadinessChecker] = None


def get_health_checker() -> HealthChecker:
    """Get health checker"""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker


def get_readiness_checker() -> ReadinessChecker:
    """Get readiness checker"""
    global _readiness_checker
    if _readiness_checker is None:
        _readiness_checker = ReadinessChecker()
    return _readiness_checker
