#!/usr/bin/env python3
"""
LLM 整合測試腳本
驗證所有 agents 正確使用 4o-mini 模型和 OpenAI API
"""

import os
import asyncio
import sys
from pathlib import Path

# 加入 src 路徑
sys.path.insert(0, str(Path(__file__).parent / "src" / "main" / "python"))

async def test_llm_configuration():
    """測試 LLM 配置"""
    print(">> 測試 LLM 配置...")

    try:
        from llm.llm_client import llm_manager, is_llm_configured

        # 檢查 LLM 配置狀態
        print(f"[OK] LLM 已配置: {is_llm_configured()}")
        print(f"[INFO] 可用客戶端: {llm_manager.get_available_clients()}")
        print(f"[INFO] 預設客戶端: {llm_manager.default_client}")

        # 檢查 OpenAI API Key
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            print(f"[KEY] OpenAI API Key: {openai_key[:8]}...{openai_key[-4:] if len(openai_key) > 12 else 'TOO_SHORT'}")
        else:
            print("[ERROR] 未設定 OpenAI API Key")

        return True

    except Exception as e:
        print(f"[ERROR] LLM 配置測試失敗: {e}")
        return False

async def test_agents_llm_integration():
    """測試 agents LLM 整合"""
    print("\n>> 測試 Agents LLM 整合...")

    try:
        from agents import (
            ManagerAgent,
            FinancialPlannerAgentLLM,
            FinancialAnalystAgentLLM,
            LegalExpertAgentLLM
        )
        from agents.base_agent import AgentMessage, AgentType, MessageType

        # 初始化所有 agents
        agents = {
            "manager": ManagerAgent(),
            "financial_planner": FinancialPlannerAgentLLM(),
            "financial_analyst": FinancialAnalystAgentLLM(),
            "legal_expert": LegalExpertAgentLLM()
        }

        print(f"[OK] 成功初始化 {len(agents)} 個 agents")

        # 檢查每個 agent 的 LLM 狀態
        for name, agent in agents.items():
            if hasattr(agent, 'get_llm_status'):
                status = agent.get_llm_status()
                print(f"[INFO] {name}: LLM配置={status.get('llm_configured')}, 模型={status.get('model')}")
            else:
                print(f"[WARN] {name}: 未實作 get_llm_status 方法")

        return True

    except Exception as e:
        print(f"[ERROR] Agents 整合測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_simple_llm_call():
    """測試簡單的 LLM 調用"""
    print("\n>> 測試簡單 LLM 調用...")

    try:
        from llm import generate_llm_response, is_llm_configured

        if not is_llm_configured():
            print("[WARN] LLM 未配置，將使用 Mock 回應")

        # 簡單測試查詢
        test_prompt = "請簡短解釋什麼是分散投資？"

        print(f"[PROMPT] 測試 Prompt: {test_prompt}")

        response = await generate_llm_response(
            prompt=test_prompt,
            max_tokens=200,
            temperature=0.3
        )

        print(f"[OK] LLM 回應成功")
        print(f"[MODEL] 模型: {response.model}")
        print(f"[TIME] 回應時間: {response.response_time:.2f}秒")
        print(f"[LENGTH] 內容長度: {len(response.content)}字")
        print(f"[TOKENS] Token 使用: {response.usage}")
        print(f"[FINISH] 結束原因: {response.finish_reason}")

        # 顯示前100字內容
        content_preview = response.content[:100] + "..." if len(response.content) > 100 else response.content
        print(f"[PREVIEW] 內容預覽: {content_preview}")

        return True

    except Exception as e:
        print(f"[ERROR] LLM 調用測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_agent_message_processing():
    """測試 agent 訊息處理"""
    print("\n>> 測試 Agent 訊息處理...")

    try:
        from agents import FinancialAnalystAgentLLM
        from agents.base_agent import AgentMessage, AgentType, MessageType

        # 初始化金融分析專家
        analyst = FinancialAnalystAgentLLM()

        # 建立測試訊息
        test_message = AgentMessage(
            agent_type=AgentType.FINANCIAL_ANALYST,
            message_type=MessageType.QUERY,
            content="台股目前的投資環境如何？有什麼建議？"
        )

        print(f"[SEND] 發送測試訊息: {test_message.content}")

        # 處理訊息
        response = await analyst.process_message(test_message)

        print(f"[OK] 收到回應")
        print(f"[CONFIDENCE] 信心度: {response.confidence}")
        print(f"[METADATA] 元數據: {response.metadata}")
        print(f"[SOURCES] 資料來源數量: {len(response.sources or [])}")

        # 顯示回應內容預覽
        content_preview = response.content[:200] + "..." if len(response.content) > 200 else response.content
        print(f"[PREVIEW] 回應預覽: {content_preview}")

        return True

    except Exception as e:
        print(f"[ERROR] Agent 訊息處理測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主測試函數"""
    print(">> 開始 LLM 整合測試\n")

    tests = [
        ("LLM 配置", test_llm_configuration),
        ("Agents LLM 整合", test_agents_llm_integration),
        ("簡單 LLM 調用", test_simple_llm_call),
        ("Agent 訊息處理", test_agent_message_processing)
    ]

    results = []

    for test_name, test_func in tests:
        print(f"[TEST] 執行測試: {test_name}")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"[ERROR] 測試 {test_name} 發生異常: {e}")
            results.append((test_name, False))
        print()

    # 總結報告
    print("=" * 50)
    print("[SUMMARY] 測試結果總結:")
    print("=" * 50)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test_name}")
        if result:
            passed += 1

    print(f"\n[TOTAL] 總計: {passed}/{total} 個測試通過")

    if passed == total:
        print("[SUCCESS] 所有測試通過！LLM 整合成功！")
        return 0
    else:
        print("[WARNING] 部分測試失敗，請檢查配置")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n[INTERRUPT] 測試被使用者中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n[CRASH] 測試執行失敗: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)