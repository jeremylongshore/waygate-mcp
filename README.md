# Waygate MCP - Foundational MCP Server

Security-hardened Model Context Protocol (MCP) server with enterprise-grade container isolation.

## Quick Start

```bash
# One-line deployment
./quickstart.sh

# Check status
docker ps | grep waygate

# View logs
docker logs waygate-mcp
```

## Directory Structure

```
waygate-mcp/
├── quickstart.sh              # One-line deployment script
├── init.sh                    # Initialize development environment
├── documentation/             # All documentation and specs
├── deployment/               # Docker, nginx, deployment configs
├── source/                   # Source code, scripts, requirements
└── venv/                     # Python virtual environment
```

## Documentation

- [Getting Started](documentation/GETTING_STARTED.md)
- [Project Knowledge](documentation/PROJECT_KNOWLEDGE.md)
- [Container Security](documentation/CONTAINER_SECURITY.md)
- [Development Tasks](documentation/ai-dev-tasks/)

## Features

- **Security-hardened containers** with read-only filesystem
- **MCP protocol** compliance for AI integrations
- **Plugin architecture** for extensibility
- **Docker deployment** with Nginx reverse proxy
- **Enterprise-ready** with comprehensive documentation

---

*Created by Intent Solutions Inc - Building foundational AI infrastructure*