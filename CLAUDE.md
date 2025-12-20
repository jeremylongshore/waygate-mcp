## Task Tracking (Beads / bd)
- Use `bd` for ALL tasks/issues (no markdown TODO lists).
- Start of session: `bd ready`
- Create work: `bd create "Title" -p 1 --description "Context + acceptance criteria"`
- Update status: `bd update <id> --status in_progress`
- Finish: `bd close <id> --reason "Done"`
- End of session: `bd sync` (flush/import/export + git sync)
- Manual testing safety:
  - Prefer `BEADS_DIR` to isolate a workspace if needed. (`BEADS_DB` exists but is deprecated.)


# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

Waygate MCP is a security-hardened, enterprise-grade MCP (Model Context Protocol) server framework that serves as the successor to NEXUS MCP. It features Turso edge database integration, comprehensive plugin architecture, and Docker containerization with extensive security hardening.

## Architecture

### Core Components

- **MCP Server** (`source/waygate_mcp.py`): FastAPI-based server with comprehensive endpoints for MCP operations, health checks, metrics, and diagnostics
- **Database Layer** (`source/database.py`): Turso (SQLite at edge) integration with fallback to local SQLite, comprehensive schema management
- **MCP Integration** (`source/mcp_integration.py`): Manages external MCP server integration, plugin lifecycle, and unified tool access
- **Plugin System** (`source/plugins/`): Modular plugin architecture for extending MCP functionality

### Database Schema

The system uses a comprehensive database schema with these core tables:
- `config`: System configuration with type validation
- `api_keys`: API key management with permissions and rate limiting
- `plugins`: Plugin registry with status tracking and error handling
- `command_history`: Command execution audit trail
- `metrics`: Performance and usage metrics
- `system_events`: System event logging
- `mcp_servers`: MCP server configurations and status

### Plugin Architecture

- **Base Plugin** (`source/plugins/base_plugin.py`): Abstract base class for all plugins
- **Plugin Loader** (`source/plugins/plugin_loader.py`): Dynamic plugin loading and management
- **MCP Bridge Plugins**: Integration plugins for external MCP servers (Firebase, BigQuery, GitHub, etc.)

## Development Commands

### Database Setup (Turso)

```bash
# Install Turso CLI
curl -sSfL https://get.tur.so/install.sh | bash

# Create database
turso db create waygate-mcp

# Get auth token
turso db tokens create waygate-mcp

# Set environment variable
export DATABASE_URL="libsql://waygate-mcp-[username].turso.io?authToken=your-token"
```

### Local Development

```bash
# Activate virtual environment
source activate_venv.sh

# Install dependencies
pip install -r source/requirements.txt

# Run development server
python -m source.waygate_mcp --host 127.0.0.1 --port 8000 --reload --env development

# Run with specific environment
WAYGATE_ENV=development python -m source.waygate_mcp
```

### Docker Deployment

```bash
# Quick secure deployment
./quickstart.sh

# Manual deployment
docker-compose up -d

# Check health
curl http://localhost:8000/health

# View logs
docker-compose logs -f waygate

# Stop services
docker-compose down
```

### Testing & Quality

```bash
# Check database health
curl http://localhost:8000/health

# View metrics
curl http://localhost:8000/metrics

# Test MCP integration
curl http://localhost:8000/mcp/status

# List available MCP tools
curl http://localhost:8000/mcp/tools
```

## Environment Configuration

### Required Environment Variables

- `DATABASE_URL`: Turso database connection string (required)
- `WAYGATE_SECRET_KEY`: Application secret key
- `WAYGATE_ENV`: Environment (development/production)

### MCP Server Integration Variables

```bash
# Firebase MCP Server
FIREBASE_PROJECT_ID=diagnostic-pro-start-up
FIREBASE_REGION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# BigQuery MCP Server
GOOGLE_CLOUD_PROJECT=diagnostic-pro-start-up
BIGQUERY_DATASET=diagnosticpro_prod

# GitHub MCP Server
GITHUB_TOKEN=your_token
GITHUB_OWNER=jeremylongshore

# MCP Configuration
MCP_SERVERS_ENABLED=firebase,bigquery,github
MCP_AUTO_INITIALIZE=true
```

## Security Features

### Container Security
- Non-root user execution (UID 1000)
- Read-only root filesystem
- Dropped capabilities (ALL)
- Resource limits (CPU: 2 cores, Memory: 1GB)
- Network isolation
- No new privileges
- AppArmor and Seccomp profiles

### Application Security
- Secure secret generation
- API key management with permissions
- Rate limiting
- CORS configuration
- Request size limits
- Comprehensive audit logging

## API Endpoints

### Core Endpoints
- `GET /`: Service information
- `GET /health`: Health check with database status
- `GET /ready`: Readiness probe
- `GET /metrics`: Prometheus metrics

### MCP Endpoints
- `POST /mcp/execute`: Execute MCP commands
- `GET /mcp/status`: MCP engine status
- `GET /mcp/servers`: List integrated MCP servers
- `GET /mcp/tools`: List all available tools
- `POST /mcp/servers/{name}/reload`: Reload specific MCP server

### Diagnostic Endpoints
- `GET /diagnostics/connection`: Connection diagnostics
- `GET /diagnostics/performance`: Performance metrics

## Plugin Development

### Creating New Plugins

1. Inherit from `BasePlugin` class
2. Implement required abstract methods
3. Register plugin in plugin loader
4. Add configuration to database

### MCP Bridge Plugin Pattern

```python
class CustomMCPPlugin(BasePlugin):
    async def configure_mcp_server(self, config):
        # Configure MCP server connection
        pass

    async def get_tools(self):
        # Return available tools
        pass

    async def execute(self, tool_name, parameters):
        # Execute tool
        pass
```

## Deployment Considerations

### Production Deployment
- Use Turso for production database
- Enable SSL with nginx profile: `docker-compose --profile ssl up -d`
- Generate secure secrets
- Configure proper CORS origins
- Enable monitoring and logging
- Regular security updates

### Resource Requirements
- Minimum: 256MB RAM, 0.5 CPU cores
- Recommended: 1GB RAM, 2 CPU cores
- Storage: Depends on log retention and data requirements

## Monitoring & Observability

### Health Checks
- Container health checks every 30s
- Application health endpoint at `/health`
- Database connectivity verification

### Logging
- Structured JSON logging with structlog
- Container logs with rotation (10MB max, 3 files)
- System events logged to database

### Metrics
- Prometheus-compatible metrics endpoint
- Database performance metrics
- MCP server status tracking
- Command execution audit trail

## Common Troubleshooting

### Database Issues
- Verify `DATABASE_URL` format for Turso
- Check network connectivity for Turso
- Fallback to SQLite for local development

### Container Issues
- Check resource limits if experiencing OOM
- Verify volume permissions for data persistence
- Review security constraints if functionality is limited

### MCP Integration Issues
- Verify MCP server configurations in database
- Check plugin loading in logs
- Validate environment variables for external services

## File Structure Notes

- `source/`: All Python source code
- `deployment/`: Docker configuration and deployment files
- `documentation/`: Additional documentation and specs
- `venv/`: Python virtual environment (development)
- Script files (`*.sh`): Deployment and setup automation