#!/usr/bin/env python3
"""
Common exceptions for Waygate MCP Server
"""

class MCPToolError(Exception):
    """Exception raised by MCP tools when execution fails."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict:
        """Convert error to dictionary format."""
        return {
            "error": self.message,
            "details": self.details
        }