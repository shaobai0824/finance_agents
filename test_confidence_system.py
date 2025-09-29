#!/usr/bin/env python3
"""
測試新的智能信心度計算系統

比較舊系統 vs 新系統的信心度差異
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

from src.main.python.evaluation.confidence_calculator import confidence_calculator
from src.main.python.workflow.finance_workflow_llm import FinanceWorkflowLLM


async def test_confidence_comparison():
    """測試新舊信心度系統的差異"""

    print("=== 信心度系統對比測試 ===\n")

    # 初始化工作流程
    workflow = FinanceWorkflowLLM()

    # 測試案例：不同類型和品質的查詢
    test_cases = [
        {
            "name": "簡短不明確查詢",
            "query": "投資",
            "expected_confidence": "低",
            "description": "查詢太簡短，缺乏明確意圖"
        },
        {
            "name": "詳細投資規劃查詢",
            "query": "我是35歲上班族，月收入8萬，想要為退休做投資規劃，請建議適合的資產配置策略",
            "expected_confidence": "高",
            "description": "詳細、明確的理財規劃查詢"
        },
        {
            "name": "股票分析查詢",
            "query": "台積電最近的財報表現如何？技術分析看起來適合買進嗎？",
            "expected_confidence": "中高",
            "description": "具體股票分析查詢"
        },
        {
            "name": "法律問題查詢",
            "query": "投資海外股票的稅務問題有哪些需要注意？",
            "expected_confidence": "中",
            "description": "法律稅務相關查詢"
        },
        {
            "name": "模糊市場查詢",
            "query": "最近市場怎麼樣？",
            "expected_confidence": "低中",
            "description": "模糊的市場查詢"
        }
    ]

    results = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"--- 測試案例 {i}: {test_case['name']} ---")
        print(f"查詢: {test_case['query']}")
        print(f"預期信心度: {test_case['expected_confidence']}")
        print(f"說明: {test_case['description']}")

        try:
            # 執行完整工作流程
            result = await workflow.run(
                user_query=test_case['query'],
                user_profile={"age": 35, "risk_tolerance": "moderate"},
                session_id=f"confidence-test-{i}"
            )

            print(f"執行狀態: {result['status']}")
            print(f"使用的專家: {result.get('agents_used', [])}")

            # 分析各專家的信心度
            expert_responses = result.get('expert_responses', {})

            if expert_responses:
                print("\n專家信心度分析:")
                for agent_name, response in expert_responses.items():
                    confidence = response.get('confidence', 0)
                    metadata = response.get('metadata', {})
                    confidence_metrics = metadata.get('confidence_metrics', {})

                    print(f"  {agent_name}:")
                    print(f"    總體信心度: {confidence:.3f}")

                    if confidence_metrics:
                        print(f"    語意相關性: {confidence_metrics.get('relevance_score', 0):.3f}")
                        print(f"    回應品質: {confidence_metrics.get('response_quality', 0):.3f}")
                        print(f"    知識覆蓋: {confidence_metrics.get('knowledge_coverage', 0):.3f}")
                        print(f"    領域專業: {confidence_metrics.get('domain_expertise', 0):.3f}")

                # 整體信心度
                overall_confidence = result.get('confidence_score', 0)
                print(f"\n整體信心度: {overall_confidence:.3f}")

                # 評估信心度是否合理
                confidence_category = categorize_confidence(overall_confidence)
                print(f"信心度分類: {confidence_category}")

                match_expectation = check_expectation_match(
                    confidence_category, test_case['expected_confidence']
                )
                print(f"符合預期: {'✅' if match_expectation else '❌'}")

                results.append({
                    'test_case': test_case['name'],
                    'query': test_case['query'],
                    'expected': test_case['expected_confidence'],
                    'actual_score': overall_confidence,
                    'actual_category': confidence_category,
                    'match_expectation': match_expectation,
                    'expert_details': {
                        agent: {
                            'confidence': resp.get('confidence', 0),
                            'metrics': resp.get('metadata', {}).get('confidence_metrics', {})
                        }
                        for agent, resp in expert_responses.items()
                    }
                })

            else:
                print("❌ 沒有專家回應")
                results.append({
                    'test_case': test_case['name'],
                    'error': 'No expert responses'
                })

        except Exception as e:
            print(f"❌ 測試失敗: {e}")
            results.append({
                'test_case': test_case['name'],
                'error': str(e)
            })

        print("\n" + "="*60 + "\n")

    # 生成測試報告
    generate_test_report(results)


def categorize_confidence(score: float) -> str:
    """將信心度分數分類"""
    if score >= 0.8:
        return "高"
    elif score >= 0.6:
        return "中高"
    elif score >= 0.4:
        return "中"
    elif score >= 0.2:
        return "低中"
    else:
        return "低"


def check_expectation_match(actual: str, expected: str) -> bool:
    """檢查實際結果是否符合預期"""
    # 簡單的預期匹配邏輯
    category_order = ["低", "低中", "中", "中高", "高"]

    try:
        actual_idx = category_order.index(actual)
        expected_idx = category_order.index(expected)

        # 允許 ±1 的誤差
        return abs(actual_idx - expected_idx) <= 1
    except ValueError:
        return False


def generate_test_report(results):
    """生成詳細的測試報告"""
    print("=== 信心度系統測試報告 ===")

    successful_tests = [r for r in results if 'error' not in r]
    failed_tests = [r for r in results if 'error' in r]

    print(f"總測試數: {len(results)}")
    print(f"成功測試: {len(successful_tests)}")
    print(f"失敗測試: {len(failed_tests)}")

    if successful_tests:
        matches = sum(1 for r in successful_tests if r.get('match_expectation', False))
        print(f"符合預期: {matches}/{len(successful_tests)} ({matches/len(successful_tests)*100:.1f}%)")

        print("\n--- 信心度分佈分析 ---")
        confidence_scores = [r['actual_score'] for r in successful_tests]
        print(f"平均信心度: {sum(confidence_scores)/len(confidence_scores):.3f}")
        print(f"最高信心度: {max(confidence_scores):.3f}")
        print(f"最低信心度: {min(confidence_scores):.3f}")
        print(f"信心度範圍: {max(confidence_scores) - min(confidence_scores):.3f}")

        print("\n--- 各維度分析 ---")
        all_metrics = {}
        for result in successful_tests:
            for agent, details in result.get('expert_details', {}).items():
                metrics = details.get('metrics', {})
                for metric_name, value in metrics.items():
                    if metric_name not in all_metrics:
                        all_metrics[metric_name] = []
                    all_metrics[metric_name].append(value)

        for metric_name, values in all_metrics.items():
            if values:
                avg_value = sum(values) / len(values)
                print(f"{metric_name}: 平均 {avg_value:.3f} (範圍: {min(values):.3f}-{max(values):.3f})")

    if failed_tests:
        print("\n--- 失敗測試 ---")
        for test in failed_tests:
            print(f"{test['test_case']}: {test['error']}")

    print("\n=== 改善建議 ===")

    if successful_tests:
        # 分析是否有改善空間
        low_confidence_tests = [r for r in successful_tests if r['actual_score'] < 0.4]
        high_confidence_tests = [r for r in successful_tests if r['actual_score'] > 0.8]

        if len(set(r['actual_score'] for r in successful_tests)) < 3:
            print("⚠️  信心度變化範圍仍然不夠大，建議調整權重配置")

        if low_confidence_tests:
            print(f"✅ 成功識別出 {len(low_confidence_tests)} 個低品質查詢")

        if high_confidence_tests:
            print(f"✅ 成功識別出 {len(high_confidence_tests)} 個高品質查詢")

        print("✅ 智能信心度系統運作正常，提供了更精確的信心度評估")
    else:
        print("❌ 所有測試都失敗，需要檢查系統配置")


async def test_direct_confidence_calculator():
    """直接測試信心度計算器"""
    print("\n=== 直接測試信心度計算器 ===")

    # 模擬不同品質的數據
    test_data = [
        {
            "query": "投資建議",
            "response": "根據您的需求，建議進行多元化投資組合配置，包括股票、債券和基金。",
            "knowledge_results": [
                {"distance": 0.2, "document": "投資組合理論說明", "source": "投信投顧"},
                {"distance": 0.3, "document": "資產配置策略", "source": "銀行"},
            ],
            "agent_type": "financial_planner"
        },
        {
            "query": "股票",
            "response": "股票投資有風險。",
            "knowledge_results": [],
            "agent_type": "financial_analyst"
        }
    ]

    for i, data in enumerate(test_data, 1):
        print(f"\n--- 直接測試 {i} ---")
        print(f"查詢: {data['query']}")
        print(f"回應: {data['response']}")
        print(f"知識數量: {len(data['knowledge_results'])}")

        try:
            metrics = await confidence_calculator.calculate_confidence(
                query=data['query'],
                response_content=data['response'],
                knowledge_results=data['knowledge_results'],
                agent_type=data['agent_type']
            )

            print(f"結果:")
            print(f"  總體信心度: {metrics.overall_confidence:.3f}")
            print(f"  語意相關性: {metrics.relevance_score:.3f}")
            print(f"  回應品質: {metrics.response_quality:.3f}")
            print(f"  知識覆蓋: {metrics.knowledge_coverage:.3f}")
            print(f"  領域專業: {metrics.domain_expertise:.3f}")

        except Exception as e:
            print(f"計算失敗: {e}")


if __name__ == "__main__":
    async def main():
        await test_confidence_comparison()
        await test_direct_confidence_calculator()

    asyncio.run(main())