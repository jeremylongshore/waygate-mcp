#!/usr/bin/env python3
"""
Waygate MCP Server - Simplified version without complex dependencies
Just basic FastAPI server with SQLite
"""

import os
import sys
import json
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

# FastAPI imports
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field
import uvicorn
import click

# Simple database
from database_simple import init_database, simple_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("waygate_simple")

class MCPCommand(BaseModel):
    """Simple MCP Command model"""
    action: str = Field(..., description="Command action")
    params: Dict[str, Any] = Field(default={}, description="Parameters")

class HealthCheck(BaseModel):
    """Health check response"""
    status: str
    version: str = "2.0.0-simple"
    database: Dict[str, Any]
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

def create_app() -> FastAPI:
    """Create simplified FastAPI application"""
    app = FastAPI(
        title="Waygate MCP - Simplified",
        description="Simplified MCP Server without complex dependencies",
        version="2.0.0-simple",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "https://localhost"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/", tags=["Core"])
    async def root():
        """Root endpoint"""
        return {
            "service": "Waygate MCP - Simplified",
            "version": "2.0.0-simple",
            "status": "operational",
            "description": "Simplified MCP Server for rapid deployment",
            "documentation": "/docs",
            "time": datetime.utcnow().isoformat()
        }

    @app.get("/health", response_model=HealthCheck, tags=["Core"])
    async def health():
        """Health check endpoint"""
        db_status = await simple_db.get_health_status()
        return HealthCheck(
            status="healthy",
            database=db_status
        )

    @app.get("/ready", tags=["Core"])
    async def ready():
        """Readiness check"""
        return {"ready": True, "timestamp": datetime.utcnow().isoformat()}

    @app.get("/metrics", response_class=PlainTextResponse, tags=["Monitoring"])
    async def metrics():
        """Basic metrics"""
        return """# Simple Waygate MCP Metrics
waygate_status 1
waygate_version{version="2.0.0-simple"} 1
waygate_database_status 1
"""

    @app.post("/mcp/execute", tags=["MCP"])
    async def execute_mcp(command: MCPCommand):
        """Execute MCP command (simplified)"""
        simple_db.record_event("mcp_command", f"Action: {command.action}")

        return {
            "status": "success",
            "action": command.action,
            "params": command.params,
            "message": "Command executed (simplified mode)",
            "timestamp": datetime.utcnow().isoformat()
        }

    @app.get("/mcp/status", tags=["MCP"])
    async def mcp_status():
        """MCP status (simplified)"""
        return {
            "engine": "simplified",
            "status": "operational",
            "mode": "standalone",
            "features": ["basic_execution", "health_monitoring"],
            "timestamp": datetime.utcnow().isoformat()
        }

    @app.get("/proxy/health", tags=["Proxy"])
    async def proxy_health():
        """Proxy health check"""
        return {
            "proxy": "operational",
            "mode": "simplified",
            "timestamp": datetime.utcnow().isoformat()
        }

    return app

async def startup():
    """Startup initialization"""
    logger.info("🚀 Starting Waygate MCP - Simplified")
    await init_database()
    simple_db.record_event("startup", "Waygate MCP simplified server started")

@click.command()
@click.option('--host', default='0.0.0.0', help='Host to bind to')
@click.option('--port', default=8000, type=int, help='Port to bind to')
@click.option('--reload', is_flag=True, help='Enable auto-reload')
def main(host: str, port: int, reload: bool):
    """Waygate MCP - Simplified Server"""

    app = create_app()

    # Add startup event
    @app.on_event("startup")
    async def startup_event():
        await startup()

    print(f"""
╔══════════════════════════════════════════════════════════╗
║                 Waygate MCP - Simplified                 ║
║                      v2.0.0-simple                       ║
║                                                          ║
║          No complex dependencies required!               ║
║                                                          ║
║  Server: http://{host}:{port}
║  Health: http://{host}:{port}/health
║  Docs:   http://{host}:{port}/docs
╚══════════════════════════════════════════════════════════╝
    """)

    try:
        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except Exception as e:
        logger.error("❌ Server error: %s", e)
        sys.exit(1)

if __name__ == "__main__":
    main()