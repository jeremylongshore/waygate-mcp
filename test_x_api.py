#!/usr/bin/env python3
"""
Direct test of X/Twitter API with proper Bearer token authentication
"""

import os
import asyncio
import aiohttp
import json

async def test_x_twitter_api():
    """Test X/Twitter API with the Bearer token"""

    # Get the Bearer token
    bearer_token = os.environ["X_BEARER_TOKEN"]

    # Test 1: Verify credentials (check if token is valid)
    print("=== Testing X/Twitter API Authentication ===")
    print(f"Using Bearer token: {bearer_token[:20]}...")

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }

    # Test credential verification
    print("\n1. Testing credential verification...")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                "https://api.x.com/2/users/me",
                headers=headers
            ) as response:
                print(f"Status: {response.status}")
                response_text = await response.text()
                print(f"Response: {response_text}")

                if response.status == 200:
                    print("✅ Credentials verified successfully!")
                    data = json.loads(response_text)
                    user_data = data.get("data", {})
                    print(f"   User: {user_data.get('username', 'N/A')} ({user_data.get('name', 'N/A')})")
                    return True
                else:
                    print("❌ Credential verification failed")
                    return False

        except Exception as e:
            print(f"❌ Error during verification: {e}")
            return False

async def test_tweet_posting():
    """Test posting a tweet"""
    bearer_token = os.environ["X_BEARER_TOKEN"]

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }

    # Test tweet posting
    print("\n2. Testing tweet posting...")
    tweet_data = {
        "text": f"Test tweet from Waygate MCP - {os.urandom(4).hex()}"
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                "https://api.x.com/2/tweets",
                headers=headers,
                json=tweet_data
            ) as response:
                print(f"Status: {response.status}")
                response_text = await response.text()
                print(f"Response: {response_text}")

                if response.status == 201:
                    print("✅ Tweet posted successfully!")
                    data = json.loads(response_text)
                    tweet_id = data.get("data", {}).get("id")
                    if tweet_id:
                        print(f"   Tweet URL: https://x.com/i/status/{tweet_id}")
                    return True
                else:
                    print("❌ Tweet posting failed")
                    return False

        except Exception as e:
            print(f"❌ Error during tweet posting: {e}")
            return False

def analyze_token_format():
    """Analyze the token format to understand the issue"""
    bearer_token = os.environ["X_BEARER_TOKEN"]

    print(f"\n=== Token Analysis ===")
    print(f"Token length: {len(bearer_token)}")
    print(f"Token format: {bearer_token}")
    print(f"Contains colon (:): {'Yes' if ':' in bearer_token else 'No'}")
    print(f"Contains 'at:': {'Yes' if 'at:' in bearer_token else 'No'}")

    # This looks like an OAuth 2.0 Access Token from Twitter's OAuth flow
    # Format: {access_token}:{expiry_timestamp}:{user_id}:{type}:{token_type}:{sequence}
    if ':' in bearer_token:
        parts = bearer_token.split(':')
        print(f"Token parts ({len(parts)}): {parts}")
        if len(parts) >= 2:
            print(f"   Likely access token: {parts[0]}")
            print(f"   Timestamp: {parts[1]}")

            # Check if timestamp is expired
            try:
                timestamp = int(parts[1])
                import time
                current_time = int(time.time())
                if timestamp < current_time:
                    print(f"   ⚠️  Token appears EXPIRED (timestamp: {timestamp}, current: {current_time})")
                else:
                    print(f"   ✅ Token appears valid (timestamp: {timestamp}, current: {current_time})")
            except:
                print(f"   ❓ Could not parse timestamp")

async def main():
    """Main test function"""
    print("Starting X/Twitter API diagnostic tests...")

    # Analyze token first
    analyze_token_format()

    # Test authentication
    auth_success = await test_x_twitter_api()

    if auth_success:
        # If auth works, try posting
        await test_tweet_posting()
    else:
        print("\n❌ Skipping tweet posting due to authentication failure")
        print("\n🔧 Troubleshooting suggestions:")
        print("   1. Check if the Bearer token is correct")
        print("   2. Verify the token hasn't expired")
        print("   3. Ensure the app has tweet write permissions")
        print("   4. Check if this is actually a Bearer token vs OAuth 2.0 access token")

if __name__ == "__main__":
    asyncio.run(main())