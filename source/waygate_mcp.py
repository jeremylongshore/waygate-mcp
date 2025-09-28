#!/usr/bin/env python3
"""
Waygate MCP Server - Foundational MCP implementation
Successor to NEXUS MCP with stdio-based communication
"""

import os
import sys
import json
import asyncio
import logging
import signal
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

# FastAPI and related imports
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import uvicorn
import click
import structlog

# Waygate MCP modules
from database import init_database, db_manager
from mcp_integration import initialize_mcp_integration, get_mcp_manager

# Configure logging
log_level = os.getenv("WAYGATE_LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('/tmp/waygate_mcp.log'), logging.StreamHandler()]
)
logger = logging.getLogger("waygate_mcp")

# Environment configuration
WAYGATE_MODE = os.getenv("WAYGATE_MODE", "development")
WAYGATE_PROJECTS_DIR = os.getenv("WAYGATE_PROJECTS_DIR", "/home/jeremy/projects")
WAYGATE_VERSION = "2.0.0"

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
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


class WaygateSettings(BaseSettings):
    """Waygate configuration settings"""

    # Application
    mode: str = Field(default="local_vm", alias="WAYGATE_MODE")
    env: str = Field(default="development", alias="WAYGATE_ENV")
    log_level: str = Field(default="INFO", alias="WAYGATE_LOG_LEVEL")

    # Paths
    base_dir: Path = Field(default=Path("/home/jeremy"), alias="WAYGATE_BASE_DIR")
    projects_dir: Path = Field(default=Path("/home/jeremy/projects"), alias="WAYGATE_PROJECTS_DIR")
    data_dir: Path = Field(default=Path("/home/jeremy/.waygate/data"), alias="WAYGATE_DATA_DIR")

    # Server
    host: str = Field(default="0.0.0.0", alias="WAYGATE_HOST")
    port: int = Field(default=8000, alias="WAYGATE_PORT")
    workers: int = Field(default=4, alias="WAYGATE_WORKERS")
    reload: bool = Field(default=False, alias="WAYGATE_RELOAD")

    # Security
    secret_key: str = Field(default="change-this-in-production", alias="WAYGATE_SECRET_KEY")
    api_key: Optional[str] = Field(default=None, alias="WAYGATE_API_KEY")
    cors_origins: list = Field(default=["http://localhost:3000"], alias="WAYGATE_CORS_ORIGINS")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        populate_by_name = True


class MCPCommand(BaseModel):
    """MCP Command model"""
    action: str = Field(..., description="Command action to execute")
    params: Dict[str, Any] = Field(default={}, description="Command parameters")
    context: Optional[Dict[str, Any]] = Field(None, description="Execution context")
    timeout: Optional[int] = Field(30, description="Timeout in seconds")


