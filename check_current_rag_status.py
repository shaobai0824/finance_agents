#!/usr/bin/env python3
"""
檢查當前RAG系統使用狀態

確認：
1. 目前使用的是哪種RAG系統
2. 資料庫中的切割方式
3. 是否有語意切割和文章感知功能
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


def check_collection_details(collection_name: str):
    """檢查特定集合的詳細信息"""
    print(f"\n=== 檢查集合：{collection_name} ===")

    try:
        vector_store = ChromaVectorStore(collection_name=collection_name)

        # 獲取集合信息
        collection = vector_store.collection
        document_count = collection.count()

        print(f"文檔總數：{document_count}")

        if document_count > 0:
            # 取樣分析前5個文檔
            results = collection.get(limit=5, include=['documents', 'metadatas'])

            print(f"\n📄 文檔樣本分析：")
            for i, (doc, metadata) in enumerate(zip(results['documents'], results['metadatas'])):
                print(f"\n--- 文檔 {i+1} ---")
                print(f"長度：{len(doc)} 字符")
                print(f"元數據：{json.dumps(metadata, ensure_ascii=False, indent=2)}")
                print(f"內容預覽：{doc[:100]}...")

                # 分析切割方式
                if '。' in doc:
                    sentence_count = doc.count('。')
                    print(f"句子數量：{sentence_count}")

                # 檢查是否有語意切割標記
                if metadata:
                    has_semantic = any(key in str(metadata).lower() for key in ['semantic', 'boundary', 'coherence'])
                    has_article_id = 'original_document_id' in metadata or 'article_id' in metadata
                    print(f"語意切割標記：{'✅' if has_semantic else '❌'}")
                    print(f"文章ID標記：{'✅' if has_article_id else '❌'}")

        return document_count > 0

    except Exception as e:
        print(f"錯誤：{e}")
        return False


def analyze_chunking_method():
    """分析當前使用的切割方法"""
    print("\n🔍 分析切割方法")
    print("-" * 40)

    # 檢查是否有語意切割相關檔案
    semantic_files = [
        "src/main/python/rag/semantic_chunking.py",
        "src/main/python/rag/enhanced_vector_store.py",
        "src/main/python/rag/chunking_config.py"
    ]

    print("語意切割系統檔案檢查：")
    for file_path in semantic_files:
        full_path = project_root / file_path
        exists = full_path.exists()
        print(f"  {file_path}: {'✅' if exists else '❌'}")

    # 檢查主要系統使用的類別
    print(f"\n主要系統使用檢查：")

    # 檢查 API main.py
    api_main_path = project_root / "src/main/python/api/main.py"
    if api_main_path.exists():
        with open(api_main_path, 'r', encoding='utf-8') as f:
            api_content = f.read()

        if 'EnhancedVectorStore' in api_content:
            print("  API 主系統：✅ 使用 EnhancedVectorStore (文章感知RAG)")
        elif 'ChromaVectorStore' in api_content:
            print("  API 主系統：🟡 使用 ChromaVectorStore (傳統RAG)")
        else:
            print("  API 主系統：❌ 未找到向量存儲使用")


def check_database_collections():
    """檢查資料庫中的所有集合"""
    print("\n📚 資料庫集合檢查")
    print("-" * 40)

    # 常見的集合名稱
    collection_names = [
        "finance_knowledge",
        "finance_knowledge_optimal",
        "financial_news",
        "test_semantic_chunking",
        "enhanced_test",
        "traditional_test"
    ]

    active_collections = []

    for collection_name in collection_names:
        try:
            has_data = check_collection_details(collection_name)
            if has_data:
                active_collections.append(collection_name)
        except Exception as e:
            print(f"集合 {collection_name} 檢查失敗：{e}")

    return active_collections


def main():
    """主要檢查函數"""
    print("🔍 RAG系統狀態檢查報告")
    print("=" * 60)

    # 1. 分析切割方法
    analyze_chunking_method()

    # 2. 檢查資料庫集合
    active_collections = check_database_collections()

    # 3. 總結報告
    print("\n" + "=" * 60)
    print("📋 總結報告")
    print("=" * 60)

    print(f"\n🎯 當前系統狀態：")

    # 檢查主要API使用的系統
    api_main_path = project_root / "src/main/python/api/main.py"
    if api_main_path.exists():
        with open(api_main_path, 'r', encoding='utf-8') as f:
            api_content = f.read()

        if 'EnhancedVectorStore' in api_content:
            print("  ✅ 主系統已升級為文章感知RAG (EnhancedVectorStore)")
            rag_type = "Article-Aware Context RAG"
        elif 'ChromaVectorStore' in api_content:
            print("  🟡 主系統仍使用傳統RAG (ChromaVectorStore)")
            rag_type = "Traditional RAG"
            if 'finance_knowledge_optimal' in api_content:
                print("  📝 使用最佳化集合 (finance_knowledge_optimal)")
        else:
            print("  ❌ 主系統配置不明")
            rag_type = "未知"

    print(f"\n📊 活躍的資料庫集合：")
    if active_collections:
        for collection in active_collections:
            print(f"  • {collection}")

        main_collection = "finance_knowledge_optimal"
        if main_collection in active_collections:
            print(f"\n🎯 主要使用的集合：{main_collection}")
            print("  這個集合使用句子感知切割 (400字符目標，重疊50字符)")
    else:
        print("  ❌ 沒有找到活躍的資料庫集合")

    print(f"\n🤔 回答您的問題：")
    print(f"1. 目前使用的方式：{rag_type}")

    if rag_type == "Traditional RAG":
        print("2. 資料庫內容：使用傳統的句子感知切割")
        print("   - 每個chunk約400字符")
        print("   - 在句號處分割")
        print("   - 有適度重疊(50字符)")
        print("   - ❌ 沒有語意邊界檢測")
        print("   - ❌ 沒有文章上下文保持")

        print("3. 搜索方式：")
        print("   - 向量相似度搜索")
        print("   - 返回最相關的個別chunks")
        print("   - ❌ 不會自動包含同一篇文章的其他chunks")

        print("\n💡 升級建議：")
        print("   如果要升級到文章感知RAG：")
        print("   1. 需要更新 API main.py 使用 EnhancedVectorStore")
        print("   2. 需要重新載入資料以添加語意切割標記")
        print("   3. 或保持現有資料，只改變搜索方式")

    elif rag_type == "Article-Aware Context RAG":
        print("2. 資料庫內容：使用語意邊界切割")
        print("   - 基於句子embedding相似度切割")
        print("   - 保持文章ID關聯")
        print("   - 有語意一致性評分")

        print("3. 搜索方式：")
        print("   - 語意相似度搜索")
        print("   - 自動包含同篇文章的相關chunks")
        print("   - 提供完整的文章上下文")


if __name__ == "__main__":
    main()