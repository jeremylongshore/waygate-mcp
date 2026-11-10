#!/usr/bin/env python3
"""
Waygate MCP Server - Foundational MCP implementation
Successor to NEXUS MCP with stdio-based communication
"""

import asyncio
import ipaddress
import logging
import os
import secrets
import signal
import sys
from datetime import datetime
from pathlib import Path
from types import FrameType
from typing import Any, Dict, Optional

import click
import structlog
import uvicorn

# FastAPI and related imports
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from source.version import VERSION as WAYGATE_VERSION

# Waygate MCP modules
from .database import db_manager, init_database
from .mcp_integration import (
    get_mcp_manager,
    initialize_mcp_integration,
    mcp_integration_manager,
)
from .mcp_tools import execute_tool, get_available_tools
from .metrics import HTTPMetrics, MetricsMiddleware

# Configure logging
log_level = os.getenv("WAYGATE_LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

# Environment configuration
WAYGATE_MODE = os.getenv("WAYGATE_MODE", "development")
WAYGATE_PROJECTS_DIR = os.getenv("WAYGATE_PROJECTS_DIR", "/home/jeremy/projects")

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger: structlog.stdlib.BoundLogger = structlog.get_logger()


class WaygateSettings(BaseSettings):
    """Waygate configuration settings"""

    # Application
    mode: str = Field(default="local_vm", alias="WAYGATE_MODE")
    env: str = Field(default="development", alias="WAYGATE_ENV")
    log_level: str = Field(default="INFO", alias="WAYGATE_LOG_LEVEL")

    # Paths
    base_dir: Path = Field(default=Path("/home/jeremy"), alias="WAYGATE_BASE_DIR")
    projects_dir: Path = Field(
        default=Path("/home/jeremy/projects"), alias="WAYGATE_PROJECTS_DIR"
    )
    data_dir: Path = Field(
        default=Path("/home/jeremy/.waygate/data"), alias="WAYGATE_DATA_DIR"
    )

    # Server
    host: str = Field(default="127.0.0.1", alias="WAYGATE_HOST")
    port: int = Field(default=8000, alias="WAYGATE_PORT")
    workers: int = Field(default=4, alias="WAYGATE_WORKERS")
    reload: bool = Field(default=False, alias="WAYGATE_RELOAD")

    # Security
    secret_key: str = Field(
        default_factory=lambda: secrets.token_hex(32), alias="WAYGATE_SECRET_KEY"
    )
    api_key: Optional[str] = Field(default=None, alias="WAYGATE_API_KEY")
    cors_origins: list = Field(
        default=["http://localhost:3000"], alias="WAYGATE_CORS_ORIGINS"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        populate_by_name=True,
        extra="ignore",
    )

    def model_post_init(self, context: Any) -> None:
        """Create configured directories and validate the loaded settings."""
        # Validate and create directories
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.projects_dir.mkdir(parents=True, exist_ok=True)

        # Validate environment
        self._validate_environment()

    def _validate_environment(self) -> bool:
        """Validate environment configuration"""
        warnings = []

        # Check database URL
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            warnings.append("DATABASE_URL not set, will use local SQLite")
        elif "turso.io" in database_url:
            warnings.append("Using Turso database - ensure connectivity")

        # Check host binding
        try:
            unspecified = ipaddress.ip_address(self.host).is_unspecified
        except ValueError:
            unspecified = False  # Hostnames are resolved by the server.
        if unspecified and self.env == "production":
            warnings.append(
                "Binding all network interfaces - ensure firewall configured"
            )

        # Check CORS origins
        if "localhost" in str(self.cors_origins) and self.env == "production":
            warnings.append(
                "CORS allows localhost in production - potential security risk"
            )

        # Log warnings
        for warning in warnings:
            logger.warning(f"Environment validation: {warning}")

        return len(warnings) == 0


class MCPCommand(BaseModel):
    """MCP Command model"""

    action: str = Field(..., description="Command action to execute")
    params: Dict[str, Any] = Field(default={}, description="Command parameters")
    context: Optional[Dict[str, Any]] = Field(None, description="Execution context")
    timeout: Optional[int] = Field(30, description="Timeout in seconds")


class MCPResponse(BaseModel):
    """MCP Response model"""

    status: str = Field(..., description="Command execution status")
    result: Optional[Any] = None
    error: Optional[str] = Field(None, description="Error message if failed")
    duration_ms: int = Field(..., description="Execution duration in milliseconds")
    command_id: str = Field(..., description="Unique command identifier")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class HealthCheck(BaseModel):
    """Health check response model"""

    status: str
    checks: Dict[str, str]
    version: str = WAYGATE_VERSION
    uptime_seconds: Optional[int] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class WaygateServer:
    """Main Waygate MCP Server"""

    def __init__(self, settings: WaygateSettings) -> None:
        self.settings = settings
        self.metrics = HTTPMetrics()
        self.app = self._create_app()
        self.logger = logger.bind(component="server")
        self.start_time = datetime.utcnow()

    def _create_app(self) -> FastAPI:
        """Create FastAPI application"""
        app = FastAPI(
            title="Waygate MCP",
            description=(
                "Enterprise-grade MCP Server Framework - Successor to NEXUS MCP"
            ),
            version=WAYGATE_VERSION,
            docs_url="/docs" if self.settings.env == "development" else None,
            redoc_url="/redoc" if self.settings.env == "development" else None,
        )

        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=self.settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        app.add_middleware(MetricsMiddleware, metrics=self.metrics)

        # Add exception handlers
        app.add_exception_handler(HTTPException, self._http_exception_handler)
        app.add_exception_handler(Exception, self._general_exception_handler)

        # Add routes
        self._setup_routes(app)

        return app

    async def _http_exception_handler(
        self, request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle HTTP exceptions"""
        if not isinstance(exc, HTTPException):
            return await self._general_exception_handler(request, exc)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "message": exc.detail,
                    "status_code": exc.status_code,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            },
        )

    async def _general_exception_handler(
        self, request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle general exceptions"""
        self.logger.error("unhandled_exception", error=str(exc), exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "message": "Internal server error",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            },
        )

    def _setup_routes(self, app: FastAPI) -> None:
        """Setup API routes"""

        @app.get("/", tags=["Core"])
        async def root() -> Dict[str, Any]:
            """Root endpoint - service information"""
            return {
                "service": "Waygate MCP",
                "version": WAYGATE_VERSION,
                "status": "operational",
                "mode": self.settings.mode,
                "description": "Enterprise-grade MCP Server Framework",
                "documentation": (
                    "/docs" if self.settings.env == "development" else None
                ),
            }

        @app.get("/health", response_model=HealthCheck, tags=["Core"])
        async def health(response: Response) -> HealthCheck:
            """Health check endpoint"""
            uptime = int((datetime.utcnow() - self.start_time).total_seconds())
            checks = await self._dependency_checks()
            healthy = all(value in {"ok", "disabled"} for value in checks.values())
            response.status_code = 200 if healthy else 503
            return HealthCheck(
                status="healthy" if healthy else "unhealthy",
                checks=checks,
                uptime_seconds=uptime,
            )

        @app.get("/ready", tags=["Core"])
        async def ready(response: Response) -> Dict[str, Any]:
            """Check required dependencies without triggering provider startup."""
            checks = await self._dependency_checks()
            ready = all(value in {"ok", "disabled"} for value in checks.values())
            response.status_code = 200 if ready else 503
            return {"ready": ready, "checks": checks}

        @app.get("/metrics", response_class=PlainTextResponse, tags=["Monitoring"])
        async def metrics() -> Response:
            """Expose measured per-process HTTP traffic, excluding scrapes."""
            return Response(
                generate_latest(self.metrics.registry),
                headers={"Content-Type": CONTENT_TYPE_LATEST},
            )

        @app.post("/mcp/execute", response_model=MCPResponse, tags=["MCP"])
        async def execute_mcp(command: MCPCommand) -> MCPResponse:
            """Execute MCP command using real tool handlers"""
            start_time = datetime.utcnow()
            command_id = f"cmd_{start_time.timestamp()}"

            self.logger.info(
                "executing_command",
                command_id=command_id,
                action=command.action,
                params=command.params,
            )

            try:
                # Execute actual MCP tool
                result = await execute_tool(command.action, command.params)

                duration_ms = int(
                    (datetime.utcnow() - start_time).total_seconds() * 1000
                )

                return MCPResponse(
                    status=result["status"],
                    result=result.get("result"),
                    error=result.get("error"),
                    duration_ms=duration_ms,
                    command_id=command_id,
                )

            except Exception as e:
                duration_ms = int(
                    (datetime.utcnow() - start_time).total_seconds() * 1000
                )
                self.logger.error("command_failed", command_id=command_id, error=str(e))

                return MCPResponse(
                    status="failed",
                    error=str(e),
                    duration_ms=duration_ms,
                    command_id=command_id,
                )

        @app.get("/mcp/status", tags=["MCP"])
        async def mcp_status() -> Dict[str, Any]:
            """Report the live registry and current integration state."""
            manager = await get_mcp_manager()
            status = await manager.get_mcp_status()
            loader = manager.plugin_loader
            return {
                "engine": (
                    "degraded"
                    if status["integration_status"] in {"inactive", "degraded"}
                    else "operational"
                ),
                "plugins_loaded": len(loader.loaded_plugins) if loader else 0,
                "commands_available": sorted(
                    tool["name"] for tool in get_available_tools()
                ),
                "protocol_version": "1.0",
                "integration": status,
            }

        @app.get("/plugins", tags=["Plugins"])
        async def list_plugins() -> Dict[str, Any]:
            """List actual registered plugins, preserving failed catalog visibility."""
            manager = await get_mcp_manager()
            if manager.plugin_loader is None:
                raise HTTPException(503, "Plugin registry is unavailable")
            status = await manager.plugin_loader.get_plugin_status()
            return {**status, "total": status["plugins_loaded"]}

        @app.post("/plugins/reload", tags=["Plugins"])
        async def reload_plugins(response: Response) -> Dict[str, Any]:
            """Reload registered plugins and report partial failures explicitly."""
            manager = await get_mcp_manager()
            try:
                result = await manager.reload_plugins()
            except Exception:
                raise HTTPException(503, "Plugin reload failed") from None
            if result["failed"]:
                response.status_code = 503
            return {
                "status": "reload_failed" if result["failed"] else "plugins_reloaded",
                **result,
            }

        # MCP Integration Endpoints
        @app.get("/mcp/servers", tags=["MCP"])
        async def list_mcp_servers() -> Dict[str, Any]:
            """List all integrated MCP servers"""
            try:
                mcp_manager = await get_mcp_manager()
                status = await mcp_manager.get_mcp_status()
                return status
            except Exception as e:
                self.logger.error("mcp_servers_list_failed", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))

        @app.get("/mcp/tools", tags=["MCP"])
        async def list_mcp_tools() -> Dict[str, Any]:
            """List all available MCP tools"""
            try:
                # Get local tools
                local_tools = get_available_tools()

                # Try to get external MCP server tools
                external_tools = {}
                try:
                    mcp_manager = await get_mcp_manager()
                    external_tools = await mcp_manager.get_all_mcp_tools()
                except Exception as e:
                    self.logger.warning(
                        "Could not get external MCP tools", error=str(e)
                    )

                # Flatten all tools for easier access
                all_tools = []

                # Add local tools
                for tool in local_tools:
                    tool["mcp_server"] = "waygate-local"
                    all_tools.append(tool)

                # Add external tools
                for server_name, server_tools in external_tools.items():
                    for tool in server_tools:
                        tool["mcp_server"] = server_name
                        all_tools.append(tool)

                return {
                    "total_tools": len(all_tools),
                    "local_tools": local_tools,
                    "external_tools": external_tools,
                    "all_tools": all_tools,
                }
            except Exception as e:
                self.logger.error("mcp_tools_list_failed", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))

        @app.post("/mcp/tools/execute", tags=["MCP"])
        async def execute_mcp_tool(request: dict) -> Dict[str, Any]:
            """Execute a tool on a specific MCP server"""
            try:
                server_name = request.get("server_name")
                tool_name = request.get("tool_name")
                parameters = request.get("parameters", {})

                if not server_name or not tool_name:
                    raise HTTPException(
                        status_code=400, detail="server_name and tool_name are required"
                    )

                mcp_manager = await get_mcp_manager()
                result = await mcp_manager.execute_mcp_tool(
                    server_name, tool_name, parameters
                )

                return result

            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("mcp_tool_execution_failed", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))

        @app.post("/mcp/servers/{server_name}/reload", tags=["MCP"])
        async def reload_mcp_server(server_name: str) -> Dict[str, Any]:
            """Reload a specific MCP server"""
            try:
                mcp_manager = await get_mcp_manager()
                success = await mcp_manager.reload_mcp_server(server_name)

                if success:
                    return {
                        "status": "success",
                        "message": f"MCP server {server_name} reloaded",
                    }
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to reload MCP server: {server_name}",
                    )
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("mcp_server_reload_failed", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))

        @app.get("/mcp/servers/{server_name}/tools", tags=["MCP"])
        async def get_mcp_server_tools(server_name: str) -> Dict[str, Any]:
            """Get tools for a specific MCP server"""
            try:
                mcp_manager = await get_mcp_manager()

                if server_name not in mcp_manager.mcp_servers:
                    raise HTTPException(
                        status_code=404, detail=f"MCP server not found: {server_name}"
                    )

                server_info = mcp_manager.mcp_servers[server_name]
                plugin = server_info["plugin"]
                tools = await plugin.get_tools()

                return {
                    "server_name": server_name,
                    "server_type": server_info["config"]["server_type"],
                    "tool_count": len(tools),
                    "tools": tools,
                }

            except HTTPException:
                raise
            except Exception as e:
                self.logger.error("mcp_server_tools_failed", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))

        @app.get("/diagnostics/connection", tags=["Diagnostics"])
        async def connection_diagnostics() -> Dict[str, Any]:
            """Run connection diagnostics"""
            return {
                "server": "running",
                "port": self.settings.port,
                "connections": {"active": 0, "total": 0},
                "timestamp": datetime.utcnow().isoformat(),
            }

        @app.get("/diagnostics/performance", tags=["Diagnostics"])
        async def performance_diagnostics() -> Dict[str, Any]:
            """Run performance diagnostics"""
            import psutil

            process = psutil.Process()

            return {
                "cpu_percent": process.cpu_percent(),
                "memory": {
                    "rss_mb": process.memory_info().rss / 1024 / 1024,
                    "vms_mb": process.memory_info().vms / 1024 / 1024,
                },
                "threads": process.num_threads(),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def _dependency_checks(self) -> Dict[str, str]:
        """Probe the configured database and observe required provider readiness."""
        checks = {}
        try:
            rows = await asyncio.wait_for(
                db_manager.execute_query("SELECT COUNT(*) AS count FROM config"),
                timeout=5,
            )
            checks["database"] = "ok" if rows else "failed"
        except Exception:
            # Health responses must not disclose connection strings or credentials.
            checks["database"] = "failed"
        providers = mcp_integration_manager.provider_readiness()
        checks["providers"] = (
            "disabled"
            if not providers
            else (
                "ok" if all(state == "ok" for state in providers.values()) else "failed"
            )
        )
        checks.update({f"provider:{name}": state for name, state in providers.items()})
        return checks

    async def start(self) -> None:
        """Start the server"""
        self.logger.info(
            "starting_waygate",
            mode=self.settings.mode,
            host=self.settings.host,
            port=self.settings.port,
            environment=self.settings.env,
        )

        # Initialize database (with fallback)
        try:
            await init_database()
            self.logger.info("Database initialized successfully")
        except Exception as e:
            self.logger.warning(
                f"Database initialization failed, continuing without database: {str(e)}"
            )

        # Initialize MCP integration system (optional)
        try:
            await initialize_mcp_integration()
            self.logger.info("MCP integration initialized successfully")
        except Exception as e:
            self.logger.warning(
                f"MCP integration failed, continuing with local tools only: {str(e)}"
            )

        config = uvicorn.Config(
            app=self.app,
            host=self.settings.host,
            port=self.settings.port,
            reload=self.settings.reload,
            log_level=self.settings.log_level.lower(),
            access_log=True,
        )

        server = uvicorn.Server(config)
        await server.serve()

    def run(self) -> None:
        """Run the server synchronously"""
        asyncio.run(self.start())


@click.command()
@click.option(
    "--host", default="127.0.0.1", envvar="WAYGATE_HOST", help="Host to bind to"
)
@click.option("--port", default=8000, type=int, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
@click.option("--workers", default=1, type=int, help="Number of workers")
@click.option(
    "--env", default="development", help="Environment (development/production)"
)
def main(host: str, port: int, reload: bool, workers: int, env: str) -> None:
    """Waygate MCP Server CLI

    Enterprise-grade MCP Server Framework - Successor to NEXUS MCP
    """

    settings = WaygateSettings(
        WAYGATE_HOST=host,
        WAYGATE_PORT=port,
        WAYGATE_RELOAD=reload,
        WAYGATE_WORKERS=workers,
        WAYGATE_ENV=env,
    )

    server = WaygateServer(settings)

    # Handle shutdown signals gracefully
    def handle_signal(signum: int, frame: FrameType | None) -> None:
        logger.info("shutdown_signal_received", signal=signum)
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        print(f"""
╔══════════════════════════════════════════════════════════╗
║                    Waygate MCP Server                     ║
║                        v{WAYGATE_VERSION}                             ║
║                                                           ║
║  Successor to NEXUS MCP with Enhanced Diagnostics        ║
║                                                           ║
║  Starting server on http://{host}:{port}
║  Environment: {env}
║  Documentation: http://{host}:{port}/docs
╚══════════════════════════════════════════════════════════╝
        """)

        server.run()
    except Exception as e:
        logger.error("server_error", error=str(e), exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
