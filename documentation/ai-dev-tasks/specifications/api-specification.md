# API Specification: Waygate MCP

**Version:** 2.0.0
**Format:** OpenAPI 3.0
**Last Updated:** 2025-01-14
**Base URL:** http://localhost:8000

## 1. Overview

### 1.1 API Information
- **Title:** Waygate MCP API
- **Description:** Enterprise-grade Model Context Protocol Server
- **Version:** 2.0.0
- **Contact:** Jeremy Longshore
- **License:** MIT

### 1.2 Servers
| Environment | URL | Description |
|-------------|-----|-------------|
| Development | http://localhost:8000 | Local development |
| Staging | http://staging.waygate.local:8000 | Staging environment |
| Production | https://waygate.production.com | Production environment |

### 1.3 Authentication
- **Type:** API Key
- **Header Name:** X-API-Key
- **Format:** Bearer token (32-character alphanumeric)

## 2. Endpoints

### 2.1 Core Endpoints

#### GET /
**Description:** Service information and status

**Response:**
```json
{
  "service": "Waygate MCP",
  "version": "2.0.0",
  "status": "operational",
  "mode": "local_vm",
  "description": "Enterprise-grade MCP Server Framework",
  "documentation": "/docs"
}
```

**Status Codes:**
- `200 OK` - Service is operational

---

#### GET /health
**Description:** Health check endpoint for monitoring

**Response:**
```json
{
  "status": "healthy",
  "checks": {
    "database": "ok",
    "cache": "ok",
    "filesystem": "ok",
    "plugins": "ok"
  },
  "version": "2.0.0",
  "uptime_seconds": 3600,
  "timestamp": "2025-01-14T10:00:00Z"
}
```

**Status Codes:**
- `200 OK` - All health checks passing
- `503 Service Unavailable` - One or more checks failing

---

#### GET /ready
**Description:** Readiness probe for deployment

**Response:**
```json
{
  "ready": true
}
```

**Status Codes:**
- `200 OK` - Service is ready
- `503 Service Unavailable` - Service not ready

---

#### GET /metrics
**Description:** Prometheus-compatible metrics endpoint

**Response:** (text/plain)
```
# HELP waygate_requests_total Total number of requests
# TYPE waygate_requests_total counter
waygate_requests_total{method="GET",endpoint="/health",status="200"} 42

# HELP waygate_response_time_seconds Response time in seconds
# TYPE waygate_response_time_seconds histogram
waygate_response_time_seconds_bucket{le="0.1"} 100
waygate_response_time_seconds_count 150
waygate_response_time_seconds_sum 12.5
```

**Status Codes:**
- `200 OK` - Metrics returned

### 2.2 MCP Endpoints

#### POST /mcp/execute
**Description:** Execute an MCP command

**Request Headers:**
- `X-API-Key` (required): API authentication key
- `Content-Type`: application/json

**Request Body:**
```json
{
  "action": "process_data",
  "params": {
    "input": "sample data",
    "format": "json",
    "options": {
      "validate": true,
      "transform": false
    }
  },
  "context": {
    "user_id": "user123",
    "session_id": "sess456"
  },
  "timeout": 30
}
```

**Response:**
```json
{
  "status": "success",
  "result": {
    "message": "Command executed successfully",
    "data": {...},
    "metadata": {...}
  },
  "error": null,
  "duration_ms": 145,
  "command_id": "cmd_1234567890",
  "timestamp": "2025-01-14T10:00:00Z"
}
```

**Status Codes:**
- `200 OK` - Command executed successfully
- `400 Bad Request` - Invalid command format
- `401 Unauthorized` - Invalid or missing API key
- `408 Request Timeout` - Command execution timeout
- `500 Internal Server Error` - Command execution failed

---

#### GET /mcp/status
**Description:** Get MCP engine status

**Response:**
```json
{
  "engine": "operational",
  "plugins_loaded": 5,
  "commands_available": [
    "test",
    "echo",
    "status",
    "process_data",
    "analyze"
  ],
  "protocol_version": "1.0",
  "capabilities": {
    "async": true,
    "batch": true,
    "streaming": false
  }
}
```

**Status Codes:**
- `200 OK` - Status retrieved

---

#### GET /mcp/commands
**Description:** List available MCP commands

**Response:**
```json
{
  "commands": [
    {
      "name": "test",
      "description": "Test command for validation",
      "parameters": {
        "message": {
          "type": "string",
          "required": false,
          "description": "Test message"
        }
      }
    },
    {
      "name": "process_data",
      "description": "Process input data",
      "parameters": {
        "input": {
          "type": "string",
          "required": true,
          "description": "Input data to process"
        },
        "format": {
          "type": "string",
          "required": false,
          "enum": ["json", "xml", "csv"],
          "default": "json"
        }
      }
    }
  ],
  "total": 2
}
```