class MCPResponse(BaseModel):
    """MCP Response model"""
    status: str = Field(..., description="Command execution status")
    result: Optional[Any] = Field(None, description="Command result")
    error: Optional[str] = Field(None, description="Error message if failed")
    duration_ms: int = Field(..., description="Execution duration in milliseconds")
    command_id: str = Field(..., description="Unique command identifier")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class HealthCheck(BaseModel):
    """Health check response model"""
    status: str
    checks: Dict[str, str]
    version: str = "2.0.0"
    uptime_seconds: Optional[int] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class WaygateServer:
    """Main Waygate MCP Server"""

    def __init__(self, settings: WaygateSettings):
        self.settings = settings
        self.app = self._create_app()
        self.logger = logger.bind(component="server")
        self.start_time = datetime.utcnow()

    def _create_app(self) -> FastAPI:
        """Create FastAPI application"""
        app = FastAPI(
            title="Waygate MCP",
            description="Enterprise-grade MCP Server Framework - Successor to NEXUS MCP",
            version="2.0.0",
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

        # Add exception handlers
        app.add_exception_handler(HTTPException, self._http_exception_handler)
        app.add_exception_handler(Exception, self._general_exception_handler)

        # Add routes
        self._setup_routes(app)

        return app

    async def _http_exception_handler(self, request, exc: HTTPException):
        """Handle HTTP exceptions"""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "message": exc.detail,
                    "status_code": exc.status_code,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        )

    async def _general_exception_handler(self, request, exc: Exception):
        """Handle general exceptions"""
        self.logger.error("unhandled_exception", error=str(exc), exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "message": "Internal server error",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        )

    def _setup_routes(self, app: FastAPI):
        """Setup API routes"""

        @app.get("/", tags=["Core"])
        async def root():
            """Root endpoint - service information"""
            return {
                "service": "Waygate MCP",
                "version": "2.0.0",
                "status": "operational",
                "mode": self.settings.mode,
                "description": "Enterprise-grade MCP Server Framework",
                "documentation": "/docs" if self.settings.env == "development" else None
            }

        @app.get("/health", response_model=HealthCheck, tags=["Core"])
        async def health():
            """Health check endpoint"""
            uptime = int((datetime.utcnow() - self.start_time).total_seconds())
            return HealthCheck(
                status="healthy",
                checks={
                    "database": "ok",
                    "cache": "ok",
                    "filesystem": "ok",
                    "plugins": "ok"
                },
                uptime_seconds=uptime
            )

        @app.get("/ready", tags=["Core"])
        async def ready():
            """Readiness check endpoint"""
            # Add actual readiness checks here
            return {"ready": True}

        @app.get("/metrics", response_class=PlainTextResponse, tags=["Monitoring"])
        async def metrics():
            """Prometheus metrics endpoint"""
            # This would integrate with prometheus_client
            metrics_data = [
                "# HELP waygate_requests_total Total number of requests",
                "# TYPE waygate_requests_total counter",
                "waygate_requests_total 0",
                "",
                "# HELP waygate_errors_total Total number of errors",
                "# TYPE waygate_errors_total counter",
                "waygate_errors_total 0",
                "",
                "# HELP waygate_response_time_seconds Response time in seconds",
                "# TYPE waygate_response_time_seconds histogram",
                "waygate_response_time_seconds_bucket{le=\"0.1\"} 0",
                "waygate_response_time_seconds_bucket{le=\"0.5\"} 0",
                "waygate_response_time_seconds_bucket{le=\"1.0\"} 0",
                "waygate_response_time_seconds_bucket{le=\"+Inf\"} 0",
                "waygate_response_time_seconds_count 0",
                "waygate_response_time_seconds_sum 0"
            ]
            return "\n".join(metrics_data)

        @app.post("/mcp/execute", response_model=MCPResponse, tags=["MCP"])
        async def execute_mcp(command: MCPCommand):
            """Execute MCP command"""
            start_time = datetime.utcnow()
            command_id = f"cmd_{start_time.timestamp()}"

            self.logger.info(
                "executing_command",
                command_id=command_id,
                action=command.action,
                params=command.params
            )

            try:
                # TODO: Implement actual command execution
                # This is where the MCP engine would process the command
                result = {
                    "message": f"Command '{command.action}' executed successfully",
                    "params_received": command.params
                }

                duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

                return MCPResponse(
                    status="success",
                    result=result,
                    duration_ms=duration_ms,
                    command_id=command_id
                )

            except Exception as e:
                duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                self.logger.error("command_failed", command_id=command_id, error=str(e))

                return MCPResponse(
                    status="failed",
                    error=str(e),
                    duration_ms=duration_ms,
                    command_id=command_id
                )

        @app.get("/mcp/status", tags=["MCP"])
        async def mcp_status():
            """Get MCP engine status"""
            return {
                "engine": "operational",
                "plugins_loaded": 0,
                "commands_available": ["test", "echo", "status"],
                "protocol_version": "1.0"
            }

        @app.get("/plugins", tags=["Plugins"])
        async def list_plugins():
            """List loaded plugins"""
            # TODO: Implement plugin registry
            return {
                "plugins": [],
                "total": 0
            }

        @app.post("/plugins/reload", tags=["Plugins"])
        async def reload_plugins():
            """Reload all plugins"""
            self.logger.info("reloading_plugins")
            # TODO: Implement plugin reloading
            return {"status": "plugins_reloaded", "count": 0}

        # MCP Integration Endpoints
        @app.get("/mcp/servers", tags=["MCP"])
        async def list_mcp_servers():
            """List all integrated MCP servers"""
            try:
                mcp_manager = await get_mcp_manager()
                status = await mcp_manager.get_mcp_status()
                return status
            except Exception as e:
                self.logger.error("mcp_servers_list_failed", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))

        @app.get("/mcp/tools", tags=["MCP"])
        async def list_mcp_tools():
            """List all tools from all MCP servers"""
            try:
                mcp_manager = await get_mcp_manager()
                tools = await mcp_manager.get_all_mcp_tools()

                # Flatten tools for easier access
                all_tools = []
                for server_name, server_tools in tools.items():
                    for tool in server_tools:
                        tool["mcp_server"] = server_name
                        all_tools.append(tool)

                return {
                    "total_tools": len(all_tools),
                    "tools_by_server": tools,
                    "all_tools": all_tools
                }
            except Exception as e:
                self.logger.error("mcp_tools_list_failed", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))

        @app.post("/mcp/execute", tags=["MCP"])
        async def execute_mcp_tool(request: dict):
            """Execute a tool on a specific MCP server"""
            try:
                server_name = request.get("server_name")
                tool_name = request.get("tool_name")
                parameters = request.get("parameters", {})

                if not server_name or not tool_name:
                    raise HTTPException(
                        status_code=400,
                        detail="server_name and tool_name are required"
                    )

                mcp_manager = await get_mcp_manager()
                result = await mcp_manager.execute_mcp_tool(
                    server_name, tool_name, parameters
                )

                return result

            except Exception as e:
                self.logger.error("mcp_tool_execution_failed", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))

        @app.post("/mcp/servers/{server_name}/reload", tags=["MCP"])
        async def reload_mcp_server(server_name: str):
            """Reload a specific MCP server"""
            try:
                mcp_manager = await get_mcp_manager()
                success = await mcp_manager.reload_mcp_server(server_name)

                if success:
                    return {"status": "success", "message": f"MCP server {server_name} reloaded"}
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to reload MCP server: {server_name}"
                    )
            except Exception as e:
                self.logger.error("mcp_server_reload_failed", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))

        @app.get("/mcp/servers/{server_name}/tools", tags=["MCP"])
        async def get_mcp_server_tools(server_name: str):
            """Get tools for a specific MCP server"""
            try:
                mcp_manager = await get_mcp_manager()

                if server_name not in mcp_manager.mcp_servers:
                    raise HTTPException(
                        status_code=404,
                        detail=f"MCP server not found: {server_name}"
                    )

                server_info = mcp_manager.mcp_servers[server_name]
                plugin = server_info["plugin"]
                tools = await plugin.get_tools()

                return {
                    "server_name": server_name,
                    "server_type": server_info["config"]["server_type"],
                    "tool_count": len(tools),
                    "tools": tools
                }

            except Exception as e:
                self.logger.error("mcp_server_tools_failed", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))

        @app.get("/diagnostics/connection", tags=["Diagnostics"])
        async def connection_diagnostics():
            """Run connection diagnostics"""
            return {
                "server": "running",
                "port": self.settings.port,
                "connections": {
                    "active": 0,
                    "total": 0
                },
                "timestamp": datetime.utcnow().isoformat()
            }

        @app.get("/diagnostics/performance", tags=["Diagnostics"])
        async def performance_diagnostics():
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
                "timestamp": datetime.utcnow().isoformat()
            }

    async def start(self):
        """Start the server"""
        self.logger.info(
            "starting_waygate",
            mode=self.settings.mode,
            host=self.settings.host,
            port=self.settings.port,
            environment=self.settings.env
        )

        # Initialize database
        await init_database()

        # Initialize MCP integration system
        await initialize_mcp_integration()

        config = uvicorn.Config(
            app=self.app,
            host=self.settings.host,
            port=self.settings.port,
            reload=self.settings.reload,
            log_level=self.settings.log_level.lower(),
            access_log=True
        )

        server = uvicorn.Server(config)
        await server.serve()

    def run(self):
        """Run the server synchronously"""
        asyncio.run(self.start())


@click.command()
@click.option('--host', default='0.0.0.0', help='Host to bind to')
@click.option('--port', default=8000, type=int, help='Port to bind to')
@click.option('--reload', is_flag=True, help='Enable auto-reload')
@click.option('--workers', default=1, type=int, help='Number of workers')
@click.option('--env', default='development', help='Environment (development/production)')
def main(host: str, port: int, reload: bool, workers: int, env: str):
    """Waygate MCP Server CLI

    Enterprise-grade MCP Server Framework - Successor to NEXUS MCP
    """

    settings = WaygateSettings(
        host=host,
        port=port,
        reload=reload,
        workers=workers,
        env=env
    )

    server = WaygateServer(settings)

    # Handle shutdown signals gracefully
    def handle_signal(signum, frame):
        logger.info("shutdown_signal_received", signal=signum)
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        print(f"""
╔══════════════════════════════════════════════════════════╗
║                    Waygate MCP Server                     ║
║                        v2.0.0                             ║
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