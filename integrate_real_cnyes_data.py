#!/usr/bin/env python3
"""
整合真實鉅亨網資料到向量資料庫
"""

import asyncio
import json
import sys
import os

# 添加項目路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'main', 'python'))

from rag import ChromaVectorStore, KnowledgeRetriever


def load_real_cnyes_data(json_file_path: str):
    """載入真實鉅亨網JSON資料"""
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def convert_to_vector_format(articles_data):
    """轉換為向量資料庫格式"""
    documents = []

    for i, article in enumerate(articles_data['articles']):
        # 清理和準備內容
        content = f"{article['title']}\n\n{article['content']}"

        # 清理內容中的特殊字符
        content = content.replace('\u200c', '').replace('\u200b', '')

        # 生成簡單的標籤
        tags = []
        title_content = (article['title'] + ' ' + article['content']).lower()

        # 基於關鍵字生成標籤
        if any(keyword in title_content for keyword in ['台積電', 'tsmc']):
            tags.append('台積電')
        if any(keyword in title_content for keyword in ['小米', 'xiaomi']):
            tags.append('小米')
        if any(keyword in title_content for keyword in ['tiktok', '字節跳動']):
            tags.append('TikTok')
        if any(keyword in title_content for keyword in ['輝達', 'nvidia']):
            tags.append('輝達')
        if any(keyword in title_content for keyword in ['intel', '英特爾']):
            tags.append('英特爾')
        if any(keyword in title_content for keyword in ['fed', '聯準會', '降息']):
            tags.append('聯準會')
        if any(keyword in title_content for keyword in ['川普', 'trump']):
            tags.append('川普')
        if any(keyword in title_content for keyword in ['美股', '美國股市']):
            tags.append('美股')
        if any(keyword in title_content for keyword in ['台股', '台灣股市']):
            tags.append('台股')
        if any(keyword in title_content for keyword in ['基金', 'fund']):
            tags.append('基金')
        if any(keyword in title_content for keyword in ['投資', 'investment']):
            tags.append('投資')
        if any(keyword in title_content for keyword in ['ai', '人工智慧']):
            tags.append('AI')

        doc_id = f"real_cnyes_{i:04d}"

        documents.append({
            "id": doc_id,
            "content": content,
            "metadata": {
                "title": article['title'],
                "url": article['url'],
                "category": article['category'],
                "publish_time": article.get('publish_time', ''),
                "source": "cnyes.com",
                "tags": ', '.join(tags),
                "scrape_time": article['scrape_time'],
                "type": "real_news"
            }
        })

    return documents


async def ingest_to_vector_store(documents):
    """將文檔載入向量資料庫"""
    print(f"開始載入 {len(documents)} 篇真實新聞到向量資料庫...")

    try:
        # 初始化向量資料庫
        vector_store = ChromaVectorStore()
        collection_name = "financial_news"

        # 獲取或創建集合
        try:
            collection = vector_store.client.get_collection(collection_name)
            print(f"使用現有集合: {collection_name}")
        except:
            collection = vector_store.client.create_collection(
                name=collection_name,
                metadata={
                    "description": "真實財經新聞資料",
                    "source": "cnyes.com",
                    "type": "real_news"
                }
            )
            print(f"建立新集合: {collection_name}")

        # 批次載入
        batch_size = 5
        total_loaded = 0

        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]

            batch_ids = [doc["id"] for doc in batch]
            batch_contents = [doc["content"] for doc in batch]
            batch_metadatas = [doc["metadata"] for doc in batch]

            collection.add(
                ids=batch_ids,
                documents=batch_contents,
                metadatas=batch_metadatas
            )

            total_loaded += len(batch)
            print(f"已載入 {total_loaded}/{len(documents)} 篇新聞")

            await asyncio.sleep(0.5)

        print(f"真實新聞載入完成！總共 {total_loaded} 篇")
        return total_loaded

    except Exception as e:
        print(f"載入失敗: {e}")
        raise


async def test_real_news_retrieval():
    """測試真實新聞檢索"""
    print("\n測試真實新聞檢索功能...")

    try:
        vector_store = ChromaVectorStore()
        collection = vector_store.client.get_collection("financial_news")

        test_queries = [
            "小米新產品發表",
            "TikTok出售案",
            "台積電",
            "美股市場",
            "輝達投資",
            "聯準會降息"
        ]

        for query in test_queries:
            print(f"\n查詢: {query}")
            results = collection.query(
                query_texts=[query],
                n_results=2
            )

            if results['documents'][0]:
                print(f"找到 {len(results['documents'][0])} 個相關結果:")
                for j, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
                    print(f"  {j+1}. {metadata['title']}")
                    print(f"     類別: {metadata['category']}")
                    print(f"     標籤: {metadata.get('tags', 'N/A')}")
                    print(f"     URL: {metadata['url']}")
            else:
                print("  未找到相關結果")

    except Exception as e:
        print(f"檢索測試失敗: {e}")


async def main():
    """主執行函數"""
    print("整合真實鉅亨網資料到向量資料庫")
    print("=" * 50)

    try:
        # 尋找最新的JSON檔案
        data_dir = "data"
        json_files = [f for f in os.listdir(data_dir) if f.startswith("real_cnyes_news") and f.endswith(".json")]

        if not json_files:
            print("未找到真實鉅亨網資料檔案")
            print("請先執行: python real_cnyes_scraper.py")
            return

        # 使用最新的檔案
        latest_file = max(json_files)
        json_file_path = os.path.join(data_dir, latest_file)

        print(f"使用資料檔案: {json_file_path}")

        # 載入資料
        print("\n[1] 載入真實鉅亨網資料...")
        articles_data = load_real_cnyes_data(json_file_path)
        print(f"載入 {articles_data['metadata']['total_articles']} 篇新聞")

        # 轉換格式
        print("\n[2] 轉換為向量資料庫格式...")
        documents = convert_to_vector_format(articles_data)
        print(f"轉換完成，共 {len(documents)} 篇文檔")

        # 載入向量資料庫
        print("\n[3] 載入到向量資料庫...")
        loaded_count = await ingest_to_vector_store(documents)

        # 測試檢索
        print("\n[4] 測試檢索功能...")
        await test_real_news_retrieval()

        print(f"\n[完成] 真實鉅亨網資料整合完成！")
        print(f"已成功載入 {loaded_count} 篇真實財經新聞")

    except Exception as e:
        print(f"整合過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())