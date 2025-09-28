#!/usr/bin/env python3
"""
測試路由修復效果
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

from src.main.python.agents.manager_agent import ManagerAgent
from src.main.python.agents.base_agent import AgentMessage, AgentType, MessageType

async def test_routing():
    """測試路由功能"""
    print("=== 測試路由修復效果 ===")

    # 初始化管理代理人
    manager = ManagerAgent()

    # 測試查詢
    test_queries = [
        "法律合規問題",
        "投資建議",
        "股票分析",
        "稅務規劃",
        "市場趨勢",
        "法規遵循",
        "資產配置",
        "合規性檢查"
    ]

    for query in test_queries:
        print(f"\n--- 測試查詢: {query} ---")

        # 創建查詢訊息
        message = AgentMessage(
            agent_type=AgentType.MANAGER,
            message_type=MessageType.QUERY,
            content=query
        )

        try:
            # 處理路由
            response = await manager.process_message(message)

            print(f"路由結果: {response.content}")
            if response.metadata:
                experts = response.metadata.get('required_experts', [])
                print(f"選中的專家: {experts}")

        except Exception as e:
            print(f"路由測試失敗: {e}")

    print(f"\n=== 路由測試完成 ===")

if __name__ == "__main__":
    asyncio.run(test_routing())