#!/usr/bin/env python3
"""
直接測試代理人，看是否使用 LLM
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加專案路徑
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

# 直接導入
sys.path.append('src/main/python')
from agents.financial_planner_agent_llm import FinancialPlannerAgentLLM
from llm.llm_client import is_llm_configured, generate_llm_response

async def test_llm_directly():
    """直接測試 LLM"""
    print("=== 測試 LLM 直接調用 ===")
    print(f"LLM 已配置: {is_llm_configured()}")

    if is_llm_configured():
        response = await generate_llm_response("你好，我想要投資建議")
        print(f"LLM 回應: {response.content[:100]}...")
        print(f"模型: {response.model}")
    else:
        print("LLM 未配置!")

async def test_agent():
    """測試理財規劃代理人"""
    print("\n=== 測試理財規劃代理人 ===")

    # 初始化代理人
    agent = FinancialPlannerAgentLLM()

    query = "我30歲，想要投資建議"
    print(f"查詢: {query}")

    # 檢查能力評分
    score = await agent.can_handle(query)
    print(f"能力評分: {score:.2f}")

    # 處理查詢
    message = await agent.process_query(query, {})

    print(f"代理人回應: {message.content[:200]}...")
    print(f"信心度: {message.confidence:.1%}")
    print(f"來源數量: {len(message.sources)}")

async def main():
    """主函式"""
    await test_llm_directly()
    await test_agent()

if __name__ == "__main__":
    asyncio.run(main())