#!/usr/bin/env python3
"""
測試法律專家路由修復效果
"""

import requests
import json

def test_legal_routing():
    """測試法律專家路由"""
    print("=== 測試法律專家路由 ===")

    # 測試查詢
    query_data = {
        'query': '法律合規問題',
        'user_profile': {
            'name': '測試用戶',
            'age': 30
        }
    }

    try:
        print(f"查詢: {query_data['query']}")

        response = requests.post(
            'http://localhost:8001/query',
            json=query_data,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            print("SUCCESS: API 回應成功")
            print(f"會話ID: {result.get('session_id')}")
            print(f"信心度: {result.get('confidence_score', 0)}")

            expert_responses = result.get("expert_responses", {})
            print(f"\n=== 專家參與情況 ===")
            print(f"參與專家數量: {len(expert_responses)}")

            for expert_type, response_data in expert_responses.items():
                print(f"- {expert_type}: 信心度 {response_data.get('confidence', 0)}")

            # 檢查是否正確路由到法律專家
            if 'legal_expert' in expert_responses:
                print("\n✅ 法律專家路由成功！")
                return True
            else:
                print(f"\n❌ 法律專家路由失敗")
                print(f"參與的專家: {list(expert_responses.keys())}")
                return False

        else:
            print(f"ERROR: 請求失敗 {response.status_code}")
            print(f"錯誤信息: {response.text}")
            return False

    except Exception as e:
        print(f"ERROR: 測試失敗 {e}")
        return False

if __name__ == "__main__":
    success = test_legal_routing()
    if success:
        print("\n=== 測試結果: 路由修復成功 ===")
    else:
        print("\n=== 測試結果: 路由仍有問題 ===")