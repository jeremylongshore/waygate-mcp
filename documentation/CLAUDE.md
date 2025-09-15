# CLAUDE.md - Waygate MCP Project Guide

**Date:** 2025-01-14
**Version:** 2.0.0
**Status:** Production-Ready with Security-Hardened Docker Containers

This file provides guidance to Claude Code (claude.ai/code) when working with the Waygate MCP repository.

## 🎯 Project Overview

Waygate MCP is a **security-first containerized Model Context Protocol (MCP) server framework** built with enterprise-grade security through Docker containers. This is the successor to NEXUS MCP, implementing defense-in-depth security that's impossible with traditional virtual environment deployments.

### Key Security Features
- **Container Isolation**: Process, network, and filesystem isolation
- **Non-root Execution**: Runs as UID 1000 (waygate user)
- **Read-only Filesystem**: Only specific volumes are writable
- **Dropped Capabilities**: All Linux capabilities dropped except NET_BIND_SERVICE
- **Resource Limits**: CPU (2 cores) and Memory (1GB) hard limits
- **Network Segmentation**: Custom Docker bridge network (172.28.0.0/16)

## 📁 Project Structure

```
waygate-mcp/
├── src/                        # Source code
│   └── waygate_mcp.py         # Main MCP server implementation
├── tests/                      # Test suites
├── configs/                    # Configuration files
├── scripts/                    # Utility scripts
│   └── docker-entrypoint.sh  # Container entry point
├── nginx/                      # Nginx reverse proxy configs
│   └── nginx.conf             # Security-hardened nginx config
├── docs/                       # Technical documentation
│   └── CONTAINER_SECURITY.md  # Comprehensive security guide
├── ai-dev-tasks/              # AI development documentation
│   ├── PRDs/                  # Product requirements
│   ├── ADRs/                  # Architecture decisions
│   ├── tasks/                 # Task breakdowns
│   ├── specifications/        # Technical specs
│   ├── runbooks/             # Operations guides
│   ├── test-plans/           # Testing documentation
│   ├── risk-register/        # Risk management
│   ├── sop/                  # Standard procedures
│   └── database/             # Schema documentation
├── Dockerfile                  # Multi-stage secure build
├── docker-compose.yml         # Production deployment
├── docker-compose.dev.yml     # Development overrides
├── quickstart.sh              # One-line secure setup
├── requirements-docker.txt    # Pinned dependencies for container
├── .env.example               # Environment template
└── README.md                  # User documentation
```

## 🚀 Quick Start Commands

### One-Line Deployment
```bash
# Automated secure setup with secret generation
./quickstart.sh
```

### Manual Setup
```bash
# Generate secure secrets
export WAYGATE_SECRET_KEY=$(openssl rand -base64 32)
export WAYGATE_API_KEY=$(uuidgen)

# Build and start containers
docker-compose build --pull --no-cache
docker-compose up -d

# Check health
curl http://localhost:8000/health
```

### Development Mode
```bash
# Run with hot reload and debug capabilities
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Access container for debugging
docker-compose exec waygate /bin/bash

# View logs
docker-compose logs -f waygate
```

## 🔒 Security Architecture

### Container Security Layers
1. **User Isolation**: Non-root user (UID 1000)
2. **Filesystem**: Read-only root with specific writable volumes
3. **Capabilities**: All dropped except NET_BIND_SERVICE
4. **Network**: Isolated bridge network with no host access
5. **Resources**: Hard cgroup limits prevent DoS
6. **Syscalls**: Seccomp profiles block dangerous operations

### Security Configuration Files
- `Dockerfile`: Multi-stage build with security hardening
- `docker-compose.yml`: Production security settings
- `nginx/nginx.conf`: SSL/TLS, rate limiting, security headers
- `docs/CONTAINER_SECURITY.md`: Complete security documentation

## 📋 Development Guidelines

### Before Making Changes
1. Review existing security configurations
2. Check `ai-dev-tasks/` for architecture decisions
3. Ensure changes maintain security posture
4. Test in development mode first

### File Management Rules (STRICT)
- **NEVER** create files without explicit permission
- **ALWAYS** prefer editing existing files
- **NEVER** modify security configurations without approval
- **ALWAYS** maintain container security best practices

### Testing Requirements
```bash
# Run tests in container
docker-compose exec waygate pytest tests/

# Security scanning
docker scan waygate-mcp:latest

# Check container configuration
docker inspect waygate-mcp | jq '.[0].Config.User'
docker inspect waygate-mcp | jq '.[0].HostConfig.ReadonlyRootfs'
```

### Git Workflow
```bash
# Never commit secrets
echo ".env" >> .gitignore

# Always test before committing
docker-compose build --no-cache
docker-compose up -d
curl http://localhost:8000/health

# Use clear commit messages
git commit -m "feat(security): enhance container isolation"
```

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Core Settings
WAYGATE_ENV=production          # production/development
WAYGATE_LOG_LEVEL=INFO         # DEBUG/INFO/WARNING/ERROR

# Security (MUST CHANGE)
WAYGATE_SECRET_KEY=<generated>  # openssl rand -base64 32
WAYGATE_API_KEY=<generated>     # uuidgen