**Status Codes:**
- `200 OK` - Commands listed

### 2.3 Plugin Endpoints

#### GET /plugins
**Description:** List loaded plugins

**Response:**
```json
{
  "plugins": [
    {
      "name": "DataProcessor",
      "version": "1.0.0",
      "description": "Data processing plugin",
      "author": "Jeremy Longshore",
      "status": "active",
      "capabilities": ["process", "transform", "validate"],
      "config": {
        "max_size": 10485760,
        "formats": ["json", "xml", "csv"]
      }
    }
  ],
  "total": 1
}
```

**Status Codes:**
- `200 OK` - Plugins listed

---

#### POST /plugins/reload
**Description:** Reload all plugins

**Request Headers:**
- `X-API-Key` (required): Admin API key

**Response:**
```json
{
  "status": "plugins_reloaded",
  "count": 5,
  "loaded": ["Plugin1", "Plugin2", "Plugin3", "Plugin4", "Plugin5"],
  "failed": [],
  "duration_ms": 250
}
```

**Status Codes:**
- `200 OK` - Plugins reloaded
- `401 Unauthorized` - Invalid API key
- `500 Internal Server Error` - Reload failed

---

#### GET /plugins/{plugin_name}
**Description:** Get specific plugin information

**Path Parameters:**
- `plugin_name` (string): Name of the plugin

**Response:**
```json
{
  "name": "DataProcessor",
  "version": "1.0.0",
  "description": "Data processing plugin",
  "author": "Jeremy Longshore",
  "status": "active",
  "capabilities": ["process", "transform", "validate"],
  "config": {...},
  "statistics": {
    "calls_total": 1543,
    "errors_total": 2,
    "avg_duration_ms": 45
  }
}
```

**Status Codes:**
- `200 OK` - Plugin found
- `404 Not Found` - Plugin not found

### 2.4 Diagnostic Endpoints

#### GET /diagnostics/connection
**Description:** Run connection diagnostics

**Response:**
```json
{
  "server": "running",
  "port": 8000,
  "connections": {
    "active": 5,
    "total": 150,
    "max": 1000
  },
  "network": {
    "interfaces": ["lo", "eth0"],
    "listening_on": "0.0.0.0:8000"
  },
  "timestamp": "2025-01-14T10:00:00Z"
}
```

**Status Codes:**
- `200 OK` - Diagnostics completed

---

#### GET /diagnostics/performance
**Description:** Run performance diagnostics

**Response:**
```json
{
  "cpu_percent": 15.5,
  "memory": {
    "rss_mb": 125.4,
    "vms_mb": 256.8,
    "percent": 3.2
  },
  "threads": 8,
  "open_files": 42,
  "response_times": {
    "p50_ms": 45,
    "p95_ms": 120,
    "p99_ms": 250
  },
  "timestamp": "2025-01-14T10:00:00Z"
}
```

**Status Codes:**
- `200 OK` - Performance data retrieved

---

#### GET /diagnostics/errors
**Description:** Get recent errors

**Query Parameters:**
- `limit` (integer, default=10): Number of errors to return
- `since` (string, ISO8601): Errors since this timestamp

**Response:**
```json
{
  "errors": [
    {
      "timestamp": "2025-01-14T09:55:00Z",
      "level": "ERROR",
      "message": "Database connection timeout",
      "code": "DB_TIMEOUT",
      "context": {
        "query": "SELECT * FROM plugins",
        "duration_ms": 5000
      }
    }
  ],
  "total": 1
}
```

**Status Codes:**
- `200 OK` - Errors retrieved

## 3. Models

### 3.1 MCPCommand
```json
{
  "type": "object",
  "required": ["action"],
  "properties": {
    "action": {
      "type": "string",
      "description": "Command action to execute"
    },
    "params": {
      "type": "object",
      "description": "Command parameters",
      "additionalProperties": true
    },
    "context": {
      "type": "object",
      "description": "Execution context",
      "additionalProperties": true
    },
    "timeout": {
      "type": "integer",
      "description": "Timeout in seconds",
      "default": 30,
      "minimum": 1,
      "maximum": 300
    }
  }
}
```

### 3.2 MCPResponse
```json
{
  "type": "object",
  "required": ["status", "duration_ms", "command_id", "timestamp"],
  "properties": {
    "status": {
      "type": "string",
      "enum": ["success", "failed", "timeout"],
      "description": "Command execution status"
    },
    "result": {
      "description": "Command result (any type)"
    },
    "error": {
      "type": "string",
      "description": "Error message if failed"
    },
    "duration_ms": {
      "type": "integer",
      "description": "Execution duration in milliseconds"
    },
    "command_id": {
      "type": "string",
      "description": "Unique command identifier"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "Response timestamp"
    }
  }
}
```

