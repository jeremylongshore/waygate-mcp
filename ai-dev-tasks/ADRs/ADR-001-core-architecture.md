# ADR-001: Core Architecture Decisions for Waygate MCP

**Architecture Decision Record**
**Status:** Accepted
**Date:** 2025-01-14
**Author:** Jeremy Longshore
**Deciders:** Jeremy Longshore
**AI-Assisted:** Yes (Claude)

## 1. Title
Core Architecture and Technology Stack for Waygate MCP Framework

## 2. Status
Accepted

## 3. Context

### 3.1 Background
We are building Waygate MCP as a replacement for NEXUS MCP, requiring decisions on:
- Core technology stack
- API framework selection
- Deployment architecture
- Plugin system design
- Monitoring and observability approach

### 3.2 Current State
- NEXUS MCP is deprecated and archived
- No existing MCP framework meets enterprise requirements
- Need for production-ready MCP implementation
- Requirement for extensive diagnostic capabilities

### 3.3 Requirements
- Python-based for consistency with existing ecosystem
- Fast API response times (< 100ms)
- Plugin extensibility
- Comprehensive monitoring
- Easy deployment to local VMs

## 4. Decision

### 4.1 Core Technology Stack
We will use:
- **Language:** Python 3.9+ (not 3.12 to ensure compatibility)
- **Web Framework:** FastAPI
- **ASGI Server:** Uvicorn with optional Gunicorn
- **Database:** SQLite (default) with PostgreSQL support
- **Logging:** structlog for structured JSON logging

### 4.2 API Architecture
- RESTful API with OpenAPI/Swagger documentation
- Async/await pattern for all I/O operations
- Pydantic for request/response validation
- Dependency injection for services

### 4.3 Plugin Architecture
- Dynamic plugin loading via Python importlib
- Plugin interface via abstract base classes
- Plugin registry with lifecycle management
- Configuration through environment variables

### 4.4 Deployment Strategy
- Primary: Direct Python execution on local VM
- Secondary: Docker containers
- Tertiary: Kubernetes for scale
- systemd service for production

## 5. Rationale

### 5.1 Why FastAPI?
- **Performance:** Among fastest Python frameworks
- **Developer Experience:** Automatic API documentation
- **Type Safety:** Full type hints support
- **Async Support:** Native async/await
- **Standards:** OpenAPI, JSON Schema compliant

### 5.2 Why structlog?
- **Structured:** JSON output for log aggregation
- **Performance:** Minimal overhead
- **Context:** Automatic context preservation
- **Integration:** Works with existing logging

### 5.3 Why SQLite Default?
- **Simplicity:** No external dependencies
- **Performance:** Sufficient for single-node
- **Migration Path:** Easy upgrade to PostgreSQL
- **Testing:** In-memory database for tests

### 5.4 Why Plugin Architecture?
- **Extensibility:** Add features without core changes
- **Isolation:** Plugin failures don't crash core
- **Modularity:** Clear separation of concerns
- **Community:** Enable third-party plugins

## 6. Consequences

### 6.1 Positive
- Fast development with modern Python features
- Excellent performance characteristics
- Strong typing reduces runtime errors
- Automatic API documentation
- Easy testing with FastAPI TestClient
- Plugin system enables customization

### 6.2 Negative
- FastAPI learning curve for new developers
- Async programming complexity
- Plugin system adds architectural overhead
- Python GIL limitations for CPU-bound work

### 6.3 Neutral
- Commitment to Python ecosystem
- Need for virtual environment management
- Dependency on third-party packages

## 7. Alternatives Considered

### 7.1 Flask
- **Pros:** Simpler, more mature, larger community
- **Cons:** No native async, manual validation, slower
- **Decision:** Rejected for performance reasons

### 7.2 Django + DRF
- **Pros:** Batteries included, admin interface
- **Cons:** Heavyweight, slower, unnecessary features
- **Decision:** Rejected as overkill for MCP server

### 7.3 aiohttp
- **Pros:** Pure async, lightweight
- **Cons:** More boilerplate, less developer friendly
- **Decision:** Rejected for developer experience

### 7.4 Go Implementation
- **Pros:** Better performance, single binary
- **Cons:** Language switch, less AI assistant support
- **Decision:** Rejected to maintain Python ecosystem

## 8. Implementation Details

### 8.1 Project Structure
```
waygate-mcp/
├── src/
│   ├── core/           # Core server logic
│   ├── api/            # API endpoints
│   ├── plugins/        # Plugin system
│   └── utils/          # Utilities
├── tests/
├── docs/
└── scripts/
```

### 8.2 Configuration Hierarchy
1. Default values in code
2. Configuration files
3. Environment variables
4. Command-line arguments

### 8.3 Plugin Interface
```python
class MCPPlugin(ABC):
    @abstractmethod
    async def initialize(self):
        pass

    @abstractmethod
    async def execute(self, command: dict):
        pass

    @abstractmethod
    async def shutdown(self):
        pass
```

## 9. Security Considerations

### 9.1 API Security
- API key authentication by default
- Optional OAuth2/JWT support
- Rate limiting per client
- Request size limits

### 9.2 Plugin Security
- Sandboxed execution environment
- Resource limits per plugin
- No direct file system access
- Validated configuration only

## 10. Monitoring Strategy

### 10.1 Metrics
- Prometheus-compatible metrics endpoint
- Custom business metrics
- Performance counters
- Error rates and latency

### 10.2 Tracing
- OpenTelemetry integration
- Distributed tracing support
- Correlation IDs
- Request/response logging

## 11. Migration Path

### 11.1 From NEXUS MCP
1. Export NEXUS configuration
2. Transform to Waygate format
3. Deploy Waygate instance
4. Verify functionality
5. Decommission NEXUS

### 11.2 Future Migrations
- Version upgrade path defined
- Backward compatibility for 2 versions
- Migration scripts provided
- Rollback procedures documented

## 12. References

- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [structlog Documentation](https://www.structlog.org)
- [MCP Protocol Specification](https://mcp.io/spec)
- [Python Async Best Practices](https://docs.python.org/3/library/asyncio.html)

## 13. Appendices

### A. Performance Benchmarks
- FastAPI: 30,000+ requests/second
- Flask: 10,000 requests/second
- Django: 5,000 requests/second
(Tests on equivalent hardware)

### B. Code Examples
See implementation in src/waygate_mcp.py

### C. Decision Matrix
| Criteria | FastAPI | Flask | Django | aiohttp |
|----------|---------|-------|--------|---------|
| Performance | 5 | 3 | 2 | 5 |
| Developer UX | 5 | 4 | 3 | 2 |
| Documentation | 5 | 4 | 5 | 3 |
| Async Support | 5 | 2 | 3 | 5 |
| **Total** | **20** | **13** | **13** | **15** |

---

**ADR ID:** ADR-001
**Related PRD:** PRD-00-waygate-mcp-framework
**Related ADRs:** None
**Supersedes:** None
**Superseded by:** None