# Waygate MCP - Enterprise-Grade MCP Server Framework

**Version:** 2.0.0
**Status:** In Development
**Successor to:** NEXUS MCP

## 🚀 Overview

Waygate MCP is an enterprise-grade Model Context Protocol (MCP) server framework designed to provide production-ready MCP implementations with comprehensive diagnostics, plugin architecture, and monitoring capabilities.

## ✨ Key Features

- **Production-Ready**: Built with FastAPI for high performance
- **Diagnostic Excellence**: Comprehensive troubleshooting tools and playbooks
- **Plugin Architecture**: Extensible through modular plugins
- **Enterprise Features**: Security, scalability, monitoring built-in
- **Backward Compatible**: Migration path from NEXUS MCP

## 📋 Quick Start

### Prerequisites

- Python 3.9+
- Git
- 1GB+ disk space

### Installation

```bash
# Clone the repository
cd /home/jeremy/projects/waygate-mcp

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python src/waygate_mcp.py
```

### Access Points

- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs (development mode)
- **Health Check**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics

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

## 🔧 Configuration

Configuration via environment variables or `.env` file:

```bash
WAYGATE_MODE=local_vm
WAYGATE_ENV=development
WAYGATE_LOG_LEVEL=INFO
WAYGATE_PORT=8000
```

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