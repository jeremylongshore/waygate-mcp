# OAuth 2.0 to OAuth 1.0a Migration Guide
**Date:** 2025-09-28
**Waygate MCP Server - Authentication Migration**

---

## Overview

This guide helps you migrate from OAuth 2.0 Bearer tokens (which expire every 2 hours) to OAuth 1.0a authentication (which never expires) for X/Twitter API integration in the Waygate MCP system.

## Why Migrate?

| Issue | OAuth 2.0 Bearer | OAuth 1.0a Solution |
|-------|------------------|---------------------|
| **Token Expiration** | Every 2 hours | Never expires |
| **401 Unauthorized** | Frequent occurrence | Rare (only if revoked) |
| **Maintenance** | Regular token refresh | Set once, works forever |
| **Reliability** | Interrupts workflows | Continuous operation |
| **Production Use** | Requires automation | Fire and forget |

## Migration Steps

### Step 1: Verify Current OAuth 2.0 Status

Check if your current OAuth 2.0 setup is having issues:

```bash
# Test current OAuth 2.0 credentials
python test_x_api.py

# Check for 401 errors in logs
grep -i "401\|unauthorized" logs/waygate.log
```

Common OAuth 2.0 Bearer token issues:
- `401 Unauthorized` errors
- Expired token messages
- Failed credential verification
- Interrupted automation

### Step 2: Set Up OAuth 1.0a Credentials

Follow the detailed setup guide:

```bash
# Read the complete setup instructions
cat X_OAUTH1A_SETUP.md
```

