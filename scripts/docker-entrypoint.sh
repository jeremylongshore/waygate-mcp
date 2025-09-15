#!/bin/bash
# docker-entrypoint.sh
# Security-hardened entrypoint script for Waygate MCP

set -euo pipefail

# Security: Validate environment
validate_environment() {
    echo "[SECURITY] Validating environment..."

    # Check if running as non-root
    if [ "$(id -u)" = "0" ]; then
        echo "[ERROR] Container running as root! Aborting."
        exit 1
    fi

    # Validate required environment variables
    required_vars=("WAYGATE_MODE" "WAYGATE_SECRET_KEY")
    for var in "${required_vars[@]}"; do
        if [ -z "${!var:-}" ]; then
            echo "[ERROR] Required variable $var is not set"
            exit 1
        fi
    done

    # Security: Check file permissions
    if [ -w /etc/passwd ]; then
        echo "[WARN] /etc/passwd is writable - potential security risk"
    fi

    echo "[SECURITY] Environment validation complete"
}

# Security: Set up secure file permissions
setup_permissions() {
    echo "[SECURITY] Setting secure permissions..."

    # Ensure log directory is writable but secure
    if [ -d /app/logs ]; then
        chmod 750 /app/logs 2>/dev/null || true
    fi

    # Ensure data directory is secure
    if [ -d /app/data ]; then
        chmod 750 /app/data 2>/dev/null || true
    fi

    # Ensure temp directory is secure
    if [ -d /app/tmp ]; then
        chmod 770 /app/tmp 2>/dev/null || true
    fi
}

# Security: Generate secure configuration
generate_secure_config() {
    echo "[SECURITY] Generating secure configuration..."

    # Generate strong secret key if not provided
    if [ "$WAYGATE_SECRET_KEY" = "changeme" ]; then
        export WAYGATE_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
        echo "[SECURITY] Generated new secret key"
    fi

    # Set secure defaults
    export WAYGATE_CORS_ORIGINS=${WAYGATE_CORS_ORIGINS:-'["https://localhost"]'}
    export WAYGATE_MAX_REQUEST_SIZE=${WAYGATE_MAX_REQUEST_SIZE:-10485760}  # 10MB
    export WAYGATE_RATE_LIMIT=${WAYGATE_RATE_LIMIT:-100}  # requests per minute

    # Security: Validate CORS origins
    if [[ "$WAYGATE_CORS_ORIGINS" == *"*"* ]]; then
        echo "[WARN] CORS origins contains wildcard - security risk in production"
    fi
}

# Log startup information
log_startup_info() {
    echo "[INFO] Waygate MCP Container Starting..."
    echo "[INFO] Version: ${VERSION:-2.0.0}"
    echo "[INFO] Environment: ${WAYGATE_ENV:-production}"
    echo "[INFO] Mode: ${WAYGATE_MODE:-container}"
    echo "[INFO] Workers: ${WAYGATE_WORKERS:-4}"
    echo "[INFO] Port: ${WAYGATE_PORT:-8000}"
}

# Main execution
main() {
    log_startup_info

    # Security checks
    validate_environment
    setup_permissions
    generate_secure_config

    echo "[INFO] Starting Waygate MCP Server..."

    # Start application with proper signal handling
    exec python3 -u /app/src/waygate_mcp.py \
        --host "${WAYGATE_HOST:-0.0.0.0}" \
        --port "${WAYGATE_PORT:-8000}" \
        --workers "${WAYGATE_WORKERS:-4}" \
        --env "${WAYGATE_ENV:-production}"
}

# Trap signals for graceful shutdown
trap 'echo "[INFO] Received shutdown signal, shutting down gracefully..."; exit 0' SIGTERM SIGINT

# Run main function
main "$@"