# Waygate MCP Security Proxy - Deployment Guide

**Date:** 2025-09-28
**Version:** 2.0.0
**Architecture:** Security-hardened proxy gateway for external network access

---

## 🎯 Overview

This guide provides comprehensive instructions for deploying Waygate MCP as a security proxy gateway that routes all external network access through a secure, auditable, and monitored proxy infrastructure.

## 🏗️ Architecture Summary

```
┌─────────────────────────────────────────────────────────────┐
│                    Security Proxy Architecture              │
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │   Client    │───▶│   Waygate   │───▶│  External   │    │
│  │    Apps     │    │    Proxy    │    │    APIs     │    │
│  └─────────────┘    └─────────────┘    └─────────────┘    │
│                            │                               │
│                            ▼                               │
│                   ┌─────────────┐                         │
│                   │ Monitoring  │                         │
│                   │ & Security  │                         │
│                   └─────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

## 🔐 Security Features

- **🛡️ Egress Firewall**: iptables-based network filtering
- **🔍 Content Inspection**: Deep packet inspection and malware scanning
- **📊 Real-time Monitoring**: Comprehensive observability stack
- **🚨 Policy Enforcement**: OPA-based access control policies
- **📝 Audit Logging**: Complete traffic audit trail
- **⚡ Rate Limiting**: Configurable rate limiting per client/destination
- **🔒 TLS Validation**: Certificate validation and encryption enforcement

## 📋 Prerequisites

### System Requirements
- **OS**: Linux (Ubuntu 20.04+ recommended)
- **Docker**: 24.0+ with Compose V2
- **Memory**: 4GB minimum, 8GB recommended
- **CPU**: 2 cores minimum, 4 cores recommended
- **Storage**: 20GB minimum, 50GB recommended
- **Network**: Internet connectivity for initial setup

### Required Credentials
```bash
# Database (Turso)
export DATABASE_URL="libsql://your-database.turso.io?authToken=your-token"

# Security
export WAYGATE_SECRET_KEY="your-secure-secret-key-here"

# MCP Server Credentials
export FIREBASE_PROJECT_ID="your-firebase-project"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
export GITHUB_TOKEN="your-github-token"
export SLACK_BOT_TOKEN="your-slack-bot-token"
```

## 🚀 Quick Deployment

### 1. Clone and Setup
```bash
cd /home/jeremy/waygate-mcp

# Make scripts executable
chmod +x scripts/proxy-entrypoint.sh
chmod +x proxy/firewall-rules.sh

# Generate secure secret key
export WAYGATE_SECRET_KEY=$(openssl rand -hex 32)
```

### 2. Configure Environment
```bash
# Copy and customize environment file
cp .env.template .env.proxy

# Edit with your specific values
nano .env.proxy
```

### 3. Deploy Proxy Gateway
```bash
# Deploy with proxy configuration
docker-compose -f deployment/docker-compose.proxy.yml up -d

# Verify deployment
docker-compose -f deployment/docker-compose.proxy.yml ps
```

### 4. Deploy Monitoring Stack
```bash
# Deploy monitoring infrastructure
docker-compose -f deployment/docker-compose.monitoring.yml up -d

# Check monitoring services
docker-compose -f deployment/docker-compose.monitoring.yml ps
```

### 5. Verify Deployment
```bash
# Check proxy health
curl http://localhost:8000/health
curl http://localhost:8080/proxy/health

# Check monitoring dashboards
# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
# Kibana: http://localhost:5601
```

## 🔧 Configuration

### Proxy Configuration
Edit `/home/jeremy/waygate-mcp/proxy/proxy-config.yml`:

```yaml
# Key configuration sections
proxy:
  enabled: true
  bind_port: 8080
  max_concurrent_connections: 1000

security:
  tls:
    enabled: true
    verify_certificates: true

  rate_limiting:
    enabled: true
    default_requests_per_minute: 60

access_control:
  default_policy: "deny"
  rules_file: "/app/config/egress-rules.json"
```

### Egress Rules
Edit `/home/jeremy/waygate-mcp/proxy/egress-rules.json`:

```json
{
  "rules": [
    {
      "name": "GitHub APIs",
      "enabled": true,
      "domains": ["api.github.com", "github.com"],
      "protocols": ["https"],
      "rate_limit": {
        "requests_per_minute": 80,
        "burst": 15
      },
      "audit": true
    }
  ]
}
```

### Firewall Rules
The firewall automatically configures based on egress rules. To customize:

```bash
# Edit firewall script
nano proxy/firewall-rules.sh

# Reload firewall rules
docker exec waygate-egress-firewall /scripts/firewall-rules.sh reload
```

## 🔍 Monitoring and Observability

### Access Monitoring Dashboards

1. **Grafana Dashboard**: http://localhost:3000
   - Username: admin
   - Password: admin (change immediately)
   - Import dashboard: `/monitoring/grafana-dashboard.json`

2. **Prometheus**: http://localhost:9090
   - Metrics and alerting rules
   - Target health monitoring

3. **Kibana**: http://localhost:5601
   - Log analysis and search
   - Security event investigation

4. **Jaeger**: http://localhost:16686
   - Distributed tracing
   - Request flow analysis

### Key Metrics to Monitor

```promql
# Security violations
rate(waygate_proxy_security_violations_total[5m])

# Request latency
histogram_quantile(0.95, rate(waygate_proxy_request_duration_seconds_bucket[5m]))

# Error rate
rate(waygate_proxy_requests_total{status=~"5.."}[5m]) / rate(waygate_proxy_requests_total[5m])

# Active connections
waygate_proxy_active_connections
```

### Log Analysis
```bash
# View proxy logs
docker logs waygate-proxy -f

# View security logs
docker exec waygate-proxy tail -f /app/logs/proxy-security.log

