"""Scheduler for automated pipeline runs"""

import os
import asyncio
import logging
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import croniter

logger = logging.getLogger("orchestration.scheduler")


class ScheduleType(Enum):
    """Schedule types"""
    CRON = "cron"
    INTERVAL = "interval"
    DAILY = "daily"
    WEEKLY = "weekly"


@dataclass
class Schedule:
    """Schedule configuration"""
    name: str
    schedule_type: str
    expression: str  # cron expression or interval seconds
    enabled: bool = True
    project_path: str = "./OpenPapyrus"
    output_path: str = "./Surypus2"
    provider: str = "ollama"
    options: Dict[str, Any] = None


@dataclass
class ScheduledRun:
    """Scheduled run record"""
    schedule_name: str
    scheduled_time: str
    started_time: Optional[str] = None
    completed_time: Optional[str] = None
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class Scheduler:
    """Pipeline scheduler"""
    
    def __init__(self):
        self.schedules: Dict[str, Schedule] = {}
        self.runs: List[ScheduledRun] = []
        self.running = False
        self._task = None
    
    def add_schedule(self, schedule: Schedule):
        """Add schedule"""
        self.schedules[schedule.name] = schedule
        logger.info(f"Added schedule: {schedule.name} ({schedule.expression})")
    
    def remove_schedule(self, name: str):
        """Remove schedule"""
        if name in self.schedules:
            del self.schedules[name]
            logger.info(f"Removed schedule: {name}")
    
    def get_next_run(self, schedule: Schedule) -> Optional[datetime]:
        """Get next run time"""
        if schedule.schedule_type == "cron":
            try:
                cron = croniter.croniter(schedule.expression)
                return cron.get_next(datetime)
            except Exception:
                return None
        
        elif schedule.schedule_type == "interval":
            try:
                interval = int(schedule.expression)
                return datetime.now() + timedelta(seconds=interval)
            except Exception:
                return None
        
        elif schedule.schedule_type == "daily":
            try:
                hour, minute = map(int, schedule.expression.split(":"))
                now = datetime.now()
                next_run = now.replace(hour=hour, minute=minute, second=0)
                if next_run <= now:
                    next_run += timedelta(days=1)
                return next_run
            except Exception:
                return None
        
        return None
    
    async def run_schedule(self, schedule: Schedule):
        """Run scheduled pipeline"""
        logger.info(f"Starting scheduled run: {schedule.name}")
        
        run = ScheduledRun(
            schedule_name=schedule.name,
            scheduled_time=datetime.now().isoformat(),
            started_time=datetime.now().isoformat(),
            status="running",
        )
        self.runs.append(run)
        
        try:
            # Import and run pipeline
            from orchestration.pipeline import run_pipeline
            
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: run_pipeline(
                    schedule.project_path,
                    schedule.output_path,
                    log_format="json",
                )
            )
            
            run.completed_time = datetime.now().isoformat()
            run.status = "completed"
            run.result = {"success": True}
            
            logger.info(f"Scheduled run completed: {schedule.name}")
            
        except Exception as e:
            run.completed_time = datetime.now().isoformat()
            run.status = "failed"
            run.error = str(e)
            
            logger.error(f"Scheduled run failed: {schedule.name} - {e}")
    
    async def start(self):
        """Start scheduler"""
        self.running = True
        logger.info("Scheduler started")
        
        while self.running:
            now = datetime.now()
            
            for name, schedule in self.schedules.items():
                if not schedule.enabled:
                    continue
                
                next_run = self.get_next_run(schedule)
                
                if next_run and next_run <= now:
                    # Time to run
                    asyncio.create_task(self.run_schedule(schedule))
            
            await asyncio.sleep(60)  # Check every minute
    
    def stop(self):
        """Stop scheduler"""
        self.running = False
        logger.info("Scheduler stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status"""
        return {
            "running": self.running,
            "schedules": [
                {
                    "name": s.name,
                    "enabled": s.enabled,
                    "expression": s.expression,
                    "next_run": self.get_next_run(s).isoformat() if self.get_next_run(s) else None,
                }
                for s in self.schedules.values()
            ],
            "recent_runs": [
                {
                    "schedule_name": r.schedule_name,
                    "status": r.status,
                    "started_time": r.started_time,
                    "completed_time": r.completed_time,
                }
                for r in self.runs[-10:]
            ],
        }


# Default schedules
DEFAULT_SCHEDULES = [
    Schedule(
        name="nightly",
        schedule_type="daily",
        expression="02:00",
        project_path="./OpenPapyrus",
        output_path="./Surypus2",
        provider="ollama",
    ),
    Schedule(
        name="hourly",
        schedule_type="interval",
        expression="3600",
        enabled=False,
    ),
]


# CLI integration
def setup_default_schedules(scheduler: Scheduler):
    """Setup default schedules"""
    for schedule in DEFAULT_SCHEDULES:
        scheduler.add_schedule(schedule)


# Cron helper
def parse_cron(expression: str) -> Dict[str, Any]:
    """Parse cron expression"""
    parts = expression.split()
    if len(parts) != 5:
        return {"error": "Invalid cron expression"}
    
    return {
        "minute": parts[0],
        "hour": parts[1],
        "day": parts[2],
        "month": parts[3],
        "weekday": parts[4],
    }


def format_next_runs(expression: str, count: int = 5) -> List[str]:
    """Format next N run times"""
    try:
        cron = croniter.croniter(expression)
        return [cron.get_next(datetime).strftime("%Y-%m-%d %H:%M") for _ in range(count)]
    except Exception:
        return []
