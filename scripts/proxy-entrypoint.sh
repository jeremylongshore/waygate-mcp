#!/bin/bash
# proxy-entrypoint.sh
# Enhanced entrypoint script for Waygate MCP Proxy Gateway

set -euo pipefail

# Configuration
WAYGATE_MODE="${WAYGATE_MODE:-proxy_gateway}"
WAYGATE_ENV="${WAYGATE_ENV:-production}"
WAYGATE_HOST="${WAYGATE_HOST:-0.0.0.0}"
WAYGATE_PORT="${WAYGATE_PORT:-8000}"
WAYGATE_PROXY_PORT="${WAYGATE_PROXY_PORT:-8080}"
WAYGATE_WORKERS="${WAYGATE_WORKERS:-4}"

# Logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] PROXY-ENTRYPOINT: $1" >&2
}

error_exit() {
    log "ERROR: $1"
    exit 1
}

# Validate environment
validate_environment() {
    log "Validating proxy gateway environment..."

    # Check required environment variables
    if [ -z "${DATABASE_URL:-}" ]; then
        error_exit "DATABASE_URL environment variable is required"
    fi

    if [ -z "${WAYGATE_SECRET_KEY:-}" ] || [ "${WAYGATE_SECRET_KEY}" = "changeme" ]; then
        error_exit "WAYGATE_SECRET_KEY must be set to a secure value"
    fi

    # Validate proxy configuration
    if [ "${PROXY_MODE:-}" != "enabled" ]; then
        error_exit "PROXY_MODE must be set to 'enabled' for proxy gateway"
    fi

    log "Environment validation completed"
}

# Set up security configurations
setup_security() {
    log "Configuring security settings..."

    # Create required directories with proper permissions
    mkdir -p /app/logs /app/data /app/tmp /app/.waygate
    chmod 700 /app/data /app/.waygate
    chmod 750 /app/logs /app/tmp

    # Set up certificate validation
    if [ ! -f /app/certs/ca-certificates.crt ]; then
        log "Copying system CA certificates..."
        cp /etc/ssl/certs/ca-certificates.crt /app/certs/ 2>/dev/null || true
    fi

    # Validate proxy configuration files
    if [ ! -f /app/config/proxy-config.yml ]; then
        error_exit "Proxy configuration file not found: /app/config/proxy-config.yml"
    fi

    if [ ! -f /app/config/egress-rules.json ]; then
        error_exit "Egress rules file not found: /app/config/egress-rules.json"
    fi

    log "Security configuration completed"
}

# Initialize proxy components
initialize_proxy() {
    log "Initializing proxy gateway components..."

    # Test database connectivity
    log "Testing database connection..."
    python3 -c "
import os
import sys
sys.path.append('/app/src')
from database import test_connection
import asyncio
if not asyncio.run(test_connection()):
    sys.exit(1)
" || error_exit "Database connection test failed"

    # Validate egress rules
    log "Validating egress rules configuration..."
    python3 -c "
import json
with open('/app/config/egress-rules.json', 'r') as f:
    rules = json.load(f)
if 'rules' not in rules or not isinstance(rules['rules'], list):
    raise ValueError('Invalid egress rules format')
print(f'Loaded {len(rules[\"rules\"])} egress rules')
" || error_exit "Egress rules validation failed"

    # Pre-warm proxy components
    log "Pre-warming proxy components..."
    python3 -c "
import sys
sys.path.append('/app/src')
from proxy_gateway import validate_configuration
validate_configuration('/app/config/proxy-config.yml')
" || error_exit "Proxy configuration validation failed"

    log "Proxy initialization completed"
}

# Start monitoring services
start_monitoring() {
    log "Starting monitoring services..."

    # Start metrics collection
    if [ "${PROXY_METRICS_ENABLED:-true}" = "true" ]; then
        log "Starting metrics collection service..."
        python3 /app/src/monitoring/metrics_collector.py &
        echo $! > /app/tmp/metrics_collector.pid
    fi

    # Start security monitor
    if [ "${PROXY_SECURITY_MONITOR:-true}" = "true" ]; then
        log "Starting security monitor..."
        python3 /app/src/monitoring/security_monitor.py &
        echo $! > /app/tmp/security_monitor.pid
    fi

    # Start health check service
    python3 /app/src/monitoring/health_checker.py &
    echo $! > /app/tmp/health_checker.pid

    log "Monitoring services started"
}

