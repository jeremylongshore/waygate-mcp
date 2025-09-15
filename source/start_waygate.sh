#!/bin/bash
# Local development runner for Waygate MCP

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Waygate MCP Server (Local Mode)${NC}"

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}🔧 Activating virtual environment...${NC}"
source venv/bin/activate

# Install/update requirements
if [ -f "requirements.txt" ]; then
    echo -e "${YELLOW}📚 Installing requirements...${NC}"
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
fi

# Set environment variables
export WAYGATE_MODE="${WAYGATE_MODE:-development}"
export WAYGATE_LOG_LEVEL="${WAYGATE_LOG_LEVEL:-INFO}"
export WAYGATE_PROJECTS_DIR="${WAYGATE_PROJECTS_DIR:-/home/jeremy/projects}"

# Create required directories
mkdir -p "$WAYGATE_PROJECTS_DIR/active"
mkdir -p "$WAYGATE_PROJECTS_DIR/archived"

echo -e "${GREEN}✅ Environment ready${NC}"
echo -e "${GREEN}📍 Projects directory: $WAYGATE_PROJECTS_DIR${NC}"
echo -e "${GREEN}🔄 Mode: $WAYGATE_MODE${NC}"
echo -e "${GREEN}📝 Log level: $WAYGATE_LOG_LEVEL${NC}"

# Run the server
echo -e "${GREEN}🎯 Starting Waygate MCP Server...${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo ""

python3 waygate_mcp.py