#!/usr/bin/env python3
"""
測試 RAG 整合功能
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

async def test_rag_integration():
    """測試 RAG 與多專家系統整合"""

    print("=== RAG 整合測試 ===")

    try:
        # 初始化工作流程
        workflow = FinanceWorkflowLLM()

        # 測試查詢
        test_queries = [
            "小米投資建議",
            "台股市場分析",
            "鈺創股票值得投資嗎？"
        ]

        for i, query in enumerate(test_queries, 1):
            print(f"\n--- 測試 {i}: {query} ---")

            result = await workflow.run(
                user_query=query,
                user_profile={"age": 35, "risk_tolerance": "moderate"},
                session_id=f"rag-test-{i}"
            )

            print(f"狀態: {result['status']}")
            print(f"信心度: {result['confidence_score']:.2%}")
            print(f"使用的專家: {result.get('agents_used', [])}")
            print(f"回應來源: {result.get('response_sources', [])}")
            print(f"專家回應數量: {len(result.get('expert_responses', {}))}")

            # 檢查是否有 RAG 知識被使用
            for agent_name, response in result.get('expert_responses', {}).items():
                metadata = response.get('metadata', {})
                knowledge_used = metadata.get('knowledge_used', 0)
                if knowledge_used > 0:
                    print(f"  {agent_name} 使用了 {knowledge_used} 個知識點")
                else:
                    print(f"  {agent_name} 未使用知識庫")

            print(f"回應內容（前100字）: {result['final_response'][:100]}...")
            print("-" * 50)

        # 檢查系統狀態
        system_info = workflow.get_system_info()
        print(f"\n=== 系統狀態 ===")
        print(f"LLM 配置: {system_info['llm_configured']}")
        print(f"RAG 系統: {system_info['rag_system']}")
        print(f"個人資料庫: {system_info['personal_db']}")
        print(f"活躍會話: {system_info['active_sessions']}")

    except Exception as e:
        print(f"測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_rag_integration())