#!/usr/bin/env python3
"""
LLM 配置檢查和設定工具
"""

import os
import sys
import asyncio
from pathlib import Path

# 添加項目路徑
sys.path.append(str(Path(__file__).parent / 'src' / 'main' / 'python'))

from llm import llm_manager, is_llm_configured, generate_llm_response


def check_environment_variables():
    """檢查環境變數配置"""
    print("[檢查] LLM 環境變數配置...")
    print("=" * 50)

    # OpenAI 配置
    openai_key = os.getenv("OPENAI_API_KEY")
    print(f"OPENAI_API_KEY: {'[已設定]' if openai_key else '[未設定]'}")
    if openai_key:
        print(f"  金鑰長度: {len(openai_key)} 字元")
        print(f"  前綴: {openai_key[:7]}...")

    # Anthropic 配置
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    print(f"ANTHROPIC_API_KEY: {'✅ 已設定' if anthropic_key else '❌ 未設定'}")
    if anthropic_key:
        print(f"  金鑰長度: {len(anthropic_key)} 字元")
        print(f"  前綴: {anthropic_key[:7]}...")

    print()


def check_available_clients():
    """檢查可用的 LLM 客戶端"""
    print("🤖 檢查可用的 LLM 客戶端...")
    print("=" * 50)

    available_clients = llm_manager.get_available_clients()
    print(f"可用客戶端: {', '.join(available_clients)}")
    print(f"預設客戶端: {llm_manager.default_client}")
    print(f"真實 LLM 可用: {'✅ 是' if is_llm_configured() else '❌ 否'}")
    print()


async def test_llm_response():
    """測試 LLM 回應"""
    print("🧪 測試 LLM 回應...")
    print("=" * 50)

    test_prompt = "請簡單介紹什麼是投資風險？"

    try:
        print(f"測試提示: {test_prompt}")
        print("生成回應中...")

        response = await generate_llm_response(test_prompt, max_tokens=200)

        print(f"✅ 回應成功！")
        print(f"模型: {response.model}")
        print(f"回應時間: {response.response_time:.2f} 秒")
        print(f"回應內容:")
        print("-" * 30)
        print(response.content)
        print("-" * 30)

    except Exception as e:
        print(f"❌ 回應失敗: {e}")

    print()


def show_configuration_guide():
    """顯示配置指南"""
    print("📖 LLM 配置指南")
    print("=" * 50)

    print("1. 設定 OpenAI API 金鑰:")
    print("   export OPENAI_API_KEY=your-openai-api-key-here")
    print("   或在 .env 檔案中添加: OPENAI_API_KEY=your-openai-api-key-here")
    print()

    print("2. 設定 Anthropic API 金鑰:")
    print("   export ANTHROPIC_API_KEY=your-anthropic-api-key-here")
    print("   或在 .env 檔案中添加: ANTHROPIC_API_KEY=your-anthropic-api-key-here")
    print()

    print("3. 安裝必要套件:")
    print("   pip install openai anthropic")
    print()

    print("4. 如何取得 API 金鑰:")
    print("   - OpenAI: https://platform.openai.com/api-keys")
    print("   - Anthropic: https://console.anthropic.com/")
    print()


def show_usage_example():
    """顯示使用範例"""
    print("💡 使用範例")
    print("=" * 50)

    example_code = '''
# 在您的 agent 中使用 LLM
from llm import generate_llm_response, is_llm_configured

async def generate_analysis(query: str):
    if is_llm_configured():
        response = await generate_llm_response(
            prompt=f"請分析以下投資問題: {query}",
            max_tokens=500,
            temperature=0.3
        )
        return response.content
    else:
        return "LLM 未配置，使用預設回應"
'''

    print(example_code)


async def main():
    """主函數"""
    print("🚀 財經理財系統 LLM 配置檢查")
    print("=" * 50)
    print()

    # 檢查環境變數
    check_environment_variables()

    # 檢查可用客戶端
    check_available_clients()

    # 測試 LLM 回應
    await test_llm_response()

    # 如果沒有配置真實 LLM，顯示配置指南
    if not is_llm_configured():
        print("⚠️ 未檢測到真實 LLM 配置，目前使用模擬回應")
        print()
        show_configuration_guide()
        show_usage_example()
    else:
        print("🎉 LLM 配置完成！您的系統已可使用真實的 AI 回應。")
        print()
        print("現在您可以:")
        print("- 使用 FinancialAnalystAgentLLM 獲得真實的 AI 分析")
        print("- 體驗更智能和個人化的理財建議")
        print("- 享受基於 LLM 的自然語言對話")


if __name__ == "__main__":
    # 嘗試載入 .env 檔案
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ 已載入 .env 檔案")
    except ImportError:
        print("⚠️ python-dotenv 未安裝，跳過 .env 檔案載入")
    except Exception:
        print("⚠️ 無法載入 .env 檔案")

    print()
    asyncio.run(main())