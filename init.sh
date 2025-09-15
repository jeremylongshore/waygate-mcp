#!/bin/bash
# init.sh - Initialize Waygate MCP Environment
# Date: 2025-01-14
# Version: 2.0.0

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Project metadata
PROJECT_NAME="Waygate MCP"
PROJECT_VERSION="2.0.0"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║         🚀 Waygate MCP - Environment Initialization        ║"
echo "║                    Version ${PROJECT_VERSION}                          ║"
echo "║              Security-Hardened Container Framework         ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Function to check dependencies
check_dependencies() {
    echo -e "\n${YELLOW}[INIT]${NC} Checking dependencies..."

    local deps_missing=false

    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}  ❌ Docker not found${NC}"
        deps_missing=true
    else
        echo -e "${GREEN}  ✅ Docker: $(docker --version)${NC}"
    fi

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null 2>&1; then
        echo -e "${RED}  ❌ Docker Compose not found${NC}"
        deps_missing=true
    else
        echo -e "${GREEN}  ✅ Docker Compose found${NC}"
    fi

    # Check Git
    if ! command -v git &> /dev/null; then
        echo -e "${YELLOW}  ⚠️  Git not found (optional but recommended)${NC}"
    else
        echo -e "${GREEN}  ✅ Git: $(git --version)${NC}"
    fi

    # Check Python (for development)
    if ! command -v python3 &> /dev/null; then
        echo -e "${YELLOW}  ⚠️  Python3 not found (optional for development)${NC}"
    else
        echo -e "${GREEN}  ✅ Python: $(python3 --version)${NC}"
    fi

    if [ "$deps_missing" = true ]; then
        echo -e "\n${RED}ERROR: Required dependencies are missing.${NC}"
        echo "Please install Docker and Docker Compose before continuing."
        exit 1
    fi
}

# Function to initialize environment
init_environment() {
    echo -e "\n${YELLOW}[ENV]${NC} Initializing environment..."

    # Create necessary directories
    mkdir -p "$PROJECT_DIR/src"
    mkdir -p "$PROJECT_DIR/tests"
    mkdir -p "$PROJECT_DIR/configs"
    mkdir -p "$PROJECT_DIR/scripts"
    mkdir -p "$PROJECT_DIR/logs"
    mkdir -p "$PROJECT_DIR/data"

    echo -e "${GREEN}  ✅ Directory structure created${NC}"

    # Create .env file if it doesn't exist
    if [ ! -f "$PROJECT_DIR/.env" ]; then
        echo -e "${YELLOW}  📝 Creating .env file...${NC}"

        # Generate secure keys
        if command -v openssl &> /dev/null; then
            SECRET_KEY=$(openssl rand -base64 32)
        else
            SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
        fi

        if command -v uuidgen &> /dev/null; then
            API_KEY=$(uuidgen)
        else
            API_KEY=$(python3 -c 'import uuid; print(str(uuid.uuid4()))')
        fi

        cat > "$PROJECT_DIR/.env" << EOF
# Waygate MCP Environment Configuration
# Generated: $(date -u +'%Y-%m-%d %H:%M:%S UTC')
# Version: ${PROJECT_VERSION}

# Environment
WAYGATE_ENV=development
WAYGATE_LOG_LEVEL=DEBUG

# Security Keys (CHANGE THESE IN PRODUCTION)
WAYGATE_SECRET_KEY=${SECRET_KEY}
WAYGATE_API_KEY=${API_KEY}

# CORS Configuration
WAYGATE_CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]

# Resource Limits
WAYGATE_MAX_REQUEST_SIZE=10485760
WAYGATE_RATE_LIMIT=100

# Database (if needed)
DATABASE_URL=postgresql://waygate:waygate@localhost:5432/waygate_db

# Redis (if needed)
REDIS_URL=redis://localhost:6379/0

# Build Arguments
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
VERSION=${PROJECT_VERSION}
EOF

        echo -e "${GREEN}  ✅ Environment file created${NC}"
        echo -e "${YELLOW}  ⚠️  Remember to update .env with production values${NC}"
    else
        echo -e "${GREEN}  ✅ Environment file exists${NC}"
    fi

    # Add .env to .gitignore if git is initialized
    if [ -d "$PROJECT_DIR/.git" ]; then
        if ! grep -q "^.env$" "$PROJECT_DIR/.gitignore" 2>/dev/null; then
            echo ".env" >> "$PROJECT_DIR/.gitignore"
            echo -e "${GREEN}  ✅ Added .env to .gitignore${NC}"
        fi
    fi
}

# Function to check Docker daemon
check_docker_daemon() {
    echo -e "\n${YELLOW}[DOCKER]${NC} Checking Docker daemon..."

    if ! docker info &> /dev/null; then
        echo -e "${RED}  ❌ Docker daemon is not running${NC}"
        echo "  Please start Docker and try again."
        exit 1
    fi

    echo -e "${GREEN}  ✅ Docker daemon is running${NC}"

    # Display Docker info
    echo -e "${CYAN}  📊 Docker System Info:${NC}"
    docker version --format '    Client: {{.Client.Version}}'
    docker version --format '    Server: {{.Server.Version}}'
    echo -e "    $(docker system df --format 'Images: {{.Images}} | Containers: {{.Containers}} | Volumes: {{.Volumes}}')"
}

