#!/usr/bin/env python3
"""
載入 cnyes 新聞數據到 RAG 向量資料庫 (最佳策略版)
使用句子感知切塊，確保最佳檢索效果
"""

import json
import sys
import asyncio
import re
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Tuple

# 添加專案路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src" / "main" / "python"))

from dotenv import load_dotenv
load_dotenv()

from src.main.python.rag.chroma_vector_store import ChromaVectorStore

def optimal_chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
    """最佳句子感知切塊策略

    特點：
    - 在句號處分割，保持語義完整
    - 適度重疊，保持上下文連貫
    - 目標大小400字符，檢索效果最佳
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    # 使用中文標點符號分割句子
    sentences = re.split(r'[。！？]', text)

    current_chunk = ""
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        # 恢復標點符號
        sentence += "。"

        # 檢查是否可以加入當前塊
        if len(current_chunk + sentence) <= chunk_size:
            current_chunk += sentence
        else:
            # 當前塊已滿，保存並開始新塊
            if current_chunk:
                chunks.append(current_chunk.strip())

                # 重疊處理：保持上下文連貫性
                if overlap > 0 and len(current_chunk) > overlap:
                    overlap_text = current_chunk[-overlap:]
                    # 找到最近的句子邊界開始重疊
                    last_period = overlap_text.rfind('。')
                    if last_period > 0:
                        overlap_text = overlap_text[last_period + 1:]
                    current_chunk = overlap_text + sentence
                else:
                    current_chunk = sentence
            else:
                # 單個句子太長，強制分割（保留重要部分）
                if len(sentence) > chunk_size:
                    chunks.append(sentence[:chunk_size])
                    current_chunk = sentence[chunk_size:]
                else:
                    current_chunk = sentence

    # 處理最後一個塊
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks

def load_cnyes_news_optimal(file_path: str) -> Tuple[List[str], List[Dict[str, Any]]]:
    """使用最佳策略載入 cnyes 新聞數據"""

    print(f"正在使用最佳策略載入新聞數據: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    documents = []
    metadatas = []

    articles = data.get('articles', [])
    source_metadata = data.get('metadata', {})

    print(f"找到 {len(articles)} 篇文章")

    for i, article in enumerate(articles, 1):
        title = article.get('title', '')
        content = article.get('content', '')
        category = article.get('category', '未分類')
        url = article.get('url', '')

        # 清理內容（移除特殊字符）
        cleaned_content = content.replace('\u200c', '').replace('\n\n', '\n').strip()

        # 組合完整文檔
        full_text = f"標題：{title}\n分類：{category}\n內容：{cleaned_content}"

        # 使用最佳策略切塊
        chunks = optimal_chunk_text(full_text, chunk_size=400, overlap=50)

        print(f"處理文章 {i}/{len(articles)}: {title[:50]}... (切分為 {len(chunks)} 個塊)")

        # 為每個 chunk 創建文檔和元數據
        for j, chunk in enumerate(chunks):
            documents.append(chunk)

            # 生成唯一 ID
            unique_id = hashlib.md5(f"{i}_{j}_{chunk[:50]}".encode()).hexdigest()[:12]

            # 為每個 chunk 準備元數據
            metadata = {
                "title": title,
                "category": category,
                "url": url,
                "source": source_metadata.get('source', 'cnyes.com'),
                "scrape_time": source_metadata.get('scrape_time', ''),
                "article_index": i,
                "chunk_index": j + 1,
                "total_chunks": len(chunks),
                "chunk_id": f"article_{i}_chunk_{j+1}",
                "unique_id": unique_id,
                "expert_domain": _determine_expert_domain(category, title, content),
                "chunk_type": _determine_chunk_type(chunk, j, len(chunks)),
                "chunk_length": len(chunk),
                "strategy": "optimal_sentence_aware"
            }

            metadatas.append(metadata)

    print(f"總共生成 {len(documents)} 個高質量文檔塊")
    return documents, metadatas

def _determine_chunk_type(chunk: str, chunk_index: int, total_chunks: int) -> str:
    """判斷 chunk 類型"""
    if chunk_index == 0:
        return "title_and_intro"  # 標題和開頭
    elif chunk_index == total_chunks - 1:
        return "conclusion"       # 結論
    else:
        return "content"          # 內容

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

        print("=== cnyes 新聞數據載入工具 (最佳策略版) ===")

        # 載入新聞數據並使用最佳策略切塊
        documents, metadatas = load_cnyes_news_optimal(str(news_file))

        if not documents:
            print("錯誤：沒有找到文檔數據")
            return

        print(f"準備載入 {len(documents)} 個高質量文檔塊")

        # 初始化向量存儲
        print("初始化 ChromaDB 向量存儲 (最佳策略版)...")
        vector_store = ChromaVectorStore(collection_name="finance_knowledge_optimal")

        # 清空現有集合
        print("清空現有集合...")
        vector_store.clear_collection()

        # 檢查當前集合狀態
        current_info = vector_store.get_collection_info()
        print(f"當前集合狀態：{current_info}")

        # 批次添加文檔（使用自定義 ID）
        batch_size = 20
        total_added = 0

        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i:i + batch_size]
            batch_metas = metadatas[i:i + batch_size]

            # 使用唯一 ID
            batch_ids = [meta['unique_id'] for meta in batch_metas]

            print(f"正在添加第 {i+1}-{min(i+batch_size, len(documents))} 個文檔塊...")

            try:
                doc_ids = vector_store.add_documents(batch_docs, batch_metas, batch_ids)
                total_added += len(doc_ids)
                print(f"成功添加 {len(doc_ids)} 個文檔塊")
            except Exception as e:
                print(f"批次添加失敗：{e}")
                continue

        # 檢查最終狀態
        final_info = vector_store.get_collection_info()
        print(f"\n=== 載入完成 ===")
        print(f"總共添加：{total_added} 個高質量文檔塊")
        print(f"最終集合狀態：{final_info}")

        # 進行高質量檢索測試
        print("\n=== 高質量檢索測試 ===")
        test_queries = [
            "小米投資建議",
            "台股指數分析",
            "科技股市場前景",
            "鈺創公司投資價值"
        ]

        for query in test_queries:
            print(f"\n測試查詢：{query}")
            results = vector_store.similarity_search(query, k=3)
            print(f"找到 {len(results)} 個高度相關結果")

            for i, result in enumerate(results, 1):
                # 只顯示前100字符避免輸出過長
                preview = result[:100] + "..." if len(result) > 100 else result
                print(f"  結果 {i}: {preview}")

        # 統計切塊品質
        print("\n=== 切塊品質統計 ===")
        chunk_lengths = [meta['chunk_length'] for meta in metadatas]
        print(f"平均塊長度: {sum(chunk_lengths) / len(chunk_lengths):.1f} 字符")
        print(f"長度範圍: {min(chunk_lengths)}-{max(chunk_lengths)} 字符")

        domain_stats = {}
        for meta in metadatas:
            domain = meta['expert_domain']
            domain_stats[domain] = domain_stats.get(domain, 0) + 1

        print("專家領域分布:")
        for domain, count in domain_stats.items():
            print(f"  {domain}: {count} 個塊")

    except Exception as e:
        print(f"載入過程發生錯誤：{e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())