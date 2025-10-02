#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自動化新聞爬取與載入流程

完整流程：
1. 爬取鉅亨網新聞（台股、美股、科技、基金、外匯、期貨）
2. 檢查 ChromaDB 去重（基於 content_hash）
3. 使用最佳策略切塊
4. 載入向量資料庫
5. 支援定時排程

遵循 Linus 哲學：
- 簡潔：清晰的流程步驟
- 實用：解決實際的自動化需求
- 好品味：重用現有組件，避免重複
"""

import sys
import hashlib
import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime

# 添加專案路徑
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src" / "main" / "python"))

from dotenv import load_dotenv
load_dotenv()

from src.main.python.etl.scrapers.cnyes_auto_scraper import CnyesAutoScraper
from src.main.python.rag.chroma_vector_store import ChromaVectorStore

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


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
                # 單個句子太長，強制分割
                if len(sentence) > chunk_size:
                    chunks.append(sentence[:chunk_size])
                    current_chunk = sentence[chunk_size:]
                else:
                    current_chunk = sentence

    # 處理最後一個塊
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


def determine_chunk_type(chunk_index: int, total_chunks: int) -> str:
    """判斷 chunk 類型"""
    if chunk_index == 0:
        return "title_and_intro"  # 標題和開頭
    elif chunk_index == total_chunks - 1:
        return "conclusion"       # 結論
    else:
        return "content"          # 內容


def get_existing_hashes(vector_store: ChromaVectorStore) -> List[str]:
    """從向量資料庫獲取現有的 content_hash"""
    try:
        collection = vector_store.collection
        all_data = collection.get(include=["metadatas"])

        hashes = []
        for metadata in all_data['metadatas']:
            if 'content_hash' in metadata:
                hashes.append(metadata['content_hash'])

        logger.info(f"從資料庫載入 {len(hashes)} 個現有文章 hash")
        return hashes

    except Exception as e:
        logger.warning(f"獲取現有 hash 失敗: {e}")
        return []


def prepare_documents_and_metadata(
    articles: List[Dict[str, Any]]
) -> Tuple[List[str], List[Dict[str, Any]]]:
    """準備文檔和元數據（使用最佳切塊策略）"""

    documents = []
    metadatas = []

    for i, article in enumerate(articles, 1):
        title = article.get('title', '')
        content = article.get('content', '')
        category = ', '.join(article.get('tags', []))
        url = article.get('url', '')
        content_hash = article.get('content_hash', '')

        # 清理內容
        cleaned_content = content.replace('\u200c', '').replace('\n\n', '\n').strip()

        # 組合完整文檔
        full_text = f"標題：{title}\n分類：{category}\n內容：{cleaned_content}"

        # 使用最佳策略切塊
        chunks = optimal_chunk_text(full_text, chunk_size=400, overlap=50)

        logger.info(f"處理文章 {i}/{len(articles)}: {title[:50]}... (切分為 {len(chunks)} 個塊)")

        # 為每個 chunk 創建文檔和元數據
        for j, chunk in enumerate(chunks):
            documents.append(chunk)

            # 生成唯一 ID
            unique_id = hashlib.md5(
                f"{content_hash}_{j}_{chunk[:50]}".encode()
            ).hexdigest()[:12]

            # 為每個 chunk 準備元數據
            metadata = {
                "title": title,
                "category": category,
                "url": url,
                "source": article.get('source_website', 'cnyes.com'),
                "scrape_time": article.get('scraped_at', ''),
                "publish_date": article.get('publish_date', ''),
                "author": article.get('author', ''),
                "article_index": i,
                "chunk_index": j + 1,
                "total_chunks": len(chunks),
                "chunk_id": f"article_{i}_chunk_{j+1}",
                "unique_id": unique_id,
                "content_hash": content_hash,  # 保存原文 hash 用於去重
                "expert_domain": article.get('expert_domain', 'financial_analysis'),
                "chunk_type": determine_chunk_type(j, len(chunks)),
                "chunk_length": len(chunk),
                "strategy": "optimal_sentence_aware"
            }

            metadatas.append(metadata)

    logger.info(f"總共生成 {len(documents)} 個文檔塊")
    return documents, metadatas


def run_auto_scrape_and_load(
    articles_per_category: int = 20,
    collection_name: str = "finance_knowledge_optimal"
) -> Dict[str, Any]:
    """執行自動爬取和載入流程

    Args:
        articles_per_category: 每個分類爬取的文章數
        collection_name: 向量資料庫集合名稱

    Returns:
        執行結果統計
    """
    stats = {
        "scraped_count": 0,
        "duplicate_count": 0,
        "loaded_count": 0,
        "chunk_count": 0,
        "start_time": datetime.now().isoformat(),
        "end_time": None,
        "success": False,
        "error": None
    }

    try:
        logger.info("=" * 80)
        logger.info("開始自動化新聞爬取與載入流程")
        logger.info("=" * 80)

        # 1. 初始化向量資料庫
        logger.info("\n[1/5] 初始化向量資料庫...")
        vector_store = ChromaVectorStore(collection_name=collection_name)

        # 2. 獲取現有文章 hash（用於去重）
        logger.info("\n[2/5] 獲取現有文章 hash...")
        existing_hashes = get_existing_hashes(vector_store)

        # 3. 爬取新聞
        logger.info("\n[3/5] 爬取鉅亨網新聞...")

        scraper_config = {
            "name": "鉅亨網自動爬蟲",
            "articles_per_category": articles_per_category,
            "request_delay": (2, 4),
            "max_retries": 3,
            "selenium_browser": "chrome"
        }

        with CnyesAutoScraper(scraper_config) as scraper:
            # 設定現有 hash
            scraper.set_existing_hashes(existing_hashes)

            # 爬取文章
            articles = scraper.scrape()

            stats["scraped_count"] = len(articles)

            if not articles:
                logger.warning("未爬取到新文章")
                stats["end_time"] = datetime.now().isoformat()
                stats["success"] = True
                return stats

            logger.info(f"爬取到 {len(articles)} 篇新文章")

            # 轉換為字典格式
            articles_dict = [article.to_dict() for article in articles]

        # 4. 準備文檔和元數據
        logger.info("\n[4/5] 準備文檔和元數據...")
        documents, metadatas = prepare_documents_and_metadata(articles_dict)

        stats["chunk_count"] = len(documents)

        # 5. 批次載入到向量資料庫
        logger.info("\n[5/5] 載入到向量資料庫...")

        batch_size = 20
        total_added = 0

        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i:i + batch_size]
            batch_metas = metadatas[i:i + batch_size]

            # 使用唯一 ID
            batch_ids = [meta['unique_id'] for meta in batch_metas]

            logger.info(
                f"正在添加第 {i+1}-{min(i+batch_size, len(documents))} 個文檔塊..."
            )

            try:
                doc_ids = vector_store.add_documents(
                    batch_docs,
                    batch_metas,
                    batch_ids
                )
                total_added += len(doc_ids)
                logger.info(f"成功添加 {len(doc_ids)} 個文檔塊")
            except Exception as e:
                logger.error(f"批次添加失敗：{e}")
                continue

        stats["loaded_count"] = total_added

        # 檢查最終狀態
        final_info = vector_store.get_collection_info()

        logger.info("\n" + "=" * 80)
        logger.info("載入完成")
        logger.info("=" * 80)
        logger.info(f"爬取文章數：{stats['scraped_count']}")
        logger.info(f"生成文檔塊：{stats['chunk_count']}")
        logger.info(f"成功載入：{stats['loaded_count']}")
        logger.info(f"資料庫總文檔數：{final_info.get('document_count', 0)}")

        stats["success"] = True

    except Exception as e:
        logger.error(f"執行流程發生錯誤：{e}")
        import traceback
        traceback.print_exc()
        stats["error"] = str(e)

    finally:
        stats["end_time"] = datetime.now().isoformat()

    return stats


if __name__ == "__main__":
    # 執行自動化流程
    result = run_auto_scrape_and_load(
        articles_per_category=10,  # 每個分類爬10篇（測試用）
        collection_name="finance_knowledge_optimal"
    )

    print("\n" + "=" * 80)
    print("執行結果統計")
    print("=" * 80)
    for key, value in result.items():
        print(f"{key}: {value}")