# Start proxy gateway
start_proxy_gateway() {
    log "Starting Waygate MCP Proxy Gateway..."

    # Display startup banner
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║                  Waygate MCP Proxy Gateway                   ║
║                         v2.0.0                               ║
║                                                              ║
║  🛡️  Security-hardened proxy for external network access    ║
║  🔍  All external requests audited and filtered             ║
║  📊  Real-time monitoring and alerting                      ║
║                                                              ║
║  Management API: http://localhost:8000                       ║
║  Proxy Gateway: http://localhost:8080                        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
EOF

    # Set Python path
    export PYTHONPATH="/app/src:${PYTHONPATH:-}"

    # Start the proxy gateway with uvicorn
    exec python3 -m uvicorn \
        --app-dir /app/src \
        --module waygate_mcp:app \
        --host "${WAYGATE_HOST}" \
        --port "${WAYGATE_PORT}" \
        --workers "${WAYGATE_WORKERS}" \
        --loop uvloop \
        --http httptools \
        --log-level info \
        --access-log \
        --use-colors \
        --proxy-headers \
        --forwarded-allow-ips '*'
}

# Cleanup function
cleanup() {
    log "Shutting down proxy gateway..."

    # Stop monitoring services
    for pidfile in /app/tmp/*.pid; do
        if [ -f "$pidfile" ]; then
            pid=$(cat "$pidfile")
            if kill -0 "$pid" 2>/dev/null; then
                log "Stopping process $pid..."
                kill -TERM "$pid" 2>/dev/null || true
                sleep 2
                kill -KILL "$pid" 2>/dev/null || true
            fi
            rm -f "$pidfile"
        fi
    done

    log "Cleanup completed"
}

# Signal handlers
trap cleanup EXIT
trap 'log "Received SIGTERM"; cleanup; exit 0' TERM
trap 'log "Received SIGINT"; cleanup; exit 0' INT

# Health check function
health_check() {
    local management_health=""
    local proxy_health=""

    # Check management API
    if curl -f -s "http://localhost:${WAYGATE_PORT}/health" > /dev/null 2>&1; then
        management_health="✅ Management API: Healthy"
    else
        management_health="❌ Management API: Unhealthy"
    fi

    # Check proxy gateway
    if curl -f -s "http://localhost:${WAYGATE_PROXY_PORT}/proxy/health" > /dev/null 2>&1; then
        proxy_health="✅ Proxy Gateway: Healthy"
    else
        proxy_health="❌ Proxy Gateway: Unhealthy"
    fi

    echo "$management_health"
    echo "$proxy_health"
}

# Pre-flight checks
preflight_checks() {
    log "Running pre-flight checks..."

    # Check disk space
    available_space=$(df /app | tail -1 | awk '{print $4}')
    if [ "$available_space" -lt 1048576 ]; then  # Less than 1GB
        log "WARNING: Low disk space available: ${available_space}KB"
    fi

    # Check memory
    available_memory=$(free | grep '^Mem:' | awk '{print $7}')
    if [ "$available_memory" -lt 262144 ]; then  # Less than 256MB
        log "WARNING: Low memory available: ${available_memory}KB"
    fi

    # Check network connectivity
    if ! nc -z 8.8.8.8 53 -w 5; then
        log "WARNING: External network connectivity test failed"
    fi

    log "Pre-flight checks completed"
}

# Main execution
main() {
    log "Starting Waygate MCP Proxy Gateway (PID: $$)..."

    # Show configuration
    log "Configuration:"
    log "  Mode: $WAYGATE_MODE"
    log "  Environment: $WAYGATE_ENV"
    log "  Management Port: $WAYGATE_PORT"
    log "  Proxy Port: $WAYGATE_PROXY_PORT"
    log "  Workers: $WAYGATE_WORKERS"

    # Execute startup sequence
    preflight_checks
    validate_environment
    setup_security
    initialize_proxy
    start_monitoring
    start_proxy_gateway
}

# Handle script arguments
case "${1:-start}" in
    start)
        main
        ;;
    health)
        health_check
        ;;
    test)
        log "Running configuration tests..."
        validate_environment
        setup_security
        initialize_proxy
        log "All tests passed ✅"
        ;;
    *)
        echo "Usage: $0 {start|health|test}"
        exit 1
        ;;
esac