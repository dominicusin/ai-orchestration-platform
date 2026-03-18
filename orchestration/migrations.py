"""Migrations for state schema"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger("orchestration.migrations")


class Migration:
    """Base migration"""
    
    version: int = 0
    
    def up(self, data: Dict) -> Dict:
        """Apply migration"""
        raise NotImplementedError
    
    def down(self, data: Dict) -> Dict:
        """Revert migration"""
        raise NotImplementedError


class AddLayerField(Migration):
    """Add layer field to tasks"""
    version = 1
    
    def up(self, data: Dict) -> Dict:
        if "tasks" in data:
            for task in data["tasks"].values():
                if "layer" not in task:
                    task["layer"] = 0
        return data
    
    def down(self, data: Dict) -> Dict:
        if "tasks" in data:
            for task in data["tasks"].values():
                task.pop("layer", None)
        return data


class AddTimestamps(Migration):
    """Add timestamps to execution"""
    version = 2
    
    def up(self, data: Dict) -> Dict:
        if "started_at" not in data:
            data["started_at"] = ""
        if "completed_at" not in data:
            data["completed_at"] = ""
        return data
    
    def down(self, data: Dict) -> Dict:
        data.pop("started_at", None)
        data.pop("completed_at", None)
        return data


class MigrationManager:
    """Manage migrations"""
    
    def __init__(self):
        self.migrations: List[Migration] = [
            AddLayerField(),
            AddTimestamps(),
        ]
    
    def migrate(self, data: Dict, from_version: int = 0, to_version: int = None) -> Dict:
        """Apply migrations"""
        if to_version is None:
            to_version = len(self.migrations)
        
        for migration in self.migrations[from_version:to_version]:
            logger.info(f"Applying migration v{migration.version}")
            data = migration.up(data)
        
        return data
    
    def rollback(self, data: Dict, to_version: int = 0) -> Dict:
        """Rollback migrations"""
        for migration in reversed(self.migrations[:to_version]):
            logger.info(f"Rolling back migration v{migration.version}")
            data = migration.down(data)
        
        return data


def migrate_state_file(path: str, to_version: int = None) -> Dict:
    """Migrate state file"""
    with open(path) as f:
        data = json.load(f)
    
    current_version = data.get("version", 0)
    manager = MigrationManager()
    
    return manager.migrate(data, current_version, to_version)