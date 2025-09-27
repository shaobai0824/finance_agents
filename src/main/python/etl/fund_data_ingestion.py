"""
基金投資商品資料擷取與向量化

實作 Linus 哲學：
1. 簡潔執念：專門處理基金資料的單一職責模組
2. 實用主義：專注提供理財專家所需的基金資訊
3. 好品味：結構化的基金資料格式和處理流程
"""

import logging
import asyncio
from typing import List, Dict, Any
from datetime import datetime

from ..rag import ChromaVectorStore, KnowledgeRetriever
from ..database.sample_data_generator import SampleDataGenerator
from ..database.personal_finance_db import PersonalFinanceDB

logger = logging.getLogger(__name__)


class FundDataProcessor:
    """基金資料處理器"""

    def __init__(self, vector_store: ChromaVectorStore = None):
        self.vector_store = vector_store if vector_store else ChromaVectorStore()
        self.knowledge_retriever = KnowledgeRetriever(self.vector_store)

    def generate_comprehensive_fund_data(self) -> List[Dict[str, Any]]:
        """生成完整的基金投資商品資料"""

        # 基本樣本資料
        db = PersonalFinanceDB()
        generator = SampleDataGenerator(db)
        base_funds = generator.generate_fund_data_for_rag()

        # 擴展更多基金產品
        additional_funds = [
            {
                "fund_code": "BOND002",
                "fund_name": "安聯收益成長基金",
                "fund_type": "債券型基金",
                "investment_focus": "投資級債券組合，追求穩定收益",
                "risk_level": "低風險",
                "expected_return": "年化報酬率 3-6%",
                "management_fee": "1.3%",
                "min_investment": "3000元",
                "description": "主要投資全球投資級債券，包括政府債券和優質企業債券。適合保守型投資人尋求穩定收益來源。",
                "investment_strategy": "透過分散投資降低風險，定期檢視債券信評，適時調整投資組合配置。",
                "suitable_investors": "保守型投資人、退休族群、尋求穩定現金流的投資者",
                "performance_data": "過去三年平均年化報酬率 4.2%，標準差 2.8%，最大回撤 -1.5%"
            },
            {
                "fund_code": "EQUITY003",
                "fund_name": "富達亞洲成長基金",
                "fund_type": "區域型股票基金",
                "investment_focus": "亞洲(不含日本)成長型企業",
                "risk_level": "高風險",
                "expected_return": "年化報酬率 8-15%",
                "management_fee": "2.1%",
                "min_investment": "5000元",
                "description": "專注投資亞洲新興市場的成長型企業，包括中國、印度、東南亞等地區的優質公司。",
                "investment_strategy": "採用由下而上的選股策略，尋找具有長期成長潛力的亞洲企業，重點關注科技、消費、金融等產業。",
                "suitable_investors": "積極型投資人、長期投資者、看好亞洲經濟成長的投資者",
                "performance_data": "過去五年平均年化報酬率 11.8%，標準差 18.5%，最大回撤 -28.3%"
            },
            {
                "fund_code": "TECH001",
                "fund_name": "貝萊德全球科技基金",
                "fund_type": "產業型股票基金",
                "investment_focus": "全球科技龍頭企業投資",
                "risk_level": "高風險",
                "expected_return": "年化報酬率 10-20%",
                "management_fee": "2.3%",
                "min_investment": "10000元",
                "description": "投資全球領先的科技企業，包括軟體、半導體、網路服務、人工智慧等領域的創新公司。",
                "investment_strategy": "聚焦具有技術領先優勢和創新能力的科技公司，重點投資數位轉型、雲端運算、5G等成長趨勢。",
                "suitable_investors": "積極型投資人、科技產業看好者、長期成長投資者",
                "performance_data": "過去三年平均年化報酬率 15.6%，標準差 22.1%，最大回撤 -35.2%"
            },
            {
                "fund_code": "GREEN001",
                "fund_name": "施羅德環球氣候變化基金",
                "fund_type": "ESG主題基金",
                "investment_focus": "氣候變化解決方案投資",
                "risk_level": "中高風險",
                "expected_return": "年化報酬率 8-14%",
                "management_fee": "1.9%",
                "min_investment": "5000元",
                "description": "投資致力於應對氣候變化的企業，包括清潔能源、節能技術、碳捕獲等綠色科技公司。",
                "investment_strategy": "專注於能源轉型、資源效率、永續交通等主題，投資在環境解決方案方面具有競爭優勢的企業。",
                "suitable_investors": "關注ESG的投資人、看好綠色經濟的投資者、中長期投資者",
                "performance_data": "過去兩年平均年化報酬率 9.7%，標準差 16.2%，最大回撤 -22.1%"
            },
            {
                "fund_code": "DIVIDEND001",
                "fund_name": "先鋒高股息收益基金",
                "fund_type": "股息收益基金",
                "investment_focus": "高股息收益股票投資",
                "risk_level": "中風險",
                "expected_return": "年化報酬率 6-10%，年配息率 4-6%",
                "management_fee": "1.4%",
                "min_investment": "3000元",
                "description": "專門投資具有穩定且持續成長配息記錄的優質企業，提供穩定的股息收入。",
                "investment_strategy": "選擇財務健全、現金流穩定、股息支付能力強的成熟企業，重點關注公用事業、消費必需品等防禦性產業。",
                "suitable_investors": "追求現金流的投資人、退休族群、穩健型投資者",
                "performance_data": "過去五年平均年化報酬率 7.8%，年配息率 4.5%，標準差 12.3%"
            },
            {
                "fund_code": "MULTI001",
                "fund_name": "駿利亨德森多重資產基金",
                "fund_type": "多重資產基金",
                "investment_focus": "股票、債券、REITs、商品多元配置",
                "risk_level": "中風險",
                "expected_return": "年化報酬率 6-12%",
                "management_fee": "1.6%",
                "min_investment": "5000元",
                "description": "採用動態資產配置策略，在股票、債券、不動產投資信託、商品等資產間靈活調整配置比例。",
                "investment_strategy": "根據市場環境和估值水準動態調整資產配置，追求風險調整後的最佳報酬，提供一站式投資解決方案。",
                "suitable_investors": "尋求多元化配置的投資人、穩健型投資者、希望簡化投資決策的投資者",
                "performance_data": "過去三年平均年化報酬率 8.1%，標準差 10.5%，最大回撤 -15.8%"
            },
            {
                "fund_code": "BIOTECH001",
                "fund_name": "富蘭克林生技領航基金",
                "fund_type": "產業型股票基金",
                "investment_focus": "生物科技與醫療保健創新",
                "risk_level": "高風險",
                "expected_return": "年化報酬率 8-18%",
                "management_fee": "2.2%",
                "min_investment": "10000元",
                "description": "投資生物科技、製藥、醫療器材等醫療保健創新領域的領先企業，掌握人口老化和醫療創新趨勢。",
                "investment_strategy": "聚焦具有創新藥物開發能力、擁有專利保護、在利基市場具領導地位的生技醫療企業。",
                "suitable_investors": "積極型投資人、看好醫療創新的投資者、願意承受較高波動的長期投資者",
                "performance_data": "過去五年平均年化報酬率 12.4%，標準差 24.7%，最大回撤 -42.1%"
            },
            {
                "fund_code": "EMERGING001",
                "fund_name": "天達新興市場企業債券基金",
                "fund_type": "新興市場債券基金",
                "investment_focus": "新興市場企業債券投資",
                "risk_level": "中高風險",
                "expected_return": "年化報酬率 5-9%",
                "management_fee": "1.5%",
                "min_investment": "5000元",
                "description": "投資新興市場優質企業發行的債券，提供比已開發市場債券更高的收益潛力。",
                "investment_strategy": "嚴格信用分析，選擇財務健全的新興市場企業債券，適度分散地區和產業風險。",
                "suitable_investors": "追求較高收益的投資人、已有基礎債券配置的投資者、中長期投資者",
                "performance_data": "過去三年平均年化報酬率 6.3%，標準差 8.9%，最大回撤 -12.4%"
            }
        ]

        # 合併所有基金資料
        all_funds = base_funds + additional_funds

        # 為每筆基金資料增加更多細節
        for fund in all_funds:
            fund["ingestion_date"] = datetime.now().isoformat()
            fund["data_source"] = "fund_database"
            fund["expert_domain"] = "financial_planning"

            # 建立用於向量化的完整文本描述
            fund["full_description"] = self._create_full_description(fund)

        return all_funds

    def _create_full_description(self, fund: Dict[str, Any]) -> str:
        """為基金創建完整的文本描述供向量化使用"""

        description_parts = [
            f"基金名稱：{fund['fund_name']}",
            f"基金代碼：{fund['fund_code']}",
            f"基金類型：{fund['fund_type']}",
            f"投資焦點：{fund['investment_focus']}",
            f"風險等級：{fund['risk_level']}",
            f"預期報酬：{fund['expected_return']}",
            f"管理費：{fund['management_fee']}",
            f"最低投資金額：{fund['min_investment']}",
            f"基金描述：{fund['description']}"
        ]

        # 添加額外資訊（如果有）
        if fund.get("investment_strategy"):
            description_parts.append(f"投資策略：{fund['investment_strategy']}")

        if fund.get("suitable_investors"):
            description_parts.append(f"適合投資人：{fund['suitable_investors']}")

        if fund.get("performance_data"):
            description_parts.append(f"歷史績效：{fund['performance_data']}")

        return "\n".join(description_parts)

    async def ingest_fund_data_to_vector_store(self) -> int:
        """將基金資料載入向量資料庫"""

        logger.info("開始載入基金投資商品資料到向量資料庫...")

        # 生成基金資料
        funds_data = self.generate_comprehensive_fund_data()

        # 準備要載入的文件
        documents = []
        for fund in funds_data:
            documents.append({
                "content": fund["full_description"],
                "metadata": {
                    "fund_code": fund["fund_code"],
                    "fund_name": fund["fund_name"],
                    "fund_type": fund["fund_type"],
                    "risk_level": fund["risk_level"],
                    "data_source": fund["data_source"],
                    "expert_domain": fund["expert_domain"],
                    "ingestion_date": fund["ingestion_date"]
                },
                "source": f"基金資料庫 - {fund['fund_name']}"
            })

        # 載入到向量資料庫
        try:
            # 使用基金專門的集合名稱
            collection_name = "fund_investment_products"

            # 檢查集合是否已存在
            existing_collections = self.vector_store.client.list_collections()
            collection_exists = any(col.name == collection_name for col in existing_collections)

            if collection_exists:
                logger.info(f"集合 {collection_name} 已存在，將清空後重新載入")
                self.vector_store.client.delete_collection(collection_name)

            # 建立新集合
            collection = self.vector_store.client.create_collection(
                name=collection_name,
                metadata={"description": "基金投資商品資料"}
            )

            # 分批載入文件
            batch_size = 10
            total_loaded = 0

            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]

                # 準備批次資料
                batch_ids = [f"fund_{i+j}" for j in range(len(batch))]
                batch_contents = [doc["content"] for doc in batch]
                batch_metadatas = [doc["metadata"] for doc in batch]

                # 載入到向量資料庫
                collection.add(
                    ids=batch_ids,
                    documents=batch_contents,
                    metadatas=batch_metadatas
                )

                total_loaded += len(batch)
                logger.info(f"已載入 {total_loaded}/{len(documents)} 筆基金資料")

            logger.info(f"基金資料載入完成！總共載入 {total_loaded} 筆基金投資商品資料")
            return total_loaded

        except Exception as e:
            logger.error(f"載入基金資料時發生錯誤: {e}")
            raise

    def test_fund_knowledge_retrieval(self) -> None:
        """測試基金知識檢索功能"""

        test_queries = [
            "適合保守型投資人的基金推薦",
            "高股息收益的基金產品",
            "ESG永續投資基金選擇",
            "科技類股票基金",
            "債券型基金風險分析"
        ]

        logger.info("測試基金知識檢索功能...")

        for query in test_queries:
            print(f"\n查詢：{query}")
            try:
                # 直接查詢基金集合
                collection = self.vector_store.client.get_collection("fund_investment_products")
                results = collection.query(
                    query_texts=[query],
                    n_results=3
                )

                print(f"找到 {len(results['documents'][0])} 個相關基金：")
                for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
                    print(f"{i+1}. {metadata['fund_name']} ({metadata['fund_code']})")
                    print(f"   類型：{metadata['fund_type']}")
                    print(f"   風險：{metadata['risk_level']}")
                    print(f"   內容：{doc[:100]}...")

            except Exception as e:
                print(f"查詢失敗：{e}")


async def main():
    """執行基金資料載入"""

    print("基金投資商品資料載入系統")
    print("=" * 50)

    try:
        # 初始化處理器
        processor = FundDataProcessor()

        # 載入基金資料
        loaded_count = await processor.ingest_fund_data_to_vector_store()
        print(f"\n[成功] 成功載入 {loaded_count} 筆基金資料")

        # 測試檢索功能
        print("\n[測試] 測試基金知識檢索功能...")
        processor.test_fund_knowledge_retrieval()

        print("\n[完成] 基金資料載入與測試完成！")

    except Exception as e:
        print(f"\n[錯誤] 處理過程中發生錯誤：{e}")
        logger.error(f"基金資料載入失敗：{e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())