#!/bin/bash
# Waygate MCP Quick Start with Turso Database
# Tech bro approved: Edge database + security-hardened deployment

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${PURPLE}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║    🚀 Waygate MCP - Turso Edge Database Deployment       ║"
echo "║                     Version 2.0.0                        ║"
echo "║    🔥 Tech Bro Stack: SQLite@Edge + Docker + Security    ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_hype() {
    echo -e "${PURPLE}🔥 $1${NC}"
}

print_tech() {
    echo -e "${CYAN}🌟 $1${NC}"
}

# Check DATABASE_URL
check_database_url() {
    print_info "Checking Turso database configuration..."

    if [ -z "${DATABASE_URL:-}" ]; then
        print_error "DATABASE_URL not set!"
        echo ""
        print_hype "TURSO DATABASE SETUP REQUIRED"
        echo ""
        print_tech "Step 1: Install Turso CLI"
        echo "   curl -sSfL https://get.tur.so/install.sh | bash"
        echo ""
        print_tech "Step 2: Create your database"
        echo "   turso db create waygate-mcp"
        echo ""
        print_tech "Step 3: Generate auth token"
        echo "   turso db tokens create waygate-mcp"
        echo ""
        print_tech "Step 4: Set environment variable"
        echo '   export DATABASE_URL="libsql://waygate-mcp-[username].turso.io?authToken=your-auth-token"'
        echo ""
        print_tech "Step 5: Or create .env file"
        echo '   echo "DATABASE_URL=libsql://your-db.turso.io?authToken=your-token" > .env'
        echo ""
        print_hype "Why Turso? 🚀"
        echo "   • SQLite at the edge (fastest globally)"
        echo "   • 1 billion row reads free tier"
        echo "   • Used by top developers worldwide"
        echo "   • Your data, your control"
        echo ""
        exit 1
    fi

    # Validate Turso URL format
    if [[ ! "$DATABASE_URL" =~ ^libsql:// ]]; then
        print_warning "DATABASE_URL doesn't look like a Turso URL"
        print_info "Expected format: libsql://your-db.turso.io?authToken=your-token"
        print_info "Current: $DATABASE_URL"
        echo ""
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi

    print_status "Turso database URL configured"
}

# Check Docker installation
check_docker() {
    print_info "Checking Docker installation..."

    if ! command -v docker &> /dev/null; then
        print_error "Docker not found"
        print_tech "Install Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
    print_status "Docker found: $(docker --version)"

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null 2>&1; then
        print_error "Docker Compose not found"
        print_tech "Install Docker Compose: https://docs.docker.com/compose/install/"
        exit 1
    fi
    print_status "Docker Compose found"

    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        print_error "Docker daemon not running"
        print_tech "Start Docker and try again"
        exit 1
    fi
    print_status "Docker daemon running"
}

# Test database connection
test_database_connection() {
    print_info "Testing Turso database connection..."

    # Try to connect using a simple Python script
    cat > /tmp/test_turso.py << 'EOF'
import os
import sys
try:
    import libsql_client
    database_url = os.getenv("DATABASE_URL")
    client = libsql_client.create_client_sync(database_url)
    result = client.execute("SELECT 1 as test")
    print("✅ Database connection successful")
    sys.exit(0)
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    sys.exit(1)
EOF

    # Run test in container to avoid local dependencies
    if docker run --rm -v /tmp/test_turso.py:/test.py -e DATABASE_URL="$DATABASE_URL" \
       python:3.12-slim bash -c "pip install libsql-client && python /test.py" 2>/dev/null; then
        print_status "Turso database connection verified"
    else
        print_warning "Could not verify database connection (container will handle this)"
    fi

    rm -f /tmp/test_turso.py
}

# Build and deploy
deploy_waygate() {
    print_hype "Building security-hardened container..."

    # Navigate to deployment directory
    cd "$(dirname "$0")"

    # Check if we have the deployment files
    if [ ! -f "deployment/docker-compose.yml" ]; then
        print_error "Deployment files not found"
        print_info "Make sure you're in the waygate-mcp directory"
        exit 1
    fi

    # Build and start
    export DATABASE_URL="$DATABASE_URL"

    print_info "Building Waygate MCP container..."
    if docker-compose -f deployment/docker-compose.yml build --no-cache; then
        print_status "Container built successfully"
    else
        print_error "Container build failed"
        exit 1
    fi

    print_info "Starting Waygate MCP with Turso database..."
    if docker-compose -f deployment/docker-compose.yml up -d; then
        print_status "Waygate MCP deployed successfully"
    else
        print_error "Deployment failed"
        exit 1
    fi
}

# Show status and next steps
show_status() {
    echo ""
    print_hype "🎉 WAYGATE MCP DEPLOYED SUCCESSFULLY!"
    echo ""

    # Wait a moment for container to start
    sleep 3

    print_tech "Container Status:"
    docker-compose -f deployment/docker-compose.yml ps

    echo ""
    print_tech "Health Check:"
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_status "Waygate MCP is running and healthy"
    else
        print_warning "Waygate MCP starting up... (check logs if issues persist)"
    fi

    echo ""
    print_tech "Quick Commands:"
    echo "   📊 View logs:     docker-compose -f deployment/docker-compose.yml logs -f"
    echo "   🔧 Stop service:  docker-compose -f deployment/docker-compose.yml down"
    echo "   🚀 Restart:       docker-compose -f deployment/docker-compose.yml restart"
    echo "   💾 Health check:  curl http://localhost:8000/health"
    echo ""
    print_tech "API Endpoint:"
    echo "   🌐 http://localhost:8000"
    echo ""
    print_hype "Your Turso database is now powering Waygate MCP! 🔥"
    echo ""
}

# Main execution
main() {
    # Load .env file if it exists
    if [ -f ".env" ]; then
        print_info "Loading .env file..."
        export $(grep -v '^#' .env | xargs)
    fi

    check_database_url
    check_docker
    test_database_connection
    deploy_waygate
    show_status
}

# Cleanup on exit
cleanup() {
    rm -f /tmp/test_turso.py 2>/dev/null || true
}
trap cleanup EXIT

# Run main function
main "$@"