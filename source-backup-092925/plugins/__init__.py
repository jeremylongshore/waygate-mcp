"""
Plugin System for Waygate MCP
Easy way to add your own tools and integrations
"""

from .base_plugin import BasePlugin
from .plugin_loader import PluginLoader

__all__ = ['BasePlugin', 'PluginLoader']