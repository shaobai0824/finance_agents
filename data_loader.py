#!/usr/bin/env python3
"""
資料載入器 - 將理財知識匯入向量資料庫

支援：
1. 文字檔案批次匯入
2. 範例理財知識建立
3. 向量化和存儲
"""

import sys
import os
import asyncio
from pathlib import Path
from typing import List, Dict, Any

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main.python.rag import ChromaVectorStore

class DataLoader:
    """資料載入器"""

    def __init__(self):
        self.vector_store = ChromaVectorStore()

    def create_sample_data(self) -> List[Dict[str, Any]]:
        """建立範例理財知識資料"""

        sample_documents = [
            # 投資理財規劃類
            {
                "content": """
年輕人投資建議（20-30歲）：
1. 投資期間長，可承受較高風險
2. 建議股票占比 70-80%，債券 20-30%
3. 定期定額投資，培養投資習慣
4. 優先投資指數型基金（ETF）分散風險
5. 建立緊急備用金（3-6個月生活費）
6. 善用複利效應，越早開始越好
                """,
                "metadata": {
                    "source": "理財規劃手冊",
                    "domain": "financial_planning",
                    "target_age": "20-30",
                    "risk_level": "moderate_to_high"
                }
            },
            {
                "content": """
中年投資策略（40-50歲）：
1. 投資期間縮短，降低風險承受度
2. 建議股票占比 50-60%，債券 40-50%
3. 增加保險規劃，保障家庭收入
4. 考慮子女教育基金準備
5. 開始規劃退休金累積
6. 分散投資於不同地區和產業
                """,
                "metadata": {
                    "source": "理財規劃手冊",
                    "domain": "financial_planning",
                    "target_age": "40-50",
                    "risk_level": "moderate"
                }
            },
            {
                "content": """
退休投資規劃（50歲以上）：
1. 以保本為主要目標
2. 建議股票占比 30-40%，債券 60-70%
3. 增加現金部位，提高流動性
4. 考慮年金保險等保證收益商品
5. 降低投資風險，避免大幅虧損
6. 規劃退休後的現金流需求
                """,
                "metadata": {
                    "source": "理財規劃手冊",
                    "domain": "financial_planning",
                    "target_age": "50+",
                    "risk_level": "conservative"
                }
            },

            # 市場分析類
            {
                "content": """
股票投資基本面分析：
1. 公司財務報表分析（資產負債表、損益表、現金流量表）
2. 評估指標：本益比（P/E）、股價淨值比（P/B）、股東權益報酬率（ROE）
3. 產業競爭力和市場地位分析
4. 管理階層素質和公司治理
5. 長期成長潛力和營運模式
6. 分析師評等和目標價參考
                """,
                "metadata": {
                    "source": "投資分析指南",
                    "domain": "financial_analysis",
                    "investment_type": "stocks",
                    "analysis_method": "fundamental"
                }
            },
            {
                "content": """
債券投資分析：
1. 信用評等：政府債券 > 投資級公司債 > 高收益債券
2. 利率風險：債券價格與利率呈反向關係
3. 存續期間：較長期債券利率敏感度較高
4. 到期收益率（YTM）計算和比較
5. 通膨保護債券（TIPS）考量
6. 投資級債券作為資產配置基石
                """,
                "metadata": {
                    "source": "投資分析指南",
                    "domain": "financial_analysis",
                    "investment_type": "bonds",
                    "analysis_method": "fundamental"
                }
            },

            # 法規合規類
            {
                "content": """
台灣個人所得稅投資相關規定：
1. 股票交易所得目前免稅
2. 債券利息所得需申報綜合所得稅
3. 基金配息超過27萬需申報
4. 海外投資所得超過100萬需申報
5. 最低稅負制：海外所得 + 證券交易所得等特定項目
6. 投資扣除額：每年27萬元儲蓄投資特別扣除額
                """,
                "metadata": {
                    "source": "稅務法規手冊",
                    "domain": "legal_compliance",
                    "regulation_type": "tax",
                    "jurisdiction": "taiwan"
                }
            },
            {
                "content": """
金融消費者保護重點：
1. 投資前充分了解商品風險
2. 詳閱投資說明書和重要資訊
3. 確認業者合法性和金管會許可
4. 保留所有交易紀錄和相關文件
5. 如有爭議可向金融消費評議中心申訴
6. 注意冷靜期規定和解約權利
                """,
                "metadata": {
                    "source": "金融法規指南",
                    "domain": "legal_compliance",
                    "regulation_type": "consumer_protection",
                    "jurisdiction": "taiwan"
                }
            },

            # 風險管理類
            {
                "content": """
投資風險管理原則：
1. 分散投資：不要把雞蛋放在同一個籃子裡
2. 資產配置：股票、債券、現金的適當比例
3. 定期檢視：至少每季檢討投資組合
4. 風險承受度評估：年齡、收入、投資經驗
5. 停損機制：設定可接受的最大虧損
6. 情緒管理：避免追高殺低的情緒性操作
                """,
                "metadata": {
                    "source": "風險管理手冊",
                    "domain": "financial_planning",
                    "topic": "risk_management",
                    "level": "basic"
                }
            },

            # ETF 投資類
            {
                "content": """
ETF（指數股票型基金）投資優勢：
1. 分散風險：一次投資多檔股票
2. 成本低廉：管理費通常低於主動式基金
3. 透明度高：每日公布持股明細
4. 流動性佳：可在股市交易時間買賣
5. 稅務效率：被動追蹤指數，較少配息
6. 適合長期投資和定期定額
                """,
                "metadata": {
                    "source": "ETF投資指南",
                    "domain": "financial_planning",
                    "investment_type": "etf",
                    "strategy": "passive_investing"
                }
            }
        ]

        return sample_documents

    async def load_sample_data(self):
        """載入範例資料到向量資料庫"""
        print("🔄 載入範例理財知識到向量資料庫...")

        sample_docs = self.create_sample_data()

        # 準備文件和元資料
        documents = [doc["content"].strip() for doc in sample_docs]
        metadatas = [doc["metadata"] for doc in sample_docs]

        try:
            # 批次新增文件
            doc_ids = self.vector_store.add_documents(
                documents=documents,
                metadatas=metadatas
            )

            print(f"✅ 成功載入 {len(doc_ids)} 筆理財知識")
            print(f"📄 文件 IDs: {doc_ids[:3]}...")  # 顯示前3個ID

            # 顯示資料庫狀態
            info = self.vector_store.get_collection_info()
            print(f"📊 資料庫狀態: {info['document_count']} 筆文件")

        except Exception as e:
            print(f"❌ 載入失敗: {e}")
            raise

    async def test_retrieval(self):
        """測試知識檢索功能"""
        print("\n🔍 測試知識檢索功能...")

        test_queries = [
            "30歲投資建議",
            "股票分析方法",
            "台灣稅務規定",
            "ETF投資優勢"
        ]

        for query in test_queries:
            print(f"\n查詢: {query}")
            results = self.vector_store.search(query, n_results=2)

            for i, result in enumerate(results, 1):
                similarity = 1 - result['distance']  # 轉換為相似度
                print(f"  {i}. 相似度: {similarity:.2%}")
                print(f"     內容: {result['document'][:100]}...")
                print(f"     領域: {result['metadata'].get('domain', 'unknown')}")

    async def load_from_json(self, json_file_path: str):
        """從 JSON 檔案載入結構化資料"""
        import json

        print(f"📥 從 JSON 檔案載入: {json_file_path}")

        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if not isinstance(data, list):
                raise ValueError("JSON 檔案必須是包含文件物件的陣列")

            documents = []
            metadatas = []

            for item in data:
                if 'content' not in item:
                    print(f"⚠️  跳過缺少 'content' 的項目: {item}")
                    continue

                documents.append(item['content'])
                metadatas.append(item.get('metadata', {}))

            if documents:
                doc_ids = self.vector_store.add_documents(
                    documents=documents,
                    metadatas=metadatas
                )
                print(f"✅ 成功載入 {len(doc_ids)} 筆資料從 JSON")
                return doc_ids
            else:
                print("❌ JSON 檔案中沒有有效的文件")
                return []

        except Exception as e:
            print(f"❌ JSON 載入失敗: {e}")
            raise

    async def load_from_txt(self, txt_file_path: str, chunk_size: int = 500):
        """從 TXT 檔案載入純文字資料"""
        print(f"📥 從 TXT 檔案載入: {txt_file_path}")

        try:
            with open(txt_file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 按段落分割（雙換行）
            sections = content.split('\n---\n')

            documents = []
            metadatas = []

            for i, section in enumerate(sections):
                section = section.strip()
                if not section:
                    continue

                # 提取標題（如果有 ## 開頭）
                lines = section.split('\n')
                title = f"Section {i+1}"
                for line in lines:
                    if line.startswith('##'):
                        title = line.replace('##', '').strip()
                        break

                # 如果內容太長，分割成較小的塊
                if len(section) > chunk_size:
                    chunks = [section[i:i+chunk_size] for i in range(0, len(section), chunk_size)]
                    for j, chunk in enumerate(chunks):
                        documents.append(chunk)
                        metadatas.append({
                            "source": txt_file_path,
                            "section": title,
                            "chunk": j+1,
                            "domain": "general"
                        })
                else:
                    documents.append(section)
                    metadatas.append({
                        "source": txt_file_path,
                        "section": title,
                        "domain": "general"
                    })

            if documents:
                doc_ids = self.vector_store.add_documents(
                    documents=documents,
                    metadatas=metadatas
                )
                print(f"✅ 成功載入 {len(doc_ids)} 筆資料從 TXT")
                return doc_ids
            else:
                print("❌ TXT 檔案中沒有有效的內容")
                return []

        except Exception as e:
            print(f"❌ TXT 載入失敗: {e}")
            raise

    async def load_from_directory(self, directory_path: str):
        """從目錄載入所有支援的檔案"""
        directory = Path(directory_path)
        if not directory.exists():
            print(f"❌ 目錄不存在: {directory_path}")
            return

        print(f"📁 掃描目錄: {directory_path}")

        total_loaded = 0

        # 載入 JSON 檔案
        for json_file in directory.glob("*.json"):
            try:
                doc_ids = await self.load_from_json(str(json_file))
                total_loaded += len(doc_ids)
            except Exception as e:
                print(f"⚠️  跳過檔案 {json_file}: {e}")

        # 載入 TXT 檔案
        for txt_file in directory.glob("*.txt"):
            try:
                doc_ids = await self.load_from_txt(str(txt_file))
                total_loaded += len(doc_ids)
            except Exception as e:
                print(f"⚠️  跳過檔案 {txt_file}: {e}")

        print(f"🎉 目錄載入完成，總計載入 {total_loaded} 筆資料")

    def clear_database(self):
        """清空資料庫（謹慎使用）"""
        print("⚠️  清空向量資料庫...")
        self.vector_store.clear_collection()
        print("✅ 資料庫已清空")

async def main():
    """主函式"""
    print("🏦 Finance Agents 資料載入器")
    print("=" * 40)

    loader = DataLoader()

    # 檢查當前資料庫狀態
    info = loader.vector_store.get_collection_info()
    print(f"📊 當前資料庫: {info['document_count']} 筆文件")

    print("\n選擇載入方式:")
    print("1. 載入內建範例資料")
    print("2. 從 JSON 檔案載入")
    print("3. 從 TXT 檔案載入")
    print("4. 從 data/ 目錄載入所有檔案")
    print("5. 清空資料庫")
    print("6. 跳過載入，直接測試")

    choice = input("\n請選擇 (1-6): ").strip()

    if choice == "1":
        if info['document_count'] > 0:
            response = input("資料庫已有資料，是否要清空並重新載入？(y/N): ")
            if response.lower() == 'y':
                loader.clear_database()
        await loader.load_sample_data()

    elif choice == "2":
        json_path = input("請輸入 JSON 檔案路徑 (預設: data/sample_knowledge.json): ").strip()
        if not json_path:
            json_path = "data/sample_knowledge.json"
        try:
            await loader.load_from_json(json_path)
        except Exception as e:
            print(f"載入失敗: {e}")

    elif choice == "3":
        txt_path = input("請輸入 TXT 檔案路徑 (預設: data/sample_knowledge.txt): ").strip()
        if not txt_path:
            txt_path = "data/sample_knowledge.txt"
        try:
            await loader.load_from_txt(txt_path)
        except Exception as e:
            print(f"載入失敗: {e}")

    elif choice == "4":
        data_dir = input("請輸入目錄路徑 (預設: data/): ").strip()
        if not data_dir:
            data_dir = "data/"
        try:
            await loader.load_from_directory(data_dir)
        except Exception as e:
            print(f"載入失敗: {e}")

    elif choice == "5":
        confirm = input("確定要清空資料庫？此操作無法復原 (y/N): ")
        if confirm.lower() == 'y':
            loader.clear_database()
        else:
            print("取消清空操作")

    elif choice == "6":
        print("⏭️  跳過資料載入")

    else:
        print("❌ 無效選擇，跳過載入")

    # 顯示最新資料庫狀態
    info = loader.vector_store.get_collection_info()
    print(f"\n📊 最終資料庫狀態: {info['document_count']} 筆文件")

    # 測試檢索功能
    if info['document_count'] > 0:
        test_choice = input("\n是否要測試檢索功能？(Y/n): ").strip()
        if test_choice.lower() != 'n':
            await loader.test_retrieval()

    print("\n🎉 資料載入器執行完成！")
    print("💡 建議執行: python simple_test.py")
    print("🌐 或開啟: test_frontend.html")

if __name__ == "__main__":
    asyncio.run(main())