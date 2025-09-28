#!/usr/bin/env python3
"""
MCP Integration Module for Waygate MCP
Handles initialization and management of integrated MCP servers
"""

import os
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional

from database import (
    db_manager, initialize_default_mcp_servers, list_mcp_servers,
    get_mcp_server, update_mcp_server_status
)
from plugins.plugin_loader import get_plugin_loader

logger = logging.getLogger("waygate_mcp.mcp_integration")

class MCPIntegrationManager:
    """
    Manages the integration of external MCP servers into Waygate MCP

    This class handles:
    - Loading MCP server configurations
    - Initializing MCP bridge plugins
    - Managing MCP server lifecycle
    - Providing unified access to all MCP tools
    """

    def __init__(self):
        self.plugin_loader = None
        self.mcp_servers = {}
        self.is_initialized = False

    async def initialize(self):
        """Initialize the MCP integration system"""
        try:
            logger.info("🚀 Initializing MCP integration system...")

            # Get plugin loader
            self.plugin_loader = await get_plugin_loader(db_manager)

            # Initialize default MCP server configurations if needed
            if os.getenv("MCP_AUTO_INITIALIZE", "true").lower() == "true":
                await self._initialize_default_configurations()

            # Load and configure enabled MCP servers
            await self._load_enabled_mcp_servers()

            self.is_initialized = True
            logger.info(f"✅ MCP integration system initialized with "
                       f"{len(self.mcp_servers)} active MCP servers")

        except Exception as e:
            logger.error(f"❌ MCP integration initialization failed: {e}")
            raise

    async def _initialize_default_configurations(self):
        """Initialize default MCP server configurations"""
        try:
            # Check if we already have MCP servers configured
            existing_servers = await list_mcp_servers()

            if not existing_servers:
                logger.info("📋 No MCP servers found, initializing defaults...")
                await initialize_default_mcp_servers()
            else:
                logger.debug(f"📋 Found {len(existing_servers)} existing MCP servers")

        except Exception as e:
            logger.error(f"❌ Failed to initialize default MCP configurations: {e}")

    async def _load_enabled_mcp_servers(self):
        """Load and configure enabled MCP servers"""
        try:
            # Get list of enabled MCP servers from environment
            enabled_servers = os.getenv("MCP_SERVERS_ENABLED", "").split(",")
            enabled_servers = [s.strip() for s in enabled_servers if s.strip()]

            if not enabled_servers:
                logger.warning("⚠️ No MCP servers enabled in MCP_SERVERS_ENABLED")
                return

            logger.info(f"🔄 Loading enabled MCP servers: {', '.join(enabled_servers)}")

            # Load each enabled MCP server
            for server_type in enabled_servers:
                await self._load_mcp_server(server_type)

        except Exception as e:
            logger.error(f"❌ Failed to load enabled MCP servers: {e}")

    async def _load_mcp_server(self, server_type: str):
        """Load a specific MCP server by type"""
        try:
            # Find MCP server configuration by type
            all_servers = await list_mcp_servers()
            server_config = None

            for server in all_servers:
                if server["server_type"] == server_type:
                    server_config = server
                    break

            if not server_config:
                logger.error(f"❌ MCP server configuration not found: {server_type}")
                return

            # Get the corresponding plugin
            plugin_name = f"{server_type}_mcp_plugin"

            if plugin_name not in self.plugin_loader.loaded_plugins:
                logger.error(f"❌ MCP plugin not found: {plugin_name}")
                await update_mcp_server_status(
                    server_config["name"], "error",
                    f"Plugin not found: {plugin_name}"
                )
                return

            # Configure the MCP plugin
            mcp_plugin = self.plugin_loader.loaded_plugins[plugin_name]

            # Load environment-based credentials
            credentials = await self._load_mcp_credentials(server_type)
            server_config["credentials"].update(credentials)

            # Configure the plugin
            if hasattr(mcp_plugin, 'configure_mcp_server'):
                await mcp_plugin.configure_mcp_server(server_config)

            # Store the configured MCP server
            self.mcp_servers[server_config["name"]] = {
                "config": server_config,
                "plugin": mcp_plugin,
                "status": "active"
            }

            # Update database status
            tool_count = len(await mcp_plugin.get_tools())
            await update_mcp_server_status(
                server_config["name"], "active",
                tool_count=tool_count
            )

            logger.info(f"✅ MCP server loaded: {server_config['display_name']} "
                       f"({tool_count} tools)")

        except Exception as e:
            logger.error(f"❌ Failed to load MCP server {server_type}: {e}")

            if server_config:
                await update_mcp_server_status(
                    server_config["name"], "error", str(e)
                )

    async def _load_mcp_credentials(self, server_type: str) -> Dict[str, Any]:
        """Load MCP server credentials from environment variables"""
        credentials = {}

        try:
            if server_type == "firebase":
                credentials = {
                    "FIREBASE_PROJECT_ID": os.getenv("FIREBASE_PROJECT_ID"),
                    "FIREBASE_REGION": os.getenv("FIREBASE_REGION"),
                    "GOOGLE_APPLICATION_CREDENTIALS": os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
                }

            elif server_type == "bigquery":
                credentials = {
                    "GOOGLE_CLOUD_PROJECT": os.getenv("GOOGLE_CLOUD_PROJECT"),
                    "BIGQUERY_DATASET": os.getenv("BIGQUERY_DATASET"),
                    "GOOGLE_APPLICATION_CREDENTIALS": os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
                }

            elif server_type == "github":
                credentials = {
                    "GITHUB_TOKEN": os.getenv("GITHUB_TOKEN"),
                    "GITHUB_OWNER": os.getenv("GITHUB_OWNER")
                }

            elif server_type == "n8n":
                credentials = {
                    "N8N_API_URL": os.getenv("N8N_API_URL"),
                    "N8N_API_KEY": os.getenv("N8N_API_KEY")
                }

            elif server_type == "docker_hub":
                credentials = {
                    "DOCKER_HUB_TOKEN": os.getenv("DOCKER_HUB_TOKEN"),
                    "DOCKER_HUB_USERNAME": os.getenv("DOCKER_HUB_USERNAME")
                }

            elif server_type == "slack":
                credentials = {
                    "SLACK_BOT_TOKEN": os.getenv("SLACK_BOT_TOKEN"),
                    "SLACK_APP_TOKEN": os.getenv("SLACK_APP_TOKEN"),
                    "SLACK_WORKSPACE": os.getenv("SLACK_WORKSPACE")
                }

            # Filter out None values
            credentials = {k: v for k, v in credentials.items() if v is not None}

            logger.debug(f"🔑 Loaded credentials for {server_type}: "
                        f"{list(credentials.keys())}")

        except Exception as e:
            logger.error(f"❌ Failed to load credentials for {server_type}: {e}")

        return credentials

    async def get_all_mcp_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all tools from all active MCP servers

        Returns:
            Dictionary mapping MCP server names to their tools
        """
        all_tools = {}

        for server_name, server_info in self.mcp_servers.items():
            try:
                plugin = server_info["plugin"]
                tools = await plugin.get_tools()
                all_tools[server_name] = tools

                logger.debug(f"🔧 Retrieved {len(tools)} tools from {server_name}")

            except Exception as e:
                logger.error(f"❌ Failed to get tools from {server_name}: {e}")
                all_tools[server_name] = []

        return all_tools

    async def execute_mcp_tool(self, server_name: str, tool_name: str,
                              parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool on a specific MCP server

        Args:
            server_name: Name of the MCP server
            tool_name: Name of the tool to execute
            parameters: Tool parameters

        Returns:
            Tool execution result
        """
        if server_name not in self.mcp_servers:
            return {
                "success": False,
                "error": f"MCP server not found: {server_name}",
                "available_servers": list(self.mcp_servers.keys())
            }

        try:
            server_info = self.mcp_servers[server_name]
            plugin = server_info["plugin"]

            logger.debug(f"🔧 Executing MCP tool: {server_name}.{tool_name}")

            result = await plugin.execute(tool_name, parameters)

            # Add context information
            if result.get("success"):
                result["mcp_server"] = server_name
                result["server_type"] = server_info["config"]["server_type"]

            return result

        except Exception as e:
            error_msg = f"MCP tool execution failed: {e}"
            logger.error(f"❌ {error_msg}")

            return {
                "success": False,
                "error": error_msg,
                "mcp_server": server_name,
                "tool": tool_name
            }

    async def get_mcp_status(self) -> Dict[str, Any]:
        """
        Get status of all MCP servers

        Returns:
            MCP integration status information
        """
        server_status = []

        for server_name, server_info in self.mcp_servers.items():
            try:
                plugin = server_info["plugin"]
                config = server_info["config"]

                plugin_info = plugin.get_info()
                tool_count = len(await plugin.get_tools())

                server_status.append({
                    "name": server_name,
                    "display_name": config["display_name"],
                    "server_type": config["server_type"],
                    "status": server_info["status"],
                    "tool_count": tool_count,
                    "communication_method": config.get("communication_method", "unknown"),
                    "plugin_info": plugin_info
                })

            except Exception as e:
                server_status.append({
                    "name": server_name,
                    "status": "error",
                    "error": str(e)
                })

        return {
            "integration_status": "active" if self.is_initialized else "inactive",
            "total_servers": len(self.mcp_servers),
            "active_servers": len([s for s in server_status if s.get("status") == "active"]),
            "total_tools": sum(s.get("tool_count", 0) for s in server_status),
            "servers": server_status
        }

    async def reload_mcp_server(self, server_name: str) -> bool:
        """
        Reload a specific MCP server

        Args:
            server_name: Name of the MCP server to reload

        Returns:
            True if reload successful, False otherwise
        """
        try:
            if server_name not in self.mcp_servers:
                logger.error(f"❌ MCP server not found for reload: {server_name}")
                return False

            server_info = self.mcp_servers[server_name]
            server_type = server_info["config"]["server_type"]

            logger.info(f"🔄 Reloading MCP server: {server_name}")

            # Remove from active servers
            del self.mcp_servers[server_name]

            # Reload the server
            await self._load_mcp_server(server_type)

            logger.info(f"✅ MCP server reloaded: {server_name}")
            return True

        except Exception as e:
            logger.error(f"❌ MCP server reload failed: {e}")
            return False

# Global MCP integration manager
mcp_integration_manager = MCPIntegrationManager()

async def initialize_mcp_integration():
    """Initialize the MCP integration system"""
    await mcp_integration_manager.initialize()

async def get_mcp_manager():
    """Get the global MCP integration manager"""
    if not mcp_integration_manager.is_initialized:
        await mcp_integration_manager.initialize()
    return mcp_integration_manager