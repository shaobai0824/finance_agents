"""
ETL 管理器 - 自動化爬蟲與向量化流程控制器

實作 Linus 哲學：
1. 簡潔執念：清晰的 ETL 流程，避免過度複雜
2. Never break userspace：穩定的處理流程，容錯機制
3. 實用主義：專注解決實際的知識庫更新需求
4. 好品味：統一的錯誤處理和監控
"""

import importlib
import logging
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
import asyncio
import sys
import os

# 添加專案路徑
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.main.python.rag import ChromaVectorStore
from .base_scraper import ScrapedArticle

logger = logging.getLogger(__name__)


class ETLManager:
    """ETL 流程管理器

    負責協調整個 Extract -> Transform -> Load 流程
    """

    def __init__(self, config: Dict[str, Any]):
        """初始化 ETL 管理器

        Args:
            config: ETL 設定字典
        """
        self.config = config
        self.vector_store = ChromaVectorStore()

        # ETL 設定
        self.chunk_size = config.get("chunk_size", 500)
        self.chunk_overlap = config.get("chunk_overlap", 50)
        self.batch_size = config.get("batch_size", 10)

        # 爬蟲設定
        self.sources = config.get("sources", [])
        self.max_articles_per_source = config.get("max_articles_per_source", 50)

        # 日誌設定
        self.logger = logging.getLogger("etl.manager")

        # 統計資訊
        self.stats = {
            "total_scraped": 0,
            "total_processed": 0,
            "total_loaded": 0,
            "failed_sources": [],
            "start_time": None,
            "end_time": None
        }

    async def run_full_etl(self) -> Dict[str, Any]:
        """執行完整的 ETL 流程

        Returns:
            執行結果統計
        """
        self.logger.info("🚀 開始執行完整 ETL 流程")
        self.stats["start_time"] = datetime.now()

        try:
            # 逐一處理每個資料來源
            for source_config in self.sources:
                if not source_config.get("enabled", True):
                    self.logger.info(f"⏭️  跳過已停用的資料來源: {source_config.get('name')}")
                    continue

                await self._process_single_source(source_config)

            self.stats["end_time"] = datetime.now()
            duration = self.stats["end_time"] - self.stats["start_time"]

            self.logger.info(f"🎉 ETL 流程完成")
            self.logger.info(f"📊 執行統計:")
            self.logger.info(f"   爬取文章: {self.stats['total_scraped']}")
            self.logger.info(f"   處理文檔: {self.stats['total_processed']}")
            self.logger.info(f"   載入向量: {self.stats['total_loaded']}")
            self.logger.info(f"   執行時間: {duration}")

            return self.stats

        except Exception as e:
            self.logger.error(f"❌ ETL 流程執行失敗: {e}", exc_info=True)
            raise

    async def _process_single_source(self, source_config: Dict[str, Any]):
        """處理單一資料來源

        Args:
            source_config: 資料來源設定
        """
        source_name = source_config.get("name", "Unknown")
        self.logger.info(f"🔄 處理資料來源: {source_name}")

        try:
            # Step 1: 擷取 (Extract)
            articles = await self._extract_data(source_config)
            if not articles:
                self.logger.warning(f"⚠️  資料來源 {source_name} 沒有爬取到任何文章")
                return

            self.stats["total_scraped"] += len(articles)
            self.logger.info(f"📥 成功爬取 {len(articles)} 篇文章")

            # Step 2: 轉換 (Transform)
            processed_chunks = await self._transform_data(articles)
            if not processed_chunks:
                self.logger.warning(f"⚠️  資料來源 {source_name} 沒有處理出任何文檔塊")
                return

            self.stats["total_processed"] += len(processed_chunks)
            self.logger.info(f"🔧 成功處理 {len(processed_chunks)} 個文檔塊")

            # Step 3: 載入 (Load)
            loaded_count = await self._load_data(processed_chunks, source_config)
            self.stats["total_loaded"] += loaded_count
            self.logger.info(f"📤 成功載入 {loaded_count} 個向量到資料庫")

        except Exception as e:
            self.logger.error(f"❌ 處理資料來源 {source_name} 失敗: {e}", exc_info=True)
            self.stats["failed_sources"].append({
                "name": source_name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })

    async def _extract_data(self, source_config: Dict[str, Any]) -> List[ScrapedArticle]:
        """擷取資料 (Extract 階段)

        Args:
            source_config: 資料來源設定

        Returns:
            爬取到的文章清單
        """
        module_name = source_config.get("module")
        if not module_name:
            raise ValueError("資料來源設定缺少 module 欄位")

        try:
            # 動態載入爬蟲模組
            scraper_module = importlib.import_module(module_name)

            # 呼叫爬蟲的 scrape 函數
            if hasattr(scraper_module, 'scrape'):
                raw_results = scraper_module.scrape(source_config)

                # 轉換為 ScrapedArticle 物件
                articles = []
                for result in raw_results[:self.max_articles_per_source]:
                    if isinstance(result, dict):
                        article = self._dict_to_article(result)
                        if article:
                            articles.append(article)

                return articles

            else:
                raise ImportError(f"爬蟲模組 {module_name} 沒有 scrape 函數")

        except ImportError as e:
            self.logger.error(f"無法載入爬蟲模組 {module_name}: {e}")
            raise

    def _dict_to_article(self, data: Dict[str, Any]) -> Optional[ScrapedArticle]:
        """將字典轉換為 ScrapedArticle 物件"""
        try:
            # 解析發布日期
            publish_date = None
            if data.get("publish_date"):
                if isinstance(data["publish_date"], str):
                    try:
                        publish_date = datetime.fromisoformat(data["publish_date"])
                    except ValueError:
                        pass
                elif isinstance(data["publish_date"], datetime):
                    publish_date = data["publish_date"]

            return ScrapedArticle(
                title=data.get("title", ""),
                content=data.get("content", ""),
                url=data.get("url", ""),
                publish_date=publish_date,
                author=data.get("author"),
                tags=data.get("tags", []),
                source_website=data.get("source_website", ""),
                expert_domain=data.get("expert_domain", "")
            )

        except Exception as e:
            self.logger.warning(f"轉換文章資料失敗: {e}")
            return None

    async def _transform_data(self, articles: List[ScrapedArticle]) -> List[Dict[str, Any]]:
        """轉換資料 (Transform 階段)

        Args:
            articles: 爬取到的文章清單

        Returns:
            處理後的文檔塊清單
        """
        processed_chunks = []

        for article in articles:
            try:
                # 文字分塊
                chunks = self._split_text(article.content)

                for i, chunk_text in enumerate(chunks):
                    if len(chunk_text.strip()) < 50:  # 過濾太短的文檔塊
                        continue

                    # 生成唯一 ID
                    chunk_id = self._generate_chunk_id(article.url, i)

                    chunk_data = {
                        "_id": chunk_id,
                        "content": chunk_text.strip(),
                        "metadata": {
                            "source_url": article.url,
                            "title": article.title,
                            "author": article.author,
                            "publish_date": article.publish_date.isoformat() if article.publish_date else None,
                            "source_website": article.source_website,
                            "expert_domain": article.expert_domain,
                            "tags": article.tags,
                            "chunk_index": i,
                            "total_chunks": len(chunks),
                            "processed_at": datetime.now().isoformat()
                        }
                    }

                    processed_chunks.append(chunk_data)

            except Exception as e:
                self.logger.warning(f"處理文章失敗 {article.url}: {e}")

        return processed_chunks

    def _split_text(self, text: str) -> List[str]:
        """分割文字為較小的文檔塊

        Args:
            text: 原始文字

        Returns:
            分割後的文字清單
        """
        if not text:
            return []

        # 簡單的分塊策略：按段落和長度分割
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            # 如果當前塊加上新段落不會超過限制，就合併
            if len(current_chunk) + len(paragraph) + 2 <= self.chunk_size:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
            else:
                # 當前塊已滿，保存並開始新塊
                if current_chunk:
                    chunks.append(current_chunk)

                # 如果單個段落太長，需要進一步分割
                if len(paragraph) > self.chunk_size:
                    sub_chunks = self._split_long_paragraph(paragraph)
                    chunks.extend(sub_chunks[:-1])  # 除了最後一個
                    current_chunk = sub_chunks[-1] if sub_chunks else ""
                else:
                    current_chunk = paragraph

        # 添加最後一個塊
        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def _split_long_paragraph(self, paragraph: str) -> List[str]:
        """分割過長的段落"""
        chunks = []
        words = paragraph.split()
        current_chunk = ""

        for word in words:
            if len(current_chunk) + len(word) + 1 <= self.chunk_size:
                if current_chunk:
                    current_chunk += " " + word
                else:
                    current_chunk = word
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = word

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def _generate_chunk_id(self, url: str, chunk_index: int) -> str:
        """生成文檔塊的唯一 ID

        Args:
            url: 原始文章 URL
            chunk_index: 文檔塊索引

        Returns:
            唯一 ID
        """
        content = f"{url}_{chunk_index}"
        hash_obj = hashlib.md5(content.encode())
        return f"chunk_{hash_obj.hexdigest()[:12]}"

    async def _load_data(self, chunks: List[Dict[str, Any]], source_config: Dict[str, Any]) -> int:
        """載入資料 (Load 階段)

        Args:
            chunks: 處理後的文檔塊清單
            source_config: 資料來源設定

        Returns:
            成功載入的文檔數量
        """
        if not chunks:
            return 0

        try:
            # 準備批次載入的文件和元資料
            documents = []
            metadatas = []
            ids = []

            for chunk in chunks:
                documents.append(chunk["content"])
                metadatas.append(chunk["metadata"])
                ids.append(chunk["_id"])

            # 批次載入到向量資料庫
            loaded_ids = self.vector_store.add_documents(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )

            return len(loaded_ids)

        except Exception as e:
            self.logger.error(f"載入資料到向量資料庫失敗: {e}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """取得 ETL 執行統計"""
        return self.stats.copy()

    async def test_single_source(self, source_name: str) -> Dict[str, Any]:
        """測試單一資料來源

        Args:
            source_name: 資料來源名稱

        Returns:
            測試結果
        """
        source_config = None
        for config in self.sources:
            if config.get("name") == source_name:
                source_config = config
                break

        if not source_config:
            raise ValueError(f"找不到資料來源: {source_name}")

        self.logger.info(f"🧪 測試資料來源: {source_name}")

        # 重置統計
        self.stats = {
            "total_scraped": 0,
            "total_processed": 0,
            "total_loaded": 0,
            "failed_sources": [],
            "start_time": datetime.now(),
            "end_time": None
        }

        await self._process_single_source(source_config)

        self.stats["end_time"] = datetime.now()
        return self.stats


# 獨立的 ETL 執行腳本函數
async def run_etl_from_config(config_path: str):
    """從設定檔執行 ETL 流程

    Args:
        config_path: 設定檔路徑
    """
    import yaml

    # 載入設定
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 建立 ETL 管理器
    etl_manager = ETLManager(config)

    # 執行 ETL 流程
    return await etl_manager.run_full_etl()


if __name__ == "__main__":
    # 測試用的簡單設定
    test_config = {
        "sources": [
            {
                "name": "全國法規資料庫測試",
                "module": "src.main.python.etl.scrapers.law_moj_scraper",
                "expert_domain": "legal_compliance",
                "enabled": True
            }
        ],
        "chunk_size": 500,
        "chunk_overlap": 50,
        "max_articles_per_source": 5
    }

    async def test_etl():
        etl_manager = ETLManager(test_config)
        stats = await etl_manager.test_single_source("全國法規資料庫測試")
        print(f"📊 測試結果: {stats}")

    # 執行測試
    asyncio.run(test_etl())