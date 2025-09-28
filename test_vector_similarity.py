#!/usr/bin/env python3
"""
測試向量相似度分數，確定適當的閾值
"""

import sys
from pathlib import Path

# 添加專案路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src" / "main" / "python"))

from dotenv import load_dotenv
load_dotenv()

from src.main.python.rag.chroma_vector_store import ChromaVectorStore

def test_similarity_scores():
    """測試相似度分數"""
    print("=== 測試向量相似度分數 ===")

    try:
        # 使用最佳策略集合
        vector_store = ChromaVectorStore(collection_name="finance_knowledge_optimal")

        # 測試查詢
        test_queries = [
            "投資建議",
            "股票分析",
            "理財規劃",
            "市場趨勢"
        ]

        for query in test_queries:
            print(f"\n--- 查詢: {query} ---")

            # 獲取原始結果（不使用閾值過濾）
            results = vector_store.client.query(
                collection_name=vector_store.collection_name,
                query_texts=[query],
                n_results=5
            )

            if results['documents'] and results['documents'][0]:
                print(f"找到 {len(results['documents'][0])} 個結果")

                # 顯示相似度分數
                for i, (doc, distance) in enumerate(zip(results['documents'][0], results['distances'][0])):
                    similarity = 1 - distance  # Chroma 使用距離，需要轉換為相似度
                    print(f"  {i+1}. 相似度: {similarity:.3f} - {doc[:50]}...")

                # 計算統計
                similarities = [1 - d for d in results['distances'][0]]
                max_sim = max(similarities)
                min_sim = min(similarities)
                avg_sim = sum(similarities) / len(similarities)

                print(f"統計: 最大={max_sim:.3f}, 最小={min_sim:.3f}, 平均={avg_sim:.3f}")

                # 推薦閾值
                if max_sim > 0.5:
                    recommended = max(0.3, min_sim * 0.8)
                    print(f"建議閾值: {recommended:.2f}")
                else:
                    print("數據相似度偏低，建議降低閾值到 0.3 或更低")
            else:
                print("沒有找到任何結果")

    except Exception as e:
        print(f"測試失敗: {e}")

if __name__ == "__main__":
    test_similarity_scores()