#!/bin/bash
# firewall-rules.sh
# Waygate MCP Proxy - Egress Firewall Configuration
# Implements strict egress filtering for enhanced security

set -euo pipefail

# Configuration
ALLOWED_DOMAINS_FILE="/config/egress-domains.txt"
LOG_PREFIX="WAYGATE-FIREWALL"
IPTABLES_SAVE_FILE="/app/data/iptables.rules"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $LOG_PREFIX: $1" >&2
}

# Error handling
error_exit() {
    log "ERROR: $1"
    exit 1
}

# Check if running with sufficient privileges
check_privileges() {
    if ! iptables -L > /dev/null 2>&1; then
        error_exit "Insufficient privileges to modify iptables rules"
    fi
}

# Flush existing rules
flush_rules() {
    log "Flushing existing iptables rules..."

    # Flush all chains
    iptables -F
    iptables -t nat -F
    iptables -t mangle -F
    iptables -X
    iptables -t nat -X
    iptables -t mangle -X

    # Set default policies
    iptables -P INPUT DROP
    iptables -P FORWARD DROP
    iptables -P OUTPUT DROP

    log "Iptables rules flushed and default policies set to DROP"
}

# Allow loopback traffic
allow_loopback() {
    log "Configuring loopback interface..."
    iptables -A INPUT -i lo -j ACCEPT
    iptables -A OUTPUT -o lo -j ACCEPT
}

# Allow established and related connections
allow_established() {
    log "Allowing established and related connections..."
    iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
    iptables -A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
}

# Allow DNS resolution
allow_dns() {
    log "Configuring DNS resolution rules..."

    # Allow DNS queries to specific servers
    iptables -A OUTPUT -p udp --dport 53 -d 8.8.8.8 -j ACCEPT
    iptables -A OUTPUT -p udp --dport 53 -d 8.8.4.4 -j ACCEPT
    iptables -A OUTPUT -p udp --dport 53 -d 1.1.1.1 -j ACCEPT
    iptables -A OUTPUT -p udp --dport 53 -d 1.0.0.1 -j ACCEPT

    # Allow TCP DNS for large responses
    iptables -A OUTPUT -p tcp --dport 53 -d 8.8.8.8 -j ACCEPT
    iptables -A OUTPUT -p tcp --dport 53 -d 8.8.4.4 -j ACCEPT
    iptables -A OUTPUT -p tcp --dport 53 -d 1.1.1.1 -j ACCEPT
    iptables -A OUTPUT -p tcp --dport 53 -d 1.0.0.1 -j ACCEPT
}

# Allow internal Docker network communication
allow_internal_docker() {
    log "Configuring internal Docker network rules..."

    # Allow communication within Docker networks
    iptables -A OUTPUT -d 172.29.0.0/16 -j ACCEPT  # DMZ network
    iptables -A OUTPUT -d 172.30.0.0/16 -j ACCEPT  # Internal network
    iptables -A OUTPUT -d 172.28.0.0/16 -j ACCEPT  # Default waygate network

    # Allow Docker daemon communication
    iptables -A OUTPUT -d 172.17.0.0/16 -j ACCEPT  # Default Docker bridge
}

# Configure specific service egress rules
configure_service_egress() {
    log "Configuring service-specific egress rules..."

    # Google APIs (Firebase, BigQuery, etc.)
    log "  - Google APIs"
    iptables -A OUTPUT -p tcp --dport 443 -d 172.217.0.0/16 -j ACCEPT
    iptables -A OUTPUT -p tcp --dport 443 -d 142.250.0.0/15 -j ACCEPT
    iptables -A OUTPUT -p tcp --dport 443 -d 216.58.192.0/19 -j ACCEPT

    # GitHub APIs
    log "  - GitHub APIs"
    iptables -A OUTPUT -p tcp --dport 443 -d 140.82.112.0/20 -j ACCEPT
    iptables -A OUTPUT -p tcp --dport 443 -d 185.199.108.0/22 -j ACCEPT

    # Slack APIs
    log "  - Slack APIs"
    iptables -A OUTPUT -p tcp --dport 443 -d 52.85.0.0/16 -j ACCEPT
    iptables -A OUTPUT -p tcp --dport 443 -d 52.86.0.0/15 -j ACCEPT

    # Docker Hub
    log "  - Docker Hub"
    iptables -A OUTPUT -p tcp --dport 443 -d 52.1.0.0/16 -j ACCEPT
    iptables -A OUTPUT -p tcp --dport 443 -d 34.192.0.0/12 -j ACCEPT

    # System updates (limited time window)
    current_hour=$(date +%H)
    if [ "$current_hour" -ge 2 ] && [ "$current_hour" -le 4 ]; then
        log "  - System updates (maintenance window)"
        iptables -A OUTPUT -p tcp --dport 80 -d 151.101.0.0/16 -j ACCEPT   # Debian repos
        iptables -A OUTPUT -p tcp --dport 443 -d 151.101.0.0/16 -j ACCEPT
        iptables -A OUTPUT -p tcp --dport 80 -d 199.232.0.0/16 -j ACCEPT   # PyPI
        iptables -A OUTPUT -p tcp --dport 443 -d 199.232.0.0/16 -j ACCEPT
    fi
}

