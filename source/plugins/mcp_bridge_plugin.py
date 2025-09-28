#!/usr/bin/env python3
"""
MCP Bridge Plugin Base Class
For integrating external MCP servers into Waygate MCP
"""

import json
import asyncio
import logging
import subprocess
from abc import abstractmethod
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone

from .base_plugin import BasePlugin

logger = logging.getLogger("waygate_mcp.mcp_bridge")

class MCPCommunicationError(Exception):
    """Exception raised when MCP communication fails"""
    pass

class MCPBridgePlugin(BasePlugin):
    """
    Base class for integrating external MCP servers into Waygate MCP

    This class provides the foundation for embedding external MCP servers
    as internal Waygate plugins, handling communication, credential management,
    and tool proxying.

    Supported Communication Methods:
    - stdio: Standard input/output communication with external process
    - http: HTTP API communication
    - python: Direct Python module integration
    - subprocess: Execute external MCP server as subprocess
    """

    def __init__(self, mcp_config: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.mcp_config = mcp_config or {}
        self.mcp_client = None
        self.credentials = {}
        self.mcp_tools = []
        self.communication_method = "stdio"  # Default
        self.process = None
        self.is_initialized = False

        # MCP server status
        self.mcp_status = {
            "connected": False,
            "last_sync": None,
            "tool_count": 0,
            "error_count": 0,
            "last_error": None
        }

    @abstractmethod
    async def get_mcp_server_command(self) -> List[str]:
        """
        Get the command to start the external MCP server

        Returns:
            List of command arguments (e.g., ['npx', 'firebase-tools', '--mcp'])
        """
        pass

    @abstractmethod
    async def get_mcp_server_config(self) -> Dict[str, Any]:
        """
        Get configuration for the MCP server

        Returns:
            Configuration dictionary
        """
        pass

    async def initialize(self):
        """Initialize the MCP bridge plugin"""
        try:
            logger.info(f"🔄 Initializing MCP bridge: {self.name}")

            # Load credentials from configuration
            await self._load_credentials()

            # Initialize MCP client based on communication method
            await self.initialize_mcp_client()

            # Fetch available tools from MCP server
            await self._sync_mcp_tools()

            self.is_initialized = True
            self.mcp_status["connected"] = True
            self.mcp_status["last_sync"] = datetime.now(timezone.utc)

            logger.info(f"✅ MCP bridge initialized: {self.name} "
                       f"({len(self.mcp_tools)} tools available)")

        except Exception as e:
            error_msg = f"MCP bridge initialization failed: {e}"
            logger.error(f"❌ {error_msg}")
            self.mcp_status["last_error"] = error_msg
            self.mcp_status["error_count"] += 1
            raise MCPCommunicationError(error_msg)

    async def initialize_mcp_client(self):
        """
        Initialize connection to external MCP server

        This method sets up communication with the external MCP server
        based on the configured communication method.
        """
        method = self.mcp_config.get("communication_method", "stdio")
        self.communication_method = method

        logger.debug(f"🔗 Initializing MCP client: {method}")

        try:
            if method == "stdio":
                await self._initialize_stdio_client()
            elif method == "http":
                await self._initialize_http_client()
            elif method == "python":
                await self._initialize_python_client()
            elif method == "subprocess":
                await self._initialize_subprocess_client()
            else:
                raise MCPCommunicationError(f"Unsupported communication method: {method}")

        except Exception as e:
            logger.error(f"❌ MCP client initialization failed: {e}")
            raise

    async def _initialize_stdio_client(self):
        """Initialize stdio-based MCP client"""
        command = await self.get_mcp_server_command()

        logger.debug(f"🚀 Starting MCP server process: {' '.join(command)}")

        # Start the external MCP server process
        self.process = await asyncio.create_subprocess_exec(
            *command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=await self._get_mcp_env()
        )

        # Verify process started successfully
        await asyncio.sleep(1)  # Give process time to start
        if self.process.returncode is not None:
            stderr_output = await self.process.stderr.read()
            raise MCPCommunicationError(f"MCP server process failed to start: {stderr_output.decode()}")

        logger.debug("✅ MCP server process started successfully")

    async def _initialize_http_client(self):
        """Initialize HTTP-based MCP client"""
        import httpx

        base_url = self.mcp_config.get("base_url")
        if not base_url:
            raise MCPCommunicationError("base_url required for HTTP communication")

        self.mcp_client = httpx.AsyncClient(
            base_url=base_url,
            headers=await self._get_http_headers(),
            timeout=30.0
        )

        # Test connection
        try:
            response = await self.mcp_client.get("/health")
            response.raise_for_status()
            logger.debug("✅ HTTP MCP server connection verified")
        except Exception as e:
            raise MCPCommunicationError(f"HTTP MCP server connection failed: {e}")

    async def _initialize_python_client(self):
        """Initialize direct Python module integration"""
        module_name = self.mcp_config.get("module_name")
        if not module_name:
            raise MCPCommunicationError("module_name required for Python communication")

        try:
            import importlib
            self.mcp_client = importlib.import_module(module_name)
            logger.debug(f"✅ Python module loaded: {module_name}")
        except ImportError as e:
            raise MCPCommunicationError(f"Failed to import Python module: {e}")

    async def _initialize_subprocess_client(self):
        """Initialize subprocess-based MCP client"""
        # Similar to stdio but for one-off command execution
        self.mcp_client = "subprocess"
        logger.debug("✅ Subprocess MCP client ready")

    async def get_tools(self) -> List[Dict[str, Any]]:
        """
        Get all tools available from this MCP bridge

        Returns:
            List of tool definitions
        """
        if not self.is_initialized:
            await self.initialize()

        return self.mcp_tools

    async def execute(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool through the MCP bridge

        Args:
            tool_name: Name of the tool to execute
            parameters: Tool parameters

        Returns:
            Tool execution result
        """
        if not self.is_initialized:
            return {
                "success": False,
                "error": "MCP bridge not initialized"
            }

        try:
            logger.debug(f"🔧 Executing MCP tool: {tool_name}")

            # Execute tool based on communication method
            if self.communication_method == "stdio":
                result = await self._execute_stdio_tool(tool_name, parameters)
            elif self.communication_method == "http":
                result = await self._execute_http_tool(tool_name, parameters)
            elif self.communication_method == "python":
                result = await self._execute_python_tool(tool_name, parameters)
            elif self.communication_method == "subprocess":
                result = await self._execute_subprocess_tool(tool_name, parameters)
            else:
                raise MCPCommunicationError(f"Unsupported communication method: {self.communication_method}")

            logger.debug(f"✅ MCP tool executed successfully: {tool_name}")
            return result

        except Exception as e:
            error_msg = f"MCP tool execution failed: {e}"
            logger.error(f"❌ {error_msg}")
            self.mcp_status["error_count"] += 1
            self.mcp_status["last_error"] = error_msg

            return {
                "success": False,
                "error": error_msg,
                "tool": tool_name,
                "parameters": parameters
            }

    async def _execute_stdio_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool via stdio communication"""
        if not self.process or self.process.returncode is not None:
            raise MCPCommunicationError("MCP server process not running")

        # Construct MCP message
        message = {
            "jsonrpc": "2.0",
            "id": f"waygate_{int(datetime.now().timestamp())}",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": parameters
            }
        }

        # Send message to MCP server
        message_json = json.dumps(message) + "\n"
        self.process.stdin.write(message_json.encode())
        await self.process.stdin.drain()

        # Read response
        response_line = await self.process.stdout.readline()
        response = json.loads(response_line.decode().strip())

        if "error" in response:
            raise MCPCommunicationError(f"MCP server error: {response['error']}")

        return {
            "success": True,
            "result": response.get("result", {}),
            "tool": tool_name
        }

    async def _execute_http_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool via HTTP API"""
        if not self.mcp_client:
            raise MCPCommunicationError("HTTP MCP client not initialized")

        payload = {
            "tool": tool_name,
            "parameters": parameters
        }

        response = await self.mcp_client.post("/tools/execute", json=payload)
        response.raise_for_status()

        result = response.json()
        return {
            "success": True,
            "result": result,
            "tool": tool_name
        }

    async def _execute_python_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool via direct Python call"""
        if not self.mcp_client:
            raise MCPCommunicationError("Python MCP client not initialized")

        # Call the function directly
        if hasattr(self.mcp_client, tool_name):
            func = getattr(self.mcp_client, tool_name)
            result = await func(**parameters) if asyncio.iscoroutinefunction(func) else func(**parameters)

            return {
                "success": True,
                "result": result,
                "tool": tool_name
            }
        else:
            raise MCPCommunicationError(f"Tool not found in Python module: {tool_name}")

    async def _execute_subprocess_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool via subprocess call"""
        command = await self.get_mcp_server_command()
        command.extend(["--tool", tool_name])

        # Add parameters as command line arguments
        for key, value in parameters.items():
            command.extend([f"--{key}", str(value)])

        # Execute command
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=await self._get_mcp_env()
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise MCPCommunicationError(f"Subprocess execution failed: {stderr.decode()}")

        try:
            result = json.loads(stdout.decode())
        except json.JSONDecodeError:
            result = {"output": stdout.decode()}

        return {
            "success": True,
            "result": result,
            "tool": tool_name
        }

    async def _sync_mcp_tools(self):
        """Sync tools from external MCP server"""
        try:
            if self.communication_method == "stdio":
                tools = await self._get_stdio_tools()
            elif self.communication_method == "http":
                tools = await self._get_http_tools()
            elif self.communication_method == "python":
                tools = await self._get_python_tools()
            elif self.communication_method == "subprocess":
                tools = await self._get_subprocess_tools()
            else:
                tools = []

            self.mcp_tools = tools
            self.mcp_status["tool_count"] = len(tools)

            logger.debug(f"🔄 Synced {len(tools)} tools from MCP server")

        except Exception as e:
            logger.error(f"❌ Tool sync failed: {e}")
            self.mcp_tools = []

    async def _get_stdio_tools(self) -> List[Dict[str, Any]]:
        """Get tools via stdio communication"""
        if not self.process or self.process.returncode is not None:
            return []

        # Send tools/list request
        message = {
            "jsonrpc": "2.0",
            "id": "waygate_tools_list",
            "method": "tools/list"
        }

        message_json = json.dumps(message) + "\n"
        self.process.stdin.write(message_json.encode())
        await self.process.stdin.drain()

        # Read response
        response_line = await self.process.stdout.readline()
        response = json.loads(response_line.decode().strip())

        return response.get("result", {}).get("tools", [])

    async def _get_http_tools(self) -> List[Dict[str, Any]]:
        """Get tools via HTTP API"""
        if not self.mcp_client:
            return []

        response = await self.mcp_client.get("/tools")
        response.raise_for_status()
        return response.json().get("tools", [])

    async def _get_python_tools(self) -> List[Dict[str, Any]]:
        """Get tools from Python module"""
        if not self.mcp_client:
            return []

        if hasattr(self.mcp_client, "get_tools"):
            return await self.mcp_client.get_tools()
        else:
            # Inspect module for available functions
            import inspect
            functions = inspect.getmembers(self.mcp_client, inspect.isfunction)
            tools = []

            for name, func in functions:
                if not name.startswith("_"):
                    tools.append({
                        "name": name,
                        "description": func.__doc__ or f"{name} function",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    })

            return tools

    async def _get_subprocess_tools(self) -> List[Dict[str, Any]]:
        """Get tools via subprocess call"""
        command = await self.get_mcp_server_command()
        command.append("--list-tools")

        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=await self._get_mcp_env()
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            logger.error(f"Failed to get tools: {stderr.decode()}")
            return []

        try:
            result = json.loads(stdout.decode())
            return result.get("tools", [])
        except json.JSONDecodeError:
            return []

    async def _load_credentials(self):
        """Load credentials from configuration"""
        credentials_config = self.mcp_config.get("credentials", {})
        self.credentials = credentials_config
        logger.debug(f"🔑 Credentials loaded for MCP server")

    async def _get_mcp_env(self) -> Dict[str, str]:
        """Get environment variables for MCP server process"""
        import os
        env = os.environ.copy()

        # Add credentials as environment variables
        for key, value in self.credentials.items():
            env[key.upper()] = str(value)

        return env

    async def _get_http_headers(self) -> Dict[str, str]:
        """Get HTTP headers including authentication"""
        headers = {"Content-Type": "application/json"}

        # Add authentication headers
        if "api_key" in self.credentials:
            headers["Authorization"] = f"Bearer {self.credentials['api_key']}"
        elif "token" in self.credentials:
            headers["Authorization"] = f"Token {self.credentials['token']}"

        return headers

    async def configure_mcp_server(self, config: Dict[str, Any]):
        """
        Configure the MCP server with provided configuration

        Args:
            config: Configuration dictionary
        """
        self.mcp_config.update(config)
        logger.debug(f"🔧 MCP server configured: {self.name}")

        # Re-initialize if already initialized
        if self.is_initialized:
            await self.cleanup()
            await self.initialize()

    async def cleanup(self):
        """Clean up MCP bridge resources"""
        try:
            # Close HTTP client
            if self.communication_method == "http" and self.mcp_client:
                await self.mcp_client.aclose()

            # Terminate subprocess
            if self.process:
                self.process.terminate()
                try:
                    await asyncio.wait_for(self.process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    self.process.kill()
                    await self.process.wait()

            self.is_initialized = False
            self.mcp_status["connected"] = False
            logger.debug(f"🧹 MCP bridge cleaned up: {self.name}")

        except Exception as e:
            logger.error(f"❌ MCP bridge cleanup failed: {e}")

    def get_info(self) -> Dict[str, str]:
        """Get MCP bridge plugin information"""
        base_info = super().get_info()
        base_info.update({
            "communication_method": self.communication_method,
            "mcp_status": self.mcp_status,
            "tool_count": len(self.mcp_tools),
            "is_initialized": self.is_initialized
        })
        return base_info