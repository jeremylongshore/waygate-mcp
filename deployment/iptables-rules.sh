#!/bin/bash
# Waygate MCP Firewall Rules
# Host-level iptables rules for enhanced security

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Configuring Waygate MCP firewall rules...${NC}"

# Flush existing rules (be careful in production)
# iptables -F
# iptables -X
# iptables -t nat -F
# iptables -t nat -X

# Default policies
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# Allow loopback
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Allow established and related connections
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Allow SSH (adjust port as needed)
iptables -A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW,ESTABLISHED -j ACCEPT

# Allow HTTP/HTTPS for updates and external API calls (outbound only)
iptables -A OUTPUT -p tcp --dport 80 -m conntrack --ctstate NEW,ESTABLISHED -j ACCEPT
iptables -A OUTPUT -p tcp --dport 443 -m conntrack --ctstate NEW,ESTABLISHED -j ACCEPT

# Allow DNS (outbound only)
iptables -A OUTPUT -p udp --dport 53 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 53 -j ACCEPT

# Allow Waygate MCP container access (localhost only)
iptables -A INPUT -p tcp --dport 8000 -s 127.0.0.1 -j ACCEPT
iptables -A INPUT -p tcp --dport 8000 -s 172.28.0.0/16 -j ACCEPT  # Docker network
iptables -A INPUT -p tcp --dport 8000 -s 172.29.0.0/24 -j ACCEPT  # Secure network

# Allow Docker daemon communication
iptables -A INPUT -i docker0 -j ACCEPT
iptables -A FORWARD -i docker0 -o docker0 -j ACCEPT

# Specific egress rules for Waygate MCP services
# Turso database access
iptables -A OUTPUT -p tcp --dport 443 -d turso.tech -m conntrack --ctstate NEW,ESTABLISHED -j ACCEPT

# Google Cloud APIs
iptables -A OUTPUT -p tcp --dport 443 -d googleapis.com -m conntrack --ctstate NEW,ESTABLISHED -j ACCEPT
iptables -A OUTPUT -p tcp --dport 443 -d "*.googleapis.com" -m conntrack --ctstate NEW,ESTABLISHED -j ACCEPT

# GitHub API
iptables -A OUTPUT -p tcp --dport 443 -d api.github.com -m conntrack --ctstate NEW,ESTABLISHED -j ACCEPT

# Slack API
iptables -A OUTPUT -p tcp --dport 443 -d hooks.slack.com -m conntrack --ctstate NEW,ESTABLISHED -j ACCEPT
iptables -A OUTPUT -p tcp --dport 443 -d slack.com -m conntrack --ctstate NEW,ESTABLISHED -j ACCEPT

# Docker Hub (for image pulls)
iptables -A OUTPUT -p tcp --dport 443 -d registry-1.docker.io -m conntrack --ctstate NEW,ESTABLISHED -j ACCEPT
iptables -A OUTPUT -p tcp --dport 443 -d index.docker.io -m conntrack --ctstate NEW,ESTABLISHED -j ACCEPT

# Log dropped packets (optional - for monitoring)
iptables -A INPUT -j LOG --log-prefix "INPUT-DROP: " --log-level 4
iptables -A FORWARD -j LOG --log-prefix "FORWARD-DROP: " --log-level 4

# Save rules
if command -v netfilter-persistent &> /dev/null; then
    netfilter-persistent save
    echo -e "${GREEN}Firewall rules saved with netfilter-persistent${NC}"
elif command -v iptables-save &> /dev/null; then
    iptables-save > /etc/iptables/rules.v4
    echo -e "${GREEN}Firewall rules saved to /etc/iptables/rules.v4${NC}"
else
    echo -e "${YELLOW}Warning: Could not save iptables rules automatically${NC}"
    echo -e "${YELLOW}Consider installing iptables-persistent package${NC}"
fi

echo -e "${GREEN}Waygate MCP firewall rules configured successfully!${NC}"
echo -e "${YELLOW}Note: These are restrictive rules. Adjust as needed for your environment.${NC}"