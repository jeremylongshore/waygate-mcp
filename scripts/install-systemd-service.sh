#!/bin/bash
# Install Waygate MCP systemd service for auto-start
# Run with: sudo ./scripts/install-systemd-service.sh

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Installing Waygate MCP systemd service...${NC}"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}❌ This script must be run as root (use sudo)${NC}"
   exit 1
fi

# Check if docker-compose exists
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ docker-compose not found. Please install Docker Compose first.${NC}"
    exit 1
fi

# Check if service file exists
SERVICE_FILE="/home/jeremy/waygate-mcp/deployment/waygate-mcp.service"
if [[ ! -f "$SERVICE_FILE" ]]; then
    echo -e "${RED}❌ Service file not found: $SERVICE_FILE${NC}"
    exit 1
fi

# Copy service file to systemd directory
echo -e "${YELLOW}📋 Installing service file...${NC}"
cp "$SERVICE_FILE" /etc/systemd/system/waygate-mcp.service
chown root:root /etc/systemd/system/waygate-mcp.service
chmod 644 /etc/systemd/system/waygate-mcp.service

# Reload systemd daemon
echo -e "${YELLOW}🔄 Reloading systemd daemon...${NC}"
systemctl daemon-reload

# Enable service for auto-start
echo -e "${YELLOW}⚡ Enabling auto-start on boot...${NC}"
systemctl enable waygate-mcp.service

# Ask user if they want to start now
read -p "Start Waygate MCP service now? [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}🚀 Starting Waygate MCP service...${NC}"
    systemctl start waygate-mcp.service

    # Wait a moment and check status
    sleep 5
    if systemctl is-active --quiet waygate-mcp.service; then
        echo -e "${GREEN}✅ Waygate MCP service started successfully!${NC}"

        # Test health endpoint
        echo -e "${YELLOW}🔍 Testing health endpoint...${NC}"
        if curl -f http://localhost:8000/health &>/dev/null; then
            echo -e "${GREEN}✅ Health check passed!${NC}"
        else
            echo -e "${YELLOW}⚠️  Health check failed - service may still be starting${NC}"
        fi
    else
        echo -e "${RED}❌ Service failed to start. Check logs with: journalctl -u waygate-mcp.service${NC}"
    fi
fi

echo -e "\n${BLUE}📋 Service Management Commands:${NC}"
echo -e "  • Start:   ${YELLOW}sudo systemctl start waygate-mcp.service${NC}"
echo -e "  • Stop:    ${YELLOW}sudo systemctl stop waygate-mcp.service${NC}"
echo -e "  • Restart: ${YELLOW}sudo systemctl restart waygate-mcp.service${NC}"
echo -e "  • Status:  ${YELLOW}systemctl status waygate-mcp.service${NC}"
echo -e "  • Logs:    ${YELLOW}journalctl -f -u waygate-mcp.service${NC}"
echo -e "  • Disable: ${YELLOW}sudo systemctl disable waygate-mcp.service${NC}"

echo -e "\n${GREEN}✅ Waygate MCP systemd service installation complete!${NC}"
echo -e "${BLUE}🔄 Service will now auto-start on system boot${NC}"