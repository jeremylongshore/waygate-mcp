# Project Knowledge: Waygate MCP

## System Context

Waygate MCP is the successor to NEXUS MCP, designed as a foundational Model Context Protocol server that prioritizes:
1. **Simplicity** - Minimal dependencies, maximum clarity
2. **Security** - Container-first architecture with defense in depth
3. **Extensibility** - Easy plugin system for custom tools
4. **Portability** - Runs anywhere Python runs

## Architecture Overview

### Core Components

```
┌─────────────────────────────────────────┐
│           Claude Code / AI Agent        │
├─────────────────────────────────────────┤
│              stdio (JSON-RPC)           │
├─────────────────────────────────────────┤
│            waygate.sh wrapper           │
├─────────────────────────────────────────┤
│           waygate_mcp.py server         │
├─────────────────────────────────────────┤
│     Resources │ Tools │ Plugins         │
├─────────────────────────────────────────┤
│         File System / Docker            │
└─────────────────────────────────────────┘
```

### Communication Flow

1. **Claude Code** sends JSON requests via stdio
2. **waygate.sh** wrapper handles environment setup
3. **waygate_mcp.py** processes requests and returns responses
4. All communication is stateless and async

### Key Design Decisions

- **stdio-based**: Uses standard input/output for maximum compatibility
- **JSON-RPC style**: Simple request/response protocol
- **Stateless**: Each request is independent
- **Async**: Built on Python's asyncio for performance
- **Plugin-based**: Core is minimal, features added via plugins

## Project Organization

### Active/Archived Pattern

```
/home/jeremy/projects/
├── active/          # Current work
│   ├── waygate-mcp/
│   ├── project-a/
│   └── project-b/
└── archived/        # Completed/paused
    ├── NEXUS_MCP/
    ├── old-project/
    └── completed-work/
```

This pattern:
- Keeps workspace focused on current work
- Preserves completed projects for reference
- Makes it easy to reactivate old projects
- Reduces cognitive load

### Directory Structure

```
waygate-mcp/
├── Core Files
│   ├── waygate_mcp.py      # Main server
│   ├── waygate.sh          # Stdio wrapper
│   └── start_waygate.sh    # Local runner
├── Configuration
│   ├── .env                # Environment config
│   └── .env.example        # Template
├── Extensions
│   └── src/
│       ├── plugins/        # Plugin directory
│       └── example_tools.py # Examples
├── Containerization
│   ├── Dockerfile          # Multi-stage build
│   ├── docker-compose.yml  # Orchestration
│   └── nginx/             # Reverse proxy
└── Documentation
    ├── README.md           # User guide
    └── docs/              # Technical docs
```

## Technical Implementation

### MCP Protocol

Waygate implements a subset of the Model Context Protocol:

**Request Types:**
- `resource` - Access data resources
- `tool` - Execute tools/functions
- `ping` - Health check

**Request Format:**
```json
{
  "type": "tool",
  "name": "waygate_echo",
  "parameters": {
    "message": "Hello World"
  }
}
```

**Response Format:**
```json
{
  "success": true,
  "result": "Hello World",
  "timestamp": "2024-01-15T12:00:00Z"
}
```

### Resource URIs

Resources use a URI scheme for addressing:

- `waygate://system` - System information
- `waygate://projects/list` - All projects
- `waygate://projects/active` - Active only
- `waygate://projects/archived` - Archived only

### Tool System

Tools are async functions that:
1. Accept parameters as a dictionary
2. Process the request
3. Return a result dictionary

Example:
```python
async def tool_echo(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
    message = parameters.get("message", "")
    return {"success": True, "echo": message}
```

### Plugin Architecture

Plugins inherit from `BasePlugin` and implement:
- `get_tools()` - List available tools
- `execute()` - Handle tool execution

Plugins are auto-discovered from `src/plugins/` directory.

## Security Model

### Container Security

When running in Docker:
- Non-root user (UID 1000)
- Read-only root filesystem
- Dropped Linux capabilities
- Resource limits (CPU/Memory)
- Network isolation

### Local Security

When running locally:
- Runs as current user
- Logs to `/tmp` (not stderr)
- No network exposure by default
- Environment-based configuration

## Environment Variables

### Core Settings
- `WAYGATE_MODE` - development/production
- `WAYGATE_LOG_LEVEL` - DEBUG/INFO/WARNING/ERROR
- `WAYGATE_PROJECTS_DIR` - Base project directory

### Security
- `WAYGATE_SECRET_KEY` - API secret key
- `WAYGATE_API_KEY` - Authentication key

### Docker
- `WAYGATE_CONTAINER_NAME` - Container name
- `WAYGATE_NETWORK_NAME` - Docker network

## Development Workflow

### Adding a New Tool

1. **Simple Method** - Add to example_tools.py:
```python
async def my_tool(self, param):
    return {"result": "success"}
```

2. **Plugin Method** - Create new plugin:
```python
class MyPlugin(BasePlugin):
    async def execute(self, tool_name, params):
        return {"result": "success"}
```

### Testing

```bash
# Unit tests
pytest tests/

# Integration test
echo '{"type": "ping"}' | python waygate_mcp.py

# Docker test
docker-compose up -d
curl http://localhost:8000/health
```

### Debugging

```bash
# Enable debug logging
export WAYGATE_LOG_LEVEL=DEBUG

# Check logs
tail -f /tmp/waygate_mcp.log

# Docker logs
docker-compose logs -f waygate
```

## Performance Considerations

- **Startup**: < 1 second for stdio mode
- **Response time**: < 100ms for simple tools
- **Memory**: < 50MB baseline
- **Concurrent requests**: Handled via asyncio

## Migration from NEXUS MCP

Key differences:
1. **stdio-based** instead of HTTP API
2. **Plugin system** for extensibility
3. **Docker-first** deployment
4. **Active/Archived** project organization
5. **Simplified dependencies**

Migration steps:
1. Move NEXUS to `archived/`
2. Deploy Waygate to `active/`
3. Update Claude Code configuration
4. Migrate custom tools to plugins

## Future Enhancements

Planned features:
- Web UI for management
- Database persistence
- Webhook support
- Cloud deployment templates
- More plugin examples

## System Prompt for AI Assistants

When working with Waygate MCP:

```
You are working with Waygate MCP, a foundational MCP server framework.

Key points:
- It uses stdio communication (JSON in/out)
- Located at /home/jeremy/waygate-mcp/
- Successor to NEXUS MCP (now archived)
- Follows active/archived project organization
- Container-first but runs locally too
- Extensible via plugins in src/plugins/

When asked to:
- Add features: Create plugins, not modify core
- Debug: Check /tmp/waygate_mcp.log
- Deploy: Use docker-compose
- Integrate: Configure via waygate.sh wrapper

Always keep code simple, secure, and well-documented.
```

## Troubleshooting

### Common Issues

**Server won't start:**
- Check Python version (3.8+)
- Verify environment variables
- Check log file permissions

**Docker issues:**
- Ensure Docker daemon running
- Check port 8000 availability
- Verify .env configuration

**Claude Code integration:**
- Path to waygate.sh must be absolute
- Script must be executable
- Check stdio communication

## References

- [Model Context Protocol](https://github.com/modelcontextprotocol)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Python Asyncio](https://docs.python.org/3/library/asyncio.html)
- [JSON-RPC Specification](https://www.jsonrpc.org/)

---

*Last Updated: 2025-01-15*
*Version: 2.0.0*
*Maintainer: Jeremy Longshore*