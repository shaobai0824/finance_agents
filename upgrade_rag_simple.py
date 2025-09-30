#!/usr/bin/env python3
"""
RAG系統升級腳本 - 簡化版

從傳統RAG升級到文章感知RAG
"""

import asyncio
import json
import sys
import time
from pathlib import Path

# 添加專案路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src" / "main" / "python"))

from dotenv import load_dotenv
load_dotenv()

from src.main.python.rag.enhanced_vector_store import EnhancedVectorStore
from src.main.python.rag.chroma_vector_store import ChromaVectorStore


async def main():
    """主升級函數"""
    print("RAG系統升級開始")
    print("=" * 40)

    # 初始化新的增強型向量存儲
    print("初始化增強型向量存儲...")
    enhanced_store = EnhancedVectorStore(
        collection_name="finance_knowledge_enhanced",
        enable_semantic_chunking=True,
        fallback_to_legacy=False
    )

    # 清空集合
    try:
        enhanced_store.collection.delete()
        print("已清空舊資料")
    except:
        print("建立新集合")

    # 重新初始化
    enhanced_store = EnhancedVectorStore(
        collection_name="finance_knowledge_enhanced",
        enable_semantic_chunking=True,
        fallback_to_legacy=False
    )

    # 載入資料
    print("載入財經新聞資料...")
    data_file = project_root / "data" / "real_cnyes_news_20250927_132114.json"

    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    articles = data.get('articles', [])
    print(f"找到 {len(articles)} 篇文章")

    # 準備文檔
    documents = []
    metadatas = []

    for i, article in enumerate(articles):
        title = article.get('title', '')
        content = article.get('content', '')
        url = article.get('url', '')
        category = article.get('category', '財經')

        full_text = f"標題：{title}\n內容：{content}"

        metadata = {
            'original_document_id': f"cnyes_article_{i+1}",
            'title': title,
            'url': url,
            'category': category,
            'source': 'cnyes.com',
            'article_index': i + 1,
            'expert_domain': 'financial_analysis'
        }

        documents.append(full_text)
        metadatas.append(metadata)

    print(f"開始語意切割處理...")
    start_time = time.time()

    # 使用語意切割載入
    result = await enhanced_store.add_documents_with_semantic_chunking(
        documents,
        metadatas=metadatas
    )

    load_time = time.time() - start_time

    print("載入完成！")
    print(f"處理時間：{load_time:.2f}秒")
    print(f"切割方法：{result['method']}")
    print(f"總文檔數：{result['total_documents']}")
    print(f"總切割片段數：{result['total_chunks']}")
    print(f"平均每文檔片段數：{result['avg_chunks_per_document']:.1f}")

    if result.get('avg_chunk_size'):
        print(f"平均片段大小：{result['avg_chunk_size']:.0f} 字符")
    if result.get('avg_semantic_coherence'):
        print(f"平均語意一致性：{result['avg_semantic_coherence']:.3f}")

    # 簡單驗證
    print("\n驗證升級效果...")
    document_count = enhanced_store.collection.count()
    print(f"新集合文檔總數：{document_count}")

    # 測試搜索
    test_query = "台積電財報"
    print(f"\n測試查詢：{test_query}")

    context_results = enhanced_store.search_with_context_expansion(
        test_query,
        n_results=1,
        include_article_context=True
    )

    if context_results:
        result = context_results[0]
        total_length = len(result['document'])
        chunk_count = 1

        print(f"主要片段：{len(result['document'])} 字符")

        if 'context_chunks' in result:
            for ctx in result['context_chunks']:
                total_length += len(ctx['document'])
                chunk_count += 1
            print(f"上下文片段：{len(result['context_chunks'])} 個")

        print(f"總回應長度：{total_length} 字符")
        print(f"總片段數：{chunk_count}")

    print("\n" + "=" * 40)
    print("升級完成！")
    print("系統已成功升級到文章感知RAG")
    print("請重新啟動API服務以使用新系統")


if __name__ == "__main__":
    asyncio.run(main())