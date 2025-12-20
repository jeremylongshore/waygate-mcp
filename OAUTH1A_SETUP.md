# OAuth 1.0a Setup for X/Twitter Integration

## Current Status ✅

The Waygate MCP server is **working correctly** with OAuth 2.0 fallback. The system successfully:
- Auto-detects X/Twitter API calls
- Routes requests through MCP proxy
- Falls back to OAuth 2.0 when OAuth 1.0a isn't available
- Returns proper error codes (401 when tokens expire)

## Problem: OAuth 2.0 Tokens Expire Every 2 Hours

Your current OAuth 2.0 token has expired, which is why you're getting 401 Unauthorized errors. This is the core issue with OAuth 2.0 for automated posting.

## Solution: OAuth 1.0a Tokens (Permanent)

OAuth 1.0a tokens **never expire** and are perfect for automated posting. Here's how to get them:

### Step 1: Generate OAuth 1.0a User Access Tokens

1. Go to [X Developer Portal](https://developer.twitter.com/en/portal/dashboard)
2. Navigate to your app's settings
3. Go to "Keys and tokens" tab
4. Under "Authentication Tokens" section
5. Click "Generate" for "Access Token and Secret"
6. **IMPORTANT**: Save these immediately - they're only shown once

### Step 2: Set Environment Variables

Add these to your shell profile (`.bashrc`, `.zshrc`, etc.):

```bash
# OAuth 1.0a Credentials (PERMANENT - NO EXPIRATION)
export X_ACCESS_TOKEN="your-access-token-here"
export X_ACCESS_TOKEN_SECRET="your-access-token-secret-here"

# You already have these (Consumer Key/Secret):
# export X_API_KEY="thpZd6tCyjgYJVTr0waBx2RolP"
# export X_API_SECRET="tAnB8BhULV3J4sfP2HC5..."
```

### Step 3: Restart MCP Server

```bash
# Kill current server
pkill -f waygate_mcp

# Restart with new credentials
cd /home/jeremy/waygate-mcp
source activate_venv.sh
python -m source.waygate_mcp --host 127.0.0.1 --port 8000 --env development
```

### Step 4: Test OAuth 1.0a

```bash
curl -X POST http://localhost:8000/mcp/execute \
  -H "Content-Type: application/json" \
  -d '{
    "action": "http_request",
    "params": {
      "url": "https://api.twitter.com/2/tweets",
      "method": "POST",
      "json": {
        "text": "🎉 OAuth 1.0a working! Permanent tokens, no more 2-hour expiration! #MCP #OAuth1a"
      }
    }
  }'
```

## How It Works Now

The `http_request` tool automatically:

1. **Detects X/Twitter API calls** (`api.twitter.com` in URL)
2. **Tries OAuth 1.0a first** (permanent tokens)
3. **Falls back to OAuth 2.0** if OAuth 1.0a unavailable
4. **Logs which authentication method is used**

## Current Available Credentials

```bash
✅ X_API_KEY (Consumer Key): thpZd6tCyjgYJVTr0waBx2RolP
✅ X_API_SECRET (Consumer Secret): tAnB8BhULV3J4sfP...
✅ X_OAUTH2_ACCESS_TOKEN: N0N3NmRfcUthdGNrOTJV... (EXPIRED)
❌ X_ACCESS_TOKEN: MISSING - Generate from Developer Portal
❌ X_ACCESS_TOKEN_SECRET: MISSING - Generate from Developer Portal
```

## Test Results

- ✅ MCP server running successfully
- ✅ Auto-detection working (`api.twitter.com` recognized)
- ✅ OAuth 2.0 fallback working (returns 401 when expired)
- ✅ API routing working correctly
- ⏳ OAuth 1.0a pending user access tokens

## Next Steps

1. **Generate OAuth 1.0a tokens** from X Developer Portal
2. **Set environment variables** as shown above
3. **Restart MCP server** to load new credentials
4. **Test posting** - should work permanently without re-authentication

## Slash Commands Ready

Once OAuth 1.0a is set up, the `/blog-both-x`, `/blog-jeremy-x`, and `/blog-startai-x` commands will automatically post to X/Twitter via the Waygate MCP proxy with **permanent authentication**.

---

**Status**: System working, just needs OAuth 1.0a tokens for permanent authentication
**Priority**: High - Solves the 2-hour token expiration problem permanently