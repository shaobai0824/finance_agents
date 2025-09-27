"""
財經新聞資料匯入向量資料庫系統

實作 Linus 哲學：
1. 簡潔執念：專門處理財經新聞的向量化匯入
2. 實用主義：支援多種資料來源和格式
3. 好品味：智能化的文章分類和標籤
4. Never break userspace：穩定的向量檢索接口
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..rag import ChromaVectorStore, KnowledgeRetriever
from .cnyes_financial_scraper import CnyesFinancialScraper, FinancialArticle

logger = logging.getLogger(__name__)


class FinancialNewsProcessor:
    """財經新聞處理器"""

    def __init__(self, vector_store: ChromaVectorStore = None):
        self.vector_store = vector_store if vector_store else ChromaVectorStore()
        self.knowledge_retriever = KnowledgeRetriever(self.vector_store)

        # 財經新聞集合名稱
        self.collection_name = "financial_news"

        # 專家領域映射
        self.expert_domain_mapping = {
            "financial_analysis": ["台股", "美股", "外匯", "國際股市", "市場分析"],
            "financial_planning": ["基金", "理財", "債券", "保險", "退休規劃"],
            "legal_compliance": ["法規", "合規", "稅務", "政策", "監管"]
        }

    async def process_cnyes_scraping(self, max_articles_per_category: int = 20) -> int:
        """執行鉅亨網爬取並處理"""
        logger.info("開始執行鉅亨網新聞爬取...")

        try:
            # 執行爬蟲
            async with CnyesFinancialScraper() as scraper:
                articles = await scraper.scrape_financial_news(max_articles_per_category)

            if not articles:
                logger.warning("未爬取到任何文章")
                return 0

            # 儲存為JSON
            json_file = self._save_articles_to_json(articles)
            logger.info(f"文章已儲存至JSON: {json_file}")

            # 載入到向量資料庫
            loaded_count = await self.ingest_articles_to_vector_store(articles)

            logger.info(f"成功處理 {len(articles)} 篇文章，載入 {loaded_count} 篇到向量資料庫")
            return loaded_count

        except Exception as e:
            logger.error(f"處理鉅亨網新聞失敗: {e}")
            raise

    async def ingest_json_file(self, json_file_path: str) -> int:
        """從JSON檔案載入新聞到向量資料庫"""
        logger.info(f"從JSON檔案載入新聞: {json_file_path}")

        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            articles = []
            for article_data in data.get("articles", []):
                article = FinancialArticle(**article_data)
                articles.append(article)

            return await self.ingest_articles_to_vector_store(articles)

        except Exception as e:
            logger.error(f"從JSON載入失敗: {e}")
            raise

    async def ingest_articles_to_vector_store(self, articles: List[FinancialArticle]) -> int:
        """將文章載入向量資料庫"""
        logger.info(f"開始載入 {len(articles)} 篇文章到向量資料庫...")

        try:
            # 檢查並準備集合
            await self._prepare_collection()

            # 準備文件資料
            documents = []
            for i, article in enumerate(articles):
                # 增強文章內容
                enhanced_article = self._enhance_article(article)

                # 轉換為向量格式
                vector_doc = enhanced_article.to_vector_format()

                # 添加唯一ID
                doc_id = f"cnyes_{datetime.now().strftime('%Y%m%d')}_{i:04d}"

                documents.append({
                    "id": doc_id,
                    "content": vector_doc["content"],
                    "metadata": vector_doc["metadata"],
                    "source": vector_doc["source"]
                })

            # 批次載入
            batch_size = 20
            total_loaded = 0

            collection = self.vector_store.client.get_collection(self.collection_name)

            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]

                # 準備批次資料
                batch_ids = [doc["id"] for doc in batch]
                batch_contents = [doc["content"] for doc in batch]
                batch_metadatas = [doc["metadata"] for doc in batch]

                # 載入到向量資料庫
                collection.add(
                    ids=batch_ids,
                    documents=batch_contents,
                    metadatas=batch_metadatas
                )

                total_loaded += len(batch)
                logger.info(f"已載入 {total_loaded}/{len(documents)} 篇文章")

                # 避免過於頻繁的操作
                await asyncio.sleep(0.5)

            logger.info(f"財經新聞載入完成！總共載入 {total_loaded} 篇文章")
            return total_loaded

        except Exception as e:
            logger.error(f"載入向量資料庫失敗: {e}")
            raise

    async def _prepare_collection(self):
        """準備向量資料庫集合"""
        try:
            # 檢查集合是否存在
            existing_collections = self.vector_store.client.list_collections()
            collection_exists = any(col.name == self.collection_name for col in existing_collections)

            if not collection_exists:
                # 建立新集合
                collection = self.vector_store.client.create_collection(
                    name=self.collection_name,
                    metadata={
                        "description": "財經新聞資料",
                        "source": "cnyes.com",
                        "created_at": datetime.now().isoformat()
                    }
                )
                logger.info(f"已建立新的向量集合: {self.collection_name}")
            else:
                logger.info(f"使用現有的向量集合: {self.collection_name}")

        except Exception as e:
            logger.error(f"準備集合失敗: {e}")
            raise

    def _enhance_article(self, article: FinancialArticle) -> FinancialArticle:
        """增強文章內容和標籤"""
        # 複製文章
        enhanced = FinancialArticle(
            title=article.title,
            content=article.content,
            url=article.url,
            category=article.category,
            publish_date=article.publish_date,
            author=article.author,
            tags=article.tags.copy(),
            summary=article.summary,
            source=article.source,
            scrape_time=article.scrape_time,
            expert_domain=article.expert_domain
        )

        # 增強標籤
        enhanced.tags.extend(self._generate_smart_tags(article))

        # 去重標籤
        enhanced.tags = list(set(enhanced.tags))

        return enhanced

    def _generate_smart_tags(self, article: FinancialArticle) -> List[str]:
        """智能生成額外標籤"""
        smart_tags = []

        # 基於內容關鍵字生成標籤
        content_lower = (article.title + " " + article.content).lower()

        # 股票相關
        if any(keyword in content_lower for keyword in ["股價", "漲跌", "成交量", "市值", "股東"]):
            smart_tags.append("股票投資")

        # 基金相關
        if any(keyword in content_lower for keyword in ["基金", "etf", "淨值", "配息", "投信"]):
            smart_tags.append("基金投資")

        # 經濟指標
        if any(keyword in content_lower for keyword in ["gdp", "cpi", "利率", "通膨", "失業率"]):
            smart_tags.append("經濟指標")

        # 央行政策
        if any(keyword in content_lower for keyword in ["央行", "升息", "降息", "貨幣政策", "聯準會"]):
            smart_tags.append("貨幣政策")

        # 產業分析
        if any(keyword in content_lower for keyword in ["科技股", "金融股", "傳產", "生技", "電子"]):
            smart_tags.append("產業分析")

        # 投資策略
        if any(keyword in content_lower for keyword in ["資產配置", "風險控管", "投資組合", "分散投資"]):
            smart_tags.append("投資策略")

        # 市場情緒
        if any(keyword in content_lower for keyword in ["牛市", "熊市", "恐慌", "樂觀", "謹慎"]):
            smart_tags.append("市場情緒")

        return smart_tags

    def _save_articles_to_json(self, articles: List[FinancialArticle], custom_filename: str = None) -> str:
        """儲存文章為JSON格式"""
        if custom_filename:
            filename = custom_filename
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"financial_news_{timestamp}.json"

        # 確保資料夾存在
        data_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            "data"
        )
        os.makedirs(data_dir, exist_ok=True)

        filepath = os.path.join(data_dir, filename)

        # 建立JSON資料結構
        json_data = {
            "metadata": {
                "source": "cnyes.com",
                "scrape_time": datetime.now().isoformat(),
                "total_articles": len(articles),
                "categories": list(set(article.category for article in articles))
            },
            "articles": [article.to_dict() for article in articles]
        }

        # 儲存檔案
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

        logger.info(f"文章已儲存至: {filepath}")
        return filepath

    async def test_financial_news_retrieval(self) -> None:
        """測試財經新聞檢索功能"""
        test_queries = [
            "台股投資分析",
            "基金投資建議",
            "美股市場趨勢",
            "債券投資風險",
            "經濟指標分析"
        ]

        logger.info("測試財經新聞檢索功能...")

        try:
            collection = self.vector_store.client.get_collection(self.collection_name)

            for query in test_queries:
                print(f"\n查詢：{query}")

                results = collection.query(
                    query_texts=[query],
                    n_results=3
                )

                if results['documents'][0]:
                    print(f"找到 {len(results['documents'][0])} 個相關文章：")
                    for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
                        print(f"{i+1}. {metadata['title']}")
                        print(f"   類別：{metadata['category']}")
                        print(f"   日期：{metadata['publish_date']}")
                        print(f"   摘要：{doc[:100]}...")
                else:
                    print("未找到相關文章")

        except Exception as e:
            print(f"檢索測試失敗：{e}")

    def get_collection_stats(self) -> Dict[str, Any]:
        """獲取集合統計資訊"""
        try:
            collection = self.vector_store.client.get_collection(self.collection_name)
            count = collection.count()

            return {
                "collection_name": self.collection_name,
                "total_documents": count,
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"獲取統計失敗: {e}")
            return {}


async def main():
    """主執行函數"""
    print("財經新聞資料處理系統")
    print("=" * 50)

    try:
        # 初始化處理器
        processor = FinancialNewsProcessor()

        print("\n[1] 執行鉅亨網新聞爬取與處理...")
        loaded_count = await processor.process_cnyes_scraping(max_articles_per_category=10)

        print(f"\n[成功] 載入 {loaded_count} 篇財經新聞到向量資料庫")

        # 顯示統計資訊
        stats = processor.get_collection_stats()
        if stats:
            print(f"\n集合統計:")
            print(f"  集合名稱: {stats['collection_name']}")
            print(f"  文檔總數: {stats['total_documents']}")

        print("\n[2] 測試財經新聞檢索功能...")
        await processor.test_financial_news_retrieval()

        print("\n[完成] 財經新聞處理系統執行完成！")

    except Exception as e:
        print(f"\n[錯誤] 系統執行失敗: {e}")
        logger.error(f"系統執行失敗: {e}", exc_info=True)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    asyncio.run(main())