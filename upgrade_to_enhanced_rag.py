#!/usr/bin/env python3
"""
RAG系統升級腳本

從傳統RAG升級到文章感知RAG：
1. 清空舊的向量資料庫
2. 使用語意切割重新載入財經新聞
3. 提供升級驗證
"""

import asyncio
import json
import sys
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
from src.main.python.rag.chroma_vector_store import ChromaVectorStore


class RAGUpgrader:
    """RAG系統升級器"""

    def __init__(self):
        self.old_collection = "finance_knowledge_optimal"
        self.new_collection = "finance_knowledge_enhanced"

    async def backup_and_clear_old_data(self):
        """備份並清空舊資料"""
        print("=== 清理舊資料 ===")

        try:
            # 檢查舊集合
            old_store = ChromaVectorStore(collection_name=self.old_collection)
            old_count = old_store.collection.count()
            print(f"舊集合文檔數：{old_count}")

            # 清空新集合（如果存在）
            try:
                new_store = EnhancedVectorStore(collection_name=self.new_collection)
                new_store.collection.delete()
                print(f"已清空新集合：{self.new_collection}")
            except Exception as e:
                print(f"新集合不存在或清空失敗：{e}")

            return old_count

        except Exception as e:
            print(f"清理過程出現錯誤：{e}")
            return 0

    async def load_cnyes_data_with_semantic_chunking(self):
        """使用語意切割載入cnyes新聞資料"""
        print("\n=== 使用語意切割載入新聞資料 ===")

        # 初始化增強型向量存儲
        enhanced_store = EnhancedVectorStore(
            collection_name=self.new_collection,
            enable_semantic_chunking=True,
            fallback_to_legacy=False
        )

        # 載入原始新聞資料
        data_file = project_root / "data" / "real_cnyes_news_20250927_132114.json"

        if not data_file.exists():
            raise FileNotFoundError(f"找不到資料檔案：{data_file}")

        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        articles = data.get('articles', [])
        print(f"找到 {len(articles)} 篇文章")

        # 處理文章
        documents = []
        metadatas = []

        for i, article in enumerate(articles):
            title = article.get('title', '')
            content = article.get('content', '')
            url = article.get('url', '')
            category = article.get('category', '財經')

            # 合併標題和內容
            full_text = f"標題：{title}\n內容：{content}"

            # 創建豐富的元數據
            metadata = {
                'original_document_id': f"cnyes_article_{i+1}",
                'title': title,
                'url': url,
                'category': category,
                'source': 'cnyes.com',
                'article_index': i + 1,
                'scrape_time': data.get('scrape_time', ''),
                'expert_domain': 'financial_analysis'
            }

            documents.append(full_text)
            metadatas.append(metadata)

        print(f"準備載入 {len(documents)} 篇文章...")

        # 使用語意切割載入
        start_time = time.time()
        result = await enhanced_store.add_documents_with_semantic_chunking(
            documents,
            metadatas=metadatas
        )

        load_time = time.time() - start_time

        print(f"載入完成！")
        print(f"處理時間：{load_time:.2f}秒")
        print(f"切割方法：{result['method']}")
        print(f"總文檔數：{result['total_documents']}")
        print(f"總切割片段數：{result['total_chunks']}")
        print(f"平均每文檔片段數：{result['avg_chunks_per_document']:.1f}")

        if 'avg_chunk_size' in result:
            print(f"平均片段大小：{result['avg_chunk_size']:.0f} 字符")
            print(f"平均語意一致性：{result['avg_semantic_coherence']:.3f}")

        return result

    async def verify_upgrade(self):
        """驗證升級效果"""
        print("\n=== 驗證升級效果 ===")

        enhanced_store = EnhancedVectorStore(collection_name=self.new_collection)

        # 檢查數據載入
        document_count = enhanced_store.collection.count()
        print(f"新集合文檔總數：{document_count}")

        # 測試文章感知搜索
        test_queries = [
            "台積電財報分析",
            "聯發科市場競爭",
            "投資風險評估"
        ]

        print("\n測試文章感知搜索：")
        for query in test_queries:
            print(f"\n查詢：{query}")

            # 傳統搜索
            basic_results = enhanced_store.search_similar_documents(query, n_results=1)
            basic_length = len(basic_results[0]['document']) if basic_results else 0

            # 文章感知搜索
            context_results = enhanced_store.search_with_context_expansion(
                query,
                n_results=1,
                include_article_context=True,
                max_context_chunks=3
            )

            context_length = 0
            chunk_count = 0
            if context_results:
                context_length += len(context_results[0]['document'])
                chunk_count += 1

                if 'context_chunks' in context_results[0]:
                    for ctx_chunk in context_results[0]['context_chunks']:
                        context_length += len(ctx_chunk['document'])
                        chunk_count += 1

            print(f"  傳統搜索：{basic_length} 字符")
            print(f"  文章感知：{context_length} 字符 ({chunk_count} 片段)")
            if basic_length > 0:
                improvement = ((context_length / basic_length) - 1) * 100
                print(f"  改善幅度：{improvement:.1f}%")

    async def run_upgrade(self):
        """執行完整升級流程"""
        print("🚀 RAG系統升級開始")
        print("=" * 50)

        start_time = time.time()

        try:
            # 1. 備份和清理
            old_count = await self.backup_and_clear_old_data()

            # 2. 重新載入
            result = await self.load_cnyes_data_with_semantic_chunking()

            # 3. 驗證
            await self.verify_upgrade()

            total_time = time.time() - start_time

            # 4. 總結
            print("\n" + "=" * 50)
            print("🎉 升級完成總結")
            print("=" * 50)
            print(f"舊系統文檔數：{old_count}")
            print(f"新系統切割片段數：{result['total_chunks']}")
            print(f"切割方法：{result['method']}")
            print(f"總升級時間：{total_time:.2f}秒")

            if 'avg_semantic_coherence' in result:
                print(f"平均語意一致性：{result['avg_semantic_coherence']:.3f}")

            print("\n✅ 系統已成功升級到文章感知RAG")
            print("💡 重新啟動API服務以使用新系統")

        except Exception as e:
            print(f"\n❌ 升級失敗：{e}")
            import traceback
            traceback.print_exc()


async def main():
    """主函數"""
    upgrader = RAGUpgrader()
    await upgrader.run_upgrade()


if __name__ == "__main__":
    asyncio.run(main())