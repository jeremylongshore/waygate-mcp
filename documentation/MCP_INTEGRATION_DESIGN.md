# MCP Server Integration Design for Waygate MCP

## Overview

This document outlines the integration strategy for embedding 6 production-ready MCP servers directly into the Waygate MCP architecture, creating a unified AI automation platform that leverages existing, battle-tested MCP servers rather than building custom solutions from scratch.

## Production-Ready MCP Servers Identified

### 1. Firebase MCP Server (Google Official)
- **Source**: Google Firebase CLI (Experimental)
- **Install**: `npx firebase-tools@beta --experimental mcp`
- **Tools**: 30+ Firebase management tools
- **Integration Pattern**: NPM package with stdio communication
- **Use Case**: DiagnosticPro platform management

### 2. BigQuery MCP Server (Google Cloud)
- **Source**: Google Cloud MCP Toolbox for Databases
- **Tools**: SQL execution, schema discovery, ML forecasting
- **Integration Pattern**: Python-based with Google Cloud APIs
- **Use Case**: Analytics for 266 production tables

### 3. GitHub MCP Server (Anthropic Official)
- **Source**: Anthropic/GitHub collaboration - official server
- **Repository**: github.com/modelcontextprotocol/servers
- **Tools**: Repository management, issues, PRs, code scanning
- **Integration Pattern**: Go-based, official reference implementation

### 4. n8n MCP Server (Community)
- **Source**: github.com/czlonkowski/n8n-mcp
- **Tools**: 525+ workflow automation nodes
- **Coverage**: 99% of n8n operations
- **Integration Pattern**: Python-based with n8n APIs

### 5. Docker Hub MCP Server (Docker Official)
- **Source**: Docker Hub MCP Server (Docker Inc.)
- **Repository**: github.com/docker/hub-mcp
- **Tools**: Container discovery, image management
- **Integration Pattern**: Docker-native with Hub APIs

### 6. Slack MCP Server (Community/Official)
- **Source**: Multiple implementations available
- **Tools**: Message management, channel operations, bot integration
- **Integration Pattern**: OAuth-based with Slack APIs
- **Use Case**: Bob's Brain Slack integration

## Integration Architecture

### Core Integration Strategy: MCP-in-MCP Pattern

Instead of running separate MCP servers, we'll embed them as **internal MCP plugins** within Waygate MCP using a multi-layered approach:

```
┌─────────────────────────────────────────────────────────────┐
│                    Waygate MCP Server                        │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                Plugin Framework                         │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      │ │
│  │  │ Firebase    │ │ BigQuery    │ │ GitHub      │      │ │
│  │  │ MCP Plugin  │ │ MCP Plugin  │ │ MCP Plugin  │      │ │
│  │  └─────────────┘ └─────────────┘ └─────────────┘      │ │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐      │ │
│  │  │ n8n         │ │ Docker Hub  │ │ Slack       │      │ │
│  │  │ MCP Plugin  │ │ MCP Plugin  │ │ MCP Plugin  │      │ │
│  │  └─────────────┘ └─────────────┘ └─────────────┘      │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │            Turso Database (Credentials)                │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Plugin Architecture Enhancement

**Current State:**
- Basic `BasePlugin` class exists
- Simple `GitHubPlugin` example (template-based)
- Missing `plugin_loader.py` (referenced but not implemented)

**Required Enhancements:**
1. **MCP Bridge Plugin Class** - Extends `BasePlugin` to interface with external MCP servers
2. **Credential Management** - Secure storage in Turso database
3. **Communication Layer** - stdio, HTTP, or direct Python imports
4. **Tool Registration** - Dynamically expose MCP server tools as Waygate tools

## Implementation Plan

### Phase 1: Framework Foundation

#### 1.1 Create MCP Bridge Plugin Architecture

```python
# source/plugins/mcp_bridge_plugin.py
class MCPBridgePlugin(BasePlugin):
    """Base class for integrating external MCP servers"""

    def __init__(self, mcp_config: Dict[str, Any]):
        super().__init__()
        self.mcp_config = mcp_config
        self.mcp_client = None
        self.credentials = {}

    async def initialize_mcp_client(self):
        """Initialize connection to external MCP server"""
        pass

    async def get_mcp_tools(self) -> List[Dict[str, Any]]:
        """Fetch tools from external MCP server"""
        pass

    async def execute_mcp_tool(self, tool_name: str, parameters: Dict[str, Any]):
        """Execute tool on external MCP server"""
        pass
