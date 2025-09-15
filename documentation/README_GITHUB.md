# 🌉 Waygate MCP

> **Foundational MCP Server Framework** - The successor to NEXUS MCP, built for extensibility and security

[![Version](https://img.shields.io/badge/version-2.0.0-blue)](https://github.com/yourusername/waygate-mcp)
[![Python](https://img.shields.io/badge/python-3.8%2B-brightgreen)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/docker-ready-099cec)](https://www.docker.com/)
[![License](https://img.shields.io/badge/license-MIT-purple)](LICENSE)

## 🚀 Overview

Waygate MCP is a **production-ready Model Context Protocol (MCP) server** that provides a solid foundation for building AI tools and integrations. It's designed to be:

- **🔒 Secure** - Container-first with enterprise-grade isolation
- **🧩 Extensible** - Simple plugin system for custom tools
- **📦 Portable** - Run locally, in Docker, or on any cloud
- **🎯 Simple** - Minimal dependencies, maximum clarity

### Why Waygate?

Unlike other MCP implementations, Waygate focuses on being a **foundational framework** that developers can build upon. It provides the scaffolding and best practices while letting you add your own tools and integrations.

## ⚡ Quick Start

### One-Line Install

```bash
git clone https://github.com/yourusername/waygate-mcp.git
cd waygate-mcp
./quickstart.sh
```

### Local Development

```bash
# Clone the repository
git clone https://github.com/yourusername/waygate-mcp.git
cd waygate-mcp

# Run locally with Python
./start_waygate.sh

# Or run with Docker
docker-compose up -d
```

### Claude Code Integration

Configure Claude Code to use Waygate MCP:

```bash
# Add to your Claude Code MCP settings
{
  "mcpServers": {
    "waygate": {
      "command": "/home/jeremy/waygate-mcp/waygate.sh"
    }
  }
}
```

## 📁 Project Structure

```
waygate-mcp/
├── waygate_mcp.py          # Core MCP server (stdio-based)
├── src/                    # Source code
│   ├── plugins/           # Drop your plugins here
│   └── example_tools.py   # Example implementations
├── waygate.sh             # Claude Code wrapper script
├── start_waygate.sh       # Local development runner
├── docker-compose.yml     # Container orchestration
├── Dockerfile             # Multi-stage secure build
└── docs/                  # Documentation
```

## 🔧 Configuration

Copy `.env.example` to `.env` and customize:

```bash
# Core settings
WAYGATE_MODE=development              # development|production
WAYGATE_LOG_LEVEL=INFO               # DEBUG|INFO|WARNING|ERROR
WAYGATE_PROJECTS_DIR=/home/jeremy/projects  # Your projects directory

# Security (CHANGE THESE!)
WAYGATE_SECRET_KEY=<your-secret-key>  # Generate: openssl rand -base64 32
WAYGATE_API_KEY=<your-api-key>        # Generate: uuidgen
```

## 📚 Core Features

### Resources

Access system information and project listings:

- `waygate://system` - System information
- `waygate://projects/list` - All projects
- `waygate://projects/active` - Active projects only
- `waygate://projects/archived` - Archived projects

### Tools

Built-in tools for project management:

- `waygate_echo` - Test tool for debugging
- `project_create` - Create new projects
- `project_archive` - Archive active projects
- `project_activate` - Reactivate archived projects

### Active/Archived Convention

Waygate follows a simple project organization pattern:

```
projects/
├── active/       # Currently working on
│   ├── project-a/
│   └── project-b/
└── archived/     # Completed or paused
    ├── project-x/
    └── project-y/
```

This keeps your workspace clean and makes it easy to focus on current work while preserving completed projects.

## 🧩 Extending Waygate

### Method 1: Add to example_tools.py

```python
# src/example_tools.py
async def my_custom_tool(self, param1: str) -> Dict[str, Any]:
    """Your custom tool logic"""
    return {"success": True, "result": "Your result"}
```

### Method 2: Create a Plugin

```python
# src/plugins/my_plugin.py
from plugins.base_plugin import BasePlugin

class MyPlugin(BasePlugin):
    async def get_tools(self):
        return [{
            "name": "my_tool",
            "description": "What it does"
        }]

    async def execute(self, tool_name, parameters):
        # Your logic here
        return {"success": True}
```

## 🐳 Docker Deployment

### Build and Run

```bash
# Build the image
docker build -t waygate-mcp:local .

# Run with docker-compose
docker-compose up -d

# Check logs
docker-compose logs -f waygate

# Stop
docker-compose down
```

### Security Features

- ✅ Non-root user (UID 1000)
- ✅ Read-only filesystem
- ✅ Dropped capabilities
- ✅ Resource limits
- ✅ Network isolation

## 🛠️ Development

### Prerequisites

- Python 3.8+
- Docker (optional)
- Git

### Setup Development Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/

# Run with debug logging
WAYGATE_LOG_LEVEL=DEBUG ./start_waygate.sh
```

### Testing

```bash
# Test stdio communication
echo '{"type": "ping"}' | python waygate_mcp.py

# Test resource access
echo '{"type": "resource", "uri": "waygate://system"}' | python waygate_mcp.py

# Test tool execution
echo '{"type": "tool", "name": "waygate_echo", "parameters": {"message": "Hello"}}' | python waygate_mcp.py
```

## 📖 Documentation

- [Getting Started](GETTING_STARTED.md) - Beginner's guide
- [Project Knowledge](docs/PROJECT_KNOWLEDGE.md) - System architecture
- [Container Security](docs/CONTAINER_SECURITY.md) - Security details
- [API Reference](docs/api-specification.md) - Complete API docs

## 🤝 Contributing

We welcome contributions! Here's how:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing`)
5. Open a Pull Request

### Development Guidelines

- Keep it simple and readable
- Add tests for new features
- Update documentation
- Follow PEP8 for Python code
- Use meaningful commit messages

## 📊 Roadmap

- [ ] Web UI for management
- [ ] More example plugins
- [ ] Database integration examples
- [ ] Authentication system
- [ ] Webhook support
- [ ] Cloud deployment guides

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/waygate-mcp/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/waygate-mcp/discussions)
- **Documentation**: [Wiki](https://github.com/yourusername/waygate-mcp/wiki)

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Credits

**Created by Jeremy Longshore**

With assistance from:
- OpenAI's ChatGPT (GPT-5)
- Anthropic's Claude

Special thanks to the MCP community for inspiration and feedback.

---

<div align="center">

**[Documentation](docs/)** • **[Issues](https://github.com/yourusername/waygate-mcp/issues)** • **[Discussions](https://github.com/yourusername/waygate-mcp/discussions)**

Made with ❤️ for the developer community

</div>