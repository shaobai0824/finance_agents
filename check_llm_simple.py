#!/usr/bin/env python3
"""
簡單的 LLM 配置檢查工具
"""

import os
import sys
from pathlib import Path

print("=== LLM 配置檢查 ===")
print()

# 檢查環境變數
openai_key = os.getenv("OPENAI_API_KEY")
anthropic_key = os.getenv("ANTHROPIC_API_KEY")

print("環境變數檢查:")
print(f"OPENAI_API_KEY: {'已設定' if openai_key else '未設定'}")
if openai_key:
    print(f"  前綴: {openai_key[:10]}...")

print(f"ANTHROPIC_API_KEY: {'已設定' if anthropic_key else '未設定'}")
if anthropic_key:
    print(f"  前綴: {anthropic_key[:10]}...")

print()

# 檢查套件安裝
try:
    import openai
    print("OpenAI 套件: 已安裝")
except ImportError:
    print("OpenAI 套件: 未安裝 (pip install openai)")

try:
    import anthropic
    print("Anthropic 套件: 已安裝")
except ImportError:
    print("Anthropic 套件: 未安裝 (pip install anthropic)")

print()

# 狀態總結
if openai_key or anthropic_key:
    print("狀態: LLM API 金鑰已配置，系統可使用真實 AI 回應")
else:
    print("狀態: 無 LLM API 金鑰，系統使用模擬回應")
    print()
    print("如何配置:")
    print("1. 取得 OpenAI API 金鑰: https://platform.openai.com/api-keys")
    print("2. 設定環境變數: set OPENAI_API_KEY=your-key-here")
    print("   或建立 .env 檔案: OPENAI_API_KEY=your-key-here")

print()
print("=== 檢查完成 ===")