```

#### 1.2 Implement Plugin Loader

```python
# source/plugins/plugin_loader.py
class PluginLoader:
    """Dynamic plugin loading with MCP server support"""

    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.loaded_plugins = {}
        self.mcp_servers = {}

    async def load_mcp_server_plugins(self):
        """Load all configured MCP server plugins"""
        pass

    async def reload_plugin(self, plugin_name: str):
        """Hot-reload a specific plugin"""
        pass
```

#### 1.3 Enhance Database Schema for MCP Credentials

```sql
-- Add to database.py
CREATE TABLE IF NOT EXISTS mcp_servers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    server_type TEXT NOT NULL, -- 'firebase', 'bigquery', etc.
    config JSON NOT NULL,
    credentials JSON NOT NULL, -- Encrypted
    status TEXT DEFAULT 'inactive',
    last_sync TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Phase 2: Individual MCP Server Integrations

#### 2.1 Firebase MCP Server Integration

**Integration Method**: NPM package execution with stdio communication

```python
# source/plugins/firebase_mcp_plugin.py
class FirebaseMCPPlugin(MCPBridgePlugin):
    """Firebase MCP Server integration"""

    async def initialize_mcp_client(self):
        # Execute: npx firebase-tools@beta --experimental mcp
        # Communicate via stdio protocol
        pass
```

**Key Features:**
- 30+ Firebase management tools
- Project configuration
- Authentication management
- Database operations for DiagnosticPro

#### 2.2 BigQuery MCP Server Integration

**Integration Method**: Google Cloud MCP Toolbox direct Python integration

```python
# source/plugins/bigquery_mcp_plugin.py
class BigQueryMCPPlugin(MCPBridgePlugin):
    """BigQuery MCP Server integration"""

    async def initialize_mcp_client(self):
        # Direct integration with Google Cloud MCP Toolbox
        # Python-based, no external process needed
        pass
```

**Key Features:**
- SQL execution against 266 production tables
- Schema discovery
- ML forecasting capabilities

#### 2.3 GitHub MCP Server Integration

**Integration Method**: Go binary execution with stdio/HTTP

```python
# source/plugins/github_mcp_plugin.py
class GitHubMCPPlugin(MCPBridgePlugin):
    """Official GitHub MCP Server integration"""

    async def initialize_mcp_client(self):
        # Use official GitHub MCP server binary
        # github.com/modelcontextprotocol/servers
        pass
```

**Key Features:**
- Repository management
- Issue and PR operations
- Code scanning integration
- OAuth authentication

#### 2.4 n8n MCP Server Integration

**Integration Method**: Python subprocess with n8n APIs

```python
# source/plugins/n8n_mcp_plugin.py
class N8nMCPPlugin(MCPBridgePlugin):
    """n8n Workflow Automation MCP integration"""

    async def initialize_mcp_client(self):
        # github.com/czlonkowski/n8n-mcp
        # 525+ workflow automation nodes
        pass
```

**Key Features:**
- 525+ automation nodes
- Workflow creation and management
- Integration with existing n8n projects

#### 2.5 Docker Hub MCP Server Integration

**Integration Method**: Docker official MCP server

```python
# source/plugins/docker_hub_mcp_plugin.py
class DockerHubMCPPlugin(MCPBridgePlugin):
    """Docker Hub MCP Server integration"""

    async def initialize_mcp_client(self):
        # Official Docker Hub MCP server
        # github.com/docker/hub-mcp
        pass
```

**Key Features:**
- Container image discovery
- Repository management
- Security scanning results

#### 2.6 Slack MCP Server Integration

**Integration Method**: OAuth-based with Slack APIs

```python
# source/plugins/slack_mcp_plugin.py
class SlackMCPPlugin(MCPBridgePlugin):
    """Slack MCP Server integration for Bob's Brain"""

    async def initialize_mcp_client(self):
        # OAuth integration with Slack APIs
        # Support for Bob's Brain Slack bot
        pass
```

