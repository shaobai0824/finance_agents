"""直接測試 LLM 是否工作"""
import asyncio
import sys
import os
from pathlib import Path

# 添加路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src" / "main" / "python"))

from dotenv import load_dotenv
load_dotenv()

from src.main.python.llm.llm_client import generate_llm_response, is_llm_configured

async def test_llm():
    print("Testing LLM configuration...")
    print(f"LLM configured: {is_llm_configured()}")
    print(f"API Key exists: {bool(os.getenv('OPENAI_API_KEY'))}")

    try:
        print("\nSending test query...")
        response = await asyncio.wait_for(
            generate_llm_response(prompt="Say hello"),
            timeout=10.0
        )
        print(f"Success! Response: {response.content}")
        print(f"Model: {response.model}")
        print(f"Response time: {response.response_time:.2f}s")
    except asyncio.TimeoutError:
        print("ERROR: LLM request timed out after 10 seconds")
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_llm())