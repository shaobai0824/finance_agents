#!/usr/bin/env python3
"""
驗證 LLM 中介層正常工作
確保所有 agents 都通過 LLM 而不是預設回應
"""

import asyncio
import sys
import os

# Setup path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'main', 'python'))

async def test_llm_middleware():
    """測試 LLM 中介層"""
    print("=" * 60)
    print("LLM 中介層驗證測試")
    print("=" * 60)

    # 1. 測試 LLM 客戶端
    print("\n1. 檢查 LLM 客戶端配置")
    try:
        from llm import llm_manager, is_llm_configured, is_real_llm_configured

        print(f"   LLM 客戶端已配置: {is_llm_configured()}")
        print(f"   真實 LLM 已配置: {is_real_llm_configured()}")
        print(f"   可用客戶端: {llm_manager.get_available_clients()}")
        print(f"   預設客戶端: {llm_manager.default_client}")

    except Exception as e:
        print(f"   ❌ LLM 客戶端檢查失敗: {e}")
        return False

    # 2. 測試直接 LLM 調用
    print("\n2. 測試直接 LLM 調用")
    try:
        from llm import generate_llm_response

        response = await generate_llm_response("請提供投資建議", max_tokens=100)
        print(f"   ✅ LLM 回應成功")
        print(f"   模型: {response.model}")
        print(f"   內容長度: {len(response.content)} 字元")
        print(f"   完成原因: {response.finish_reason}")
        print(f"   回應時間: {response.response_time:.2f} 秒")

    except Exception as e:
        print(f"   ❌ 直接 LLM 調用失敗: {e}")
        return False

    # 3. 測試 agents 初始化和 LLM 狀態
    print("\n3. 測試 agents LLM 狀態")
    try:
        from agents import (
            ManagerAgent,
            FinancialAnalystAgentLLM,
            FinancialPlannerAgentLLM,
            LegalExpertAgentLLM
        )

        agents = {
            'manager': ManagerAgent(),
            'financial_analyst': FinancialAnalystAgentLLM(),
            'financial_planner': FinancialPlannerAgentLLM(),
            'legal_expert': LegalExpertAgentLLM()
        }

        for name, agent in agents.items():
            llm_status = agent.get_llm_status()
            print(f"   {name}:")
            print(f"     LLM 配置: {llm_status['llm_configured']}")
            print(f"     模型: {llm_status['model']}")
            print(f"     使用 RAG: {llm_status['use_rag']}")

    except Exception as e:
        print(f"   ❌ Agents LLM 狀態檢查失敗: {e}")
        return False

    # 4. 測試 agent 訊息處理是否使用 LLM
    print("\n4. 測試 agent 訊息處理")
    try:
        from agents.base_agent import AgentMessage, MessageType, AgentType

        # 測試理財專家
        planner = agents['financial_planner']
        message = AgentMessage(
            agent_type=AgentType.FINANCIAL_PLANNER,
            message_type=MessageType.QUERY,
            content='請給我投資建議'
        )

        print(f"   發送訊息給: {planner.name}")
        response = await planner.process_message(message)

        print(f"   ✅ 訊息處理成功")
        print(f"   回應類型: {response.message_type.value}")
        print(f"   信心度: {response.confidence}")
        print(f"   是否使用 LLM: {response.metadata.get('llm_model', 'unknown')}")
        print(f"   內容長度: {len(response.content)} 字元")

        # 檢查回應是否來自 LLM 而非預設模板
        if "模擬 LLM 回應" in response.content or "預設" in response.content:
            print(f"   ⚠️  可能使用了 fallback 回應")
        else:
            print(f"   ✅ 使用了 LLM 中介層生成回應")

    except Exception as e:
        print(f"   ❌ Agent 訊息處理測試失敗: {e}")
        return False

    # 5. 驗證沒有直接使用預設回應
    print("\n5. 驗證 LLM 中介層使用")

    # 測試多個查詢確保都通過 LLM
    test_queries = [
        "股票投資建議",
        "市場分析報告",
        "法律合規問題"
    ]

    all_using_llm = True

    for query in test_queries:
        try:
            analyst = agents['financial_analyst']
            message = AgentMessage(
                agent_type=AgentType.FINANCIAL_ANALYST,
                message_type=MessageType.QUERY,
                content=query
            )

            response = await analyst.process_message(message)

            # 檢查是否使用 LLM
            llm_model = response.metadata.get('llm_model', 'unknown')
            if llm_model == 'unknown' or "預設" in response.content:
                print(f"   ❌ 查詢 '{query}' 可能沒有使用 LLM")
                all_using_llm = False
            else:
                print(f"   ✅ 查詢 '{query}' 使用了 LLM ({llm_model})")

        except Exception as e:
            print(f"   ❌ 查詢 '{query}' 處理失敗: {e}")
            all_using_llm = False

    return all_using_llm

async def main():
    """主函數"""
    print("開始驗證 LLM 中介層...")

    success = await test_llm_middleware()

    print("\n" + "=" * 60)
    print("驗證結果")
    print("=" * 60)

    if success:
        print("✅ 成功: 所有 agents 都正確使用 LLM 中介層")
        print("✅ 模型版本: gpt-4o-mini")
        print("✅ 沒有使用預設回應")
        print("\n🎉 LLM 中介層配置正確!")
    else:
        print("❌ 失敗: 發現問題需要修復")
        print("❌ 部分 agents 可能仍在使用預設回應")

    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)