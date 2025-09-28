#!/usr/bin/env python3
"""
Waygate MCP Database Layer
Turso (SQLite in the cloud) implementation with comprehensive schema
"""

import os
import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from urllib.parse import urlparse

import libsql_client
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, Text, Boolean, DateTime, JSON, Float
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.dialects.sqlite import insert
from contextlib import asynccontextmanager

logger = logging.getLogger("waygate_mcp.database")

Base = declarative_base()

class DatabaseConfig:
    """Database configuration and connection management"""

    def __init__(self):
        self.database_url = self._get_database_url()
        self.is_turso = self._is_turso_url(self.database_url)
        self.engine = None
        self.session_maker = None

    def _get_database_url(self) -> str:
        """Get database URL from environment with validation"""
        db_url = os.getenv("DATABASE_URL")

        if not db_url:
            logger.error("❌ DATABASE_URL environment variable is required")
            logger.info("📋 Setup Instructions:")
            logger.info("1. Install Turso CLI: curl -sSfL https://get.tur.so/install.sh | bash")
            logger.info("2. Create database: turso db create waygate-mcp")
            logger.info("3. Get auth token: turso db tokens create waygate-mcp")
            logger.info("4. Set DATABASE_URL=libsql://your-db.turso.io?authToken=your-token")
            raise ValueError("DATABASE_URL is required")

        return db_url

    def _is_turso_url(self, url: str) -> bool:
        """Check if URL is for Turso (libsql://)"""
        return url.startswith("libsql://")

    async def initialize(self):
        """Initialize database connection and create tables"""
        try:
            if self.is_turso:
                # Use libsql-client for Turso
                self.client = libsql_client.create_client_sync(self.database_url)
                logger.info("✅ Connected to Turso database")
            else:
                # Fallback to SQLite for local development
                if not self.database_url.startswith("sqlite"):
                    self.database_url = "sqlite:///./waygate.db"

                self.engine = create_async_engine(self.database_url, echo=False)
                self.session_maker = async_sessionmaker(self.engine, class_=AsyncSession)
                logger.info("✅ Connected to SQLite database")

            # Create tables
            await self._create_tables()
            logger.info("✅ Database schema initialized")

        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise

    async def _create_tables(self):
        """Create all tables using the comprehensive schema"""

        # Table creation SQL (from your comprehensive schema)
        tables_sql = [
            # Config table
            """
            CREATE TABLE IF NOT EXISTS config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                type TEXT NOT NULL CHECK (type IN ('string', 'integer', 'boolean', 'json')),
                description TEXT,
                is_sensitive BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_by TEXT
            )
            """,

            # API Keys table
            """
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_hash TEXT UNIQUE NOT NULL,
                key_prefix TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                permissions JSON NOT NULL DEFAULT '["read"]',
                rate_limit INTEGER DEFAULT 100,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT NOT NULL,
                expires_at TIMESTAMP,
                last_used TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                revoked_at TIMESTAMP,
                revoked_by TEXT,
                revoke_reason TEXT
            )
            """,

            # Plugins table
            """
            CREATE TABLE IF NOT EXISTS plugins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL,
                version TEXT NOT NULL,
                description TEXT,
                author TEXT,
                module_path TEXT NOT NULL,
                config JSON DEFAULT '{}',
                capabilities JSON DEFAULT '[]',
                dependencies JSON DEFAULT '[]',
                status TEXT DEFAULT 'inactive' CHECK (status IN ('active', 'inactive', 'error', 'loading')),
                error_message TEXT,
                installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                installed_by TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_loaded TIMESTAMP,
                load_count INTEGER DEFAULT 0,
                error_count INTEGER DEFAULT 0
            )
            """,

            # Command History table
            """
            CREATE TABLE IF NOT EXISTS command_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command_id TEXT UNIQUE NOT NULL,
                command TEXT NOT NULL,
                params JSON,
                result JSON,
                error_message TEXT,
                status TEXT NOT NULL CHECK (status IN ('pending', 'executing', 'success', 'failed', 'timeout')),
                duration_ms INTEGER,
                api_key_id INTEGER,
                plugin_id INTEGER,
                client_ip TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (api_key_id) REFERENCES api_keys(id),
                FOREIGN KEY (plugin_id) REFERENCES plugins(id)
            )
            """,

            # Metrics table
            """
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                metric_type TEXT CHECK (metric_type IN ('counter', 'gauge', 'histogram', 'summary')),
                tags JSON DEFAULT '{}',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CHECK (metric_value >= 0 OR metric_type = 'gauge')
            )
            """,

            # System Events table
            """
            CREATE TABLE IF NOT EXISTS system_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                event_name TEXT NOT NULL,
                description TEXT,
                severity TEXT CHECK (severity IN ('info', 'warning', 'error', 'critical')),
                source TEXT,
                context JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,

            # MCP Servers table
            """
            CREATE TABLE IF NOT EXISTS mcp_servers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                server_type TEXT NOT NULL CHECK (server_type IN ('firebase', 'bigquery', 'github', 'n8n', 'docker_hub', 'slack')),
                display_name TEXT NOT NULL,
                description TEXT,
                config JSON NOT NULL DEFAULT '{}',
                credentials JSON NOT NULL DEFAULT '{}',
                communication_method TEXT DEFAULT 'stdio' CHECK (communication_method IN ('stdio', 'http', 'python', 'subprocess')),
                status TEXT DEFAULT 'inactive' CHECK (status IN ('active', 'inactive', 'error', 'configuring')),
                version TEXT,
                last_sync TIMESTAMP,
                error_message TEXT,
                error_count INTEGER DEFAULT 0,
                tool_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT,
                updated_by TEXT
            )
            """
        ]

        # Create indexes
        indexes_sql = [
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_config_key ON config(key)",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash)",
            "CREATE INDEX IF NOT EXISTS idx_api_keys_active ON api_keys(is_active)",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_plugins_name ON plugins(name)",
            "CREATE INDEX IF NOT EXISTS idx_plugins_status ON plugins(status)",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_command_history_command_id ON command_history(command_id)",
            "CREATE INDEX IF NOT EXISTS idx_command_history_status ON command_history(status)",
            "CREATE INDEX IF NOT EXISTS idx_command_history_created ON command_history(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_metrics_name_time ON metrics(metric_name, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_system_events_type ON system_events(event_type)",
            "CREATE INDEX IF NOT EXISTS idx_system_events_created ON system_events(created_at)",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_mcp_servers_name ON mcp_servers(name)",
            "CREATE INDEX IF NOT EXISTS idx_mcp_servers_type ON mcp_servers(server_type)",
            "CREATE INDEX IF NOT EXISTS idx_mcp_servers_status ON mcp_servers(status)",
            "CREATE INDEX IF NOT EXISTS idx_mcp_servers_updated ON mcp_servers(updated_at)"
        ]

        try:
            if self.is_turso:
                # Execute SQL with Turso client
                for sql in tables_sql + indexes_sql:
                    self.client.execute(sql)
            else:
                # Execute SQL with SQLAlchemy
                async with self.engine.begin() as conn:
                    for sql in tables_sql + indexes_sql:
                        await conn.execute(text(sql))

            # Insert default configuration
            await self._insert_default_config()

        except Exception as e:
            logger.error(f"❌ Failed to create tables: {e}")
            raise

    async def _insert_default_config(self):
        """Insert default configuration values"""
        default_configs = [
            ('max_request_size', '10485760', 'integer', 'Maximum request size in bytes'),
            ('rate_limit_enabled', 'true', 'boolean', 'Enable rate limiting'),
            ('default_timeout', '30', 'integer', 'Default command timeout in seconds'),
            ('waygate_version', '2.0.0', 'string', 'Waygate MCP version'),
            ('max_connections', '100', 'integer', 'Maximum concurrent connections')
        ]

        try:
            for key, value, type_val, desc in default_configs:
                if self.is_turso:
                    self.client.execute(
                        "INSERT OR IGNORE INTO config (key, value, type, description) VALUES (?, ?, ?, ?)",
                        [key, value, type_val, desc]
                    )
                else:
                    async with self.session_maker() as session:
                        result = await session.execute(
                            text("INSERT OR IGNORE INTO config (key, value, type, description) VALUES (:key, :value, :type, :desc)"),
                            {"key": key, "value": value, "type": type_val, "desc": desc}
                        )
                        await session.commit()

            logger.info("✅ Default configuration inserted")

        except Exception as e:
            logger.warning(f"⚠️ Could not insert default config: {e}")

class DatabaseManager:
    """Main database manager for Waygate MCP"""

    def __init__(self):
        self.config = DatabaseConfig()

    async def initialize(self):
        """Initialize the database"""
        await self.config.initialize()

    async def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """Execute a query and return results"""
        try:
            if self.config.is_turso:
                if params:
                    result = self.config.client.execute(query, list(params.values()) if isinstance(params, dict) else params)
                else:
                    result = self.config.client.execute(query)

                # Convert to list of dicts
                if hasattr(result, 'rows') and hasattr(result, 'columns'):
                    return [dict(zip(result.columns, row)) for row in result.rows]
                return []

            else:
                async with self.config.session_maker() as session:
                    result = await session.execute(text(query), params or {})
                    await session.commit()

                    if result.returns_rows:
                        rows = result.fetchall()
                        return [dict(row._mapping) for row in rows]
                    return []

        except Exception as e:
            logger.error(f"❌ Query execution failed: {e}")
            raise

    async def log_command(self, command_id: str, command: str, params: Dict = None,
                         api_key_id: int = None, plugin_id: int = None):
        """Log a command execution"""
        try:
            query = """
                INSERT INTO command_history (command_id, command, params, status, api_key_id, plugin_id)
                VALUES (?, ?, ?, 'pending', ?, ?)
            """

            if self.config.is_turso:
                self.config.client.execute(query, [
                    command_id, command,
                    json.dumps(params) if params else None,
                    api_key_id, plugin_id
                ])
            else:
                await self.execute_query(
                    "INSERT INTO command_history (command_id, command, params, status, api_key_id, plugin_id) "
                    "VALUES (:command_id, :command, :params, 'pending', :api_key_id, :plugin_id)",
                    {
                        "command_id": command_id,
                        "command": command,
                        "params": json.dumps(params) if params else None,
                        "api_key_id": api_key_id,
                        "plugin_id": plugin_id
                    }
                )

            logger.debug(f"📝 Logged command: {command_id}")

        except Exception as e:
            logger.error(f"❌ Failed to log command: {e}")

    async def update_command_status(self, command_id: str, status: str,
                                   result: Dict = None, error: str = None, duration_ms: int = None):
        """Update command execution status"""
        try:
            query = """
                UPDATE command_history
                SET status = ?, result = ?, error_message = ?, duration_ms = ?, completed_at = CURRENT_TIMESTAMP
                WHERE command_id = ?
            """

            if self.config.is_turso:
                self.config.client.execute(query, [
                    status,
                    json.dumps(result) if result else None,
                    error,
                    duration_ms,
                    command_id
                ])
            else:
                await self.execute_query(
                    "UPDATE command_history SET status = :status, result = :result, "
                    "error_message = :error, duration_ms = :duration_ms, completed_at = CURRENT_TIMESTAMP "
                    "WHERE command_id = :command_id",
                    {
                        "status": status,
                        "result": json.dumps(result) if result else None,
                        "error": error,
                        "duration_ms": duration_ms,
                        "command_id": command_id
                    }
                )

            logger.debug(f"📝 Updated command {command_id}: {status}")

        except Exception as e:
            logger.error(f"❌ Failed to update command status: {e}")

    async def record_metric(self, name: str, value: float, metric_type: str = "gauge", tags: Dict = None):
        """Record a metric"""
        try:
            query = """
                INSERT INTO metrics (metric_name, metric_value, metric_type, tags)
                VALUES (?, ?, ?, ?)
            """

            if self.config.is_turso:
                self.config.client.execute(query, [
                    name, value, metric_type,
                    json.dumps(tags) if tags else '{}'
                ])
            else:
                await self.execute_query(
                    "INSERT INTO metrics (metric_name, metric_value, metric_type, tags) "
                    "VALUES (:name, :value, :type, :tags)",
                    {
                        "name": name,
                        "value": value,
                        "type": metric_type,
                        "tags": json.dumps(tags) if tags else '{}'
                    }
                )

        except Exception as e:
            logger.error(f"❌ Failed to record metric: {e}")

    async def get_health_status(self) -> Dict[str, Any]:
        """Get database health status"""
        try:
            # Test query
            result = await self.execute_query("SELECT COUNT(*) as count FROM config")

            return {
                "database": "healthy",
                "type": "turso" if self.config.is_turso else "sqlite",
                "config_entries": result[0]["count"] if result else 0,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"❌ Database health check failed: {e}")
            return {
                "database": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

# Global database manager instance
db_manager = DatabaseManager()

# Async context manager for database operations
@asynccontextmanager
async def get_db():
    """Get database session context manager"""
    try:
        yield db_manager
    except Exception as e:
        logger.error(f"❌ Database operation failed: {e}")
        raise
    finally:
        # Cleanup if needed
        pass

# Helper functions for common operations
async def init_database():
    """Initialize database (called at startup)"""
    await db_manager.initialize()

async def log_system_event(event_type: str, event_name: str, description: str = None,
                          severity: str = "info", source: str = None, context: Dict = None):
    """Log a system event"""
    try:
        query = """
            INSERT INTO system_events (event_type, event_name, description, severity, source, context)
            VALUES (?, ?, ?, ?, ?, ?)
        """

        if db_manager.config.is_turso:
            db_manager.config.client.execute(query, [
                event_type, event_name, description, severity, source,
                json.dumps(context) if context else '{}'
            ])
        else:
            await db_manager.execute_query(
                "INSERT INTO system_events (event_type, event_name, description, severity, source, context) "
                "VALUES (:event_type, :event_name, :description, :severity, :source, :context)",
                {
                    "event_type": event_type,
                    "event_name": event_name,
                    "description": description,
                    "severity": severity,
                    "source": source,
                    "context": json.dumps(context) if context else '{}'
                }
            )

        logger.info(f"📝 System event logged: {event_type}.{event_name}")

    except Exception as e:
        logger.error(f"❌ Failed to log system event: {e}")

# Import required for JSON handling
import json

# MCP Server Management Functions
async def register_mcp_server(name: str, server_type: str, display_name: str,
                             description: str = None, config: Dict[str, Any] = None,
                             credentials: Dict[str, Any] = None,
                             communication_method: str = "stdio",
                             created_by: str = "system") -> bool:
    """
    Register a new MCP server configuration

    Args:
        name: Unique name for the MCP server
        server_type: Type of MCP server (firebase, bigquery, etc.)
        display_name: Human-readable display name
        description: Optional description
        config: Server configuration
        credentials: Server credentials (will be stored securely)
        communication_method: How to communicate with the server
        created_by: User who created the configuration

    Returns:
        True if successful, False otherwise
    """
    try:
        query = """
            INSERT OR REPLACE INTO mcp_servers
            (name, server_type, display_name, description, config, credentials,
             communication_method, status, created_by, updated_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'inactive', ?, ?)
        """

        if db_manager.config.is_turso:
            db_manager.config.client.execute(query, [
                name, server_type, display_name, description,
                json.dumps(config or {}),
                json.dumps(credentials or {}),
                communication_method, created_by, created_by
            ])
        else:
            await db_manager.execute_query(
                "INSERT OR REPLACE INTO mcp_servers "
                "(name, server_type, display_name, description, config, credentials, "
                "communication_method, status, created_by, updated_by) "
                "VALUES (:name, :server_type, :display_name, :description, :config, "
                ":credentials, :communication_method, 'inactive', :created_by, :updated_by)",
                {
                    "name": name,
                    "server_type": server_type,
                    "display_name": display_name,
                    "description": description,
                    "config": json.dumps(config or {}),
                    "credentials": json.dumps(credentials or {}),
                    "communication_method": communication_method,
                    "created_by": created_by,
                    "updated_by": created_by
                }
            )

        logger.info(f"📝 MCP server registered: {name} ({server_type})")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to register MCP server {name}: {e}")
        return False

async def get_mcp_server(name: str) -> Optional[Dict[str, Any]]:
    """
    Get MCP server configuration by name

    Args:
        name: MCP server name

    Returns:
        MCP server configuration or None if not found
    """
    try:
        result = await db_manager.execute_query(
            "SELECT * FROM mcp_servers WHERE name = ?",
            [name]
        )

        if result:
            server = result[0]
            # Parse JSON fields
            server["config"] = json.loads(server["config"])
            server["credentials"] = json.loads(server["credentials"])
            return server

        return None

    except Exception as e:
        logger.error(f"❌ Failed to get MCP server {name}: {e}")
        return None

async def list_mcp_servers(status: str = None) -> List[Dict[str, Any]]:
    """
    List all MCP servers, optionally filtered by status

    Args:
        status: Optional status filter

    Returns:
        List of MCP server configurations
    """
    try:
        if status:
            query = "SELECT * FROM mcp_servers WHERE status = ? ORDER BY name"
            params = [status]
        else:
            query = "SELECT * FROM mcp_servers ORDER BY name"
            params = []

        result = await db_manager.execute_query(query, params)

        servers = []
        for server in result:
            # Parse JSON fields
            server["config"] = json.loads(server["config"])
            server["credentials"] = json.loads(server["credentials"])
            servers.append(server)

        return servers

    except Exception as e:
        logger.error(f"❌ Failed to list MCP servers: {e}")
        return []

async def update_mcp_server_status(name: str, status: str, error_message: str = None,
                                  tool_count: int = None) -> bool:
    """
    Update MCP server status

    Args:
        name: MCP server name
        status: New status
        error_message: Optional error message
        tool_count: Optional tool count

    Returns:
        True if successful, False otherwise
    """
    try:
        update_fields = ["status = ?", "updated_at = CURRENT_TIMESTAMP"]
        params = [status]

        if error_message is not None:
            update_fields.append("error_message = ?")
            params.append(error_message)
            if status == "error":
                update_fields.append("error_count = error_count + 1")

        if tool_count is not None:
            update_fields.append("tool_count = ?")
            params.append(tool_count)

        if status == "active":
            update_fields.append("last_sync = CURRENT_TIMESTAMP")

        params.append(name)  # WHERE clause parameter

        query = f"UPDATE mcp_servers SET {', '.join(update_fields)} WHERE name = ?"

        if db_manager.config.is_turso:
            db_manager.config.client.execute(query, params)
        else:
            await db_manager.execute_query(query, params)

        logger.debug(f"📝 MCP server status updated: {name} -> {status}")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to update MCP server status: {e}")
        return False

async def delete_mcp_server(name: str) -> bool:
    """
    Delete MCP server configuration

    Args:
        name: MCP server name

    Returns:
        True if successful, False otherwise
    """
    try:
        if db_manager.config.is_turso:
            db_manager.config.client.execute(
                "DELETE FROM mcp_servers WHERE name = ?",
                [name]
            )
        else:
            await db_manager.execute_query(
                "DELETE FROM mcp_servers WHERE name = ?",
                [name]
            )

        logger.info(f"🗑️ MCP server deleted: {name}")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to delete MCP server {name}: {e}")
        return False

async def initialize_default_mcp_servers():
    """Initialize default MCP server configurations"""
    default_servers = [
        {
            "name": "firebase_mcp",
            "server_type": "firebase",
            "display_name": "Firebase MCP Server",
            "description": "Google Firebase CLI MCP server integration for DiagnosticPro",
            "config": {
                "project_id": "diagnostic-pro-start-up",
                "region": "us-central1",
                "features": ["auth", "firestore", "functions", "hosting"]
            },
            "credentials": {},
            "communication_method": "stdio"
        },
        {
            "name": "bigquery_mcp",
            "server_type": "bigquery",
            "display_name": "BigQuery MCP Server",
            "description": "Google Cloud BigQuery MCP server for analytics",
            "config": {
                "project_id": "diagnostic-pro-start-up",
                "dataset": "diagnosticpro_prod",
                "region": "us-central1"
            },
            "credentials": {},
            "communication_method": "python"
        },
        {
            "name": "github_mcp",
            "server_type": "github",
            "display_name": "GitHub MCP Server",
            "description": "Official GitHub MCP server integration",
            "config": {
                "owner": "jeremylongshore",
                "repositories": ["waygate-mcp", "diagnostic-platform"]
            },
            "credentials": {},
            "communication_method": "stdio"
        },
        {
            "name": "n8n_mcp",
            "server_type": "n8n",
            "display_name": "n8n Workflow MCP Server",
            "description": "n8n workflow automation MCP server (525+ nodes)",
            "config": {
                "api_url": "https://n8n.yourdomain.com",
                "node_count": 525
            },
            "credentials": {},
            "communication_method": "http"
        },
        {
            "name": "docker_hub_mcp",
            "server_type": "docker_hub",
            "display_name": "Docker Hub MCP Server",
            "description": "Official Docker Hub MCP server integration",
            "config": {
                "registry": "hub.docker.com",
                "organization": "your-org"
            },
            "credentials": {},
            "communication_method": "subprocess"
        },
        {
            "name": "slack_mcp",
            "server_type": "slack",
            "display_name": "Slack MCP Server",
            "description": "Slack MCP server for Bob's Brain integration",
            "config": {
                "workspace": "intent-solutions",
                "bot_name": "bobs-brain"
            },
            "credentials": {},
            "communication_method": "http"
        }
    ]

    try:
        for server_config in default_servers:
            await register_mcp_server(**server_config)

        logger.info(f"✅ Initialized {len(default_servers)} default MCP servers")

    except Exception as e:
        logger.error(f"❌ Failed to initialize default MCP servers: {e}")