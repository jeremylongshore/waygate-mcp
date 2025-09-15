# Waygate MCP - Foundational MCP Server

🔥 **Tech bro approved**: Security-hardened MCP server with **Turso edge database**

## Features

✅ **Turso Database**: SQLite at the edge, 1B reads free
✅ **Security Hardened**: Read-only containers, non-root user
✅ **Enterprise Ready**: Comprehensive audit trails & metrics
✅ **Plug & Play**: Clone from GitHub and deploy instantly
✅ **Scalable**: Edge replicas globally for speed

## Quick Start

### 1. Setup Your Database (2 minutes)
```bash
# Install Turso CLI
curl -sSfL https://get.tur.so/install.sh | bash

# Create your database
turso db create waygate-mcp

# Get auth token
turso db tokens create waygate-mcp
# Copy the libsql://... URL with token
```

### 2. Deploy Waygate MCP
```bash
git clone https://github.com/jeremylongshore/waygate-mcp.git
cd waygate-mcp

# Set your database URL
export DATABASE_URL="libsql://waygate-mcp-[your-username].turso.io?authToken=your-token"

# Deploy (tech bro style)
./quickstart-turso.sh
```

### 3. Verify
```bash
# Check health
curl http://localhost:8000/health

# View your data in Turso dashboard
turso db shell waygate-mcp
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

## Why Turso?

🌍 **Global Edge Network**: Your database runs close to users worldwide
🚀 **Blazing Fast**: SQLite performance with cloud scalability
💰 **Free Tier**: 1 billion row reads, 9GB storage
🔧 **Developer Friendly**: SQLite syntax everyone knows
📊 **Built for Scale**: Used by production apps globally

## Documentation

- [Getting Started](documentation/GETTING_STARTED.md)
- [Database Schema](documentation/database-schema.md)
- [Container Security](documentation/CONTAINER_SECURITY.md)
- [Development Tasks](documentation/ai-dev-tasks/)

## Tech Stack

- **Database**: Turso (SQLite at the edge)
- **Security**: Read-only containers, non-root user
- **Protocol**: MCP (Model Context Protocol)
- **Language**: Python 3.12 + FastAPI
- **Deployment**: Docker + security hardening

---

*Created by Intent Solutions Inc - Building foundational AI infrastructure*