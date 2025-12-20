#!/usr/bin/env python3
"""
Plugin Loader for Waygate MCP
Handles dynamic loading of plugins and MCP server integrations
"""

import os
import sys
import json
import asyncio
import importlib
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Type
from datetime import datetime, timezone

from .base_plugin import BasePlugin

logger = logging.getLogger("waygate_mcp.plugin_loader")

class PluginLoadError(Exception):
    """Exception raised when plugin loading fails"""
    pass

class PluginLoader:
    """
    Dynamic plugin loading with MCP server support

    Features:
    - Auto-discovery of plugins in plugins directory
    - MCP server integration support
    - Hot-reloading capabilities
    - Plugin lifecycle management
    - Error handling and recovery
    """

    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        self.loaded_plugins: Dict[str, BasePlugin] = {}
        self.plugin_configs: Dict[str, Dict[str, Any]] = {}
        self.mcp_servers: Dict[str, Any] = {}
        self.plugins_directory = Path(__file__).parent

        # Plugin status tracking
        self.plugin_stats = {
            "total_loaded": 0,
            "total_failed": 0,
            "last_load_time": None,
            "mcp_servers_active": 0
        }

    async def discover_plugins(self) -> List[str]:
        """
        Discover all available plugins in the plugins directory

        Returns:
            List of plugin module names
        """
        plugin_files = []

        try:
            for file_path in self.plugins_directory.glob("*_plugin.py"):
                if file_path.name not in ["__init__.py", "base_plugin.py"]:
                    plugin_name = file_path.stem
                    plugin_files.append(plugin_name)
                    logger.debug(f"📦 Discovered plugin: {plugin_name}")

            logger.info(f"📦 Found {len(plugin_files)} plugins to load")
            return plugin_files

        except Exception as e:
            logger.error(f"❌ Plugin discovery failed: {e}")
            return []

    async def load_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """
        Load a single plugin by name

        Args:
            plugin_name: Name of the plugin module (without .py extension)

        Returns:
            Loaded plugin instance or None if failed
        """
        try:
            # Import the plugin module
            module_name = f"plugins.{plugin_name}"

            # Remove from sys.modules if already imported (for hot-reloading)
            if module_name in sys.modules:
                importlib.reload(sys.modules[module_name])
            else:
                module = importlib.import_module(module_name)

            # Find the plugin class (should inherit from BasePlugin)
            plugin_class = None
            module = sys.modules[module_name]

            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and
                    issubclass(attr, BasePlugin) and
                    attr != BasePlugin):
                    plugin_class = attr
                    break

            if not plugin_class:
                raise PluginLoadError(f"No plugin class found in {plugin_name}")

            # Instantiate the plugin
            plugin_instance = plugin_class()

            # Load plugin configuration if available
            await self._load_plugin_config(plugin_name, plugin_instance)

            # Initialize plugin if it has initialization method
            if hasattr(plugin_instance, 'initialize'):
                await plugin_instance.initialize()

            # Store the loaded plugin
            self.loaded_plugins[plugin_name] = plugin_instance

            # Update database record
            if self.db_manager:
                await self._update_plugin_status(plugin_name, "active", None)

            logger.info(f"✅ Plugin loaded: {plugin_name} ({plugin_instance.name})")
            return plugin_instance

        except Exception as e:
            error_msg = f"Failed to load plugin {plugin_name}: {e}"
            logger.error(f"❌ {error_msg}")

            # Update database with error
            if self.db_manager:
                await self._update_plugin_status(plugin_name, "error", error_msg)

            self.plugin_stats["total_failed"] += 1
            return None

    async def load_all_plugins(self) -> Dict[str, BasePlugin]:
        """
        Load all discovered plugins

        Returns:
            Dictionary of successfully loaded plugins
        """
        logger.info("🔄 Loading all plugins...")

        try:
            # Discover available plugins
            plugin_names = await self.discover_plugins()

            # Load each plugin
            load_tasks = []
            for plugin_name in plugin_names:
                task = asyncio.create_task(self.load_plugin(plugin_name))
                load_tasks.append((plugin_name, task))

            # Wait for all plugins to load
            results = await asyncio.gather(*[task for _, task in load_tasks],
                                         return_exceptions=True)

            # Process results
            successful_plugins = {}
            for (plugin_name, _), result in zip(load_tasks, results):
                if isinstance(result, BasePlugin):
                    successful_plugins[plugin_name] = result
                    self.plugin_stats["total_loaded"] += 1
                elif isinstance(result, Exception):
                    logger.error(f"❌ Plugin {plugin_name} failed: {result}")
                    self.plugin_stats["total_failed"] += 1

            self.plugin_stats["last_load_time"] = datetime.now(timezone.utc)

            logger.info(f"✅ Plugin loading complete: {len(successful_plugins)} loaded, "
                       f"{self.plugin_stats['total_failed']} failed")

            # Load MCP server configurations
            await self.load_mcp_server_plugins()

            return successful_plugins

        except Exception as e:
            logger.error(f"❌ Failed to load plugins: {e}")
            return {}

    async def load_mcp_server_plugins(self):
        """
        Load MCP server configurations from database
        """
        if not self.db_manager:
            logger.warning("⚠️ No database manager available for MCP server loading")
            return

        try:
            # Query MCP servers from database
            mcp_servers = await self.db_manager.execute_query(
                "SELECT * FROM mcp_servers WHERE status = 'active'"
            )

            for server in mcp_servers:
                server_name = server["name"]
                server_type = server["server_type"]
                config = json.loads(server["config"])

                # Load the corresponding MCP plugin
                plugin_name = f"{server_type}_mcp_plugin"
                if plugin_name in self.loaded_plugins:
                    mcp_plugin = self.loaded_plugins[plugin_name]

                    # Configure the MCP plugin with server config
                    if hasattr(mcp_plugin, 'configure_mcp_server'):
                        await mcp_plugin.configure_mcp_server(config)

                    self.mcp_servers[server_name] = {
                        "plugin": mcp_plugin,
                        "config": config,
                        "status": "active"
                    }

                    self.plugin_stats["mcp_servers_active"] += 1
                    logger.info(f"🔗 MCP server configured: {server_name} ({server_type})")
                else:
                    logger.warning(f"⚠️ MCP plugin not found: {plugin_name}")

        except Exception as e:
            logger.error(f"❌ Failed to load MCP server plugins: {e}")

    async def reload_plugin(self, plugin_name: str) -> bool:
        """
        Hot-reload a specific plugin

        Args:
            plugin_name: Name of the plugin to reload

        Returns:
            True if reload successful, False otherwise
        """
        logger.info(f"🔄 Reloading plugin: {plugin_name}")

        try:
            # Unload existing plugin
            if plugin_name in self.loaded_plugins:
                old_plugin = self.loaded_plugins[plugin_name]

                # Call cleanup if available
                if hasattr(old_plugin, 'cleanup'):
                    await old_plugin.cleanup()

                # Remove from loaded plugins
                del self.loaded_plugins[plugin_name]

            # Reload the plugin
            reloaded_plugin = await self.load_plugin(plugin_name)

            if reloaded_plugin:
                logger.info(f"✅ Plugin reloaded successfully: {plugin_name}")
                return True
            else:
                logger.error(f"❌ Plugin reload failed: {plugin_name}")
                return False

        except Exception as e:
            logger.error(f"❌ Plugin reload error: {e}")
            return False

    async def unload_plugin(self, plugin_name: str) -> bool:
        """
        Unload a specific plugin

        Args:
            plugin_name: Name of the plugin to unload

        Returns:
            True if unload successful, False otherwise
        """
        try:
            if plugin_name not in self.loaded_plugins:
                logger.warning(f"⚠️ Plugin not loaded: {plugin_name}")
                return False

            plugin = self.loaded_plugins[plugin_name]

            # Call cleanup if available
            if hasattr(plugin, 'cleanup'):
                await plugin.cleanup()

            # Remove from loaded plugins
            del self.loaded_plugins[plugin_name]

            # Update database status
            if self.db_manager:
                await self._update_plugin_status(plugin_name, "inactive", None)

            logger.info(f"✅ Plugin unloaded: {plugin_name}")
            return True

        except Exception as e:
            logger.error(f"❌ Plugin unload failed: {e}")
            return False

    async def get_plugin_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all tools from all loaded plugins

        Returns:
            Dictionary mapping plugin names to their tools
        """
        all_tools = {}

        for plugin_name, plugin in self.loaded_plugins.items():
            try:
                tools = await plugin.get_tools()
                all_tools[plugin_name] = tools
            except Exception as e:
                logger.error(f"❌ Failed to get tools from {plugin_name}: {e}")
                all_tools[plugin_name] = []

        return all_tools

    async def execute_plugin_tool(self, plugin_name: str, tool_name: str,
                                parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool from a specific plugin

        Args:
            plugin_name: Name of the plugin
            tool_name: Name of the tool to execute
            parameters: Parameters for the tool

        Returns:
            Tool execution result
        """
        if plugin_name not in self.loaded_plugins:
            return {
                "success": False,
                "error": f"Plugin not found: {plugin_name}"
            }

        try:
            plugin = self.loaded_plugins[plugin_name]
            result = await plugin.execute(tool_name, parameters)

            logger.debug(f"🔧 Tool executed: {plugin_name}.{tool_name}")
            return result

        except Exception as e:
            error_msg = f"Tool execution failed: {e}"
            logger.error(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }

    async def get_plugin_status(self) -> Dict[str, Any]:
        """
        Get overall plugin system status

        Returns:
            Plugin system status information
        """
        plugin_list = []

        for plugin_name, plugin in self.loaded_plugins.items():
            plugin_info = plugin.get_info()
            plugin_info["status"] = "active"
            plugin_info["tools_count"] = len(await plugin.get_tools())
            plugin_list.append(plugin_info)

        mcp_server_list = []
        for server_name, server_info in self.mcp_servers.items():
            mcp_server_list.append({
                "name": server_name,
                "status": server_info["status"],
                "plugin": server_info["plugin"].name
            })

        return {
            "plugins_loaded": len(self.loaded_plugins),
            "plugins_failed": self.plugin_stats["total_failed"],
            "mcp_servers_active": self.plugin_stats["mcp_servers_active"],
            "last_load_time": self.plugin_stats["last_load_time"],
            "plugins": plugin_list,
            "mcp_servers": mcp_server_list
        }

    async def _load_plugin_config(self, plugin_name: str, plugin_instance: BasePlugin):
        """
        Load configuration for a plugin from database

        Args:
            plugin_name: Name of the plugin
            plugin_instance: Plugin instance to configure
        """
        if not self.db_manager:
            return

        try:
            # Query plugin configuration from database
            config_result = await self.db_manager.execute_query(
                "SELECT config FROM plugins WHERE name = ?",
                [plugin_name]
            )

            if config_result:
                config_data = json.loads(config_result[0]["config"])
                self.plugin_configs[plugin_name] = config_data

                # Apply configuration to plugin if it supports it
                if hasattr(plugin_instance, 'configure'):
                    await plugin_instance.configure(config_data)

                logger.debug(f"📋 Plugin configuration loaded: {plugin_name}")

        except Exception as e:
            logger.warning(f"⚠️ Failed to load config for {plugin_name}: {e}")

    async def _update_plugin_status(self, plugin_name: str, status: str,
                                  error_message: Optional[str] = None):
        """
        Update plugin status in database

        Args:
            plugin_name: Name of the plugin
            status: New status ('active', 'inactive', 'error')
            error_message: Error message if status is 'error'
        """
        if not self.db_manager:
            return

        try:
            # Get plugin info
            plugin_info = {}
            if plugin_name in self.loaded_plugins:
                plugin = self.loaded_plugins[plugin_name]
                plugin_info = plugin.get_info()

            # Update or insert plugin record
            await self.db_manager.execute_query("""
                INSERT OR REPLACE INTO plugins
                (name, display_name, version, description, status, error_message,
                 last_loaded, load_count, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP,
                        COALESCE((SELECT load_count FROM plugins WHERE name = ?), 0) + 1,
                        CURRENT_TIMESTAMP)
            """, [
                plugin_name,
                plugin_info.get('name', plugin_name),
                plugin_info.get('version', '1.0.0'),
                plugin_info.get('description', 'Waygate MCP Plugin'),
                status,
                error_message,
                plugin_name
            ])

        except Exception as e:
            logger.error(f"❌ Failed to update plugin status: {e}")

# Global plugin loader instance
plugin_loader = None

async def get_plugin_loader(db_manager=None):
    """
    Get the global plugin loader instance

    Args:
        db_manager: Database manager instance

    Returns:
        PluginLoader instance
    """
    global plugin_loader

    if plugin_loader is None:
        plugin_loader = PluginLoader(db_manager)
        # Initialize plugins on first access
        await plugin_loader.load_all_plugins()

    return plugin_loader

async def initialize_plugins(db_manager=None):
    """
    Initialize the plugin system

    Args:
        db_manager: Database manager instance
    """
    global plugin_loader
    plugin_loader = PluginLoader(db_manager)
    await plugin_loader.load_all_plugins()
    logger.info("🎯 Plugin system initialized")