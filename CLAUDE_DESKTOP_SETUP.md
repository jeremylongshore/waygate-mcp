# 🖥️ CLAUDE DESKTOP INTEGRATION SETUP

**Connect Waygate MCP Server to Claude Desktop for powerful development tools**

---

## 📋 PREREQUISITES

- Claude Desktop installed
- Waygate MCP server functional (use `./scripts/dashboard.sh` to verify)
- Python virtual environment activated

---

## ⚡ QUICK SETUP

### 1. Start Waygate MCP Server

```bash
# Navigate to waygate-mcp directory
cd /home/jeremy/waygate-mcp

# Activate virtual environment
source venv/bin/activate

# Start server (choose development or production)
python -m source.waygate_mcp --port 8000 --env development
```

### 2. Configure Claude Desktop

**Location of config file:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

**Add this configuration:**

```json
{
  "mcpServers": {
    "waygate-mcp": {
      "command": "python",
      "args": [
        "-m",
        "source.waygate_mcp",
        "--port", "8000",
        "--env", "production"
      ],
      "cwd": "/home/jeremy/waygate-mcp",
      "env": {
        "WAYGATE_ENV": "production",
        "WAYGATE_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### 3. Restart Claude Desktop

Close and reopen Claude Desktop to load the new MCP server configuration.

---

## 🛠️ AVAILABLE MCP TOOLS

Once connected, you can use these tools in Claude Desktop:

### **📁 File Operations**
- `execute_command` - Run system commands safely
- `read_file` - Read file contents
- `write_file` - Write content to files
- `list_directory` - List directory contents
- `search_files` - Search files by name or content

### **🔍 Example Usage in Claude Desktop:**

```
"Use the execute_command tool to check the current directory"
"Read the README.md file using read_file"
"List all Python files in the current directory"
"Search for files containing 'MCP' in their content"
```

---

## 🔧 TROUBLESHOOTING

### Server Won't Start
```bash
# Check dependencies
source venv/bin/activate
pip install -r requirements.txt

# Check ports
netstat -tulpn | grep :8000

# Test basic startup
python -m source.waygate_mcp --help
```

### Claude Desktop Can't Connect
1. **Verify server is running:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Check config file syntax:**
   ```bash
   python -m json.tool ~/.config/Claude/claude_desktop_config.json
   ```

3. **Verify path in config:**
   ```bash
   cd /home/jeremy/waygate-mcp
   pwd  # Should match "cwd" in config
   ```

### Database Connection Issues
The server will fallback to local operation if Turso database is unavailable:

```bash
# Remove DATABASE_URL to use local SQLite
unset DATABASE_URL

# Or comment it out in .env file
# DATABASE_URL=libsql://your-turso-url
```

---

## 🔐 SECURITY CONSIDERATIONS

### For Production Use:

1. **Generate secure keys:**
   ```bash
   python -c "import secrets; print('WAYGATE_SECRET_KEY=' + secrets.token_hex(32))"
   python -c "import secrets; print('WAYGATE_API_KEY=' + secrets.token_hex(32))"
   ```

2. **Update .env file:**
   ```bash
   echo "WAYGATE_SECRET_KEY=your-generated-key" >> .env
   echo "WAYGATE_API_KEY=your-generated-key" >> .env
   ```

3. **Restrict file access:**
   ```bash
   chmod 600 .env
   chmod 755 /home/jeremy/waygate-mcp
   ```

---

## 📊 VERIFICATION COMMANDS

### Test Server Health
```bash
curl http://localhost:8000/health
curl http://localhost:8000/mcp/tools
```

### Expected Response:
```json
{
  "status": "healthy",
  "checks": {
    "database": "ok",
    "cache": "ok",
    "filesystem": "ok",
    "plugins": "ok"
  }
}
```

---

## 🚀 ADVANCED CONFIGURATION

### Custom Environment Variables

Add to the `env` section in claude_desktop_config.json:

```json
"env": {
  "WAYGATE_ENV": "production",
  "WAYGATE_LOG_LEVEL": "DEBUG",
  "WAYGATE_HOST": "127.0.0.1",
  "WAYGATE_PORT": "8000",
  "WAYGATE_CORS_ORIGINS": "[\"https://claude.ai\"]"
}
```

### Multiple MCP Servers

You can run multiple instances on different ports:

```json
{
  "mcpServers": {
    "waygate-dev": {
      "command": "python",
      "args": ["-m", "source.waygate_mcp", "--port", "8001", "--env", "development"],
      "cwd": "/home/jeremy/waygate-mcp"
    },
    "waygate-prod": {
      "command": "python",
      "args": ["-m", "source.waygate_mcp", "--port", "8002", "--env", "production"],
      "cwd": "/home/jeremy/waygate-mcp"
    }
  }
}
```

---

## 📈 MONITORING

### View Logs
```bash
# Server logs
tail -f /tmp/waygate_mcp.log

# Live server status
./scripts/dashboard.sh
```

### Performance Metrics
```bash
curl http://localhost:8000/metrics
curl http://localhost:8000/diagnostics/performance
```

---

## 🔄 UPDATES

### Update Server
```bash
cd /home/jeremy/waygate-mcp
git pull origin main
pip install -r requirements.txt
# Restart Claude Desktop
```

### Backup Configuration
```bash
cp ~/.config/Claude/claude_desktop_config.json \
   ~/.config/Claude/claude_desktop_config.json.backup
```

---

**✅ SUCCESS CRITERIA:**
- Server starts without errors
- Health endpoint returns 200 OK
- MCP tools are listed in /mcp/tools
- Claude Desktop shows waygate-mcp as connected
- Can execute commands through Claude Desktop

**🎯 USER:** waygateai | **PROJECT:** waygate-mcp | **STATUS:** Ready for Claude Desktop integration