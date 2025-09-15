# 🚀 Getting Started with Waygate MCP

Welcome! This guide will help you get Waygate MCP running in **under 5 minutes**, even if you're not technical.

## 📋 What is Waygate MCP?

Waygate MCP is a **foundation framework** for building AI tools and integrations. Think of it as a "starter kit" that you can customize for your needs.

## 🎯 Quick Start (One Command!)

Open your terminal and run:

```bash
cd ~/waygate-mcp && ./quickstart.sh
```

That's it! Your MCP server is now running at http://localhost:8000 🎉

## 🛠️ What Can I Build With This?

### For Non-Technical Users
- **Personal Assistant**: Note taking, reminders, to-do lists
- **Data Manager**: Store and retrieve information
- **Automation Hub**: Connect to GitHub, APIs, databases

### For Developers
- **Custom MCP Tools**: Build your own AI integrations
- **Plugin System**: Drop in new features easily
- **API Gateway**: Secure, containerized microservices

## 📦 Pre-Built Examples Included

We've included working examples you can use right away:

### 1. **Note Taking System**
```python
# Save notes with tags
await save_note("Meeting Notes", "Discussed Q1 goals", ["work", "important"])
```

### 2. **To-Do List Manager**
```python
# Add tasks with priorities
await add_todo("Review pull requests", "high")
```

### 3. **GitHub Integration**
```python
# Create repos, issues, and READMEs
await create_github_repo("my-awesome-project", "This project is amazing!")
```

### 4. **Simple Calculator**
```python
# Do calculations
await calculate("125 * 4")
```

### 5. **Information Lookup**
```python
# Query your knowledge base
await lookup_info("office wifi password")
```

## 🔌 How to Add Your Own Tools

### Method 1: Copy & Modify (Easiest)

1. Open `src/example_tools.py`
2. Find a tool similar to what you want
3. Copy it and change the name
4. Modify the logic
5. Restart the server

### Method 2: Create a Plugin

1. Create a new file in `src/plugins/`
2. Copy this template:

```python
from plugins.base_plugin import BasePlugin

class MyPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.name = "My Cool Plugin"
        self.description = "Does cool stuff"

    async def get_tools(self):
        return [{
            "name": "my_tool",
            "description": "What it does"
        }]

    async def execute(self, tool_name, parameters):
        # Your code here
        return {"success": True, "result": "It worked!"}
```

3. Save and restart - it auto-loads!

## 🔒 Security Features

Your Waygate MCP runs in a **secure Docker container** with:
- ✅ Isolated from your system
- ✅ Non-root user
- ✅ Read-only filesystem
- ✅ Resource limits
- ✅ Network isolation

## 📝 Configuration

Edit `.env` file to customize:

```bash
# Change the port
WAYGATE_PORT=8000

# Set API key (for security)
WAYGATE_API_KEY=your-secret-key

# Enable debug mode
WAYGATE_DEBUG=true
```

## 🚦 Common Commands

```bash
# Start the server
docker-compose up -d

# Stop the server
docker-compose down

# View logs
docker-compose logs -f

# Restart after changes
docker-compose restart

# Check if it's running
curl http://localhost:8000/health
```

## 🎨 Customization Ideas

### For Personal Use
- Add your calendar integration
- Connect to your smart home
- Create personal automation workflows
- Build a knowledge base

### For Teams
- Shared note system
- Team task manager
- Documentation generator
- Code review assistant

### For Business
- Customer support bot
- Data analysis tools
- Report generator
- API integrations

## 📚 Example Use Cases

### Use Case 1: Personal Assistant
```python
# Morning routine
await save_note("Daily Plan", "1. Team standup\n2. Code review\n3. Lunch with client")
await add_todo("Prepare presentation", "high")
await set_reminder("Team meeting", "14:00")
```

### Use Case 2: Development Helper
```python
# Create a new project
await create_github_repo("new-feature", "Implementing user authentication")
await create_readme("New Feature", "User authentication system", "npm install", "John Doe")
await create_issue("new-feature", "Add login page", "Need to implement OAuth")
```

### Use Case 3: Data Management
```python
# Store and retrieve information
await save_note("API Keys", "Production: xxx-xxx\nStaging: yyy-yyy", ["sensitive", "credentials"])
await lookup_info("production api")
```

## 🤝 Contributing

Want to add features? It's easy!

1. **Fork** this repository
2. **Add** your feature to `src/plugins/`
3. **Test** it locally
4. **Submit** a pull request

## 📖 File Structure

```
waygate-mcp/
├── src/
│   ├── waygate_mcp.py      # Main server (don't modify unless needed)
│   ├── example_tools.py    # Example tools (copy these!)
│   └── plugins/            # Drop your plugins here
│       ├── github_plugin.py
│       └── your_plugin.py  # Your custom plugins
├── .env                    # Your configuration
├── docker-compose.yml      # Container settings
└── quickstart.sh          # One-click setup
```

## ❓ FAQ

**Q: Do I need to know Docker?**
A: No! Just run `./quickstart.sh` and it handles everything.

**Q: Can I add my own tools without coding?**
A: Yes! Copy an example and modify the text/logic.

**Q: Is this secure?**
A: Yes! Runs in an isolated container with enterprise security.

**Q: Can I share my plugins?**
A: Absolutely! Create a PR or share in discussions.

**Q: Works on Windows/Mac/Linux?**
A: Yes! Anywhere Docker runs.

## 🆘 Need Help?

- **Examples**: Check `src/example_tools.py`
- **Plugins**: Look in `src/plugins/`
- **Issues**: Open a GitHub issue
- **Community**: Join our discussions

## 🎉 Next Steps

1. ✅ Run `./quickstart.sh`
2. ✅ Check examples in `src/example_tools.py`
3. ✅ Copy and modify a tool
4. ✅ Restart and test
5. ✅ Share what you built!

---

**Remember**: You don't need to understand everything to start. Just copy, modify, and experiment! 🚀

*Built with ❤️ for both beginners and experts*