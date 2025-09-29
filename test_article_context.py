#!/usr/bin/env python3
"""
文章關聯檢索測試工具

驗證同篇文章的 chunks 是否能被關聯檢索
測試文章上下文完整性
"""

import asyncio
import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Any

# 添加專案路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src" / "main" / "python"))

from dotenv import load_dotenv
load_dotenv()

from src.main.python.rag.enhanced_vector_store import EnhancedVectorStore


async def test_article_context_retrieval():
    """測試文章上下文檢索功能"""
    print("=== 文章上下文檢索測試 ===\n")

    # 初始化增強型向量存儲
    store = EnhancedVectorStore(
        collection_name="test_article_context",
        enable_semantic_chunking=True,
        fallback_to_legacy=True
    )

    # 創建測試文章（模擬被切割的財經新聞）
    test_article = """
    台積電今日公布第三季財報，表現超越市場預期。
    營收達到新台幣6,136億元，較前季成長14.6%，較去年同期成長16.9%。
    毛利率為54.3%，營業利益率為45.1%。

    執行長魏哲家在法說會中表示，公司受惠於智慧型手機和高效能運算需求強勁。
    特別是蘋果iPhone 15系列的導入，為公司帶來顯著的營收貢獻。
    預計第四季營收將持續成長，但成長幅度可能趨緩。

    然而，法人分析師對於明年第一季的展望較為保守。
    主要關注點包括智慧型手機市場飽和、地緣政治風險持續。
    此外，全球經濟成長趨緩也可能影響半導體需求。

    技術面分析方面，台積電股價在500元附近遇到強勁阻力。
    今日成交量較前一交易日減少15%，顯示投資人持觀望態度。
    若能突破510元關卡，下一個技術目標價位可能落在530元。

    公司同時宣布在美國亞利桑那州第二座晶圓廠的建設進度。
    預計2025年開始量產，初期月產能為2萬片12吋晶圓。
    這項投資將有助於台積電分散地緣政治風險，強化全球供應鏈彈性。
    """

    print(f"測試文章長度: {len(test_article)} 字符")

    # 添加測試文章（會被自動切割）
    article_metadata = {
        "source": "financial_news",
        "category": "股市分析",
        "company": "台積電",
        "date": "2024-01-15"
    }

    print("\n1. 添加測試文章並進行語意切割...")
    result = await store.add_documents_with_semantic_chunking(
        [test_article],
        metadatas=[article_metadata],
        ids=["tsmc_q3_report_2024"]
    )

    print(f"切割結果: {result['method']}")
    print(f"產生 {result['total_chunks']} 個語意切割片段")
    print(f"平均片段大小: {result.get('avg_chunk_size', 0):.0f} 字符")

    # 測試不同的檢索方式
    test_queries = [
        ("財報", "財務數據查詢"),
        ("法說會", "管理層評論查詢"),
        ("股價分析", "技術分析查詢"),
        ("美國工廠", "投資計劃查詢")
    ]

    article_id = "tsmc_q3_report_2024"

    print("\n2. 測試基本檢索 vs 上下文擴展檢索對比")
    print("=" * 60)

    for query, description in test_queries:
        print(f"\n查詢: '{query}' ({description})")
        print("-" * 40)

        # 基本檢索
        print("📋 基本檢索結果:")
        basic_results = store.search_with_metadata_filtering(
            query, n_results=3, include_metadata=True
        )

        for i, result in enumerate(basic_results, 1):
            article_ref = result.get('metadata', {}).get('original_document_id', 'unknown')
            chunk_idx = result.get('metadata', {}).get('chunk_index', '?')
            print(f"  {i}. 文章ID: {article_ref[:20]}..., Chunk: {chunk_idx}")
            print(f"     相關性: {result['relevance_score']:.3f}")
            print(f"     內容: {result['document'][:80]}...")

        # 上下文擴展檢索
        print("\n🔗 上下文擴展檢索結果:")
        context_results = store.search_with_context_expansion(
            query,
            n_results=3,
            include_article_context=True,
            max_chunks_per_article=3,
            context_similarity_threshold=0.2
        )

        primary_count = sum(1 for r in context_results if r.get('chunk_role') == 'primary')
        context_count = sum(1 for r in context_results if r.get('chunk_role') == 'context')

        print(f"  總結果數: {len(context_results)} (主要: {primary_count}, 上下文: {context_count})")

        for i, result in enumerate(context_results, 1):
            article_ref = result.get('metadata', {}).get('original_document_id', 'unknown')
            chunk_idx = result.get('metadata', {}).get('chunk_index', '?')
            role = result.get('chunk_role', 'unknown')
            print(f"  {i}. 文章ID: {article_ref[:20]}..., Chunk: {chunk_idx}, 角色: {role}")
            print(f"     相關性: {result['relevance_score']:.3f}")
            print(f"     內容: {result['document'][:80]}...")

    print("\n3. 測試完整文章上下文檢索")
    print("=" * 40)

    article_context = store.get_article_context(
        article_id,
        include_all_chunks=True,
        sort_by_order=True
    )

    if 'error' not in article_context:
        print(f"文章ID: {article_context['article_id']}")
        print(f"總 chunks 數: {article_context['total_chunks']}")
        print(f"平均語意一致性: {article_context['avg_semantic_coherence']:.3f}")
        print(f"使用的切割方式: {article_context['chunking_methods_used']}")

        print("\nChunks 詳細資訊:")
        for chunk in article_context['chunks']:
            print(f"  Chunk {chunk['chunk_index']}: {len(chunk['document'])} 字符")
            print(f"    語意一致性: {chunk['semantic_coherence']:.3f}")
            print(f"    邊界信心度: {chunk['boundary_confidence']:.3f}")
            print(f"    重疊長度: {chunk['overlap_length']}")
            print(f"    內容: {chunk['document'][:60]}...")
            print()

        # 測試重建完整內容
        full_content = article_context['full_content']
        print(f"重建內容長度: {len(full_content)} 字符")
        print(f"原始內容長度: {len(test_article)} 字符")
        print(f"內容完整性: {len(full_content) / len(test_article) * 100:.1f}%")

    else:
        print(f"獲取文章上下文失敗: {article_context['error']}")

    print("\n4. 測試文章感知檢索")
    print("=" * 40)

    for query, description in test_queries[:2]:  # 測試前兩個查詢
        print(f"\n查詢: '{query}'")

        article_aware_results = store.search_article_aware(
            query,
            n_results=5,
            prioritize_complete_articles=True,
            min_article_coverage=0.5
        )

        if article_aware_results:
            first_result = article_aware_results[0]
            print(f"  文章評分: {first_result.get('article_score', 0):.3f}")
            print(f"  文章覆蓋率: {first_result.get('article_coverage', 0):.1%}")
            print(f"  返回 chunks 數: {len(article_aware_results)}")

            chunks_in_order = sorted(article_aware_results,
                                   key=lambda x: x.get('metadata', {}).get('chunk_index', 0))

            print("  Chunks 順序:")
            for chunk in chunks_in_order:
                chunk_idx = chunk.get('metadata', {}).get('chunk_index', '?')
                role = chunk.get('chunk_role', 'unknown')
                print(f"    Chunk {chunk_idx} ({role}): {chunk['document'][:50]}...")

    return store


