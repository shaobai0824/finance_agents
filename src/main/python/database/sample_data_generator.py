"""
樣本資料生成器 - 建立模擬客戶財務資料

實作 Linus 哲學：
1. 實用主義：生成真實合理的樣本資料
2. 簡潔執念：清晰的資料生成邏輯
3. 好品味：多樣化但一致的資料模式
"""

import logging
from decimal import Decimal
from datetime import datetime, timedelta
import random
from typing import List, Dict, Any

from .personal_finance_db import PersonalFinanceDB, RiskLevel, AccountType, AssetType

logger = logging.getLogger(__name__)


class SampleDataGenerator:
    """樣本資料生成器"""

    def __init__(self, db: PersonalFinanceDB):
        self.db = db

    def generate_sample_customers(self, count: int = 10) -> List[str]:
        """生成樣本客戶資料"""
        customers = []

        # 檢查是否已有客戶資料
        existing_customers = self.db.search_customers_by_criteria({})
        if existing_customers:
            print(f"資料庫已存在 {len(existing_customers)} 個客戶，跳過生成")
            return [c["customer_id"] for c in existing_customers]

        # 樣本客戶基本資料
        sample_profiles = [
            {
                "name": "王小明",
                "age": 28,
                "email": "ming.wang@example.com",
                "phone": "0912345678",
                "risk_level": RiskLevel.MODERATE.value,
                "annual_income": 800000,
                "employment_status": "軟體工程師",
                "investment_experience": 2
            },
            {
                "name": "李美麗",
                "age": 35,
                "email": "meili.li@example.com",
                "phone": "0923456789",
                "risk_level": RiskLevel.CONSERVATIVE.value,
                "annual_income": 1200000,
                "employment_status": "會計師",
                "investment_experience": 5
            },
            {
                "name": "張大華",
                "age": 42,
                "email": "dahua.zhang@example.com",
                "phone": "0934567890",
                "risk_level": RiskLevel.AGGRESSIVE.value,
                "annual_income": 2000000,
                "employment_status": "企業主管",
                "investment_experience": 10
            },
            {
                "name": "陳雅婷",
                "age": 26,
                "email": "yating.chen@example.com",
                "phone": "0945678901",
                "risk_level": RiskLevel.MODERATE.value,
                "annual_income": 600000,
                "employment_status": "行銷專員",
                "investment_experience": 1
            },
            {
                "name": "林志明",
                "age": 38,
                "email": "zhiming.lin@example.com",
                "phone": "0956789012",
                "risk_level": RiskLevel.CONSERVATIVE.value,
                "annual_income": 1500000,
                "employment_status": "醫師",
                "investment_experience": 8
            },
            {
                "name": "黃淑芬",
                "age": 45,
                "email": "shufen.huang@example.com",
                "phone": "0967890123",
                "risk_level": RiskLevel.AGGRESSIVE.value,
                "annual_income": 2500000,
                "employment_status": "投資顧問",
                "investment_experience": 15
            },
            {
                "name": "吳俊傑",
                "age": 32,
                "email": "junjie.wu@example.com",
                "phone": "0978901234",
                "risk_level": RiskLevel.MODERATE.value,
                "annual_income": 900000,
                "employment_status": "設計師",
                "investment_experience": 3
            },
            {
                "name": "劉亦菲",
                "age": 29,
                "email": "yifei.liu@example.com",
                "phone": "0989012345",
                "risk_level": RiskLevel.CONSERVATIVE.value,
                "annual_income": 700000,
                "employment_status": "教師",
                "investment_experience": 2
            },
            {
                "name": "鄭智勇",
                "age": 40,
                "email": "zhiyong.zheng@example.com",
                "phone": "0990123456",
                "risk_level": RiskLevel.AGGRESSIVE.value,
                "annual_income": 1800000,
                "employment_status": "科技公司CEO",
                "investment_experience": 12
            },
            {
                "name": "蔡慧玲",
                "age": 33,
                "email": "huiling.cai@example.com",
                "phone": "0901234567",
                "risk_level": RiskLevel.MODERATE.value,
                "annual_income": 1000000,
                "employment_status": "財務分析師",
                "investment_experience": 6
            }
        ]

        for i in range(min(count, len(sample_profiles))):
            profile = sample_profiles[i]
            customer_id = self.db.create_customer(profile)
            customers.append(customer_id)

            # 為每個客戶建立帳戶和投資組合
            self._create_customer_accounts(customer_id, profile)
            self._create_customer_portfolio(customer_id, profile)

            logger.info(f"已建立樣本客戶: {profile['name']} ({customer_id})")

        return customers

    def _create_customer_accounts(self, customer_id: str, profile: Dict[str, Any]):
        """為客戶建立銀行帳戶"""
        # 儲蓄帳戶
        savings_balance = random.randint(50000, 500000)
        self.db.create_account(customer_id, {
            "account_type": AccountType.SAVINGS.value,
            "account_name": "主要儲蓄帳戶",
            "balance": savings_balance,
            "currency": "TWD"
        })

        # 支票帳戶
        checking_balance = random.randint(20000, 100000)
        self.db.create_account(customer_id, {
            "account_type": AccountType.CHECKING.value,
            "account_name": "日常支票帳戶",
            "balance": checking_balance,
            "currency": "TWD"
        })

        # 投資帳戶（依照風險偏好調整金額）
        risk_multiplier = {
            RiskLevel.CONSERVATIVE.value: 0.5,
            RiskLevel.MODERATE.value: 1.0,
            RiskLevel.AGGRESSIVE.value: 2.0
        }
        investment_balance = int(profile["annual_income"] * 0.3 * risk_multiplier[profile["risk_level"]])
        self.db.create_account(customer_id, {
            "account_type": AccountType.INVESTMENT.value,
            "account_name": "投資專戶",
            "balance": investment_balance,
            "currency": "TWD"
        })

    def _create_customer_portfolio(self, customer_id: str, profile: Dict[str, Any]):
        """為客戶建立投資組合"""
        portfolio_id = self.db.create_portfolio(customer_id, f"{profile['name']}的投資組合")

        risk_level = profile["risk_level"]
        total_investment = int(profile["annual_income"] * 0.2)  # 假設投資年收入的20%

        if risk_level == RiskLevel.CONSERVATIVE.value:
            self._create_conservative_portfolio(portfolio_id, total_investment)
        elif risk_level == RiskLevel.MODERATE.value:
            self._create_moderate_portfolio(portfolio_id, total_investment)
        else:  # AGGRESSIVE
            self._create_aggressive_portfolio(portfolio_id, total_investment)

    def _create_conservative_portfolio(self, portfolio_id: str, total_amount: int):
        """建立保守型投資組合"""
        # 保守型：60% 債券基金，30% 平衡基金，10% 股票基金
        holdings = [
            {
                "asset_type": AssetType.FUNDS.value,
                "symbol": "BOND001",
                "asset_name": "政府債券基金",
                "quantity": int(total_amount * 0.6 / 15),  # 假設基金淨值15元
                "avg_cost": 15.0,
                "current_price": 15.2
            },
            {
                "asset_type": AssetType.FUNDS.value,
                "symbol": "BALANCED001",
                "asset_name": "穩健平衡基金",
                "quantity": int(total_amount * 0.3 / 12),
                "avg_cost": 12.0,
                "current_price": 12.5
            },
            {
                "asset_type": AssetType.FUNDS.value,
                "symbol": "EQUITY001",
                "asset_name": "台股大型股基金",
                "quantity": int(total_amount * 0.1 / 20),
                "avg_cost": 20.0,
                "current_price": 19.8
            }
        ]

        for holding in holdings:
            self.db.add_holding(portfolio_id, holding)

    def _create_moderate_portfolio(self, portfolio_id: str, total_amount: int):
        """建立穩健型投資組合"""
        # 穩健型：40% 股票基金，30% 債券基金，20% ETF，10% 個股
        holdings = [
            {
                "asset_type": AssetType.FUNDS.value,
                "symbol": "EQUITY002",
                "asset_name": "台股成長基金",
                "quantity": int(total_amount * 0.4 / 25),
                "avg_cost": 25.0,
                "current_price": 26.2
            },
            {
                "asset_type": AssetType.FUNDS.value,
                "symbol": "BOND002",
                "asset_name": "投資級債券基金",
                "quantity": int(total_amount * 0.3 / 18),
                "avg_cost": 18.0,
                "current_price": 18.3
            },
            {
                "asset_type": AssetType.ETF.value,
                "symbol": "0050",
                "asset_name": "元大台灣50",
                "quantity": int(total_amount * 0.2 / 140),
                "avg_cost": 140.0,
                "current_price": 145.5
            },
            {
                "asset_type": AssetType.STOCKS.value,
                "symbol": "2330",
                "asset_name": "台積電",
                "quantity": int(total_amount * 0.1 / 600),
                "avg_cost": 600.0,
                "current_price": 610.0
            }
        ]

        for holding in holdings:
            self.db.add_holding(portfolio_id, holding)

    def _create_aggressive_portfolio(self, portfolio_id: str, total_amount: int):
        """建立積極型投資組合"""
        # 積極型：50% 個股，30% 成長基金，15% 科技ETF，5% 加密貨幣
        holdings = [
            {
                "asset_type": AssetType.STOCKS.value,
                "symbol": "2330",
                "asset_name": "台積電",
                "quantity": int(total_amount * 0.3 / 600),
                "avg_cost": 600.0,
                "current_price": 610.0
            },
            {
                "asset_type": AssetType.STOCKS.value,
                "symbol": "2454",
                "asset_name": "聯發科",
                "quantity": int(total_amount * 0.2 / 1000),
                "avg_cost": 1000.0,
                "current_price": 980.0
            },
            {
                "asset_type": AssetType.FUNDS.value,
                "symbol": "GROWTH001",
                "asset_name": "科技成長基金",
                "quantity": int(total_amount * 0.3 / 35),
                "avg_cost": 35.0,
                "current_price": 38.2
            },
            {
                "asset_type": AssetType.ETF.value,
                "symbol": "QQQ",
                "asset_name": "那斯達克100 ETF",
                "quantity": int(total_amount * 0.15 / 400),
                "avg_cost": 400.0,
                "current_price": 420.0
            },
            {
                "asset_type": AssetType.CRYPTO.value,
                "symbol": "BTC",
                "asset_name": "比特幣",
                "quantity": total_amount * 0.05 / 2000000,  # 假設BTC價格200萬
                "avg_cost": 2000000.0,
                "current_price": 2100000.0
            }
        ]

        for holding in holdings:
            self.db.add_holding(portfolio_id, holding)

    def generate_fund_data_for_rag(self) -> List[Dict[str, Any]]:
        """生成基金資料供 RAG 系統使用"""
        funds_data = [
            {
                "fund_code": "BOND001",
                "fund_name": "富邦台灣政府債券基金",
                "fund_type": "債券型基金",
                "investment_focus": "主要投資台灣政府公債及高信評公司債",
                "risk_level": "低風險",
                "expected_return": "年化報酬率 3-5%",
                "management_fee": "1.2%",
                "min_investment": "3000元",
                "description": "以追求穩定收益為目標，適合保守型投資人。主要投資政府債券和投資級公司債，提供穩定的利息收入。"
            },
            {
                "fund_code": "BALANCED001",
                "fund_name": "國泰穩健平衡基金",
                "fund_type": "平衡型基金",
                "investment_focus": "股債配置比例約40:60，追求穩健成長",
                "risk_level": "中低風險",
                "expected_return": "年化報酬率 5-8%",
                "management_fee": "1.5%",
                "min_investment": "3000元",
                "description": "採用動態資產配置策略，在股票和債券間彈性調整，兼顧成長與穩定。適合穩健型投資人。"
            },
            {
                "fund_code": "EQUITY001",
                "fund_name": "元大台灣大型股基金",
                "fund_type": "股票型基金",
                "investment_focus": "投資台股市值前100大企業",
                "risk_level": "中風險",
                "expected_return": "年化報酬率 8-12%",
                "management_fee": "1.8%",
                "min_investment": "3000元",
                "description": "專注投資台灣大型優質企業，如台積電、鴻海等，參與台灣經濟成長。適合中長期投資。"
            },
            {
                "fund_code": "EQUITY002",
                "fund_name": "統一台股成長基金",
                "fund_type": "股票型基金",
                "investment_focus": "投資具成長潛力的台股企業",
                "risk_level": "中高風險",
                "expected_return": "年化報酬率 10-15%",
                "management_fee": "2.0%",
                "min_investment": "5000元",
                "description": "聚焦高成長潛力的台股企業，包括科技、生技、綠能等新興產業。適合積極型投資人。"
            },
            {
                "fund_code": "GROWTH001",
                "fund_name": "野村全球科技成長基金",
                "fund_type": "股票型基金",
                "investment_focus": "全球科技龍頭企業投資",
                "risk_level": "高風險",
                "expected_return": "年化報酬率 12-20%",
                "management_fee": "2.2%",
                "min_investment": "10000元",
                "description": "投資全球頂尖科技公司，包括Apple、Microsoft、Google等。掌握科技創新趨勢，適合長期投資。"
            },
            {
                "fund_code": "ASIA001",
                "fund_name": "摩根亞洲新興市場基金",
                "fund_type": "區域型基金",
                "investment_focus": "亞洲新興市場股票投資",
                "risk_level": "高風險",
                "expected_return": "年化報酬率 8-18%",
                "management_fee": "2.0%",
                "min_investment": "5000元",
                "description": "投資亞洲新興市場具潛力企業，包括中國、印度、東南亞等。分享亞洲經濟成長紅利。"
            },
            {
                "fund_code": "REIT001",
                "fund_name": "群益不動產投資信託基金",
                "fund_type": "REITs基金",
                "investment_focus": "全球不動產投資信託",
                "risk_level": "中風險",
                "expected_return": "年化報酬率 6-10%",
                "management_fee": "1.6%",
                "min_investment": "5000元",
                "description": "投資全球優質不動產，提供穩定租金收入。具有通膨保護效果，適合資產配置需求。"
            },
            {
                "fund_code": "ESG001",
                "fund_name": "永豐ESG永續投資基金",
                "fund_type": "ESG主題基金",
                "investment_focus": "永續發展企業投資",
                "risk_level": "中風險",
                "expected_return": "年化報酬率 7-12%",
                "management_fee": "1.8%",
                "min_investment": "3000元",
                "description": "投資符合ESG(環境、社會、治理)標準的優質企業，兼顧投資報酬與社會責任。"
            }
        ]

        return funds_data


def main():
    """執行樣本資料生成"""
    # 初始化資料庫
    db = PersonalFinanceDB()

    # 生成器
    generator = SampleDataGenerator(db)

    # 生成樣本客戶
    print("正在生成樣本客戶資料...")
    customers = generator.generate_sample_customers(10)
    print(f"已建立 {len(customers)} 個樣本客戶")

    # 顯示第一個客戶的詳細資料
    if customers:
        first_customer = customers[0]
        profile = db.get_customer_profile(first_customer)
        print(f"\n樣本客戶資料 - {profile['customer']['name']}:")
        print(f"年齡: {profile['customer']['age']}")
        print(f"風險偏好: {profile['customer']['risk_level']}")
        print(f"年收入: {profile['customer']['annual_income']:,}")
        print(f"總資產: {profile['summary']['total_assets']:,.0f}")
        print(f"現金比例: {profile['summary']['cash_ratio']:.1%}")
        print(f"投資比例: {profile['summary']['investment_ratio']:.1%}")

    print("\n樣本資料生成完成！")


if __name__ == "__main__":
    main()