# Network
WAYGATE_CORS_ORIGINS=["https://yourdomain.com"]
WAYGATE_RATE_LIMIT=100          # requests per minute

# Resources
WAYGATE_MAX_REQUEST_SIZE=10485760  # 10MB
```

### Docker Security Settings
```yaml
# READ-ONLY: These settings are critical for security
read_only: true                 # Read-only root filesystem
cap_drop: ALL                   # Drop all capabilities
user: "1000:1000"               # Non-root user
security_opt:
  - no-new-privileges:true      # Prevent privilege escalation
```

## 📊 API Endpoints

| Endpoint | Method | Authentication | Description |
|----------|--------|---------------|-------------|
| `/health` | GET | None | Health check |
| `/ready` | GET | None | Readiness probe |
| `/metrics` | GET | Internal only | Prometheus metrics |
| `/mcp/execute` | POST | API Key | Execute MCP command |
| `/mcp/status` | GET | API Key | MCP engine status |
| `/plugins` | GET | API Key | List available plugins |

## 🚨 Security Checklist

### Before Deployment
- [ ] Changed default SECRET_KEY
- [ ] Changed default API_KEY
- [ ] Configured CORS origins
- [ ] Enabled HTTPS (nginx profile)
- [ ] Set production log level
- [ ] Reviewed rate limits
- [ ] Scanned for vulnerabilities

### Container Security
- [ ] Non-root user verified
- [ ] Read-only filesystem confirmed
- [ ] Capabilities dropped
- [ ] Resource limits set
- [ ] Network isolation verified
- [ ] Secrets not in image layers

## 📚 Documentation

### Core Documents
- **Security**: `docs/CONTAINER_SECURITY.md` - Complete security architecture
- **PRD**: `ai-dev-tasks/PRDs/00-prd-waygate-mcp-framework.md` - Product requirements
- **Architecture**: `ai-dev-tasks/ADRs/ADR-001-core-architecture.md` - Design decisions
- **Tech Spec**: `ai-dev-tasks/specifications/tech-spec-waygate-mcp.md` - Technical details
- **Operations**: `ai-dev-tasks/runbooks/waygate-operations-runbook.md` - Ops procedures

### Quick Reference
- **Logs**: `docker-compose logs -f waygate`
- **Shell**: `docker-compose exec waygate /bin/bash`
- **Restart**: `docker-compose restart waygate`
- **Stop**: `docker-compose down`
- **Update**: `docker-compose pull && docker-compose up -d`

## 🔍 Troubleshooting

### Common Issues

#### Container Won't Start
```bash
# Check logs
docker-compose logs waygate

# Verify permissions
ls -la scripts/docker-entrypoint.sh  # Should be executable

# Check resources
docker system df
```

#### Health Check Failing
```bash
# Test from inside container
docker-compose exec waygate curl http://localhost:8000/health

# Check if port is bound
netstat -tlnp | grep 8000
```

#### Permission Denied Errors
```bash
# Ensure correct ownership
docker-compose exec waygate ls -la /app

# Check user context
docker-compose exec waygate whoami  # Should be 'waygate'
```

## ⚠️ Security Warnings

### NEVER DO THIS
- ❌ Run container as root
- ❌ Disable read-only filesystem
- ❌ Add unnecessary capabilities
- ❌ Expose container ports directly to internet
- ❌ Store secrets in image layers
- ❌ Use 'latest' tags in production

### ALWAYS DO THIS
- ✅ Use specific version tags
- ✅ Scan images for vulnerabilities
- ✅ Rotate secrets regularly
- ✅ Monitor container logs
- ✅ Keep base images updated
- ✅ Use multi-stage builds

## 🎯 Development Priorities

1. **Security First**: Every change must maintain or improve security
2. **Container Native**: Design for container deployment, not VMs
3. **Immutable Infrastructure**: Containers are cattle, not pets
4. **Zero Trust**: Assume breach, implement defense in depth
5. **Observability**: Comprehensive logging and monitoring

## 📈 Performance Targets

- Container startup: < 5 seconds
- Health check response: < 100ms
- API response time: < 200ms
- Memory usage: < 256MB baseline
- CPU usage: < 10% idle

## 🤝 Contributing

1. Review security documentation first
2. Test in development container
3. Run security scans
4. Update documentation
5. Submit PR with security impact assessment

## 🔄 Migration from NEXUS MCP

NEXUS MCP (archived at `/home/jeremy/projects/archived/NEXUS_MCP/`) used virtual environments. Waygate MCP provides:

- **10x better security** through containerization
- **Process isolation** preventing lateral movement
- **Network segmentation** with custom bridge networks
- **Resource limits** preventing DoS attacks
- **Immutable deployments** with read-only filesystems

## 📞 Support

- **Documentation**: See `ai-dev-tasks/` directory
- **Security Issues**: Review `docs/CONTAINER_SECURITY.md`
- **Operations**: Check `ai-dev-tasks/runbooks/`

---

**Last Updated:** 2025-01-14
**Maintained By:** Jeremy Longshore
**Architecture:** Security-Hardened Docker Containers
**Status:** ✅ Production-Ready