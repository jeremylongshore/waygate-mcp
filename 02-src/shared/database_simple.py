#!/usr/bin/env python3
"""
Waygate MCP Database Layer - Simplified SQLite-only version
No external dependencies, just pure SQLite
"""

import os
import sqlite3
import json
import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from contextlib import asynccontextmanager

logger = logging.getLogger("waygate_mcp.database_simple")

class SimpleDatabaseManager:
    """Simplified database manager using only SQLite"""

    def __init__(self):
        self.db_path = os.getenv("DATABASE_URL", "sqlite:///./waygate.db").replace("sqlite:///", "")
        if not self.db_path.endswith('.db'):
            self.db_path = "./waygate.db"

    async def initialize(self):
        """Initialize database with basic schema"""
        try:
            # Create database and basic tables
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Simple config table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Simple metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Simple events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Insert default config
            cursor.execute(
                "INSERT OR IGNORE INTO config (key, value) VALUES (?, ?)",
                ("waygate_version", "2.0.0")
            )

            conn.commit()
            conn.close()

            logger.info("✅ SQLite database initialized: %s", self.db_path)

        except Exception as e:
            logger.error("❌ Database initialization failed: %s", e)
            raise

    async def get_health_status(self) -> Dict[str, Any]:
        """Get database health status"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM config")
            count = cursor.fetchone()[0]
            conn.close()

            return {
                "database": "healthy",
                "type": "sqlite",
                "config_entries": count,
                "path": self.db_path,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error("❌ Database health check failed: %s", e)
            return {
                "database": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    def record_event(self, event_type: str, description: str = None):
        """Record a simple event"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO events (event_type, description) VALUES (?, ?)",
                (event_type, description)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error("❌ Failed to record event: %s", e)

# Global instance
simple_db = SimpleDatabaseManager()

# Compatibility functions
async def init_database():
    """Initialize database (called at startup)"""
    await simple_db.initialize()

# For backward compatibility
db_manager = simple_db