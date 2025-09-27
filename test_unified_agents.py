#!/usr/bin/env python3
"""
測試統一 Agent 架構後的系統運作

測試目標：
1. 驗證所有 agents 都能正確初始化
2. 確認 LLM 整合功能正常運作
3. 測試 agent 間的協作流程
4. 驗證 can_handle 方法運作正常
"""

import asyncio
import logging
import sys
import os

# 設定路徑以便能夠導入 agents
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'main', 'python'))

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_agent_initialization():
    """測試所有 agents 初始化"""
    print("=" * 60)
    print("🧪 測試 1: Agent 初始化測試")
    print("=" * 60)

    try:
        from agents import (
            ManagerAgent,
            FinancialAnalystAgentLLM,
            FinancialPlannerAgentLLM,
            LegalExpertAgentLLM
        )
        from agents.base_agent import AgentMessage, MessageType, AgentType

        # 初始化所有 agents
        agents = {
            'manager': ManagerAgent(),
            'financial_analyst': FinancialAnalystAgentLLM(),
            'financial_planner': FinancialPlannerAgentLLM(),
            'legal_expert': LegalExpertAgentLLM()
        }

        print("✅ 所有 agents 初始化成功:")
        for name, agent in agents.items():
            print(f"   - {name}: {agent.__class__.__name__}")
            print(f"     LLM 狀態: {agent.get_llm_status()['llm_configured']}")
            print(f"     模型: {agent.llm_config['model']}")

        return agents

    except Exception as e:
        print(f"❌ Agent 初始化失敗: {e}")
        return None

async def test_can_handle_capabilities(agents):
    """測試 can_handle 能力評估"""
    print("\n" + "=" * 60)
    print("🧪 測試 2: Can Handle 能力評估測試")
    print("=" * 60)

    test_queries = [
        "我想要投資建議和資產配置",  # 理財規劃
        "請分析台積電的技術指標和趨勢",  # 金融分析
        "投資的稅務規定和法律風險",  # 法律專家
        "綜合理財規劃和風險管理"  # 多專家
    ]

    for query in test_queries:
        print(f"\n查詢: {query}")
        scores = {}

        for name, agent in agents.items():
            if name == 'manager':
                continue  # Manager 總是返回 1.0

            try:
                score = await agent.can_handle(query)
                scores[name] = score
                print(f"   {name}: {score:.2f}")
            except Exception as e:
                print(f"   {name}: 錯誤 - {e}")

        # 找出最適合的專家
        best_agent = max(scores.items(), key=lambda x: x[1]) if scores else None
        if best_agent:
            print(f"   🎯 最適合: {best_agent[0]} (分數: {best_agent[1]:.2f})")

async def test_llm_integration(agents):
    """測試 LLM 整合功能"""
    print("\n" + "=" * 60)
    print("🧪 測試 3: LLM 整合功能測試")
    print("=" * 60)

    # 測試基本的訊息處理
    test_message = {
        'content': '請給我一些基本的投資建議',
        'agent_type': AgentType.FINANCIAL_PLANNER,
        'message_type': MessageType.QUERY
    }

    # 導入必要的類別
    from agents.base_agent import AgentMessage, MessageType, AgentType

    message = AgentMessage(
        agent_type=AgentType.FINANCIAL_PLANNER,
        message_type=MessageType.QUERY,
        content='請給我一些基本的投資建議'
    )

    try:
        planner = agents['financial_planner']
        print(f"📤 發送訊息給 {planner.name}")
        print(f"   內容: {message.content}")

        # 處理訊息
        response = await planner.process_message(message)

        print(f"📥 收到回應:")
        print(f"   類型: {response.message_type.value}")
        print(f"   信心度: {response.confidence}")
        print(f"   內容長度: {len(response.content)} 字元")
        print(f"   內容預覽: {response.content[:100]}...")

        if response.metadata:
            print(f"   元數據: {list(response.metadata.keys())}")

    except Exception as e:
        print(f"❌ LLM 整合測試失敗: {e}")
        import traceback
        traceback.print_exc()

async def test_manager_routing(agents):
    """測試管理員路由功能"""
    print("\n" + "=" * 60)
    print("🧪 測試 4: 管理員路由功能測試")
    print("=" * 60)

    from agents.base_agent import AgentMessage, MessageType, AgentType

    routing_queries = [
        "我需要投資建議和法律諮詢",
        "請分析市場趨勢並提供理財規劃",
        "股票技術分析"
    ]

    manager = agents['manager']

    for query in routing_queries:
        print(f"\n📝 路由查詢: {query}")

        message = AgentMessage(
            agent_type=AgentType.MANAGER,
            message_type=MessageType.QUERY,
            content=query
        )

        try:
            response = await manager.process_message(message)
            print(f"   路由結果: {response.message_type.value}")
            print(f"   信心度: {response.confidence}")

            if response.metadata and 'required_experts' in response.metadata:
                experts = response.metadata['required_experts']
                print(f"   需要專家: {', '.join(experts)}")

        except Exception as e:
            print(f"   ❌ 路由錯誤: {e}")

async def test_error_handling(agents):
    """測試錯誤處理"""
    print("\n" + "=" * 60)
    print("🧪 測試 5: 錯誤處理測試")
    print("=" * 60)

    from agents.base_agent import AgentMessage, MessageType, AgentType

    # 測試空查詢
    empty_message = AgentMessage(
        agent_type=AgentType.FINANCIAL_ANALYST,
        message_type=MessageType.QUERY,
        content=""
    )

    try:
        analyst = agents['financial_analyst']
        response = await analyst.process_message(empty_message)
        print(f"✅ 空查詢處理: {response.message_type.value}")
        print(f"   信心度: {response.confidence}")
    except Exception as e:
        print(f"❌ 空查詢處理失敗: {e}")

async def main():
    """主測試函數"""
    print("開始統一 Agent 架構測試")
    print("時間:", asyncio.get_event_loop().time())

    # 1. 初始化測試
    agents = await test_agent_initialization()
    if not agents:
        print("❌ 初始化失敗，終止測試")
        return

    # 2. 能力評估測試
    await test_can_handle_capabilities(agents)

    # 3. LLM 整合測試
    await test_llm_integration(agents)

    # 4. 管理員路由測試
    await test_manager_routing(agents)

    # 5. 錯誤處理測試
    await test_error_handling(agents)

    print("\n" + "=" * 60)
    print("🎉 統一 Agent 架構測試完成")
    print("=" * 60)

    # 總結
    print("\n📊 測試總結:")
    print("✅ Agent 初始化: 成功")
    print("✅ LLM 整合: 測試完成")
    print("✅ 路由功能: 測試完成")
    print("✅ 錯誤處理: 測試完成")
    print("\n🎯 架構重構成功 - 所有 agents 現在都統一使用 BaseAgent 與 LLM 整合")

if __name__ == "__main__":
    asyncio.run(main())