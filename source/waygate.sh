#!/bin/bash
# Waygate MCP stdio wrapper for Claude Code integration
# This script enables Claude Code to communicate with Waygate MCP via stdio

set -e

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Environment configuration
export WAYGATE_MODE="${WAYGATE_MODE:-development}"
export WAYGATE_LOG_LEVEL="${WAYGATE_LOG_LEVEL:-INFO}"
export WAYGATE_PROJECTS_DIR="${WAYGATE_PROJECTS_DIR:-/home/jeremy/projects}"

# Check if running in Docker or locally
if [ -f /.dockerenv ]; then
    # Running inside Docker container
    exec python3 /app/waygate_mcp.py "$@"
elif command -v docker &> /dev/null && docker ps -q -f name=waygate-mcp &> /dev/null; then
    # Waygate container is running, use it
    exec docker exec -i waygate-mcp python3 /app/waygate_mcp.py "$@"
else
    # Run locally with Python
    if [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
        # Use virtual environment if available
        source "$SCRIPT_DIR/venv/bin/activate"
    fi

    # Run the MCP server
    exec python3 "$SCRIPT_DIR/waygate_mcp.py" "$@"
fi