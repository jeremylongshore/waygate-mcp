# MCP PROXY POLICY - MANDATORY FOR ALL PROJECTS

**Effective Date**: 2025-09-28
**Policy Level**: CRITICAL SECURITY REQUIREMENT
**Scope**: ALL Claude Code instances, ALL external network access

---

## 🚨 MANDATORY SECURITY POLICY

### **ALL EXTERNAL NETWORK ACCESS MUST ROUTE THROUGH WAYGATE MCP PROXY**

This is a **non-negotiable security requirement** for all projects and AI agents.

---

## 🛡️ WAYGATE MCP PROXY REQUIREMENTS

### **1. Proxy Configuration**
```bash
# Waygate MCP Proxy Endpoints
WAYGATE_PROXY_URL=http://localhost:8000
WAYGATE_PROXY_API=http://localhost:8000/mcp

# Environment Variables Required
export HTTP_PROXY=http://localhost:8080
export HTTPS_PROXY=http://localhost:8080
export WAYGATE_API_KEY=[your-api-key]
```

### **2. Prohibited Direct Access**
❌ **NEVER access external URLs directly**
❌ **NEVER bypass the Waygate proxy**
❌ **NEVER use direct HTTP/HTTPS calls to external services**

### **3. Required Proxy Routing**
✅ **ALL web scraping through Waygate**
✅ **ALL API calls through Waygate**
✅ **ALL external database connections through Waygate**
✅ **ALL file downloads through Waygate**
✅ **ALL RSS feeds through Waygate**

---

## 🔧 IMPLEMENTATION REQUIREMENTS

### **For Python Projects**
```python
# REQUIRED: Use Waygate proxy for all requests
import requests

# Configure session with Waygate proxy
session = requests.Session()
session.proxies = {
    'http': 'http://localhost:8080',
    'https': 'http://localhost:8080'
}

# Add Waygate authentication
session.headers.update({
    'X-Waygate-API-Key': os.environ['WAYGATE_API_KEY']
})

# ALL external requests MUST use this session
response = session.get('https://external-api.com/data')
```

### **For Node.js Projects**
```javascript
// REQUIRED: Configure proxy for all external requests
const axios = require('axios');

const waygateClient = axios.create({
  proxy: {
    host: 'localhost',
    port: 8080
  },
  headers: {
    'X-Waygate-API-Key': process.env.WAYGATE_API_KEY
  }
});

// ALL external requests MUST use waygateClient
const response = await waygateClient.get('https://external-api.com/data');
```

### **For Slash Commands**
```bash
# BEFORE (PROHIBITED):
curl https://api.external.com/data

# AFTER (REQUIRED):
curl -H "X-Waygate-API-Key: $WAYGATE_API_KEY" \
     --proxy http://localhost:8080 \
     https://api.external.com/data
```

---

## 📊 MONITORING & COMPLIANCE

### **Audit Requirements**
- ✅ ALL external requests logged in Waygate
- ✅ Security violations automatically detected
- ✅ Traffic analysis and anomaly detection
- ✅ Complete audit trail maintained

### **Compliance Verification**
```bash
# Check Waygate proxy status
curl http://localhost:8000/health

# View traffic logs
curl http://localhost:8000/metrics

# Monitor security violations
curl http://localhost:8000/mcp/audit
```

---

## 🚀 WAYGATE MCP REST API

### **Core Endpoints**
```bash
# Health Check
GET http://localhost:8000/health

# MCP Server Status
GET http://localhost:8000/mcp/status

# Available Tools
GET http://localhost:8000/mcp/tools

# Execute MCP Commands
POST http://localhost:8000/mcp/execute
{
  "server_name": "external-api",
  "tool_name": "fetch_data",
  "parameters": {"url": "https://api.example.com"}
}

# Proxy Statistics
GET http://localhost:8000/metrics

# Security Audit
GET http://localhost:8000/diagnostics/security
```

### **Overnight Operations API**
```bash
# Schedule Background Tasks
POST http://localhost:8000/tasks/schedule
{
  "task_type": "data_collection",
  "schedule": "0 2 * * *",
  "parameters": {"source": "external-api"}
}

# Monitor Background Tasks
GET http://localhost:8000/tasks/status

# Task History
GET http://localhost:8000/tasks/history
```

---

## 🎯 ENFORCEMENT

### **Automatic Detection**
Waygate MCP automatically detects and blocks:
- Direct external network connections
- Unauthorized API access
- Bypass attempts
- Security policy violations

### **Violation Response**
1. **Block request immediately**
2. **Log security violation**
3. **Alert system administrators**
4. **Generate incident report**

---

## 📋 PROJECT INTEGRATION CHECKLIST

For each project, verify:
- [ ] Waygate proxy configured in code
- [ ] Environment variables set
- [ ] Direct external access removed
- [ ] Tests updated for proxy usage
- [ ] Documentation updated with proxy requirements
- [ ] Security audit completed

---

## 🔧 AUTO-START CONFIGURATION

### **Waygate MCP Service**
```bash
# Install auto-start service
sudo ./scripts/install-systemd-service.sh

# Verify auto-start
systemctl status waygate-mcp.service

# Enable if not already enabled
sudo systemctl enable waygate-mcp.service
```

### **Boot Verification**
```bash
# Test after reboot
curl http://localhost:8000/health

# Check service startup
journalctl -u waygate-mcp.service
```

---

## ⚠️ CRITICAL WARNINGS

1. **NO EXCEPTIONS**: This policy applies to ALL external access
2. **NO BYPASS**: Direct external connections are security violations
3. **MANDATORY COMPLIANCE**: Non-compliance will trigger security alerts
4. **IMMEDIATE IMPLEMENTATION**: All existing code must be updated

---

**This policy ensures that all external network access is secure, monitored, and compliant with enterprise security standards.**

**Contact**: Waygate Security Team
**Emergency**: Check service status at http://localhost:8000/health