# Function to validate project files
validate_project() {
    echo -e "\n${YELLOW}[VALIDATE]${NC} Validating project structure..."

    local validation_passed=true

    # Check critical files
    local critical_files=(
        "Dockerfile"
        "docker-compose.yml"
        "README.md"
        "CLAUDE.md"
    )

    for file in "${critical_files[@]}"; do
        if [ -f "$PROJECT_DIR/$file" ]; then
            echo -e "${GREEN}  ✅ $file exists${NC}"
        else
            echo -e "${RED}  ❌ $file missing${NC}"
            validation_passed=false
        fi
    done

    # Check executable permissions
    if [ -f "$PROJECT_DIR/quickstart.sh" ]; then
        if [ -x "$PROJECT_DIR/quickstart.sh" ]; then
            echo -e "${GREEN}  ✅ quickstart.sh is executable${NC}"
        else
            chmod +x "$PROJECT_DIR/quickstart.sh"
            echo -e "${YELLOW}  🔧 Made quickstart.sh executable${NC}"
        fi
    fi

    if [ -f "$PROJECT_DIR/scripts/docker-entrypoint.sh" ]; then
        if [ -x "$PROJECT_DIR/scripts/docker-entrypoint.sh" ]; then
            echo -e "${GREEN}  ✅ docker-entrypoint.sh is executable${NC}"
        else
            chmod +x "$PROJECT_DIR/scripts/docker-entrypoint.sh"
            echo -e "${YELLOW}  🔧 Made docker-entrypoint.sh executable${NC}"
        fi
    fi

    if [ "$validation_passed" = false ]; then
        echo -e "\n${RED}ERROR: Project validation failed.${NC}"
        echo "Some critical files are missing. Please check the project structure."
        exit 1
    fi
}

# Function to display status
display_status() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✅ Waygate MCP Environment Initialized Successfully!${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

    echo -e "\n📁 ${YELLOW}Project Location:${NC}"
    echo "   $PROJECT_DIR"

    echo -e "\n🔐 ${YELLOW}Security Configuration:${NC}"
    echo "   • Container isolation: Enabled"
    echo "   • Non-root user: waygate (UID 1000)"
    echo "   • Read-only filesystem: Configured"
    echo "   • Network isolation: 172.28.0.0/16"
    echo "   • Resource limits: CPU 2 cores, Memory 1GB"

    echo -e "\n📚 ${YELLOW}Documentation:${NC}"
    echo "   • Project Guide: CLAUDE.md"
    echo "   • User Docs: README.md"
    echo "   • Security: docs/CONTAINER_SECURITY.md"
    echo "   • AI Tasks: ai-dev-tasks/"

    echo -e "\n🚀 ${YELLOW}Next Steps:${NC}"
    echo "   1. Review and update .env configuration"
    echo "   2. Run './quickstart.sh' for automated deployment"
    echo "   3. Or use 'docker-compose up -d' for manual start"
    echo "   4. Check health: curl http://localhost:8000/health"

    echo -e "\n💻 ${YELLOW}Development Commands:${NC}"
    echo "   • Start: docker-compose up -d"
    echo "   • Logs: docker-compose logs -f waygate"
    echo "   • Shell: docker-compose exec waygate /bin/bash"
    echo "   • Stop: docker-compose down"
    echo "   • Rebuild: docker-compose build --no-cache"

    echo -e "\n📖 ${YELLOW}Quick Reference:${NC}"
    echo "   • API Endpoint: http://localhost:8000"
    echo "   • Health Check: http://localhost:8000/health"
    echo "   • Metrics: http://localhost:8000/metrics"
    echo "   • Documentation: http://localhost:8000/docs (dev mode)"

    if [ -f "$PROJECT_DIR/.env" ]; then
        API_KEY=$(grep WAYGATE_API_KEY "$PROJECT_DIR/.env" | cut -d'=' -f2)
        if [ ! -z "$API_KEY" ]; then
            echo -e "\n🔑 ${YELLOW}API Key:${NC}"
            echo "   $API_KEY"
        fi
    fi

    echo -e "\n${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}Happy coding with Waygate MCP! 🚀${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}\n"
}

# Function to offer quick start
offer_quickstart() {
    echo -e "\n${YELLOW}Would you like to start Waygate MCP now? (y/n)${NC}"
    read -r response

    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo -e "\n${BLUE}Starting Waygate MCP...${NC}"

        if [ -f "$PROJECT_DIR/quickstart.sh" ]; then
            bash "$PROJECT_DIR/quickstart.sh"
        else
            echo -e "${YELLOW}Building and starting containers...${NC}"
            docker-compose build --pull --no-cache
            docker-compose up -d

            echo -e "\n${GREEN}✅ Waygate MCP is starting!${NC}"
            echo "   Check status: docker-compose ps"
            echo "   View logs: docker-compose logs -f waygate"
        fi
    else
        echo -e "\n${BLUE}You can start Waygate MCP later with:${NC}"
        echo "   ./quickstart.sh"
        echo "   or"
        echo "   docker-compose up -d"
    fi
}

# Main execution
main() {
    cd "$PROJECT_DIR"

    # Run initialization steps
    check_dependencies
    init_environment
    check_docker_daemon
    validate_project
    display_status

    # Offer to start the service
    offer_quickstart
}

# Handle interrupts gracefully
trap 'echo -e "\n${YELLOW}Initialization interrupted.${NC}"; exit 1' INT TERM

# Run main function
main "$@"

# Date: 2025-01-14
# End of init.sh