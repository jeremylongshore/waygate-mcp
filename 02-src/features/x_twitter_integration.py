#!/usr/bin/env python3
"""
X/Twitter API Integration for Waygate MCP Server
Provides secure X/Twitter posting functionality with proper OAuth handling
"""

import os
import json
import asyncio
import logging
import aiohttp
from typing import Dict, Any, Optional, List
from datetime import datetime
from .exceptions import MCPToolError

logger = logging.getLogger("waygate_mcp.x_twitter")

class XTwitterAPI:
    """
    X/Twitter API integration with OAuth 2.0 Bearer Token support
    NOTE: Consider migrating to OAuth 1.0a for permanent authentication
    """

    def __init__(self):
        self.base_url = "https://api.x.com/2"
        self.bearer_token = self._get_bearer_token()
        self.oauth1a_available = self._check_oauth1a_availability()

    def _get_bearer_token(self) -> Optional[str]:
        """Get Bearer token from environment variables"""
        # Try different environment variable names for Bearer token
        token_vars = [
            "X_BEARER_TOKEN",
            "TWITTER_BEARER_TOKEN",
            "X_API_BEARER_TOKEN",
            "TWITTER_API_BEARER_TOKEN"
        ]

        for var in token_vars:
            token = os.getenv(var)
            if token:
                logger.info(f"Found Bearer token in {var}")
                return token

        # Check if we have an OAuth 2.0 access token that needs conversion
        oauth_token = os.getenv("X_OAUTH2_ACCESS_TOKEN")
        if oauth_token:
            logger.warning("Found OAuth 2.0 access token, but Bearer token is preferred for app-only auth")
            # For now, try to use it as-is (this might work if it's actually a Bearer token)
            return oauth_token

        logger.warning("No X/Twitter Bearer token found in environment variables")
        logger.info("💡 Consider using OAuth 1.0a for permanent authentication (see X_OAUTH1A_SETUP.md)")
        return None

    def _check_oauth1a_availability(self) -> bool:
        """Check if OAuth 1.0a credentials are available as fallback"""
        try:
            from .x_oauth1a_auth import validate_oauth1a_credentials
            result = validate_oauth1a_credentials()
            if result["success"]:
                logger.info("✅ OAuth 1.0a credentials available as fallback")
                return True
            else:
                logger.debug("OAuth 1.0a credentials not available")
                return False
        except ImportError:
            logger.debug("OAuth 1.0a module not available")
            return False
        except Exception as e:
            logger.debug(f"OAuth 1.0a check failed: {e}")
            return False

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for X API requests"""
        if not self.bearer_token:
            error_msg = "No X/Twitter Bearer token configured"
            if self.oauth1a_available:
                error_msg += ". OAuth 1.0a available - consider using oauth1a tools instead"
            raise MCPToolError(error_msg)

        return {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json"
        }

    async def verify_credentials(self) -> Dict[str, Any]:
        """Verify API credentials by getting user info"""
        try:
            headers = self._get_auth_headers()

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/users/me",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "success": True,
                            "user": data.get("data", {}),
                            "message": "X/Twitter credentials verified successfully"
                        }
                    else:
                        error_data = await response.text()
                        message = f"Credential verification failed with status {response.status}"
                        if self.oauth1a_available and response.status == 401:
                            message += ". OAuth 1.0a available - consider using verify_x_oauth1a_credentials tool instead"

                        return {
                            "success": False,
                            "status_code": response.status,
                            "error": error_data,
                            "message": message,
                            "oauth1a_available": self.oauth1a_available
                        }

        except Exception as e:
            logger.error(f"Credential verification failed: {str(e)}")
            message = "Failed to verify X/Twitter credentials"
            if self.oauth1a_available and "Bearer token" in str(e):
                message += ". OAuth 1.0a available - consider using verify_x_oauth1a_credentials tool instead"

            return {
                "success": False,
                "error": str(e),
                "message": message,
                "oauth1a_available": self.oauth1a_available
            }

    async def post_tweet(self, text: str, **kwargs) -> Dict[str, Any]:
        """Post a tweet to X/Twitter"""
        try:
            if not text or len(text.strip()) == 0:
                raise MCPToolError("Tweet text cannot be empty")

            if len(text) > 280:
                raise MCPToolError(f"Tweet text too long: {len(text)} characters (max 280)")

            headers = self._get_auth_headers()

            # Prepare tweet data
            tweet_data = {"text": text}

            # Add optional parameters
            if kwargs.get("reply_to_id"):
                tweet_data["reply"] = {"in_reply_to_tweet_id": kwargs["reply_to_id"]}

            if kwargs.get("poll"):
                tweet_data["poll"] = kwargs["poll"]

            if kwargs.get("media_ids"):
                tweet_data["media"] = {"media_ids": kwargs["media_ids"]}

            logger.info(f"Posting tweet: {text[:50]}..." if len(text) > 50 else f"Posting tweet: {text}")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/tweets",
                    headers=headers,
                    json=tweet_data
                ) as response:
                    response_text = await response.text()

                    if response.status == 201:
                        # Success - tweet posted
                        data = json.loads(response_text)
                        tweet_id = data.get("data", {}).get("id")
                        return {
                            "success": True,
                            "tweet_id": tweet_id,
                            "text": text,
                            "url": f"https://x.com/i/status/{tweet_id}" if tweet_id else None,
                            "data": data,
                            "message": "Tweet posted successfully"
                        }
                    else:
                        # Error response
                        try:
                            error_data = json.loads(response_text)
                        except:
                            error_data = {"detail": response_text}

                        error_message = self._parse_error_message(response.status, error_data)

                        return {
                            "success": False,
                            "status_code": response.status,
                            "error": error_data,
                            "message": error_message,
                            "text": text
                        }

        except MCPToolError:
            raise
        except Exception as e:
            logger.error(f"Tweet posting failed: {str(e)}")
            raise MCPToolError(f"Failed to post tweet: {str(e)}")

    def _parse_error_message(self, status_code: int, error_data: Dict[str, Any]) -> str:
        """Parse X API error response into human-readable message"""
        if status_code == 401:
            return "Authentication failed - check Bearer token validity"
        elif status_code == 403:
            detail = error_data.get("detail", "")
            if "duplicate" in detail.lower():
                return "Tweet appears to be a duplicate"
            elif "suspended" in detail.lower():
                return "Account suspended"
            else:
                return f"Forbidden - {detail}"
        elif status_code == 429:
            return "Rate limit exceeded - too many requests"
        elif status_code == 400:
            errors = error_data.get("errors", [])
            if errors:
                return f"Bad request - {errors[0].get('message', 'Invalid parameters')}"
            return "Bad request - invalid parameters"
        else:
            return f"API error {status_code}: {error_data.get('detail', 'Unknown error')}"

    async def get_user_info(self, username: Optional[str] = None) -> Dict[str, Any]:
        """Get user information"""
        try:
            headers = self._get_auth_headers()

            if username:
                url = f"{self.base_url}/users/by/username/{username}"
            else:
                url = f"{self.base_url}/users/me"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "success": True,
                            "user": data.get("data", {}),
                            "message": "User info retrieved successfully"
                        }
                    else:
                        error_data = await response.text()
                        return {
                            "success": False,
                            "status_code": response.status,
                            "error": error_data,
                            "message": f"Failed to get user info: {response.status}"
                        }

        except Exception as e:
            logger.error(f"Get user info failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to retrieve user information"
            }

# Global X/Twitter API instance
x_api = XTwitterAPI()

async def post_tweet_tool(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """MCP tool for posting tweets"""
    text = parameters.get("text")
    if not text:
        raise MCPToolError("Text parameter is required for posting tweets")

    # Optional parameters
    reply_to_id = parameters.get("reply_to_id")
    poll = parameters.get("poll")
    media_ids = parameters.get("media_ids")

    result = await x_api.post_tweet(
        text=text,
        reply_to_id=reply_to_id,
        poll=poll,
        media_ids=media_ids
    )

    return result

async def verify_x_credentials_tool(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """MCP tool for verifying X/Twitter credentials"""
    result = await x_api.verify_credentials()
    return result

async def get_x_user_info_tool(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """MCP tool for getting X/Twitter user information"""
    username = parameters.get("username")
    result = await x_api.get_user_info(username)
    return result

# Export tools for registration
X_TWITTER_TOOLS = {
    "post_tweet": post_tweet_tool,
    "verify_x_credentials": verify_x_credentials_tool,
    "get_x_user_info": get_x_user_info_tool
}

def get_x_twitter_tools() -> List[Dict[str, Any]]:
    """Get X/Twitter tool definitions for registration"""
    tools = [
        {
            "name": "post_tweet",
            "description": "Post a tweet to X/Twitter using OAuth 2.0 Bearer token (expires every 2 hours)",
            "parameters": {
                "text": {"type": "string", "required": True, "description": "Tweet content (max 280 chars)"},
                "reply_to_id": {"type": "string", "required": False, "description": "Tweet ID to reply to"},
                "poll": {"type": "object", "required": False, "description": "Poll options"},
                "media_ids": {"type": "array", "required": False, "description": "Media attachment IDs"}
            },
            "notes": "For permanent authentication, use post_tweet_oauth1a instead"
        },
        {
            "name": "verify_x_credentials",
            "description": "Verify X/Twitter OAuth 2.0 Bearer token credentials are working",
            "parameters": {},
            "notes": "For permanent authentication, use verify_x_oauth1a_credentials instead"
        },
        {
            "name": "get_x_user_info",
            "description": "Get X/Twitter user information using OAuth 2.0 Bearer token",
            "parameters": {
                "username": {"type": "string", "required": False, "description": "Username (omit for own info)"}
            },
            "notes": "For permanent authentication, use get_x_user_info_oauth1a instead"
        }
    ]

    # Add OAuth 1.0a availability note if available
    try:
        from .x_oauth1a_auth import validate_oauth1a_credentials
        result = validate_oauth1a_credentials()
        if result["success"]:
            for tool in tools:
                tool["oauth1a_alternative"] = f"{tool['name']}_oauth1a"
    except:
        pass

    return tools