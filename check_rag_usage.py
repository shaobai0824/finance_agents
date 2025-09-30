#!/usr/bin/env python3
"""
檢查 RAG 使用情況的診斷工具
"""

import asyncio
import sys
from pathlib import Path

# 添加專案路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src" / "main" / "python"))

from dotenv import load_dotenv
load_dotenv()

from src.main.python.workflow.finance_workflow_llm import FinanceWorkflowLLM

async def check_rag_usage():
    """檢查 RAG 系統使用情況"""

    print("=== RAG 使用情況檢查 ===")

    try:
        # 初始化工作流程
        workflow = FinanceWorkflowLLM()

        # 測試不同類型的查詢
        test_queries = [
            ("投資建議", "理財規劃類查詢"),
            ("台積電股票分析", "股票分析類查詢"),
            ("小米投資如何", "包含RAG數據的查詢"),
        ]

        for query, description in test_queries:
            print(f"\n--- {description}: {query} ---")

            result = await workflow.run(
                user_query=query,
                user_profile={"age": 35, "risk_tolerance": "moderate"},
                session_id=f"rag-check-{query[:5]}"
            )

            print(f"狀態: {result['status']}")
            print(f"使用的專家: {result.get('agents_used', [])}")

            # 檢查專家回應中的知識使用情況
            for agent_name, response in result.get('expert_responses', {}).items():
                metadata = response.get('metadata', {})
                knowledge_used = metadata.get('knowledge_used', 0)
                personal_context_used = metadata.get('personal_context_used', False)

                print(f"  {agent_name}:")
                print(f"    知識檢索數量: {knowledge_used}")
                print(f"    個人上下文: {personal_context_used}")
                print(f"    信心度: {response.get('confidence', 0):.1%}")

                if knowledge_used > 0:
                    print(f"    ✅ 該專家成功使用了 RAG 知識")
                else:
                    print(f"    ❌ 該專家未使用 RAG 知識")

            # 檢查回應來源
            response_sources = result.get('response_sources', [])
            print(f"回應來源: {response_sources}")

            if response_sources:
                print(f"✅ 發現 {len(response_sources)} 個回應來源")
            else:
                print(f"❌ 沒有找到回應來源")

            print("-" * 50)

        # 檢查系統狀態
        system_info = workflow.get_system_info()
        print(f"\n=== 系統狀態檢查 ===")
        print(f"LLM 配置: {system_info['llm_configured']}")
        print(f"RAG 系統: {system_info['rag_system']}")
        print(f"個人資料庫: {system_info['personal_db']}")

        # 直接測試向量資料庫
        print(f"\n=== 向量資料庫直接檢查 ===")
        vector_store = workflow.vector_store
        collection_info = vector_store.get_collection_info()
        print(f"集合資訊: {collection_info}")

        # 測試直接檢索
        test_search = vector_store.search("小米", n_results=3)
        print(f"直接檢索 '小米' 結果: {len(test_search)} 個")

        if test_search:
            print("檢索內容預覽:")
            for i, result in enumerate(test_search[:2], 1):
                print(f"  {i}. {result['document'][:100]}...")

    except Exception as e:
        print(f"檢查過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_rag_usage())