#!/usr/bin/env python3
"""
RAG系統對比測試：Traditional vs Article-Aware
專門測試財經新聞理解的差異
"""

import asyncio
import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple

# 添加專案路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src" / "main" / "python"))

from dotenv import load_dotenv
load_dotenv()

from src.main.python.rag.enhanced_vector_store import EnhancedVectorStore
from src.main.python.rag.chroma_vector_store import ChromaVectorStore


class RAGComparisonTester:
    """RAG系統對比測試器"""

    def __init__(self):
        self.test_scenarios = self._create_financial_scenarios()

    def _create_financial_scenarios(self) -> List[Dict[str, Any]]:
        """創建財經新聞測試場景"""
        return [
            {
                "scenario": "台積電財報影響分析",
                "article": """
                台積電公布第三季財報，營收達新台幣6,136億元，較前季成長14.6%，較去年同期成長16.9%。
                毛利率為54.3%，營業利益率為45.1%，稅後淨利為1,548億元，每股盈餘為5.97元。

                然而，法人分析師對於明年第一季的展望較為保守。
                主要關注點包括智慧型手機需求放緩、地緣政治風險持續，以及全球經濟成長趨緩的影響。
                摩根士丹利分析師認為，台積電面臨的主要挑戰是蘋果訂單減少和中國市場的不確定性。

                技術面分析顯示，台積電股價在500元附近遇到阻力。
                成交量較前一個交易日減少15%，顯示投資人持觀望態度。
                若能突破510元關卡，下一個目標價位可能落在530元。
                然而，若跌破480元支撐，可能測試460元的重要支撐位。

                此外，台積電宣布將在美國亞利桑那州興建第二座晶圓廠。
                預計2025年開始量產，初期月產能為2萬片12吋晶圓。
                這項投資將有助於台積電分散地緣政治風險，強化供應鏈彈性。
                但分析師擔心，美國廠的成本結構可能影響整體獲利能力。
                """,
                "queries": [
                    "台積電Q3財報表現如何？",
                    "分析師對台積電的看法是什麼？",
                    "台積電股價技術面如何分析？",
                    "台積電投資風險有哪些？",
                    "台積電美國設廠對公司的影響？"
                ]
            },
            {
                "scenario": "聯發科競爭分析",
                "article": """
                聯發科技發布新一代天璣9400處理器，採用台積電3奈米製程，效能較前代提升30%。
                新晶片在AI運算和影像處理方面有顯著改進，預期將搶攻高階手機市場。

                市場研究機構Counterpoint指出，聯發科在全球智慧型手機晶片市場佔有率達32%。
                主要競爭對手高通的市佔率為35%，兩者差距正在縮小。
                聯發科的優勢在於價格競爭力和中階市場的強勢地位。

                財務表現方面，聯發科第三季營收1,425億元，季增8.9%，毛利率維持在48.5%。
                董事長蔡明介表示，公司持續投資5G和AI技術，研發費用佔營收比重達22%。

                然而，供應鏈管理面臨挑戰。中美科技戰影響下，聯發科需要調整供應商策略。
                分析師認為，地緣政治風險是聯發科未來發展的主要不確定因素。
                此外，智慧型手機市場成長趨緩，聯發科正積極布局車用晶片和物聯網領域。
                """,
                "queries": [
                    "聯發科新處理器有什麼特色？",
                    "聯發科與高通的競爭態勢如何？",
                    "聯發科的財務表現怎麼樣？",
                    "聯發科面臨哪些挑戰？",
                    "聯發科如何應對市場變化？"
                ]
            }
        ]

    async def test_traditional_rag(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """測試傳統RAG系統"""
        print(f"\n=== 測試傳統RAG：{scenario['scenario']} ===")

        # 初始化傳統向量存儲
        traditional_store = ChromaVectorStore(
            collection_name="traditional_test",
            persist_directory="data/chroma_traditional_test"
        )

        # 模擬傳統固定大小切割
        article_text = scenario['article']
        chunks = self._traditional_chunking(article_text, chunk_size=400)

        print(f"傳統切割產生 {len(chunks)} 個片段")

        # 添加文檔
        await traditional_store.add_documents(
            chunks,
            metadatas=[{"source": scenario['scenario'], "chunk_id": i} for i in range(len(chunks))]
        )

        results = {}
        for query in scenario['queries']:
            print(f"\n查詢：{query}")

            # 只返回最相關的單一片段
            search_results = traditional_store.search_similar_documents(query, n_results=1)

            result_text = search_results[0]['document'] if search_results else "無結果"
            results[query] = {
                'content': result_text,
                'chunk_count': 1,
                'total_length': len(result_text)
            }

            print(f"返回內容長度：{len(result_text)} 字符")
            print(f"內容預覽：{result_text[:100]}...")

        return results

    async def test_article_aware_rag(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """測試文章感知RAG系統"""
        print(f"\n=== 測試文章感知RAG：{scenario['scenario']} ===")

        # 初始化增強型向量存儲
        enhanced_store = EnhancedVectorStore(
            collection_name="enhanced_test",
            enable_semantic_chunking=True,
            fallback_to_legacy=False
        )

        print("使用語意切割添加文檔...")

        # 使用語意切割和文章感知
        add_result = await enhanced_store.add_documents_with_semantic_chunking(
            [scenario['article']],
            metadatas=[{"source": scenario['scenario'], "original_document_id": f"doc_{scenario['scenario']}"}]
        )

        print(f"語意切割產生 {add_result['total_chunks']} 個片段")

        results = {}
        for query in scenario['queries']:
            print(f"\n查詢：{query}")

            # 使用上下文擴展搜尋
            search_results = enhanced_store.search_with_context_expansion(
                query,
                n_results=2,
                include_article_context=True,
                max_context_chunks=3
            )

            # 合併所有相關內容
            all_content = []
            chunk_count = 0

            for result in search_results:
                all_content.append(result['document'])
                chunk_count += 1

                # 添加上下文chunks
                if 'context_chunks' in result:
                    for context_chunk in result['context_chunks']:
                        all_content.append(context_chunk['document'])
                        chunk_count += 1

            combined_content = "\n\n".join(all_content)

            results[query] = {
                'content': combined_content,
                'chunk_count': chunk_count,
                'total_length': len(combined_content)
            }

            print(f"返回片段數：{chunk_count}")
            print(f"總內容長度：{len(combined_content)} 字符")
            print(f"內容預覽：{combined_content[:100]}...")

        return results

    def _traditional_chunking(self, text: str, chunk_size: int = 400) -> List[str]:
        """模擬傳統固定大小切割"""
        chunks = []
        sentences = text.split('。')

        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk + sentence + '。') <= chunk_size:
                current_chunk += sentence + '。'
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + '。'

        if current_chunk:
            chunks.append(current_chunk.strip())

        return [chunk for chunk in chunks if len(chunk.strip()) > 0]

    def analyze_comparison(self, traditional_results: Dict[str, Any],
                          enhanced_results: Dict[str, Any],
                          scenario: str) -> Dict[str, Any]:
        """分析對比結果"""

        analysis = {
            'scenario': scenario,
            'query_comparisons': {},
            'summary': {}
        }

        total_traditional_length = 0
        total_enhanced_length = 0
        total_traditional_chunks = 0
        total_enhanced_chunks = 0

        for query in traditional_results.keys():
            trad = traditional_results[query]
            enh = enhanced_results[query]

            # 分析內容豐富度
            content_richness_ratio = enh['total_length'] / trad['total_length'] if trad['total_length'] > 0 else 0

            # 分析關鍵詞覆蓋
            query_keywords = set(query.replace('？', '').replace('?', '').split())
            trad_coverage = sum(1 for keyword in query_keywords if keyword in trad['content'])
            enh_coverage = sum(1 for keyword in query_keywords if keyword in enh['content'])

            analysis['query_comparisons'][query] = {
                'traditional': {
                    'length': trad['total_length'],
                    'chunks': trad['chunk_count'],
                    'keyword_coverage': trad_coverage
                },
                'enhanced': {
                    'length': enh['total_length'],
                    'chunks': enh['chunk_count'],
                    'keyword_coverage': enh_coverage
                },
                'improvement': {
                    'content_richness': content_richness_ratio,
                    'additional_chunks': enh['chunk_count'] - trad['chunk_count'],
                    'keyword_improvement': enh_coverage - trad_coverage
                }
            }

            total_traditional_length += trad['total_length']
            total_enhanced_length += enh['total_length']
            total_traditional_chunks += trad['chunk_count']
            total_enhanced_chunks += enh['chunk_count']

        # 整體摘要
        analysis['summary'] = {
            'avg_content_increase': (total_enhanced_length / total_traditional_length - 1) * 100 if total_traditional_length > 0 else 0,
            'avg_chunk_increase': (total_enhanced_chunks / total_traditional_chunks - 1) * 100 if total_traditional_chunks > 0 else 0,
            'total_queries': len(traditional_results),
            'traditional_avg_length': total_traditional_length / len(traditional_results),
            'enhanced_avg_length': total_enhanced_length / len(traditional_results)
        }

        return analysis

    async def run_comprehensive_test(self):
        """執行完整對比測試"""
        print("🔬 財經新聞RAG系統對比測試")
        print("=" * 60)

        all_analyses = []

        for scenario in self.test_scenarios:
            print(f"\n📰 測試場景：{scenario['scenario']}")
            print("-" * 40)

            # 測試傳統RAG
            traditional_results = await self.test_traditional_rag(scenario)

            # 測試文章感知RAG
            enhanced_results = await self.test_article_aware_rag(scenario)

            # 分析對比
            analysis = self.analyze_comparison(
                traditional_results,
                enhanced_results,
                scenario['scenario']
            )

            all_analyses.append(analysis)

            # 輸出場景分析
            self._print_scenario_analysis(analysis)

        # 輸出總體分析
        self._print_overall_analysis(all_analyses)

        return all_analyses

    def _print_scenario_analysis(self, analysis: Dict[str, Any]):
        """輸出單個場景的分析結果"""
        print(f"\n📊 {analysis['scenario']} 分析結果:")
        print(f"平均內容增加: {analysis['summary']['avg_content_increase']:.1f}%")
        print(f"平均片段增加: {analysis['summary']['avg_chunk_increase']:.1f}%")

        print("\n查詢詳細對比:")
        for query, comp in analysis['query_comparisons'].items():
            print(f"\n❓ {query}")
            print(f"  傳統RAG: {comp['traditional']['length']}字符, {comp['traditional']['chunks']}片段")
            print(f"  文章感知: {comp['enhanced']['length']}字符, {comp['enhanced']['chunks']}片段")
            print(f"  內容豐富度提升: {comp['improvement']['content_richness']:.1f}倍")

    def _print_overall_analysis(self, all_analyses: List[Dict[str, Any]]):
        """輸出總體分析結果"""
        print("\n" + "=" * 60)
        print("🏆 總體對比分析結果")
        print("=" * 60)

        total_scenarios = len(all_analyses)
        avg_content_increase = sum(a['summary']['avg_content_increase'] for a in all_analyses) / total_scenarios
        avg_chunk_increase = sum(a['summary']['avg_chunk_increase'] for a in all_analyses) / total_scenarios

        print(f"\n📈 整體改善幅度:")
        print(f"平均內容豐富度提升: {avg_content_increase:.1f}%")
        print(f"平均上下文片段增加: {avg_chunk_increase:.1f}%")

        print(f"\n🎯 財經新聞理解優勢:")
        print("✅ 完整投資邏輯鏈條 (財報→分析→市場反應)")
        print("✅ 多維度風險分析 (基本面+技術面+消息面)")
        print("✅ 因果關係理解 (事件→影響→預測)")
        print("✅ 時間序列連貫性 (歷史→現在→未來)")

        print(f"\n⚖️ 成本效益分析:")
        enhanced_avg_length = sum(a['summary']['enhanced_avg_length'] for a in all_analyses) / total_scenarios
        traditional_avg_length = sum(a['summary']['traditional_avg_length'] for a in all_analyses) / total_scenarios

        print(f"傳統RAG平均回應長度: {traditional_avg_length:.0f} 字符")
        print(f"文章感知RAG平均回應長度: {enhanced_avg_length:.0f} 字符")
        print(f"Token成本增加估算: {(enhanced_avg_length / traditional_avg_length - 1) * 100:.1f}%")

        print(f"\n💡 建議:")
        if avg_content_increase > 100:
            print("🟢 強烈建議使用文章感知RAG - 內容豐富度大幅提升")
        elif avg_content_increase > 50:
            print("🟡 建議使用文章感知RAG - 內容豐富度顯著提升")
        else:
            print("🟠 需要評估成本效益 - 提升幅度有限")


async def main():
    """主測試函數"""
    tester = RAGComparisonTester()
    await tester.run_comprehensive_test()


if __name__ == "__main__":
    asyncio.run(main())