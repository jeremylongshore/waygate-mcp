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
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

# Configure logging
log_level = os.getenv("WAYGATE_LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('/tmp/waygate_mcp.log')]  # Log to file only, not stderr
)
logger = logging.getLogger("waygate_mcp")

# Environment configuration
WAYGATE_MODE = os.getenv("WAYGATE_MODE", "development")
WAYGATE_PROJECTS_DIR = os.getenv("WAYGATE_PROJECTS_DIR", "/home/jeremy/projects")
WAYGATE_VERSION = "2.0.0"


class WaygateMCPServer:
    """
    Main MCP server implementation with stdio communication.
    """

    def __init__(self):
        self.version = WAYGATE_VERSION
        self.mode = WAYGATE_MODE
        self.projects_dir = Path(WAYGATE_PROJECTS_DIR)
        self.active_dir = self.projects_dir / "active"
        self.archived_dir = self.projects_dir / "archived"

        # Ensure directories exist
        self.active_dir.mkdir(parents=True, exist_ok=True)
        self.archived_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Waygate MCP Server v{self.version} initializing in {self.mode} mode")

    # ============================================
    # Resources Section
    # ============================================

    async def handle_resource(self, resource_uri: str) -> Dict[str, Any]:
        """
        Handle resource requests.

        Example resources:
        - waygate://system - System information
        - waygate://projects/list - List all projects
        - waygate://projects/active - List active projects
        """
        logger.debug(f"Handling resource: {resource_uri}")

        if resource_uri == "waygate://system":
            return await self.get_system_info()
        elif resource_uri == "waygate://projects/list":
            return await self.list_all_projects()
        elif resource_uri == "waygate://projects/active":
            return await self.list_active_projects()
        elif resource_uri == "waygate://projects/archived":
            return await self.list_archived_projects()
        else:
            return {
                "error": f"Unknown resource: {resource_uri}",
                "available_resources": [
                    "waygate://system",
                    "waygate://projects/list",
                    "waygate://projects/active",
                    "waygate://projects/archived"
                ]
            }

    async def get_system_info(self) -> Dict[str, Any]:
        """
        Return system information.
        """
        return {
            "server": "Waygate MCP",
            "version": self.version,
            "mode": self.mode,
            "projects_dir": str(self.projects_dir),
            "active_projects": len(list(self.active_dir.iterdir())) if self.active_dir.exists() else 0,
            "archived_projects": len(list(self.archived_dir.iterdir())) if self.archived_dir.exists() else 0,
            "timestamp": datetime.now().isoformat()
        }

    async def list_all_projects(self) -> Dict[str, Any]:
        """
        List all projects (active and archived).
        """
        active = await self.list_active_projects()
        archived = await self.list_archived_projects()

        return {
            "total": active["count"] + archived["count"],
            "active": active["projects"],
            "archived": archived["projects"],
            "timestamp": datetime.now().isoformat()
        }

    async def list_active_projects(self) -> Dict[str, Any]:
        """
        List active projects.
        """
        projects = []
        if self.active_dir.exists():
            for project_path in self.active_dir.iterdir():
                if project_path.is_dir():
                    projects.append({
                        "name": project_path.name,
                        "path": str(project_path),
                        "modified": datetime.fromtimestamp(project_path.stat().st_mtime).isoformat()
                    })

        return {
            "count": len(projects),
            "projects": projects,
            "directory": str(self.active_dir)
        }

    async def list_archived_projects(self) -> Dict[str, Any]:
        """
        List archived projects.
        """
        projects = []
        if self.archived_dir.exists():
            for project_path in self.archived_dir.iterdir():
                if project_path.is_dir():
                    projects.append({
                        "name": project_path.name,
                        "path": str(project_path),
                        "modified": datetime.fromtimestamp(project_path.stat().st_mtime).isoformat()
                    })

        return {
            "count": len(projects),
            "projects": projects,
            "directory": str(self.archived_dir)
        }

    # ============================================
    # Tools Section
    # ============================================

    async def handle_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle tool execution requests.

        Available tools:
        - waygate_echo: Echo back input
        - project_create: Create a new project
        - project_archive: Archive an active project
        - project_activate: Reactivate an archived project
        """
        logger.debug(f"Executing tool: {tool_name} with parameters: {parameters}")

        if tool_name == "waygate_echo":
            return await self.tool_echo(parameters)
        elif tool_name == "project_create":
            return await self.tool_create_project(parameters)
        elif tool_name == "project_archive":
            return await self.tool_archive_project(parameters)
        elif tool_name == "project_activate":
            return await self.tool_activate_project(parameters)
        else:
            return {
                "error": f"Unknown tool: {tool_name}",
                "available_tools": [
                    "waygate_echo",
                    "project_create",
                    "project_archive",
                    "project_activate"
                ]
            }

    async def tool_echo(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simple echo tool for testing.
        """
        message = parameters.get("message", "No message provided")
        return {
            "success": True,
            "echo": message,
            "timestamp": datetime.now().isoformat(),
            "mode": self.mode
        }

    async def tool_create_project(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new project in the active directory.
        """
        project_name = parameters.get("name")
        if not project_name:
            return {"success": False, "error": "Project name is required"}

        project_path = self.active_dir / project_name

        if project_path.exists():
            return {"success": False, "error": f"Project '{project_name}' already exists"}

        try:
            project_path.mkdir(parents=True)

            # Create basic project structure
            (project_path / "README.md").write_text(f"# {project_name}\n\nCreated by Waygate MCP\n")
            (project_path / ".gitignore").write_text("*.pyc\n__pycache__/\n.env\n")

            return {
                "success": True,
                "message": f"Project '{project_name}' created successfully",
                "path": str(project_path)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def tool_archive_project(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Archive an active project.
        """
        project_name = parameters.get("name")
        if not project_name:
            return {"success": False, "error": "Project name is required"}

        source = self.active_dir / project_name
        destination = self.archived_dir / project_name

        if not source.exists():
            return {"success": False, "error": f"Active project '{project_name}' not found"}

        if destination.exists():
            return {"success": False, "error": f"Archived project '{project_name}' already exists"}

        try:
            source.rename(destination)
            return {
                "success": True,
                "message": f"Project '{project_name}' archived successfully",
                "new_path": str(destination)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def tool_activate_project(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reactivate an archived project.
        """
        project_name = parameters.get("name")
        if not project_name:
            return {"success": False, "error": "Project name is required"}

        source = self.archived_dir / project_name
        destination = self.active_dir / project_name

        if not source.exists():
            return {"success": False, "error": f"Archived project '{project_name}' not found"}

        if destination.exists():
            return {"success": False, "error": f"Active project '{project_name}' already exists"}

        try:
            source.rename(destination)
            return {
                "success": True,
                "message": f"Project '{project_name}' reactivated successfully",
                "new_path": str(destination)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ============================================
    # STDIO Communication
    # ============================================

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main request handler for stdio communication.
        """
        request_type = request.get("type")

        if request_type == "resource":
            return await self.handle_resource(request.get("uri", ""))
        elif request_type == "tool":
            return await self.handle_tool(
                request.get("name", ""),
                request.get("parameters", {})
            )
        elif request_type == "ping":
            return {"pong": True, "timestamp": datetime.now().isoformat()}
        else:
            return {
                "error": f"Unknown request type: {request_type}",
                "supported_types": ["resource", "tool", "ping"]
            }

    async def run_stdio(self):
        """
        Run the server in stdio mode for MCP communication.
        """
        logger.info("Starting Waygate MCP Server in stdio mode")

        # Send initialization message
        init_msg = {
            "type": "initialization",
            "server": "Waygate MCP",
            "version": self.version,
            "capabilities": {
                "resources": True,
                "tools": True,
                "stdio": True
            }
        }
        print(json.dumps(init_msg))
        sys.stdout.flush()

        # Main request loop
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break

                request = json.loads(line.strip())
                logger.debug(f"Received request: {request}")

                response = await self.handle_request(request)

                print(json.dumps(response))
                sys.stdout.flush()

            except json.JSONDecodeError as e:
                error_response = {"error": f"Invalid JSON: {e}"}
                print(json.dumps(error_response))
                sys.stdout.flush()
            except KeyboardInterrupt:
                logger.info("Received interrupt signal, shutting down")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                error_response = {"error": f"Server error: {e}"}
                print(json.dumps(error_response))
                sys.stdout.flush()

    # ============================================
    # Diagnostics Section
    # ============================================

    async def run_diagnostics(self) -> Dict[str, Any]:
        """
        Run server diagnostics.
        """
        diagnostics = {
            "server_status": "healthy",
            "version": self.version,
            "mode": self.mode,
            "directories": {
                "projects": self.projects_dir.exists(),
                "active": self.active_dir.exists(),
                "archived": self.archived_dir.exists()
            },
            "environment": {
                "WAYGATE_MODE": WAYGATE_MODE,
                "WAYGATE_LOG_LEVEL": log_level,
                "WAYGATE_PROJECTS_DIR": WAYGATE_PROJECTS_DIR
            },
            "timestamp": datetime.now().isoformat()
        }

        logger.info(f"Diagnostics: {diagnostics}")
        return diagnostics


async def main():
    """
    Main entry point.
    """
    server = WaygateMCPServer()

    # Run diagnostics on startup
    diagnostics = await server.run_diagnostics()
    logger.info(f"Server diagnostics: {diagnostics}")

    # Start stdio communication
    await server.run_stdio()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)