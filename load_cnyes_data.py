#!/usr/bin/env python3
"""
載入 cnyes 新聞數據到 RAG 向量資料庫
"""

import json
import sys
import asyncio
from pathlib import Path
from typing import List, Dict, Any

# 添加專案路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src" / "main" / "python"))

from dotenv import load_dotenv
load_dotenv()

from src.main.python.rag.chroma_vector_store import ChromaVectorStore

def load_cnyes_news(file_path: str) -> tuple[List[str], List[Dict[str, Any]]]:
    """載入 cnyes 新聞數據

    Args:
        file_path: JSON 文件路徑

    Returns:
        tuple: (documents, metadatas)
    """
    print(f"正在載入新聞數據: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    documents = []
    metadatas = []

    articles = data.get('articles', [])
    source_metadata = data.get('metadata', {})

    print(f"找到 {len(articles)} 篇文章")

    for i, article in enumerate(articles, 1):
        # 準備文檔內容
        title = article.get('title', '')
        content = article.get('content', '')
        category = article.get('category', '未分類')
        url = article.get('url', '')

        # 清理內容（移除過多的特殊字符和重複內容）
        cleaned_content = content.replace('‌', '').replace('\n\n', '\n').strip()

        # 組合完整文檔
        full_document = f"標題：{title}\n分類：{category}\n內容：{cleaned_content}"

        # 如果文檔太長，截取前 2000 字符
        if len(full_document) > 2000:
            full_document = full_document[:2000] + "..."

        documents.append(full_document)

        # 準備元數據
        metadata = {
            "title": title,
            "category": category,
            "url": url,
            "source": source_metadata.get('source', 'cnyes.com'),
            "scrape_time": source_metadata.get('scrape_time', ''),
            "article_index": i,
            "expert_domain": _determine_expert_domain(category, title, content)
        }

        metadatas.append(metadata)

        print(f"處理文章 {i}/{len(articles)}: {title[:50]}...")

    return documents, metadatas

def _determine_expert_domain(category: str, title: str, content: str) -> str:
    """根據文章內容判斷適合的專家領域"""
    content_lower = (title + " " + content + " " + category).lower()

    # 理財規劃關鍵字
    financial_planning_keywords = ["投資", "理財", "基金", "保險", "資產配置", "退休", "儲蓄"]

    # 金融分析關鍵字
    financial_analysis_keywords = ["股票", "股市", "台股", "美股", "市場", "分析", "漲跌", "技術分析"]

    # 法律專家關鍵字
    legal_keywords = ["法規", "稅務", "法律", "合規", "政策", "監管"]

    # 計算匹配分數
    planning_score = sum(1 for keyword in financial_planning_keywords if keyword in content_lower)
    analysis_score = sum(1 for keyword in financial_analysis_keywords if keyword in content_lower)
    legal_score = sum(1 for keyword in legal_keywords if keyword in content_lower)

    # 判斷主要領域
    if analysis_score >= planning_score and analysis_score >= legal_score:
        return "financial_analysis"
    elif legal_score > planning_score and legal_score > analysis_score:
        return "legal_expert"
    else:
        return "financial_planning"

async def main():
    """主函數"""
    try:
        # 檢查文件是否存在
        news_file = project_root / "data" / "real_cnyes_news_20250927_132114.json"
        if not news_file.exists():
            print(f"錯誤：找不到新聞文件 {news_file}")
            return

        print("=== cnyes 新聞數據載入工具 ===")

        # 載入新聞數據
        documents, metadatas = load_cnyes_news(str(news_file))

        if not documents:
            print("錯誤：沒有找到文檔數據")
            return

        print(f"準備載入 {len(documents)} 篇文檔")

        # 初始化向量存儲
        print("初始化 ChromaDB 向量存儲...")
        vector_store = ChromaVectorStore()

        # 檢查當前集合狀態
        current_info = vector_store.get_collection_info()
        print(f"當前集合狀態：{current_info}")

        # 批次添加文檔（每次 10 篇）
        batch_size = 10
        total_added = 0

        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i:i + batch_size]
            batch_metas = metadatas[i:i + batch_size]

            print(f"正在添加第 {i+1}-{min(i+batch_size, len(documents))} 篇文檔...")

            try:
                doc_ids = vector_store.add_documents(batch_docs, batch_metas)
                total_added += len(doc_ids)
                print(f"成功添加 {len(doc_ids)} 篇文檔")
            except Exception as e:
                print(f"批次添加失敗：{e}")
                continue

        # 檢查最終狀態
        final_info = vector_store.get_collection_info()
        print(f"\n=== 載入完成 ===")
        print(f"總共添加：{total_added} 篇文檔")
        print(f"最終集合狀態：{final_info}")

        # 進行簡單測試
        print("\n=== 測試檢索功能 ===")
        test_queries = ["小米投資", "股票市場", "台股分析"]

        for query in test_queries:
            print(f"測試查詢：{query}")
            results = vector_store.similarity_search(query, k=2)
            print(f"找到 {len(results)} 個相關結果")
            if results:
                print(f"最相關：{results[0][:100]}...")
            print()

    except Exception as e:
        print(f"載入過程發生錯誤：{e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())