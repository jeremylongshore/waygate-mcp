"""
Base Plugin Class - Inherit from this to create your own plugins
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BasePlugin(ABC):
    """
    Simple base class for creating MCP plugins.

    To create a plugin:
    1. Create a new file in src/plugins/
    2. Import and inherit from BasePlugin
    3. Implement the required methods
    4. Drop it in the plugins folder - it auto-loads!
    """

    def __init__(self):
        self.name = self.__class__.__name__
        self.version = "1.0.0"
        self.description = "A Waygate MCP Plugin"

    @abstractmethod
    async def get_tools(self) -> List[Dict[str, Any]]:
        """
        Return a list of tools this plugin provides.

        Example return:
        [
            {
                "name": "my_tool",
                "description": "What this tool does",
                "parameters": {
                    "param1": "string",
                    "param2": "optional string"
                }
            }
        ]
        """
        pass

    @abstractmethod
    async def execute(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool from this plugin.

        Args:
            tool_name: Name of the tool to execute
            parameters: Parameters passed to the tool

        Returns:
            Dictionary with results
        """
        pass

    def get_info(self) -> Dict[str, str]:
        """
        Get plugin information.
        """
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description
        }