async def test_multiple_articles():
    """測試多篇文章的關聯檢索"""
    print("\n=== 多篇文章關聯檢索測試 ===\n")

    store = EnhancedVectorStore(
        collection_name="test_multi_articles",
        enable_semantic_chunking=True
    )

    # 創建多篇相關文章
    articles = [
        {
            "id": "tsmc_earnings",
            "content": "台積電公布亮眼財報，營收創歷史新高。第三季營收6136億元，年增16.9%。毛利率54.3%表現優異。",
            "metadata": {"company": "台積電", "type": "財報", "category": "earnings"}
        },
        {
            "id": "tsmc_expansion",
            "content": "台積電宣布美國亞利桑那州工廠擴建計劃。投資額達400億美元，預計2025年量產。此舉將分散地緣政治風險。",
            "metadata": {"company": "台積電", "type": "投資", "category": "expansion"}
        },
        {
            "id": "semiconductor_market",
            "content": "半導體市場展望樂觀，AI晶片需求持續強勁。台積電、NVIDIA、AMD等公司將受惠。預估明年成長15%。",
            "metadata": {"industry": "半導體", "type": "市場分析", "category": "market"}
        }
    ]

    print(f"添加 {len(articles)} 篇測試文章...")

    # 添加所有文章
    for article in articles:
        result = await store.add_documents_with_semantic_chunking(
            [article["content"]],
            metadatas=[article["metadata"]],
            ids=[article["id"]]
        )
        print(f"  {article['id']}: {result['total_chunks']} chunks")

    # 測試跨文章檢索
    print("\n測試跨文章檢索:")

    query = "台積電業績分析"
    print(f"查詢: '{query}'")

    # 基本檢索
    basic_results = store.search_with_metadata_filtering(query, n_results=5)
    print(f"\n基本檢索返回 {len(basic_results)} 個結果:")

    article_distribution = {}
    for result in basic_results:
        article_id = result.get('metadata', {}).get('original_document_id', 'unknown')
        article_distribution[article_id] = article_distribution.get(article_id, 0) + 1
        print(f"  文章: {article_id}, 相關性: {result['relevance_score']:.3f}")

    print(f"\n文章分佈: {article_distribution}")

    # 上下文擴展檢索
    context_results = store.search_with_context_expansion(
        query,
        n_results=5,
        include_article_context=True,
        max_chunks_per_article=2
    )

    print(f"\n上下文擴展檢索返回 {len(context_results)} 個結果:")

    context_article_distribution = {}
    for result in context_results:
        article_id = result.get('metadata', {}).get('original_document_id', 'unknown')
        role = result.get('chunk_role', 'unknown')
        key = f"{article_id}_{role}"
        context_article_distribution[key] = context_article_distribution.get(key, 0) + 1

    print(f"上下文文章分佈: {context_article_distribution}")

    return store


