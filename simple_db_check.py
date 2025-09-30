#!/usr/bin/env python3
"""
簡單的資料庫檢查腳本
"""

import sys
import json
from pathlib import Path

# 添加專案路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src" / "main" / "python"))

from dotenv import load_dotenv
load_dotenv()

from src.main.python.rag.chroma_vector_store import ChromaVectorStore


def main():
    print("RAG系統狀態檢查")
    print("=" * 40)

    # 檢查 API 使用的系統
    api_main_path = project_root / "src/main/python/api/main.py"
    if api_main_path.exists():
        with open(api_main_path, 'r', encoding='utf-8') as f:
            api_content = f.read()

        print("主系統使用:")
        if 'EnhancedVectorStore' in api_content:
            print("  文章感知RAG (EnhancedVectorStore)")
        elif 'ChromaVectorStore' in api_content:
            print("  傳統RAG (ChromaVectorStore)")
            if 'finance_knowledge_optimal' in api_content:
                print("  集合: finance_knowledge_optimal")

    # 檢查資料庫內容
    print("\n資料庫內容檢查:")
    try:
        vector_store = ChromaVectorStore(collection_name="finance_knowledge_optimal")
        collection = vector_store.collection
        document_count = collection.count()
        print(f"  文檔總數: {document_count}")

        if document_count > 0:
            # 取樣前2個文檔
            results = collection.get(limit=2, include=['documents', 'metadatas'])

            print("\n文檔樣本:")
            for i, (doc, metadata) in enumerate(zip(results['documents'], results['metadatas'])):
                print(f"\n--- 文檔 {i+1} ---")
                print(f"長度: {len(doc)} 字符")
                print(f"元數據: {metadata}")
                print(f"內容: {doc[:150]}...")

                # 檢查語意切割標記
                if metadata:
                    has_semantic = any(key in str(metadata).lower()
                                     for key in ['semantic', 'boundary', 'coherence'])
                    has_article_id = ('original_document_id' in metadata or
                                    'article_id' in metadata)
                    print(f"語意切割標記: {'有' if has_semantic else '無'}")
                    print(f"文章ID標記: {'有' if has_article_id else '無'}")

    except Exception as e:
        print(f"資料庫檢查錯誤: {e}")

    # 總結
    print("\n" + "=" * 40)
    print("總結:")
    print("1. 目前主系統使用: 傳統RAG (ChromaVectorStore)")
    print("2. 資料庫切割方式: 句子感知切割 (~400字符)")
    print("3. 搜索方式: 向量相似度，返回個別chunks")
    print("4. 文章上下文: 無自動關聯")

    print("\n升級選項:")
    print("A) 保持現有資料，只升級搜索方式")
    print("B) 重新載入資料，使用語意切割")


if __name__ == "__main__":
    main()