**Quick Setup:**
1. Go to [developer.x.com](https://developer.x.com)
2. Navigate to your app → "Keys and Tokens"
3. Generate Access Token and Secret
4. Set environment variables:

```bash
export X_CONSUMER_KEY="your_consumer_key"
export X_CONSUMER_SECRET="your_consumer_secret"
export X_ACCESS_TOKEN="your_access_token"
export X_ACCESS_TOKEN_SECRET="your_access_token_secret"
```

### Step 3: Validate OAuth 1.0a Setup

Test your OAuth 1.0a credentials:

```bash
# Validate setup
python test_oauth1a_setup.py

# Test integration
python test_x_oauth1a_integration.py
```

Expected output:
```
✅ PASS Environment Variables: All required variables present
✅ PASS Credential Validation: OAuth 1.0a credentials validated successfully
✅ PASS API Verification: API credentials verified successfully
```

### Step 4: Update Your Code

#### Before (OAuth 2.0):
```python
# Using OAuth 2.0 tools (expire every 2 hours)
result = await execute_tool("post_tweet", {"text": "Hello World!"})
result = await execute_tool("verify_x_credentials", {})
result = await execute_tool("get_x_user_info", {"username": "x"})
```

#### After (OAuth 1.0a):
```python
# Using OAuth 1.0a tools (never expire)
result = await execute_tool("post_tweet_oauth1a", {"text": "Hello World!"})
result = await execute_tool("verify_x_oauth1a_credentials", {})
result = await execute_tool("get_x_user_info_oauth1a", {"username": "x"})
result = await execute_tool("search_tweets_oauth1a", {"query": "X API"})
```

### Step 5: Test Side-by-Side

Run both authentication methods to compare:

```python
# Test OAuth 2.0 (if still working)
oauth2_result = await execute_tool("verify_x_credentials", {})
print("OAuth 2.0:", oauth2_result)

# Test OAuth 1.0a
oauth1a_result = await execute_tool("verify_x_oauth1a_credentials", {})
print("OAuth 1.0a:", oauth1a_result)
```

### Step 6: Gradual Migration

1. **Keep both systems running** during migration
2. **Start with read-only operations** (user info, search)
3. **Test posting with OAuth 1.0a**
4. **Update automation scripts**
5. **Remove OAuth 2.0 when confident**

## Tool Mapping

| OAuth 2.0 Tool | OAuth 1.0a Equivalent | New Features |
|-----------------|----------------------|--------------|
| `post_tweet` | `post_tweet_oauth1a` | Same functionality |
| `verify_x_credentials` | `verify_x_oauth1a_credentials` | Same functionality |
| `get_x_user_info` | `get_x_user_info_oauth1a` | Same functionality |
| ❌ Not available | `search_tweets_oauth1a` | ✅ New! Search tweets |
| ❌ Not available | `validate_oauth1a_setup` | ✅ New! Setup validation |

## MCP HTTP Request Tool

The `http_request` tool now supports OAuth 1.0a:

```python
# Use OAuth 1.0a with http_request tool
result = await execute_tool("http_request", {
    "method": "GET",
    "url": "https://api.x.com/2/users/me",
    "use_oauth1a": True  # Enable OAuth 1.0a authentication
})
```

## Error Handling Improvements

### OAuth 2.0 Error Messages (Old):
```
❌ Authentication failed - check Bearer token validity
❌ No X/Twitter Bearer token configured
```

### OAuth 1.0a Error Messages (New):
```
✅ OAuth 1.0a credentials available - consider using oauth1a tools instead
✅ For permanent authentication, use verify_x_oauth1a_credentials instead
```

## Testing Scripts

### Complete Setup Validation:
```bash
# Comprehensive credential testing
python test_oauth1a_setup.py

# Expected: All tests pass
```

### Integration Testing:
```bash
# Test all OAuth 1.0a functionality
python test_x_oauth1a_integration.py

# Test live posting (optional)
python test_x_oauth1a_integration.py --post-tweet
```

### Legacy OAuth 2.0 Testing:
```bash
# Test current OAuth 2.0 setup
python test_x_api.py

# Check for expiration issues
python x_auth_solution.py
```

## Production Deployment

### Environment Variables

**For Development (.env file):**
```bash
# OAuth 1.0a credentials (permanent)
X_CONSUMER_KEY=your_consumer_key
X_CONSUMER_SECRET=your_consumer_secret
X_ACCESS_TOKEN=your_access_token
X_ACCESS_TOKEN_SECRET=your_access_token_secret

# OAuth 2.0 credentials (backup - optional)
X_BEARER_TOKEN=your_bearer_token
```

**For Production (Docker):**
```yaml
services:
  waygate:
    environment:
      # OAuth 1.0a (primary)
      - X_CONSUMER_KEY=${X_CONSUMER_KEY}
      - X_CONSUMER_SECRET=${X_CONSUMER_SECRET}
      - X_ACCESS_TOKEN=${X_ACCESS_TOKEN}
      - X_ACCESS_TOKEN_SECRET=${X_ACCESS_TOKEN_SECRET}
      # OAuth 2.0 (backup)
      - X_BEARER_TOKEN=${X_BEARER_TOKEN}
```

### Security Considerations

1. **Never commit credentials to git**
2. **Use secrets management in production**
3. **Rotate tokens if compromised**
4. **Monitor API usage in X Developer Portal**

```bash
# Secure file permissions
chmod 600 .env

# Check git status
git status  # Ensure .env is in .gitignore
```

## Troubleshooting

### Common Migration Issues

#### 1. "OAuth 1.0a module not available"
```bash
# Ensure files are in place
ls source/x_oauth1a_auth.py
ls source/x_twitter_oauth1a.py

# Restart application
python -m source.waygate_mcp --reload
```

#### 2. "Invalid signature" errors
```bash
# Check credentials format
echo $X_CONSUMER_KEY | wc -c    # Should be ~25 chars
echo $X_ACCESS_TOKEN | wc -c     # Should be ~50+ chars

# Verify no extra spaces
env | grep ^X_ | cat -A
```

#### 3. "App permissions" errors
- Check app permissions in X Developer Portal
- Ensure "Read and Write" permissions for posting
- Regenerate access tokens after permission changes

### Rollback Plan

If OAuth 1.0a has issues, you can temporarily rollback:

1. **Keep OAuth 2.0 credentials in environment**
2. **Use original OAuth 2.0 tools**
3. **Fix OAuth 1.0a setup**
4. **Re-migrate when ready**

## Benefits After Migration

### ✅ Reliability
- No more 2-hour token expiration
- Reduced 401 Unauthorized errors
- Continuous operation

### ✅ Maintenance
- Set up once, works forever
- No token refresh automation needed
- Simplified deployment

### ✅ Features
- All original functionality preserved
- New tweet search capability
- Better error messages and diagnostics

### ✅ Security
- Signature-based authentication
- More secure than Bearer tokens
- Per-request authentication

## Support

### If You Need Help

1. **Review logs for specific errors**
2. **Run validation scripts**
3. **Check X Developer Portal app settings**
4. **Verify environment variables**

### Useful Commands

```bash
# Check environment
env | grep -E "^(X_|TWITTER_)" | sort

# Test OAuth 1.0a directly
python -c "from source.x_oauth1a_auth import validate_oauth1a_credentials; print(validate_oauth1a_credentials())"

# View available tools
python -c "from source.mcp_tools import get_available_tools; [print(t['name']) for t in get_available_tools()]"
```

## Success Criteria

✅ **Migration Complete When:**
- OAuth 1.0a credentials validated
- All tests pass
- Applications using oauth1a tools
- No more 401 expiration errors
- Posting and reading working correctly

---

**Last Updated:** 2025-09-28
**Migration Status:** ✅ Ready for production use
**OAuth 1.0a Implementation:** Complete and tested