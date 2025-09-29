#!/usr/bin/env python3
"""
MCP Tools Implementation for Waygate MCP Server
Real tool handlers that replace placeholder responses
"""

import os
import json
import asyncio
import subprocess
import logging
import aiohttp
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger("waygate_mcp.tools")

class MCPToolError(Exception):
    """Custom exception for MCP tool errors"""
    pass

class MCPToolsHandler:
    """Handler for all MCP tools with security validation"""

    def __init__(self, base_path: str = "/home/jeremy"):
        self.base_path = Path(base_path)
        self.allowed_paths = [
            self.base_path / "waygate-mcp",
            self.base_path / "projects",
            Path("/tmp"),
            Path("/var/tmp")
        ]

    def _validate_path(self, path_str: str) -> Path:
        """Validate file path is within allowed directories"""
        try:
            path = Path(path_str).resolve()

            # Check if path is within allowed directories
            for allowed in self.allowed_paths:
                try:
                    path.relative_to(allowed.resolve())
                    return path
                except ValueError:
                    continue

            raise MCPToolError(f"Path not allowed: {path}")

        except Exception as e:
            raise MCPToolError(f"Invalid path: {str(e)}")

    def _validate_command(self, command: str) -> str:
        """Validate command for security"""
        dangerous_commands = [
            'rm -rf', 'sudo', 'chmod 777', 'mkfs', 'dd if=',
            'curl', 'wget', 'nc ', 'netcat', '>/dev/', 'format'
        ]

        command_lower = command.lower()
        for dangerous in dangerous_commands:
            if dangerous in command_lower:
                raise MCPToolError(f"Dangerous command not allowed: {dangerous}")

        return command

    async def execute_command(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute system command with safety validation"""
        try:
            command = parameters.get("command")
            timeout = parameters.get("timeout", 30)

            if not command:
                raise MCPToolError("Command parameter is required")

            # Validate command
            validated_command = self._validate_command(command)

            logger.info(f"Executing command: {validated_command}")

            # Execute command with timeout
            process = await asyncio.create_subprocess_shell(
                validated_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.base_path
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                raise MCPToolError(f"Command timed out after {timeout} seconds")

            return {
                "success": True,
                "stdout": stdout.decode('utf-8', errors='replace'),
                "stderr": stderr.decode('utf-8', errors='replace'),
                "return_code": process.returncode,
                "command": validated_command
            }

        except MCPToolError:
            raise
        except Exception as e:
            logger.error(f"Command execution failed: {str(e)}")
            raise MCPToolError(f"Command execution failed: {str(e)}")

    async def read_file(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Read file contents with safety validation"""
        try:
            path_str = parameters.get("path")
            encoding = parameters.get("encoding", "utf-8")

            if not path_str:
                raise MCPToolError("Path parameter is required")

            # Validate path
            file_path = self._validate_path(path_str)

            if not file_path.exists():
                raise MCPToolError(f"File does not exist: {file_path}")

            if not file_path.is_file():
                raise MCPToolError(f"Path is not a file: {file_path}")

            # Check file size (limit to 10MB)
            file_size = file_path.stat().st_size
            if file_size > 10 * 1024 * 1024:
                raise MCPToolError(f"File too large: {file_size} bytes")

            logger.info(f"Reading file: {file_path}")

            # Read file content
            content = file_path.read_text(encoding=encoding)

            return {
                "success": True,
                "content": content,
                "path": str(file_path),
                "size": file_size,
                "encoding": encoding
            }

        except MCPToolError:
            raise
        except Exception as e:
            logger.error(f"File read failed: {str(e)}")
            raise MCPToolError(f"File read failed: {str(e)}")

    async def write_file(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Write content to file with safety validation"""
        try:
            path_str = parameters.get("path")
            content = parameters.get("content")
            encoding = parameters.get("encoding", "utf-8")

            if not path_str:
                raise MCPToolError("Path parameter is required")

            if content is None:
                raise MCPToolError("Content parameter is required")

            # Validate path
            file_path = self._validate_path(path_str)

            # Create directory if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Check content size (limit to 5MB)
            content_size = len(content.encode(encoding))
            if content_size > 5 * 1024 * 1024:
                raise MCPToolError(f"Content too large: {content_size} bytes")

            logger.info(f"Writing file: {file_path}")

            # Write file content
            file_path.write_text(content, encoding=encoding)

            return {
                "success": True,
                "path": str(file_path),
                "size": content_size,
                "encoding": encoding
            }

        except MCPToolError:
            raise
        except Exception as e:
            logger.error(f"File write failed: {str(e)}")
            raise MCPToolError(f"File write failed: {str(e)}")

    async def list_directory(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """List directory contents with filtering"""
        try:
            path_str = parameters.get("path")
            recursive = parameters.get("recursive", False)
            pattern = parameters.get("pattern", "*")

            if not path_str:
                raise MCPToolError("Path parameter is required")

            # Validate path
            dir_path = self._validate_path(path_str)

            if not dir_path.exists():
                raise MCPToolError(f"Directory does not exist: {dir_path}")

            if not dir_path.is_dir():
                raise MCPToolError(f"Path is not a directory: {dir_path}")

            logger.info(f"Listing directory: {dir_path}")

            # List directory contents
            entries = []

            if recursive:
                for item in dir_path.rglob(pattern):
                    entries.append(self._get_file_info(item))
            else:
                for item in dir_path.glob(pattern):
                    entries.append(self._get_file_info(item))

            return {
                "success": True,
                "path": str(dir_path),
                "entries": entries,
                "count": len(entries),
                "recursive": recursive,
                "pattern": pattern
            }

        except MCPToolError:
            raise
        except Exception as e:
            logger.error(f"Directory listing failed: {str(e)}")
            raise MCPToolError(f"Directory listing failed: {str(e)}")

    async def search_files(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Search for files by content or name"""
        try:
            query = parameters.get("query")
            search_path = parameters.get("path", ".")
            search_type = parameters.get("type", "both")

            if not query:
                raise MCPToolError("Query parameter is required")

            # Validate path
            base_path = self._validate_path(search_path)

            if not base_path.exists():
                raise MCPToolError(f"Search path does not exist: {base_path}")

            logger.info(f"Searching files: query='{query}', path='{base_path}', type='{search_type}'")

            results = []

            for file_path in base_path.rglob("*"):
                if file_path.is_file():
                    match_found = False
                    match_type = []

                    # Search filename
                    if search_type in ["filename", "both"]:
                        if query.lower() in file_path.name.lower():
                            match_found = True
                            match_type.append("filename")

                    # Search content (only for text files under 1MB)
                    if search_type in ["content", "both"] and file_path.stat().st_size < 1024 * 1024:
                        try:
                            content = file_path.read_text(encoding='utf-8', errors='ignore')
                            if query.lower() in content.lower():
                                match_found = True
                                match_type.append("content")
                        except:
                            pass  # Skip binary files or unreadable files

                    if match_found:
                        file_info = self._get_file_info(file_path)
                        file_info["match_type"] = match_type
                        results.append(file_info)

            return {
                "success": True,
                "query": query,
                "search_path": str(base_path),
                "search_type": search_type,
                "results": results,
                "count": len(results)
            }

        except MCPToolError:
            raise
        except Exception as e:
            logger.error(f"File search failed: {str(e)}")
            raise MCPToolError(f"File search failed: {str(e)}")

    async def http_request(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP requests for external API calls (like X/Twitter API)"""
        try:
            method = parameters.get("method", "GET").upper()
            url = parameters.get("url")
            headers = parameters.get("headers", {})
            json_data = parameters.get("json")
            data = parameters.get("data")
            timeout = parameters.get("timeout", 30)

            if not url:
                raise MCPToolError("URL parameter is required")

            # Security validation: only allow HTTPS for external APIs
            if not url.startswith("https://"):
                raise MCPToolError("Only HTTPS URLs are allowed for external requests")

            logger.info(f"Making HTTP {method} request to: {url}")

            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=json_data,
                    data=data
                ) as response:
                    response_text = await response.text()

                    # Try to parse as JSON, fallback to text
                    try:
                        response_data = await response.json() if response_text else None
                    except:
                        response_data = response_text

                    return {
                        "success": True,
                        "status_code": response.status,
                        "headers": dict(response.headers),
                        "data": response_data,
                        "url": url,
                        "method": method
                    }

        except MCPToolError:
            raise
        except aiohttp.ClientTimeout:
            raise MCPToolError(f"Request timeout after {timeout} seconds")
        except aiohttp.ClientError as e:
            raise MCPToolError(f"HTTP client error: {str(e)}")
        except Exception as e:
            logger.error(f"HTTP request failed: {str(e)}")
            raise MCPToolError(f"HTTP request failed: {str(e)}")

    def _get_file_info(self, path: Path) -> Dict[str, Any]:
        """Get file/directory information"""
        try:
            stat = path.stat()
            return {
                "name": path.name,
                "path": str(path),
                "type": "directory" if path.is_dir() else "file",
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "permissions": oct(stat.st_mode)[-3:]
            }
        except Exception:
            return {
                "name": path.name,
                "path": str(path),
                "type": "unknown",
                "error": "Could not get file info"
            }

# Global tools handler instance
tools_handler = MCPToolsHandler()

# Tool registry for easy access
TOOL_REGISTRY = {
    "execute_command": tools_handler.execute_command,
    "read_file": tools_handler.read_file,
    "write_file": tools_handler.write_file,
    "list_directory": tools_handler.list_directory,
    "search_files": tools_handler.search_files,
    "http_request": tools_handler.http_request
}

async def execute_tool(tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a specific MCP tool"""
    try:
        if tool_name not in TOOL_REGISTRY:
            available_tools = list(TOOL_REGISTRY.keys())
            raise MCPToolError(f"Unknown tool: {tool_name}. Available tools: {available_tools}")

        tool_func = TOOL_REGISTRY[tool_name]
        result = await tool_func(parameters)

        return {
            "tool": tool_name,
            "status": "success",
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }

    except MCPToolError as e:
        logger.error(f"Tool execution failed: {tool_name} - {str(e)}")
        return {
            "tool": tool_name,
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Unexpected tool error: {tool_name} - {str(e)}")
        return {
            "tool": tool_name,
            "status": "error",
            "error": f"Unexpected error: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }

def get_available_tools() -> List[Dict[str, Any]]:
    """Get list of available tools with their schemas"""
    return [
        {
            "name": "execute_command",
            "description": "Execute system commands with safety validation",
            "parameters": {
                "command": {"type": "string", "required": True},
                "timeout": {"type": "integer", "default": 30}
            }
        },
        {
            "name": "read_file",
            "description": "Read file contents with safety validation",
            "parameters": {
                "path": {"type": "string", "required": True},
                "encoding": {"type": "string", "default": "utf-8"}
            }
        },
        {
            "name": "write_file",
            "description": "Write content to file with safety validation",
            "parameters": {
                "path": {"type": "string", "required": True},
                "content": {"type": "string", "required": True},
                "encoding": {"type": "string", "default": "utf-8"}
            }
        },
        {
            "name": "list_directory",
            "description": "List directory contents with filtering",
            "parameters": {
                "path": {"type": "string", "required": True},
                "recursive": {"type": "boolean", "default": False},
                "pattern": {"type": "string", "default": "*"}
            }
        },
        {
            "name": "search_files",
            "description": "Search for files by content or name",
            "parameters": {
                "query": {"type": "string", "required": True},
                "path": {"type": "string", "default": "."},
                "type": {"type": "string", "enum": ["content", "filename", "both"], "default": "both"}
            }
        },
        {
            "name": "http_request",
            "description": "Make HTTP requests for external API calls (X/Twitter, etc.)",
            "parameters": {
                "method": {"type": "string", "default": "GET"},
                "url": {"type": "string", "required": True},
                "headers": {"type": "object", "default": {}},
                "json": {"type": "object", "default": None},
                "data": {"type": "string", "default": None},
                "timeout": {"type": "integer", "default": 30}
            }
        }
    ]