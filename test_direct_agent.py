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

    # 建立訊息並處理
    from agents.base_agent import AgentMessage, MessageType, AgentType
    input_message = AgentMessage(
        agent_type=AgentType.FINANCIAL_PLANNER,
        message_type=MessageType.QUERY,
        content=query,
        metadata={}
    )

    # 處理訊息
    response_message = await agent.process_message(input_message)

    # 安全處理 Unicode 字符
    safe_content = ''.join(char for char in response_message.content if ord(char) < 65536)
    print(f"代理人回應: {safe_content[:200]}...")
    print(f"信心度: {response_message.confidence:.1%}")
    print(f"來源數量: {len(response_message.sources)}")

async def test_rag():
    """測試 RAG 系統整合"""
    print("\n=== 測試 RAG 系統整合 ===")

    try:
        # 導入 RAG 相關模組
        from rag.chroma_vector_store import ChromaVectorStore
        from rag.knowledge_retriever import KnowledgeRetriever, ExpertDomain

        # 初始化向量存儲
        vector_store = ChromaVectorStore()
        collection_info = vector_store.get_collection_info()
        print(f"向量庫狀態: {collection_info}")

        # 初始化知識檢索器
        knowledge_retriever = KnowledgeRetriever(vector_store)

        # 初始化帶 RAG 的代理人
        agent = FinancialPlannerAgentLLM(
            name="理財規劃專家",
            knowledge_retriever=knowledge_retriever
        )

        # 測試查詢（與新聞數據相關）
        query = "小米投資建議"
        print(f"RAG 查詢: {query}")

        # 建立訊息並處理
        from agents.base_agent import AgentMessage, MessageType, AgentType
        input_message = AgentMessage(
            agent_type=AgentType.FINANCIAL_PLANNER,
            message_type=MessageType.QUERY,
            content=query,
            metadata={"user_profile": {"age": 35}}
        )

        # 處理訊息
        response_message = await agent.process_message(input_message)

        # 安全處理 Unicode 字符
        safe_content = ''.join(char for char in response_message.content if ord(char) < 65536)
        print(f"RAG 代理人回應: {safe_content[:200]}...")
        print(f"信心度: {response_message.confidence:.1%}")
        print(f"來源數量: {len(response_message.sources)}")

        # 檢查 metadata 中的知識使用情況
        metadata = response_message.metadata or {}
        knowledge_used = metadata.get('knowledge_used', 0)
        print(f"使用的知識點數量: {knowledge_used}")

        if knowledge_used > 0:
            print("○ RAG 知識庫已成功被調用")
        else:
            print("X RAG 知識庫未被調用")

        # 直接測試知識檢索
        print("\n--- 直接測試知識檢索 ---")
        results = await knowledge_retriever.retrieve_for_expert(
            query=query,
            expert_domain=ExpertDomain.FINANCIAL_PLANNING,
            max_results=3
        )

        print(f"檢索結果數量: {len(results)}")
        for i, result in enumerate(results, 1):
            print(f"結果 {i}: {result.content[:100]}...")

    except Exception as e:
        print(f"RAG 測試失敗: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """主函式"""
    await test_llm_directly()
    await test_agent()
    await test_rag()

if __name__ == "__main__":
    asyncio.run(main())