async def performance_comparison():
    """比較不同檢索方式的性能"""
    print("\n=== 檢索性能比較 ===\n")

    store = EnhancedVectorStore(
        collection_name="test_performance",
        enable_semantic_chunking=True
    )

    # 創建較大的測試資料集
    test_content = """
    台積電作為全球最大的晶圓代工廠，在先進製程技術方面保持領先地位。
    公司第三季財報顯示，7奈米和5奈米製程貢獻了超過50%的營收。
    隨著AI晶片需求激增，台積電的高效能運算平台業務快速成長。

    在地緣政治方面，台積電積極推動全球化佈局。
    美國亞利桑那州的兩座12吋晶圓廠建設進展順利。
    第一座工廠預計2024年開始量產5奈米製程。
    第二座工廠將於2025年量產更先進的3奈米製程。

    市場分析師認為，台積電在AI時代具有不可替代的競爭優勢。
    公司與NVIDIA、AMD、蘋果等主要客戶的關係穩固。
    預估未來三年，AI相關業務將為台積電貢獻30%以上的營收成長。

    然而，投資者也需要關注潛在風險。
    包括中美科技競爭加劇、全球經濟放緩、以及新興競爭者的威脅。
    台積電必須持續投資研發，維持技術領先優勢。
    """ * 3  # 重複3次以增加內容量

    print(f"測試內容長度: {len(test_content)} 字符")

    # 添加測試內容
    start_time = time.time()
    result = await store.add_documents_with_semantic_chunking(
        [test_content],
        metadatas=[{"source": "performance_test"}],
        ids=["perf_test_article"]
    )
    indexing_time = time.time() - start_time

    print(f"索引建立時間: {indexing_time:.3f}秒")
    print(f"產生 chunks: {result['total_chunks']}")

    # 測試不同檢索方式的性能
    test_queries = ["台積電財報", "AI晶片", "美國工廠", "競爭優勢", "技術風險"]

    print("\n檢索性能測試:")
    print("方式\t\t平均時間(ms)\t結果數量\t上下文完整性")
    print("-" * 60)

    # 基本檢索
    basic_times = []
    basic_results_count = []

    for query in test_queries:
        start = time.time()
        results = store.search_with_metadata_filtering(query, n_results=3)
        elapsed = (time.time() - start) * 1000
        basic_times.append(elapsed)
        basic_results_count.append(len(results))

    avg_basic_time = sum(basic_times) / len(basic_times)
    avg_basic_count = sum(basic_results_count) / len(basic_results_count)

    print(f"基本檢索\t\t{avg_basic_time:.1f}\t\t{avg_basic_count:.1f}\t\t低")

    # 上下文擴展檢索
    context_times = []
    context_results_count = []

    for query in test_queries:
        start = time.time()
        results = store.search_with_context_expansion(query, n_results=3)
        elapsed = (time.time() - start) * 1000
        context_times.append(elapsed)
        context_results_count.append(len(results))

    avg_context_time = sum(context_times) / len(context_times)
    avg_context_count = sum(context_results_count) / len(context_results_count)

    print(f"上下文擴展\t\t{avg_context_time:.1f}\t\t{avg_context_count:.1f}\t\t高")

    # 文章感知檢索
    article_times = []
    article_results_count = []

    for query in test_queries:
        start = time.time()
        results = store.search_article_aware(query, n_results=3)
        elapsed = (time.time() - start) * 1000
        article_times.append(elapsed)
        article_results_count.append(len(results))

    avg_article_time = sum(article_times) / len(article_times)
    avg_article_count = sum(article_results_count) / len(article_results_count)

    print(f"文章感知\t\t{avg_article_time:.1f}\t\t{avg_article_count:.1f}\t\t最高")

    print(f"\n性能開銷:")
    print(f"  上下文擴展比基本檢索慢: {((avg_context_time - avg_basic_time) / avg_basic_time * 100):+.1f}%")
    print(f"  文章感知比基本檢索慢: {((avg_article_time - avg_basic_time) / avg_basic_time * 100):+.1f}%")

    return store


