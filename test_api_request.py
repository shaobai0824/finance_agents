#!/usr/bin/env python3
"""
測試 API 請求
"""

import asyncio
import json

import aiohttp


async def test_api():
    """測試 API 端點"""

    url = "http://localhost:8000/query"
    data = {
        "query": "我想要投資建議",
        "user_profile": {"age": 30},
        "session_id": "test-003"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                print(f"Status: {response.status}")
                result = await response.json()
                print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_api())