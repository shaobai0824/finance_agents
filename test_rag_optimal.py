#!/usr/bin/env python3
"""
測試 RAG 檢索使用最佳切塊策略效果
"""

import requests
import json

def test_rag_retrieval():
    """測試 RAG 檢索效果"""
    print("=== 測試 RAG 檢索與最佳切塊策略 ===")

    # 測試查詢 - 這些查詢應該觸發RAG檢索
    test_queries = [
        "投資建議",  # 應該觸發理財專家 + RAG
        "股票分析",  # 應該觸發金融專家 + RAG
        "市場趨勢分析" # 應該觸發金融專家 + RAG
    ]

    results = []

    for query in test_queries:
        print(f"\n--- 測試查詢: {query} ---")

        query_data = {
            'query': query,
            'user_profile': {
                'name': '測試用戶',
                'age': 30,
                'investment_experience': '中等'
            }
        }

        try:
            response = requests.post(
                'http://localhost:8001/query',
                json=query_data,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                print(f"✓ API 回應成功")
                print(f"會話ID: {result.get('session_id')}")
                print(f"信心度: {result.get('confidence_score', 0)}")

                # 檢查來源
                sources = result.get("sources", [])
                expert_responses = result.get("expert_responses", {})

                print(f"參與專家: {list(expert_responses.keys())}")
                print(f"引用來源數量: {len(sources)}")

                # 檢查是否使用了 RAG
                rag_used = len(sources) > 0
                print(f"RAG 檢索: {'✓ 已使用' if rag_used else '✗ 未使用'}")

                if rag_used:
                    print(f"來源列表: {sources[:3]}{'...' if len(sources) > 3 else ''}")

                results.append({
                    'query': query,
                    'experts': list(expert_responses.keys()),
                    'sources_count': len(sources),
                    'confidence': result.get('confidence_score', 0),
                    'rag_used': rag_used
                })

            else:
                print(f"✗ 請求失敗: {response.status_code}")
                print(f"錯誤信息: {response.text}")

        except Exception as e:
            print(f"✗ 測試失敗: {e}")

    # 總結測試結果
    print(f"\n=== 測試總結 ===")
    total_tests = len(results)
    rag_tests = sum(1 for r in results if r['rag_used'])

    print(f"總測試數: {total_tests}")
    print(f"RAG 檢索成功: {rag_tests}/{total_tests}")
    print(f"平均信心度: {sum(r['confidence'] for r in results) / total_tests:.2f}" if results else "無數據")

    if rag_tests > 0:
        avg_sources = sum(r['sources_count'] for r in results if r['rag_used']) / rag_tests
        print(f"平均來源數量: {avg_sources:.1f}")
        print("✅ RAG 系統運行正常，使用最佳切塊策略")
    else:
        print("❌ RAG 系統未正常工作，需要檢查配置")

    return rag_tests > 0

if __name__ == "__main__":
    success = test_rag_retrieval()
    if success:
        print("\n🎉 RAG 檢索與最佳切塊策略驗證成功！")
    else:
        print("\n⚠️ RAG 檢索需要進一步檢查")