# Configure rate limiting
configure_rate_limiting() {
    log "Configuring rate limiting rules..."

    # Limit outbound connections per minute
    iptables -A OUTPUT -p tcp --syn -m limit --limit 100/min --limit-burst 20 -j ACCEPT

    # Limit ICMP
    iptables -A OUTPUT -p icmp -m limit --limit 10/min -j ACCEPT
}

# Configure logging for blocked traffic
configure_logging() {
    log "Configuring traffic logging..."

    # Log blocked outbound traffic
    iptables -A OUTPUT -m limit --limit 5/min -j LOG --log-prefix "$LOG_PREFIX-BLOCKED-OUT: " --log-level 4

    # Log blocked inbound traffic
    iptables -A INPUT -m limit --limit 5/min -j LOG --log-prefix "$LOG_PREFIX-BLOCKED-IN: " --log-level 4
}

# Apply emergency access rules
apply_emergency_rules() {
    log "Applying emergency access rules..."

    # Allow SSH for emergency access (if needed)
    # iptables -A INPUT -p tcp --dport 22 -s 192.168.1.0/24 -j ACCEPT

    # Allow management interface
    iptables -A INPUT -p tcp --dport 8000 -s 172.28.0.0/16 -j ACCEPT
    iptables -A INPUT -p tcp --dport 8080 -s 172.28.0.0/16 -j ACCEPT
}

# Save rules for persistence
save_rules() {
    log "Saving iptables rules..."

    if command -v iptables-save > /dev/null; then
        iptables-save > "$IPTABLES_SAVE_FILE"
        log "Rules saved to $IPTABLES_SAVE_FILE"
    else
        log "WARNING: iptables-save not available, rules will not persist across reboots"
    fi
}

# Monitor and alert on rule violations
monitor_violations() {
    log "Starting firewall violation monitoring..."

    # Monitor kernel logs for dropped packets
    (
        tail -f /var/log/kern.log 2>/dev/null | grep "$LOG_PREFIX-BLOCKED" | while read -r line; do
            echo "[SECURITY ALERT] Firewall violation: $line"
            # Here you could send alerts to monitoring systems
        done
    ) &
}

# Health check function
health_check() {
    local status="healthy"
    local errors=0

    # Check if iptables rules are active
    if ! iptables -L OUTPUT | grep -q "policy DROP"; then
        log "ERROR: Default OUTPUT policy is not DROP"
        status="unhealthy"
        ((errors++))
    fi

    # Check if essential rules exist
    if ! iptables -L OUTPUT | grep -q "lo"; then
        log "ERROR: Loopback rules missing"
        status="unhealthy"
        ((errors++))
    fi

    echo "{\"status\": \"$status\", \"errors\": $errors, \"timestamp\": \"$(date -Iseconds)\"}"
}

# Cleanup function
cleanup() {
    log "Cleaning up firewall rules..."
    # Kill background monitoring processes
    jobs -p | xargs -r kill
}

# Signal handlers
trap cleanup EXIT
trap 'log "Received SIGTERM, shutting down..."; cleanup; exit 0' TERM
trap 'log "Received SIGINT, shutting down..."; cleanup; exit 0' INT

# Main execution
main() {
    log "Starting Waygate MCP Egress Firewall configuration..."

    # Validate environment
    check_privileges

    # Apply firewall rules
    flush_rules
    allow_loopback
    allow_established
    allow_dns
    allow_internal_docker
    configure_service_egress
    configure_rate_limiting
    apply_emergency_rules
    configure_logging

    # Save and monitor
    save_rules
    monitor_violations

    log "Firewall configuration completed successfully"

    # Health check endpoint
    while true; do
        if [ -f /tmp/firewall-health-check ]; then
            health_check > /tmp/firewall-health-status
            rm -f /tmp/firewall-health-check
        fi
        sleep 10
    done
}

# Handle script arguments
case "${1:-start}" in
    start)
        main
        ;;
    health)
        health_check
        ;;
    stop)
        cleanup
        ;;
    reload)
        log "Reloading firewall rules..."
        main
        ;;
    *)
        echo "Usage: $0 {start|health|stop|reload}"
        exit 1
        ;;
esac