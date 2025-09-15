# Waygate MCP - Secure Containerized MCP Server Framework 🐳🔒

**Version:** 2.0.0
**Status:** Production-Ready
**Successor to:** NEXUS MCP
**Architecture:** Security-Hardened Docker Containers

## 🚀 Overview

Waygate MCP is an enterprise-grade Model Context Protocol (MCP) server framework built with **security-first containerization**. Unlike traditional virtual environment deployments, Waygate uses Docker containers for superior isolation, security, and reproducibility.

## 🔐 Why Containers > Virtual Environments

| Security Aspect | Virtual Environment | Container | Advantage |
|-----------------|-------------------|-----------|-----------|
| **Process Isolation** | ❌ Shared with host | ✅ Isolated namespace | Prevents interference |
| **Network Isolation** | ❌ Uses host network | ✅ Private network | Controls traffic |
| **File System** | ❌ Full host access | ✅ Isolated filesystem | Limits breach impact |
| **Resource Limits** | ❌ No limits | ✅ cgroups limits | Prevents DoS |
| **Privilege Escalation** | ⚠️ Easier | ✅ Non-root user | Reduced attack surface |

## ✨ Key Features

- **Security-Hardened Containers**: Non-root execution, read-only filesystem, dropped capabilities
- **Production-Ready**: Built with FastAPI for high performance
- **Diagnostic Excellence**: Comprehensive troubleshooting tools and playbooks
- **Plugin Architecture**: Extensible through modular plugins
- **Enterprise Features**: SSL/TLS, rate limiting, monitoring built-in
- **One-Line Setup**: Automated secure deployment with `quickstart.sh`

## 🚀 Quick Start (One Command!)

```bash
# Secure automated setup
curl -sSL https://raw.githubusercontent.com/jeremylongshore/waygate-mcp/main/quickstart.sh | bash
```

Or clone and run locally:

```bash
git clone https://github.com/jeremylongshore/waygate-mcp.git
cd waygate-mcp
chmod +x quickstart.sh
./quickstart.sh
```

## 📋 Manual Installation

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- Git
- 2GB+ disk space

### Step-by-Step Setup

```bash
# 1. Clone the repository
git clone https://github.com/jeremylongshore/waygate-mcp.git
cd waygate-mcp

# 2. Generate secure configuration
export WAYGATE_SECRET_KEY=$(openssl rand -base64 32)
export WAYGATE_API_KEY=$(uuidgen)

# 3. Create environment file
cat > .env << EOF
WAYGATE_ENV=production
WAYGATE_SECRET_KEY=${WAYGATE_SECRET_KEY}
WAYGATE_API_KEY=${WAYGATE_API_KEY}
EOF

# 4. Build and start containers
docker-compose build --pull --no-cache
docker-compose up -d

# 5. Verify health
curl http://localhost:8000/health
```

### Access Points

- **API**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics
- **Documentation**: http://localhost:8000/docs (development mode)

## 📁 Project Structure

```
waygate-mcp/
├── ai-dev-tasks/         # AI development documentation
│   ├── PRDs/            # Product requirements
│   ├── ADRs/            # Architecture decisions
│   ├── tasks/           # Task breakdowns
│   └── specifications/  # Technical specs
├── src/                 # Source code
├── tests/               # Test suites
├── docs/                # Documentation
├── scripts/             # Utility scripts
└── configs/             # Configuration files
```

## 🐳 Development Mode

```bash
# Run in development mode with hot reload
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Access container shell for debugging
docker-compose exec waygate /bin/bash

# View logs
docker-compose logs -f waygate
```

## 🔧 Configuration

Configuration via environment variables in `.env` file:

```bash
# Environment
WAYGATE_ENV=production          # production/development
WAYGATE_LOG_LEVEL=INFO          # DEBUG/INFO/WARNING/ERROR

# Security (CHANGE THESE!)
WAYGATE_SECRET_KEY=<generated>  # Generate with: openssl rand -base64 32
WAYGATE_API_KEY=<generated>     # Generate with: uuidgen

# Network
WAYGATE_CORS_ORIGINS=["https://yourdomain.com"]
WAYGATE_RATE_LIMIT=100          # Requests per minute

# Resources
WAYGATE_MAX_REQUEST_SIZE=10485760  # 10MB
```

## 🛡️ Security Features

### Container Security
- ✅ **Non-root user**: Runs as UID 1000 (waygate user)
- ✅ **Read-only filesystem**: Writable volumes only where needed
- ✅ **Dropped capabilities**: All capabilities dropped except NET_BIND_SERVICE
- ✅ **No new privileges**: Prevents privilege escalation
- ✅ **Resource limits**: CPU (2 cores) and Memory (1GB) limits
- ✅ **Network isolation**: Custom Docker network with defined subnet
- ✅ **Secrets management**: Environment-based with .env file

### Application Security
- ✅ **API key authentication**: Required for API access
- ✅ **Rate limiting**: Configurable per-endpoint limits
- ✅ **CORS protection**: Configurable allowed origins
- ✅ **Input validation**: Pydantic models for all inputs
- ✅ **SSL/TLS ready**: Nginx configuration included

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Service information |
| `/health` | GET | Health check |
| `/ready` | GET | Readiness check |
| `/metrics` | GET | Prometheus metrics |
| `/mcp/execute` | POST | Execute MCP command |
| `/mcp/status` | GET | MCP engine status |
| `/plugins` | GET | List plugins |
| `/diagnostics/connection` | GET | Connection diagnostics |
| `/diagnostics/performance` | GET | Performance diagnostics |

## 🔍 Diagnostics

Run diagnostics to troubleshoot issues:

```bash
# Check server status
curl http://localhost:8000/health

# Run connection diagnostics
curl http://localhost:8000/diagnostics/connection

# Check performance metrics
curl http://localhost:8000/diagnostics/performance
```

## 🚦 Development

### Running Tests

```bash
pytest tests/ -v --cov=src
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
flake8 src/ tests/

# Type checking
mypy src/
```

## 📝 Documentation

- **PRD**: `ai-dev-tasks/PRDs/00-prd-waygate-mcp-framework.md`
- **Architecture**: `ai-dev-tasks/ADRs/ADR-001-core-architecture.md`
- **Tech Spec**: `ai-dev-tasks/specifications/tech-spec-waygate-mcp.md`
- **Tasks**: `ai-dev-tasks/tasks/00-tasks-waygate-mcp-implementation.md`

## 🔄 Migration from NEXUS MCP

NEXUS MCP has been archived at `/home/jeremy/projects/archived/NEXUS_MCP`.

To migrate:
1. Export NEXUS configuration
2. Transform to Waygate format
3. Deploy Waygate instance
4. Verify functionality

## 🤝 Contributing

1. Create feature branch
2. Make changes
3. Run tests
4. Submit PR

## 📄 License

Open Source - MIT License

## 🆘 Support

For issues or questions, check the documentation in `ai-dev-tasks/` or create an issue.

---

**Built with AI Assistance** - Developed with Claude (Anthropic)
**Maintained by**: Jeremy Longshore
**Last Updated**: 2025-01-14