#!/usr/bin/env python3
"""
語意切割系統測試工具

驗證語意切割的效果，比較新舊切割方式的差異
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

from src.main.python.rag.semantic_chunking import SemanticChunker, ChunkingConfig
from src.main.python.rag.enhanced_vector_store import EnhancedVectorStore
from src.main.python.rag.chunking_config import ConfigManager, create_default_config_file


async def test_semantic_chunking_basic():
    """基礎語意切割測試"""
    print("=== 基礎語意切割測試 ===\n")

    # 測試文本（模擬財經新聞）
    test_text = """
    台積電公布第三季財報，營收達新台幣6,136億元，較前季成長14.6%，較去年同期成長16.9%。
    毛利率為54.3%，營業利益率為45.1%，稅後淨利為1,548億元，每股盈餘為5.97元。

    然而，法人分析師對於明年第一季的展望較為保守。
    主要關注點包括智慧型手機需求放緩、地緣政治風險持續，以及全球經濟成長趨緩的影響。

    技術面分析顯示，台積電股價在500元附近遇到阻力。
    成交量較前一個交易日減少15%，顯示投資人持觀望態度。
    若能突破510元關卡，下一個目標價位可能落在530元。

    此外，台積電宣布將在美國亞利桑那州興建第二座晶圓廠。
    預計2025年開始量產，初期月產能為2萬片12吋晶圓。
    這項投資將有助於台積電分散地緣政治風險，強化供應鏈彈性。
    """

    # 創建配置
    config = ChunkingConfig(
        min_chunk_size=150,
        max_chunk_size=500,
        target_chunk_size=300,
        similarity_threshold=0.7,
        boundary_confidence_threshold=0.5,
        enable_financial_optimization=True
    )

    # 初始化切割器
    chunker = SemanticChunker(config)

    try:
        print("執行語意切割...")
        start_time = time.time()
        chunks = await chunker.chunk_text(test_text)
        processing_time = time.time() - start_time

        print(f"切割完成，耗時: {processing_time:.2f}秒")
        print(f"總共產生 {len(chunks)} 個切割片段\n")

        # 分析切割結果
        for i, chunk in enumerate(chunks, 1):
            print(f"--- 片段 {i} ---")
            print(f"長度: {len(chunk.text)} 字符")
            print(f"句子數: {chunk.metadata.get('sentence_count', 'N/A')}")
            print(f"邊界信心度: {chunk.boundary_confidence:.3f}")
            print(f"語意一致性: {chunk.semantic_coherence:.3f}")
            print(f"重疊長度: {chunk.overlap_length}")
            print(f"內容預覽: {chunk.text[:100]}...")
            print()

        return chunks

    except Exception as e:
        print(f"測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return []


async def test_vs_legacy_chunking():
    """對比測試：語意切割 vs 傳統切割"""
    print("=== 語意切割 vs 傳統切割對比 ===\n")

    # 載入測試數據
    test_data_path = project_root / "data" / "real_cnyes_news_20250927_132114.json"

    if not test_data_path.exists():
        print(f"測試數據文件不存在: {test_data_path}")
        print("將使用模擬數據進行測試")

        test_articles = [
            "台積電第三季營收創新高，受惠於蘋果iPhone 15系列需求強勁。然而分析師擔心明年景氣不確定性。",
            "聯發科發布新一代5G晶片，效能提升30%。預計將搶攻中高階手機市場，與高通展開激烈競爭。",
            "央行宣布維持利率不變，符合市場預期。但暗示未來可能採取更積極的貨幣政策因應通膨壓力。"
        ]
    else:
        with open(test_data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        articles = data.get('articles', [])
        test_articles = [
            f"標題：{article.get('title', '')}\n內容：{article.get('content', '')}"
            for article in articles[:3]  # 測試前3篇
        ]

    print(f"測試 {len(test_articles)} 篇文章")

    # 語意切割測試
    print("\n1. 語意切割結果:")
    semantic_chunker = SemanticChunker(ChunkingConfig(
        min_chunk_size=200,
        max_chunk_size=600,
        enable_financial_optimization=True
    ))

    semantic_results = []
    semantic_total_time = 0

    for i, article in enumerate(test_articles, 1):
        print(f"\n文章 {i} (長度: {len(article)} 字符):")

        start_time = time.time()
        chunks = await semantic_chunker.chunk_text(article)
        processing_time = time.time() - start_time
        semantic_total_time += processing_time

        chunk_sizes = [len(chunk.text) for chunk in chunks]
        avg_coherence = sum(chunk.semantic_coherence for chunk in chunks) / len(chunks) if chunks else 0

        result = {
            'article_length': len(article),
            'chunk_count': len(chunks),
            'avg_chunk_size': sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0,
            'chunk_size_range': f"{min(chunk_sizes)}-{max(chunk_sizes)}" if chunk_sizes else "0-0",
            'avg_coherence': avg_coherence,
            'processing_time': processing_time
        }

        semantic_results.append(result)

        print(f"  切割片段數: {result['chunk_count']}")
        print(f"  平均片段大小: {result['avg_chunk_size']:.0f} 字符")
        print(f"  大小範圍: {result['chunk_size_range']}")
        print(f"  平均語意一致性: {result['avg_coherence']:.3f}")
        print(f"  處理時間: {result['processing_time']:.3f}秒")

    # 傳統切割測試（模擬）
    print("\n2. 傳統切割結果:")
    legacy_results = []

    for i, article in enumerate(test_articles, 1):
        print(f"\n文章 {i}:")

        # 簡單的固定大小切割
        chunk_size = 400
        chunks = []
        start = 0

        while start < len(article):
            end = min(start + chunk_size, len(article))
            # 尋找句號
            if end < len(article):
                for j in range(end, max(start + chunk_size // 2, start), -1):
                    if article[j] in '。！？':
                        end = j + 1
                        break
            chunks.append(article[start:end])
            start = end

        chunk_sizes = [len(chunk) for chunk in chunks]

        result = {
            'article_length': len(article),
            'chunk_count': len(chunks),
            'avg_chunk_size': sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0,
            'chunk_size_range': f"{min(chunk_sizes)}-{max(chunk_sizes)}" if chunk_sizes else "0-0"
        }

        legacy_results.append(result)

        print(f"  切割片段數: {result['chunk_count']}")
        print(f"  平均片段大小: {result['avg_chunk_size']:.0f} 字符")
        print(f"  大小範圍: {result['chunk_size_range']}")

    # 對比分析
    print("\n3. 對比分析:")
    print("=" * 50)

    semantic_avg_chunks = sum(r['chunk_count'] for r in semantic_results) / len(semantic_results)
    legacy_avg_chunks = sum(r['chunk_count'] for r in legacy_results) / len(legacy_results)

    semantic_avg_size = sum(r['avg_chunk_size'] for r in semantic_results) / len(semantic_results)
    legacy_avg_size = sum(r['avg_chunk_size'] for r in legacy_results) / len(legacy_results)

    semantic_avg_coherence = sum(r['avg_coherence'] for r in semantic_results) / len(semantic_results)

    print(f"平均切割片段數:")
    print(f"  語意切割: {semantic_avg_chunks:.1f}")
    print(f"  傳統切割: {legacy_avg_chunks:.1f}")
    print(f"  差異: {semantic_avg_chunks - legacy_avg_chunks:+.1f}")

    print(f"\n平均片段大小:")
    print(f"  語意切割: {semantic_avg_size:.0f} 字符")
    print(f"  傳統切割: {legacy_avg_size:.0f} 字符")
    print(f"  差異: {semantic_avg_size - legacy_avg_size:+.0f} 字符")

    print(f"\n語意一致性:")
    print(f"  語意切割: {semantic_avg_coherence:.3f}")
    print(f"  傳統切割: N/A")

    print(f"\n總處理時間:")
    print(f"  語意切割: {semantic_total_time:.3f}秒")
    print(f"  傳統切割: ~0.001秒 (估算)")

    improvement_ratio = (semantic_avg_coherence - 0.5) / 0.5 * 100 if semantic_avg_coherence > 0.5 else 0
    print(f"\n預估改善幅度: {improvement_ratio:.1f}%")


async def test_enhanced_vector_store():
    """測試增強型向量存儲"""
    print("\n=== 增強型向量存儲測試 ===\n")

    try:
        # 初始化增強型向量存儲
        enhanced_store = EnhancedVectorStore(
            collection_name="test_semantic_chunking",
            enable_semantic_chunking=True,
            fallback_to_legacy=True
        )

        print("增強型向量存儲初始化成功")

        # 測試文檔
        test_documents = [
            "台積電公布亮眼財報，營收創新高。但分析師對明年展望保守，擔心景氣不確定性影響。",
            "聯發科推出新晶片，效能大幅提升。預計將在5G手機市場與高通激烈競爭。"
        ]

        print(f"\n添加 {len(test_documents)} 個測試文檔...")

        # 使用語意切割添加文檔
        result = await enhanced_store.add_documents_with_semantic_chunking(
            test_documents,
            metadatas=[{"source": "test", "category": "financial_news"} for _ in test_documents]
        )

        print("添加結果:")
        print(f"  方法: {result['method']}")
        print(f"  總文檔數: {result['total_documents']}")
        print(f"  總切割片段數: {result['total_chunks']}")
        print(f"  平均每文檔片段數: {result['avg_chunks_per_document']:.1f}")
        print(f"  處理時間: {result['processing_time']:.3f}秒")

        if 'avg_chunk_size' in result:
            print(f"  平均片段大小: {result['avg_chunk_size']:.0f} 字符")
            print(f"  平均語意一致性: {result['avg_semantic_coherence']:.3f}")

        # 測試搜尋
        print("\n測試搜尋功能...")
        search_queries = ["台積電財報", "聯發科晶片", "市場競爭"]

        for query in search_queries:
            print(f"\n查詢: '{query}'")

            results = enhanced_store.search_with_metadata_filtering(
                query,
                n_results=3,
                chunking_method_filter="semantic",
                include_metadata=True
            )

            for i, result in enumerate(results, 1):
                print(f"  結果 {i}:")
                print(f"    相關性: {result['relevance_score']:.3f}")
                print(f"    切割方式: {result.get('chunking_method', 'N/A')}")
                print(f"    語意一致性: {result.get('semantic_coherence', 0):.3f}")
                print(f"    內容: {result['document'][:50]}...")

        # 性能統計
        print("\n性能統計:")
        stats = enhanced_store.get_performance_stats()
        for key, value in stats.items():
            if key != 'configuration_summary':
                print(f"  {key}: {value}")

    except Exception as e:
        print(f"增強型向量存儲測試失敗: {e}")
        import traceback
        traceback.print_exc()


async def test_configuration_system():
    """測試配置系統"""
    print("\n=== 配置系統測試 ===\n")

    # 創建預設配置檔案
    config_file = "test_semantic_chunking.yaml"
    create_default_config_file(config_file)
    print(f"創建預設配置檔案: {config_file}")

    # 測試配置載入
    config_manager = ConfigManager(config_file)
    config_summary = config_manager.get_summary()

    print("\n當前配置摘要:")
    for key, value in config_summary.items():
        print(f"  {key}: {value}")

    # 測試動態配置更新
    print("\n測試動態配置更新...")
    config_manager.update_config({
        'chunk_size': {
            'target_size': 600
        },
        'boundary': {
            'similarity_threshold': 0.8
        }
    })

    updated_summary = config_manager.get_summary()
    print("更新後配置:")
    print(f"  target_chunk_size: {updated_summary['target_chunk_size']}")
    print(f"  similarity_threshold: {updated_summary['similarity_threshold']}")

    # 清理測試檔案
    Path(config_file).unlink(missing_ok=True)
    print(f"\n清理測試檔案: {config_file}")


async def main():
    """主測試函數"""
    print("🔬 語意切割系統完整測試\n")
    print("=" * 60)

    test_functions = [
        ("基礎語意切割", test_semantic_chunking_basic),
        ("對比測試", test_vs_legacy_chunking),
        ("增強型向量存儲", test_enhanced_vector_store),
        ("配置系統", test_configuration_system)
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

    print("\n🎉 所有測試執行完成！")

    # 提供使用建議
    print("\n📝 使用建議:")
    print("1. 根據測試結果調整配置參數")
    print("2. 在生產環境使用前，建議進行更大規模的 A/B 測試")
    print("3. 監控語意一致性指標，確保切割品質")
    print("4. 定期檢查和更新財經關鍵詞列表")


if __name__ == "__main__":
    asyncio.run(main())