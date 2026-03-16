"""Database migration utilities"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger("orchestration.migration")


@dataclass
class MigrationStep:
    """Migration step"""
    version: str
    description: str
    sql_up: str
    sql_down: str


class DatabaseMigrator:
    """PostgreSQL database migrator"""
    
    def __init__(self, connection_string: str = None):
        self.connection_string = connection_string or os.getenv("DATABASE_URL")
        self.migrations: List[MigrationStep] = []
        self._register_migrations()
    
    def _register_migrations(self):
        """Register built-in migrations"""
        self.migrations = [
            MigrationStep(
                version="001",
                description="Initial schema",
                sql_up="""
CREATE TABLE IF NOT EXISTS conversion_projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    source_path TEXT,
    output_path TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS converted_files (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES conversion_projects(id),
    source_file VARCHAR(512),
    output_file VARCHAR(512),
    format VARCHAR(50),
    status VARCHAR(50) DEFAULT 'pending',
    ai_provider VARCHAR(100),
    ai_tokens INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_usage (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES conversion_projects(id),
    provider VARCHAR(100),
    model VARCHAR(100),
    tokens INTEGER DEFAULT 0,
    cost DECIMAL(10, 4) DEFAULT 0,
    latency_ms INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_files_project ON converted_files(project_id);
CREATE INDEX idx_usage_project ON ai_usage(project_id);
CREATE INDEX idx_usage_provider ON ai_usage(provider);
""",
                sql_down="""
DROP TABLE IF EXISTS ai_usage CASCADE;
DROP TABLE IF EXISTS converted_files CASCADE;
DROP TABLE IF EXISTS conversion_projects CASCADE;
""",
            ),
            MigrationStep(
                version="002",
                description="Add cache tracking",
                sql_up="""
CREATE TABLE IF NOT EXISTS cache_entries (
    id SERIAL PRIMARY KEY,
    cache_key VARCHAR(512) UNIQUE NOT NULL,
    cache_value TEXT,
    format VARCHAR(50),
    hit_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_hit_at TIMESTAMP
);

CREATE INDEX idx_cache_key ON cache_entries(cache_key);
CREATE INDEX idx_cache_hit ON cache_entries(hit_count);
""",
                sql_down="""
DROP TABLE IF EXISTS cache_entries;
""",
            ),
            MigrationStep(
                version="003",
                description="Add validation results",
                sql_up="""
CREATE TABLE IF NOT EXISTS validation_results (
    id SERIAL PRIMARY KEY,
    file_id INTEGER REFERENCES converted_files(id),
    validator VARCHAR(50),
    valid BOOLEAN DEFAULT false,
    errors JSONB,
    warnings JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_validation_file ON validation_results(file_id);
""",
                sql_down="""
DROP TABLE IF EXISTS validation_results;
""",
            ),
        ]
    
    def get_migrations(self) -> List[MigrationStep]:
        """Get all migrations"""
        return self.migrations
    
    def create_migration(self, version: str, description: str, sql_up: str, sql_down: str = ""):
        """Create a new migration"""
        self.migrations.append(MigrationStep(
            version=version,
            description=description,
            sql_up=sql_up,
            sql_down=sql_down,
        ))
    
    async def migrate_up(self, target_version: str = None):
        """Apply migrations"""
        if not self.connection_string:
            logger.warning("No database connection, skipping migrations")
            return
        
        try:
            import asyncpg
            conn = await asyncpg.connect(self.connection_string)
            
            # Create migrations table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(10) PRIMARY KEY,
                    description TEXT,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Get applied migrations
            rows = await conn.fetch("SELECT version FROM schema_migrations")
            applied = {row["version"] for row in rows}
            
            # Apply pending migrations
            for migration in self.migrations:
                if migration.version in applied:
                    continue
                
                if target_version and migration.version > target_version:
                    break
                
                logger.info(f"Applying migration {migration.version}: {migration.description}")
                
                # Execute SQL
                for statement in migration.sql_up.split(";"):
                    statement = statement.strip()
                    if statement:
                        await conn.execute(statement)
                
                # Record migration
                await conn.execute(
                    "INSERT INTO schema_migrations (version, description) VALUES ($1, $2)",
                    migration.version,
                    migration.description,
                )
            
            await conn.close()
            logger.info("Migrations completed")
            
        except ImportError:
            logger.warning("asyncpg not installed, skipping migrations")
        except Exception as e:
            logger.error(f"Migration failed: {e}")
    
    async def migrate_down(self, target_version: str):
        """Rollback migrations"""
        if not self.connection_string:
            return
        
        try:
            import asyncpg
            conn = await asyncpg.connect(self.connection_string)
            
            # Get applied migrations
            rows = await conn.fetch("SELECT version FROM schema_migrations ORDER BY version DESC")
            
            for row in rows:
                version = row["version"]
                
                if version <= target_version:
                    break
                
                # Find migration
                migration = next((m for m in self.migrations if m.version == version), None)
                
                if migration and migration.sql_down:
                    logger.info(f"Rolling back migration {version}")
                    
                    for statement in migration.sql_down.split(";"):
                        statement = statement.strip()
                        if statement:
                            await conn.execute(statement)
                    
                    await conn.execute("DELETE FROM schema_migrations WHERE version = $1", version)
            
            await conn.close()
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
    
    def export_sql(self, output_dir: str = "./migrations"):
        """Export migrations as SQL files"""
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        
        for migration in self.migrations:
            up_file = out_dir / f"{migration.version}_{migration.description.lower().replace(' ', '_')}_up.sql"
            up_file.write_text(migration.sql_up)
            
            if migration.sql_down:
                down_file = out_dir / f"{migration.version}_{migration.description.lower().replace(' ', '_')}_down.sql"
                down_file.write_text(migration.sql_down)
        
        logger.info(f"Exported {len(self.migrations)} migrations to {output_dir}")


# CLI
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Database migrations")
    parser.add_argument("command", choices=["up", "down", "list", "export"])
    parser.add_argument("--target", help="Target version")
    parser.add_argument("--output", default="./migrations", help="Output directory")
    
    args = parser.parse_args()
    
    migrator = DatabaseMigrator()
    
    if args.command == "up":
        asyncio.run(migrator.migrate_up(args.target))
    elif args.command == "down":
        if args.target:
            asyncio.run(migrator.migrate_down(args.target))
        else:
            print("Error: --target required for down")
    elif args.command == "list":
        for m in migrator.get_migrations():
            print(f"{m.version}: {m.description}")
    elif args.command == "export":
        migrator.export_sql(args.output)


if __name__ == "__main__":
    main()