# View audit logs
docker exec waygate-proxy tail -f /app/logs/proxy-audit.log
```

## 🚨 Security Monitoring

### Critical Alerts

The system monitors for:
- **Security Violations**: Blocked malicious requests
- **DLP Violations**: Data loss prevention triggers
- **Rate Limiting**: Excessive request patterns
- **Certificate Issues**: SSL/TLS problems
- **Policy Violations**: Egress policy breaches

### Incident Response

1. **Security Alert Investigation**:
   ```bash
   # Check recent security events
   curl "http://localhost:9090/api/v1/query?query=waygate_proxy_security_violations_total"

   # Review audit logs
   docker exec waygate-proxy grep "SECURITY" /app/logs/proxy-audit.log
   ```

2. **Block Suspicious IP**:
   ```bash
   # Add IP to firewall blacklist
   docker exec waygate-egress-firewall iptables -A INPUT -s SUSPICIOUS_IP -j DROP
   ```

3. **Emergency Shutdown**:
   ```bash
   # Stop proxy gateway (blocks all external access)
   docker-compose -f deployment/docker-compose.proxy.yml stop waygate-proxy
   ```

## 🛠️ Maintenance

### Regular Tasks

1. **Update Security Rules** (Weekly):
   ```bash
   # Update egress rules
   nano proxy/egress-rules.json

   # Reload configuration
   curl -X POST http://localhost:8000/proxy/reload-config
   ```

2. **Certificate Management** (Monthly):
   ```bash
   # Check certificate status
   curl http://localhost:8000/proxy/certificates/status

   # Renew certificates if needed
   docker exec waygate-proxy /app/scripts/renew-certificates.sh
   ```

3. **Log Rotation** (Daily):
   ```bash
   # Archive old logs
   docker exec waygate-proxy /app/scripts/rotate-logs.sh
   ```

### Performance Tuning

1. **Adjust Worker Processes**:
   ```bash
   # Edit docker-compose.proxy.yml
   environment:
     - WAYGATE_WORKERS=8  # Increase for high load
   ```

2. **Optimize Rate Limits**:
   ```yaml
   # In proxy-config.yml
   rate_limiting:
     default_requests_per_minute: 120  # Adjust based on needs
     burst_multiplier: 3
   ```

3. **Scale Monitoring**:
   ```bash
   # Scale Prometheus for large environments
   docker-compose -f deployment/docker-compose.monitoring.yml up -d --scale prometheus=3
   ```

## 🔄 Integration with Existing Systems

### Route Application Traffic

1. **Configure Application Proxy**:
   ```bash
   # Set proxy environment variables in applications
   export HTTP_PROXY=http://waygate-proxy:8080
   export HTTPS_PROXY=http://waygate-proxy:8080
   export NO_PROXY=localhost,127.0.0.1
   ```

2. **MCP Server Integration**:
   ```python
   # In MCP server configuration
   proxy_config = {
       "http_proxy": "http://waygate-proxy:8080",
       "https_proxy": "http://waygate-proxy:8080",
       "verify_ssl": True
   }
   ```

3. **Docker Container Network Routing**:
   ```yaml
   # In application docker-compose.yml
   services:
     your-app:
       environment:
         - HTTP_PROXY=http://waygate-proxy:8080
         - HTTPS_PROXY=http://waygate-proxy:8080
       networks:
         - waygate-dmz
   ```

## 🆘 Troubleshooting

### Common Issues

1. **Proxy Not Starting**:
   ```bash
   # Check configuration
   docker exec waygate-proxy python3 /app/proxy-entrypoint.sh test

   # Verify environment variables
   docker exec waygate-proxy env | grep WAYGATE
   ```

2. **External Requests Blocked**:
   ```bash
   # Check egress rules
   docker exec waygate-proxy cat /app/config/egress-rules.json

   # Review firewall logs
   docker exec waygate-egress-firewall dmesg | grep WAYGATE-FIREWALL
   ```

3. **High Latency**:
   ```bash
   # Check system resources
   docker stats waygate-proxy

   # Review performance metrics
   curl http://localhost:9090/api/v1/query?query=waygate_proxy_request_duration_seconds
   ```

### Debug Mode

```bash
# Enable debug logging
docker-compose -f deployment/docker-compose.proxy.yml \
  exec waygate-proxy \
  python3 -c "import logging; logging.getLogger().setLevel(logging.DEBUG)"
```

## 📊 Performance Benchmarks

### Expected Performance
- **Throughput**: 1000+ requests/second
- **Latency**: <100ms added latency
- **Concurrent Connections**: 1000+
- **Memory Usage**: <1GB under normal load
- **CPU Usage**: <50% with 4 cores

### Load Testing
```bash
# Install hey for load testing
go install github.com/rakyll/hey@latest

# Test proxy performance
hey -n 10000 -c 100 -H "X-API-Key: your-api-key" \
  http://localhost:8080/proxy/test
```

## 🔒 Security Hardening

### Additional Security Measures

1. **Enable Fail2Ban**:
   ```bash
   # Install and configure fail2ban for additional protection
   sudo apt install fail2ban
   # Configure with custom rules for proxy logs
   ```

2. **Network Segmentation**:
   ```bash
   # Use separate VLANs for different traffic types
   # DMZ for external-facing services
   # Internal network for inter-service communication
   ```

3. **Regular Security Audits**:
   ```bash
   # Run security scans
   docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
     aquasec/trivy image waygate-mcp-proxy:latest
   ```

---

**Last Updated**: 2025-09-28
**Status**: ✅ Production Ready
**Next Review**: 2025-10-28

For support and updates, refer to the main project documentation at `/home/jeremy/waygate-mcp/CLAUDE.md`.