async def main():
    """主測試函數"""
    print("🔍 文章關聯檢索系統測試\n")
    print("=" * 60)

    test_functions = [
        ("文章上下文檢索", test_article_context_retrieval),
        ("多篇文章關聯檢索", test_multiple_articles),
        ("檢索性能比較", performance_comparison)
    ]

    for test_name, test_func in test_functions:
        print(f"\n🧪 執行測試: {test_name}")
        print("-" * 40)

        try:
            start_time = time.time()
            await test_func()
            test_time = time.time() - start_time
            print(f"\n✅ {test_name} 測試完成 (耗時: {test_time:.2f}秒)")

        except Exception as e:
            print(f"\n❌ {test_name} 測試失敗: {e}")
            import traceback
            traceback.print_exc()

        print("\n" + "=" * 60)

    print("\n🎉 文章關聯檢索測試完成！")

    print("\n📊 功能摘要:")
    print("✅ 基本檢索: 快速，但可能丟失上下文")
    print("✅ 上下文擴展: 自動包含同篇文章的相關chunks")
    print("✅ 文章感知檢索: 優先返回完整文章，最佳上下文")
    print("✅ 完整文章檢索: 可重建原始文章內容")

    print("\n🚀 使用建議:")
    print("- 簡單事實查詢: 使用基本檢索")
    print("- 需要上下文理解: 使用上下文擴展檢索")
    print("- 複雜分析任務: 使用文章感知檢索")
    print("- 需要完整資訊: 使用完整文章檢索")


if __name__ == "__main__":
    asyncio.run(main())