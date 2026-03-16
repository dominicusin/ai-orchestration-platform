"""Migration system for database schema updates"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("orchestration.migrations")


class MigrationStatus(Enum):
    """Migration status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class Migration:
    """Migration definition"""
    version: str
    name: str
    up: Callable
    down: Optional[Callable] = None
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class MigrationRecord:
    """Record of applied migration"""
    version: str
    name: str
    applied_at: str
    status: str
    checksum: str
    error: Optional[str] = None


class MigrationManager:
    """Manage database migrations"""
    
    def __init__(self, migrations_dir: str = "./migrations"):
        self.migrations_dir = Path(migrations_dir)
        self.migrations_dir.mkdir(parents=True, exist_ok=True)
        
        self.migrations: Dict[str, Migration] = {}
        self._load_migrations()
        
        self.state_file = self.migrations_dir / "state.json"
        self.state = self._load_state()
    
    def _load_migrations(self):
        """Load migration definitions"""
        # Register built-in migrations
        self.register_migration(Migration(
            version="001",
            name="initial_schema",
            up=self._001_initial_schema,
            down=self._001_initial_schema_down,
        ))
        
        self.register_migration(Migration(
            version="002",
            name="add_haskell_cache",
            up=self._002_add_haskell_cache,
            down=self._002_add_haskell_cache_down,
            dependencies=["001"],
        ))
        
        self.register_migration(Migration(
            version="003",
            name="add_ai_metrics",
            up=self._003_add_ai_metrics,
            down=self._003_add_ai_metrics_down,
            dependencies=["001", "002"],
        ))
    
    def register_migration(self, migration: Migration):
        """Register a migration"""
        self.migrations[migration.version] = migration
        logger.info(f"Registered migration: {migration.version} - {migration.name}")
    
    def _load_state(self) -> Dict[str, Any]:
        """Load migration state"""
        if self.state_file.exists():
            return json.loads(self.state_file.read_text())
        return {"applied": [], "current_version": None}
    
    def _save_state(self):
        """Save migration state"""
        self.state_file.write_text(json.dumps(self.state, indent=2))
    
    def get_pending_migrations(self) -> List[Migration]:
        """Get migrations that need to be applied"""
        applied = self.state.get("applied", [])
        applied_versions = [m["version"] for m in applied]
        
        pending = []
        for version, migration in sorted(self.migrations.items()):
            if version not in applied_versions:
                # Check dependencies
                deps_met = all(dep in applied_versions for dep in migration.dependencies)
                if deps_met:
                    pending.append(migration)
        
        return pending
    
    def get_applied_migrations(self) -> List[MigrationRecord]:
        """Get applied migrations"""
        return [
            MigrationRecord(
                version=m["version"],
                name=m["name"],
                applied_at=m["applied_at"],
                status=m["status"],
                checksum=m.get("checksum", ""),
            )
            for m in self.state.get("applied", [])
        ]
    
    def migrate_up(self, target_version: str = None) -> bool:
        """Apply pending migrations"""
        pending = self.get_pending_migrations()
        
        if target_version:
            pending = [m for m in pending if m.version <= target_version]
        
        if not pending:
            logger.info("No pending migrations")
            return True
        
        logger.info(f"Applying {len(pending)} migration(s)")
        
        for migration in pending:
            logger.info(f"Applying migration {migration.version}: {migration.name}")
            
            record = {
                "version": migration.version,
                "name": migration.name,
                "applied_at": datetime.now().isoformat(),
                "status": "running",
                "checksum": "",
            }
            
            self.state["applied"].append(record)
            self._save_state()
            
            try:
                # Run migration
                migration.up()
                
                # Update record
                for rec in self.state["applied"]:
                    if rec["version"] == migration.version:
                        rec["status"] = "completed"
                        rec["checksum"] = f"checksum_{migration.version}"
                
                self.state["current_version"] = migration.version
                self._save_state()
                
                logger.info(f"Migration {migration.version} completed")
                
            except Exception as e:
                logger.error(f"Migration {migration.version} failed: {e}")
                
                for rec in self.state["applied"]:
                    if rec["version"] == migration.version:
                        rec["status"] = "failed"
                        rec["error"] = str(e)
                
                self._save_state()
                return False
        
        return True
    
    def migrate_down(self, target_version: str) -> bool:
        """Rollback migrations"""
        applied = self.get_applied_migrations()
        
        # Find migrations to rollback
        to_rollback = [
            m for m in applied
            if m.version > target_version
        ]
        
        if not to_rollback:
            logger.info("No migrations to rollback")
            return True
        
        logger.info(f"Rolling back {len(to_rollback)} migration(s)")
        
        for record in reversed(to_rollback):
            migration = self.migrations.get(record.version)
            
            if not migration or not migration.down:
                logger.warning(f"No down migration for {record.version}")
                continue
            
            try:
                migration.down()
                
                # Update state
                self.state["applied"] = [
                    a for a in self.state["applied"]
                    if a["version"] != record.version
                ]
                self._save_state()
                
                logger.info(f"Rolled back {record.version}")
                
            except Exception as e:
                logger.error(f"Rollback {record.version} failed: {e}")
                return False
        
        return True
    
    # Migration definitions
    def _001_initial_schema(self):
        """Initial schema migration"""
        # Create initial tables
        logger.info("Creating initial schema...")
    
    def _001_initial_schema_down(self):
        """Rollback initial schema"""
        logger.info("Dropping initial schema...")
    
    def _002_add_haskell_cache(self):
        """Add Haskell cache table"""
        logger.info("Adding Haskell cache...")
    
    def _002_add_haskell_cache_down(self):
        """Rollback Haskell cache"""
        logger.info("Dropping Haskell cache...")
    
    def _003_add_ai_metrics(self):
        """Add AI metrics table"""
        logger.info("Adding AI metrics...")
    
    def _003_add_ai_metrics_down(self):
        """Rollback AI metrics"""
        logger.info("Dropping AI metrics...")


class SchemaValidator:
    """Validate database schema"""
    
    def __init__(self):
        self.rules = []
    
    def add_rule(self, name: str, check: Callable):
        """Add validation rule"""
        self.rules.append({"name": name, "check": check})
    
    def validate(self, schema: Dict) -> Dict[str, Any]:
        """Validate schema"""
        results = {"valid": True, "errors": [], "warnings": []}
        
        for rule in self.rules:
            try:
                rule["check"](schema)
            except AssertionError as e:
                results["valid"] = False
                results["errors"].append(f"{rule['name']}: {e}")
            except Exception as e:
                results["warnings"].append(f"{rule['name']}: {e}")
        
        return results


# Global migration manager
_migration_manager: Optional[MigrationManager] = None


def get_migration_manager() -> MigrationManager:
    """Get migration manager"""
    global _migration_manager
    if _migration_manager is None:
        _migration_manager = MigrationManager()
    return _migration_manager