**Key Features:**
- Message management
- Channel operations
- Bob's Brain integration
- OAuth authentication

### Phase 3: Integration and Testing

#### 3.1 Docker Compose Enhancement

```yaml
# deployment/docker-compose.yml - Additional services
services:
  waygate:
    # ... existing configuration
    environment:
      # MCP Server configurations
      - FIREBASE_PROJECT_ID=${FIREBASE_PROJECT_ID}
      - GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT}
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - N8N_API_URL=${N8N_API_URL}
      - SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN}
      - DOCKER_HUB_TOKEN=${DOCKER_HUB_TOKEN}
```

#### 3.2 Credentials Management

```python
# Enhanced database operations for MCP credentials
async def store_mcp_credentials(server_name: str, credentials: Dict[str, Any]):
    """Securely store MCP server credentials in Turso"""
    encrypted_creds = encrypt_credentials(credentials)
    await db_manager.execute_query(
        "INSERT OR REPLACE INTO mcp_servers (name, credentials) VALUES (?, ?)",
        [server_name, json.dumps(encrypted_creds)]
    )
```

## Security Considerations

### 1. Credential Encryption
- All MCP server credentials stored encrypted in Turso
- Environment variables for sensitive tokens
- OAuth tokens with proper refresh mechanisms

### 2. Container Security
- MCP servers run within Waygate's secure container
- No external container spawning
- Inherited security hardening (read-only filesystem, non-root user)

### 3. Network Isolation
- All MCP communication within Docker network
- No direct external MCP server exposure
- API rate limiting and quotas

## Benefits of This Approach

### 1. **Unified Interface**
- Single Waygate MCP endpoint for all operations
- Consistent authentication and logging
- Centralized monitoring and metrics

### 2. **Production-Ready Components**
- Leverage battle-tested MCP servers
- Official Google, Anthropic, Docker implementations
- Community-maintained servers with proven track records

### 3. **Scalable Architecture**
- Plugin-based system for easy extension
- Hot-reloading capabilities
- Independent MCP server lifecycle management

### 4. **Enhanced Capabilities**
- Firebase → DiagnosticPro platform management
- BigQuery → Analytics on 266 production tables
- GitHub → Repository and code management
- n8n → Workflow automation (525+ nodes)
- Docker Hub → Container management
- Slack → Bob's Brain integration

## Testing Strategy

### 1. **Unit Tests**
- Individual MCP plugin functionality
- Credential management operations
- Error handling and recovery

### 2. **Integration Tests**
- End-to-end MCP server communication
- Authentication flow validation
- Tool execution across all servers

### 3. **Performance Tests**
- Concurrent MCP server operations
- Memory and CPU usage monitoring
- Response time benchmarks

## Deployment Considerations

### 1. **Environment Setup**
```bash
# Required environment variables
export DATABASE_URL="libsql://waygate-mcp.turso.io?authToken=..."
export FIREBASE_PROJECT_ID="diagnostic-pro-start-up"
export GOOGLE_CLOUD_PROJECT="diagnostic-pro-start-up"
export GITHUB_TOKEN="ghp_..."
export N8N_API_URL="https://your-n8n-instance.com"
export SLACK_BOT_TOKEN="xoxb-..."
export DOCKER_HUB_TOKEN="dckr_pat_..."
```

### 2. **Database Migration**
```bash
# Initialize MCP server tables
cd waygate-mcp
./waygate.sh migrate-mcp-schema
```

### 3. **Plugin Configuration**
```bash
# Configure MCP servers
./waygate.sh configure-mcp-servers
```

## Next Steps

1. **Implement Framework Foundation** (Phase 1)
   - Create MCP bridge plugin architecture
   - Implement plugin loader
   - Enhance database schema

2. **Firebase Integration** (Proof of Concept)
   - Implement Firebase MCP plugin
   - Test with DiagnosticPro platform
   - Validate integration approach

3. **Sequential Integration** (Phases 2-3)
   - BigQuery → GitHub → n8n → Docker Hub → Slack
   - Testing and validation at each stage
   - Performance optimization

This design provides a comprehensive roadmap for integrating all 6 production-ready MCP servers into Waygate MCP, creating a unified AI automation platform that leverages the best available MCP implementations while maintaining security and scalability.