### 3.3 Error Response
```json
{
  "type": "object",
  "required": ["error"],
  "properties": {
    "error": {
      "type": "object",
      "properties": {
        "code": {
          "type": "string",
          "description": "Error code"
        },
        "message": {
          "type": "string",
          "description": "Human-readable error message"
        },
        "details": {
          "type": "object",
          "description": "Additional error details"
        },
        "timestamp": {
          "type": "string",
          "format": "date-time"
        },
        "request_id": {
          "type": "string",
          "description": "Request tracking ID"
        }
      }
    }
  }
}
```

## 4. Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| INVALID_REQUEST | 400 | Request format is invalid |
| MISSING_PARAMETER | 400 | Required parameter missing |
| UNAUTHORIZED | 401 | Authentication failed |
| FORBIDDEN | 403 | Access denied |
| NOT_FOUND | 404 | Resource not found |
| METHOD_NOT_ALLOWED | 405 | HTTP method not allowed |
| TIMEOUT | 408 | Request timeout |
| RATE_LIMITED | 429 | Too many requests |
| INTERNAL_ERROR | 500 | Internal server error |
| SERVICE_UNAVAILABLE | 503 | Service temporarily unavailable |

## 5. Rate Limiting

### 5.1 Default Limits
| Endpoint | Rate Limit | Window |
|----------|------------|--------|
| /mcp/execute | 100 requests | 1 minute |
| /health | 1000 requests | 1 minute |
| /metrics | 100 requests | 1 minute |
| All others | 500 requests | 1 minute |

### 5.2 Rate Limit Headers
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1673784000
```

## 6. Pagination

For endpoints returning lists:

**Query Parameters:**
- `page` (integer, default=1): Page number
- `limit` (integer, default=10, max=100): Items per page

**Response Headers:**
```
X-Total-Count: 150
X-Page-Count: 15
Link: <http://localhost:8000/plugins?page=2>; rel="next"
```

## 7. Versioning

API versioning through:
1. URL path: `/v2/endpoint` (future)
2. Header: `Accept: application/vnd.waygate.v2+json`
3. Query parameter: `?version=2` (deprecated)

## 8. Security

### 8.1 HTTPS
Production environments must use HTTPS with valid SSL certificates.

### 8.2 CORS
```
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, X-API-Key
```

### 8.3 Security Headers
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'
```

## 9. Examples

### 9.1 cURL Examples

#### Health Check
```bash
curl -X GET http://localhost:8000/health
```

#### Execute Command
```bash
curl -X POST http://localhost:8000/mcp/execute \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "action": "test",
    "params": {"message": "Hello, Waygate!"}
  }'
```

#### Get Metrics
```bash
curl -X GET http://localhost:8000/metrics
```

### 9.2 Python Example

```python
import requests

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "your-api-key-here"

# Health check
response = requests.get(f"{BASE_URL}/health")
print(response.json())

# Execute command
headers = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

command = {
    "action": "process_data",
    "params": {
        "input": "sample data",
        "format": "json"
    }
}

response = requests.post(
    f"{BASE_URL}/mcp/execute",
    json=command,
    headers=headers
)

result = response.json()
print(f"Status: {result['status']}")
print(f"Duration: {result['duration_ms']}ms")
```

### 9.3 JavaScript Example

```javascript
// Using fetch API
const BASE_URL = 'http://localhost:8000';
const API_KEY = 'your-api-key-here';

// Health check
fetch(`${BASE_URL}/health`)
  .then(response => response.json())
  .then(data => console.log(data));

// Execute command
const command = {
  action: 'process_data',
  params: {
    input: 'sample data',
    format: 'json'
  }
};

fetch(`${BASE_URL}/mcp/execute`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY
  },
  body: JSON.stringify(command)
})
  .then(response => response.json())
  .then(result => {
    console.log(`Status: ${result.status}`);
    console.log(`Duration: ${result.duration_ms}ms`);
  });
```

## 10. WebSocket Support (Future)

### 10.1 Connection
```
ws://localhost:8000/ws
```

### 10.2 Message Format
```json
{
  "type": "command",
  "id": "msg_123",
  "payload": {
    "action": "subscribe",
    "channel": "events"
  }
}
```

## 11. Deprecation Policy

- Deprecated features marked with `Deprecated` header
- Minimum 6 months notice before removal
- Migration guide provided for breaking changes

---

**Document Status:** Complete
**OpenAPI File:** `openapi.yaml` (generated from code)
**Postman Collection:** Available on request