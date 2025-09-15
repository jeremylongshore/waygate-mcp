#!/bin/bash
# quickstart.sh - Secure one-line setup for Waygate MCP

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║          🚀 Waygate MCP - Secure Container Setup          ║"
echo "║                    Version 2.0.0                          ║"
echo "║           Successor to NEXUS MCP with Enhanced            ║"
echo "║              Security & Containerization                  ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check Docker installation
check_docker() {
    echo -e "${YELLOW}[CHECK]${NC} Verifying Docker installation..."

    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker not found.${NC}"
        echo "   Please install Docker first:"
        echo "   Visit: https://docs.docker.com/get-docker/"
        exit 1
    fi
    echo -e "${GREEN}✅ Docker found:${NC} $(docker --version)"

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null 2>&1; then
        echo -e "${RED}❌ Docker Compose not found.${NC}"
        echo "   Please install Docker Compose:"
        echo "   Visit: https://docs.docker.com/compose/install/"
        exit 1
    fi
    echo -e "${GREEN}✅ Docker Compose found${NC}"

    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        echo -e "${RED}❌ Docker daemon is not running.${NC}"
        echo "   Please start Docker and try again."
        exit 1
    fi
    echo -e "${GREEN}✅ Docker daemon is running${NC}"
}

# Generate secure configuration
generate_config() {
    echo -e "\n${YELLOW}[CONFIG]${NC} Generating secure configuration..."

    # Generate secure secret key
    if command -v openssl &> /dev/null; then
        export WAYGATE_SECRET_KEY=$(openssl rand -base64 32)
    else
        export WAYGATE_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
    fi
    echo -e "${GREEN}✅ Generated secure secret key${NC}"

    # Generate API key
    if command -v uuidgen &> /dev/null; then
        export WAYGATE_API_KEY=$(uuidgen)
    else
        export WAYGATE_API_KEY=$(python3 -c 'import uuid; print(str(uuid.uuid4()))')
    fi
    echo -e "${GREEN}✅ Generated API key${NC}"

    # Create .env file with secure defaults
    cat > .env << EOF
# Waygate MCP Environment Configuration
# Generated: $(date -u +'%Y-%m-%d %H:%M:%S UTC')

# Environment
WAYGATE_ENV=production
WAYGATE_LOG_LEVEL=INFO

# Security Keys (CHANGE THESE IN PRODUCTION)
WAYGATE_SECRET_KEY=${WAYGATE_SECRET_KEY}
WAYGATE_API_KEY=${WAYGATE_API_KEY}

# CORS Configuration
WAYGATE_CORS_ORIGINS=["https://localhost"]

# Resource Limits
WAYGATE_MAX_REQUEST_SIZE=10485760
WAYGATE_RATE_LIMIT=100

# Build Arguments
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
VERSION=2.0.0
EOF

    echo -e "${GREEN}✅ Created secure environment configuration${NC}"
}

# Build containers
build_containers() {
    echo -e "\n${YELLOW}[BUILD]${NC} Building secure containers..."

    # Pull latest base images for security updates
    docker pull python:3.11-slim-bookworm

    # Build with no cache for fresh security updates
    if docker-compose build --pull --no-cache; then
        echo -e "${GREEN}✅ Containers built successfully${NC}"
    else
        echo -e "${RED}❌ Container build failed${NC}"
        echo "   Check the error messages above"
        exit 1
    fi
}

# Start services
start_services() {
    echo -e "\n${YELLOW}[START]${NC} Starting Waygate MCP services..."

    # Stop any existing containers
    docker-compose down 2>/dev/null || true

    # Start services
    if docker-compose up -d; then
        echo -e "${GREEN}✅ Services started${NC}"
    else
        echo -e "${RED}❌ Failed to start services${NC}"
        exit 1
    fi
}

# Wait for health check
wait_for_health() {
    echo -e "\n${YELLOW}[HEALTH]${NC} Waiting for service to be healthy..."

    local timeout=30
    local elapsed=0

    while [ $elapsed -lt $timeout ]; do
        if docker-compose exec -T waygate curl -f http://localhost:8000/health &>/dev/null 2>&1; then
            echo -e "${GREEN}✅ Waygate MCP is healthy!${NC}"
            return 0
        fi
        echo -n "."
        sleep 2
        elapsed=$((elapsed + 2))
    done

    echo -e "\n${RED}❌ Service health check failed${NC}"
    echo "   Checking logs..."
    docker-compose logs --tail=20 waygate
    return 1
}

# Display status
display_status() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}🎉 Waygate MCP is running successfully!${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

    echo -e "\n📊 ${YELLOW}Service Status:${NC}"
    docker-compose ps

    echo -e "\n🔐 ${YELLOW}Security Features Enabled:${NC}"
    echo "  ✓ Non-root user execution"
    echo "  ✓ Read-only root filesystem"
    echo "  ✓ Network isolation"
    echo "  ✓ Resource limits (CPU: 2 cores, Memory: 1GB)"
    echo "  ✓ Dropped capabilities"
    echo "  ✓ No new privileges"
    echo "  ✓ Secure secrets generation"

    echo -e "\n🌐 ${YELLOW}Access Points:${NC}"
    echo "  • API: http://localhost:8000"
    echo "  • Health: http://localhost:8000/health"
    echo "  • Metrics: http://localhost:8000/metrics"
    echo "  • Documentation: http://localhost:8000/docs"

    echo -e "\n🔑 ${YELLOW}API Key:${NC}"
    echo "  $(grep WAYGATE_API_KEY .env | cut -d'=' -f2)"

    echo -e "\n📝 ${YELLOW}Useful Commands:${NC}"
    echo "  • View logs: docker-compose logs -f waygate"
    echo "  • Stop services: docker-compose down"
    echo "  • Restart services: docker-compose restart"
    echo "  • Update containers: docker-compose pull && docker-compose up -d"

    echo -e "\n⚠️  ${YELLOW}Security Notes:${NC}"
    echo "  • Change default secrets in .env for production"
    echo "  • Enable HTTPS with nginx profile for public deployment"
    echo "  • Review security settings in docker-compose.yml"
    echo "  • Run security scans regularly"

    echo -e "\n📚 ${YELLOW}Documentation:${NC}"
    echo "  • README: https://github.com/jeremylongshore/waygate-mcp"
    echo "  • AI Dev Tasks: ./ai-dev-tasks/README.md"
    echo "  • Security: ./docs/CONTAINER_SECURITY.md"
}

# Main execution
main() {
    echo -e "${YELLOW}Starting Waygate MCP setup...${NC}\n"

    # Run setup steps
    check_docker
    generate_config
    build_containers
    start_services

    if wait_for_health; then
        display_status
        echo -e "\n${GREEN}✨ Setup completed successfully!${NC}"
        exit 0
    else
        echo -e "\n${RED}Setup failed. Please check the logs above.${NC}"
        exit 1
    fi
}

# Handle interrupts
trap 'echo -e "\n${YELLOW}Setup interrupted. Cleaning up...${NC}"; docker-compose down 2>/dev/null; exit 1' INT TERM

# Run main function
main "$@"