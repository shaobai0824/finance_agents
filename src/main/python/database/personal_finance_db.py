"""
個人理財資料庫系統 - 模擬真實銀行帳戶

實作 Linus 哲學：
1. 簡潔執念：清晰的資料庫架構，每張表職責單純
2. 好品味：基於實際銀行業務的資料模型設計
3. 實用主義：支援理財分析所需的所有資料
4. Never break userspace：穩定的 API 接口
"""

import sqlite3
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import uuid
from decimal import Decimal
import os

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """風險偏好等級"""
    CONSERVATIVE = "conservative"    # 保守型
    MODERATE = "moderate"           # 穩健型
    AGGRESSIVE = "aggressive"       # 積極型


class AccountType(Enum):
    """帳戶類型"""
    SAVINGS = "savings"             # 儲蓄帳戶
    CHECKING = "checking"           # 支票帳戶
    INVESTMENT = "investment"       # 投資帳戶
    RETIREMENT = "retirement"       # 退休帳戶


class AssetType(Enum):
    """資產類型"""
    CASH = "cash"                   # 現金
    STOCKS = "stocks"               # 股票
    BONDS = "bonds"                 # 債券
    FUNDS = "funds"                 # 基金
    ETF = "etf"                     # ETF
    CRYPTO = "crypto"               # 加密貨幣
    REAL_ESTATE = "real_estate"     # 不動產


@dataclass
class Customer:
    """客戶資料"""
    customer_id: str
    name: str
    age: int
    email: str
    phone: str
    risk_level: RiskLevel
    annual_income: Decimal
    employment_status: str
    investment_experience: int      # 投資經驗年數
    created_at: datetime
    updated_at: datetime


@dataclass
class Account:
    """帳戶資料"""
    account_id: str
    customer_id: str
    account_type: AccountType
    account_name: str
    balance: Decimal
    currency: str
    created_at: datetime
    is_active: bool


@dataclass
class Portfolio:
    """投資組合"""
    portfolio_id: str
    customer_id: str
    portfolio_name: str
    total_value: Decimal
    created_at: datetime
    updated_at: datetime


@dataclass
class Holding:
    """持有部位"""
    holding_id: str
    portfolio_id: str
    asset_type: AssetType
    symbol: str
    asset_name: str
    quantity: Decimal
    avg_cost: Decimal
    current_price: Decimal
    market_value: Decimal
    updated_at: datetime


class PersonalFinanceDB:
    """個人理財資料庫管理器"""

    def __init__(self, db_path: str = None):
        """初始化資料庫連接"""
        if db_path is None:
            # 使用專案根目錄下的 data 資料夾
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            db_dir = os.path.join(project_root, "data")
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, "personal_finance.db")

        self.db_path = db_path
        self.init_database()
        logger.info(f"個人理財資料庫已初始化: {self.db_path}")

    def get_connection(self) -> sqlite3.Connection:
        """獲取資料庫連接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 使結果可以像字典一樣存取
        return conn

    def init_database(self):
        """初始化資料庫結構"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 客戶基本資料表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    customer_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    age INTEGER NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    phone TEXT,
                    risk_level TEXT NOT NULL CHECK (risk_level IN ('conservative', 'moderate', 'aggressive')),
                    annual_income DECIMAL(15,2) NOT NULL,
                    employment_status TEXT NOT NULL,
                    investment_experience INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 帳戶資料表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    account_id TEXT PRIMARY KEY,
                    customer_id TEXT NOT NULL,
                    account_type TEXT NOT NULL CHECK (account_type IN ('savings', 'checking', 'investment', 'retirement')),
                    account_name TEXT NOT NULL,
                    balance DECIMAL(15,2) NOT NULL DEFAULT 0,
                    currency TEXT NOT NULL DEFAULT 'TWD',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
                )
            """)

            # 投資組合表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS portfolios (
                    portfolio_id TEXT PRIMARY KEY,
                    customer_id TEXT NOT NULL,
                    portfolio_name TEXT NOT NULL,
                    total_value DECIMAL(15,2) NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
                )
            """)

            # 持有部位表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS holdings (
                    holding_id TEXT PRIMARY KEY,
                    portfolio_id TEXT NOT NULL,
                    asset_type TEXT NOT NULL CHECK (asset_type IN ('cash', 'stocks', 'bonds', 'funds', 'etf', 'crypto', 'real_estate')),
                    symbol TEXT NOT NULL,
                    asset_name TEXT NOT NULL,
                    quantity DECIMAL(15,4) NOT NULL,
                    avg_cost DECIMAL(10,4) NOT NULL,
                    current_price DECIMAL(10,4) NOT NULL,
                    market_value DECIMAL(15,2) NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (portfolio_id) REFERENCES portfolios (portfolio_id)
                )
            """)

            # 交易記錄表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    transaction_id TEXT PRIMARY KEY,
                    account_id TEXT,
                    portfolio_id TEXT,
                    transaction_type TEXT NOT NULL CHECK (transaction_type IN ('deposit', 'withdrawal', 'buy', 'sell', 'dividend', 'fee')),
                    asset_symbol TEXT,
                    quantity DECIMAL(15,4),
                    price DECIMAL(10,4),
                    amount DECIMAL(15,2) NOT NULL,
                    fee DECIMAL(15,2) DEFAULT 0,
                    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT,
                    FOREIGN KEY (account_id) REFERENCES accounts (account_id),
                    FOREIGN KEY (portfolio_id) REFERENCES portfolios (portfolio_id)
                )
            """)

            # 建立索引以提升查詢效能
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_accounts_customer_id ON accounts (customer_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_portfolios_customer_id ON portfolios (customer_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_holdings_portfolio_id ON holdings (portfolio_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_account_id ON transactions (account_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_portfolio_id ON transactions (portfolio_id)")

            conn.commit()
            logger.info("資料庫結構初始化完成")

    def create_customer(self, customer_data: Dict[str, Any]) -> str:
        """建立新客戶"""
        customer_id = str(uuid.uuid4())

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO customers (
                    customer_id, name, age, email, phone, risk_level,
                    annual_income, employment_status, investment_experience
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                customer_id,
                customer_data["name"],
                customer_data["age"],
                customer_data["email"],
                customer_data.get("phone", ""),
                customer_data["risk_level"],
                float(customer_data["annual_income"]),
                customer_data["employment_status"],
                customer_data.get("investment_experience", 0)
            ))
            conn.commit()

        logger.info(f"新客戶已建立: {customer_id}")
        return customer_id

    def create_account(self, customer_id: str, account_data: Dict[str, Any]) -> str:
        """為客戶建立新帳戶"""
        account_id = str(uuid.uuid4())

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO accounts (
                    account_id, customer_id, account_type, account_name,
                    balance, currency
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                account_id,
                customer_id,
                account_data["account_type"],
                account_data["account_name"],
                float(account_data.get("balance", 0)),
                account_data.get("currency", "TWD")
            ))
            conn.commit()

        logger.info(f"新帳戶已建立: {account_id}")
        return account_id

    def create_portfolio(self, customer_id: str, portfolio_name: str) -> str:
        """建立投資組合"""
        portfolio_id = str(uuid.uuid4())

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO portfolios (portfolio_id, customer_id, portfolio_name)
                VALUES (?, ?, ?)
            """, (portfolio_id, customer_id, portfolio_name))
            conn.commit()

        logger.info(f"新投資組合已建立: {portfolio_id}")
        return portfolio_id

    def add_holding(self, portfolio_id: str, holding_data: Dict[str, Any]) -> str:
        """新增持有部位"""
        holding_id = str(uuid.uuid4())

        # 計算市值
        quantity = Decimal(str(holding_data["quantity"]))
        current_price = Decimal(str(holding_data["current_price"]))
        market_value = quantity * current_price

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO holdings (
                    holding_id, portfolio_id, asset_type, symbol, asset_name,
                    quantity, avg_cost, current_price, market_value
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                holding_id, portfolio_id,
                holding_data["asset_type"],
                holding_data["symbol"],
                holding_data["asset_name"],
                float(quantity),
                float(holding_data["avg_cost"]),
                float(current_price),
                float(market_value)
            ))
            conn.commit()

        # 更新組合總值
        self._update_portfolio_value(portfolio_id)

        logger.info(f"新持有部位已新增: {holding_id}")
        return holding_id

    def get_customer_profile(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """獲取客戶完整資料"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 獲取客戶基本資料
            cursor.execute("SELECT * FROM customers WHERE customer_id = ?", (customer_id,))
            customer_row = cursor.fetchone()

            if not customer_row:
                return None

            customer_data = dict(customer_row)

            # 獲取帳戶資料
            cursor.execute("""
                SELECT * FROM accounts
                WHERE customer_id = ? AND is_active = TRUE
                ORDER BY created_at DESC
            """, (customer_id,))
            accounts = [dict(row) for row in cursor.fetchall()]

            # 獲取投資組合資料
            cursor.execute("""
                SELECT * FROM portfolios
                WHERE customer_id = ?
                ORDER BY created_at DESC
            """, (customer_id,))
            portfolios = [dict(row) for row in cursor.fetchall()]

            # 獲取每個組合的持有部位
            for portfolio in portfolios:
                cursor.execute("""
                    SELECT * FROM holdings
                    WHERE portfolio_id = ?
                    ORDER BY market_value DESC
                """, (portfolio["portfolio_id"],))
                portfolio["holdings"] = [dict(row) for row in cursor.fetchall()]

            # 計算總資產
            total_cash = sum(Decimal(str(acc["balance"])) for acc in accounts)
            total_investments = sum(Decimal(str(port["total_value"])) for port in portfolios)
            total_assets = total_cash + total_investments

            return {
                "customer": customer_data,
                "accounts": accounts,
                "portfolios": portfolios,
                "summary": {
                    "total_cash": float(total_cash),
                    "total_investments": float(total_investments),
                    "total_assets": float(total_assets),
                    "cash_ratio": float(total_cash / total_assets) if total_assets > 0 else 0,
                    "investment_ratio": float(total_investments / total_assets) if total_assets > 0 else 0
                }
            }

    def get_asset_allocation(self, customer_id: str) -> Dict[str, Any]:
        """獲取客戶資產配置分析"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 獲取所有投資組合的持有部位
            cursor.execute("""
                SELECT h.asset_type, SUM(h.market_value) as total_value
                FROM holdings h
                INNER JOIN portfolios p ON h.portfolio_id = p.portfolio_id
                WHERE p.customer_id = ?
                GROUP BY h.asset_type
                ORDER BY total_value DESC
            """, (customer_id,))

            asset_allocation = {}
            total_investment_value = Decimal('0')

            for row in cursor.fetchall():
                asset_type = row["asset_type"]
                value = Decimal(str(row["total_value"]))
                asset_allocation[asset_type] = float(value)
                total_investment_value += value

            # 計算比例
            allocation_percentages = {}
            if total_investment_value > 0:
                for asset_type, value in asset_allocation.items():
                    allocation_percentages[asset_type] = (value / float(total_investment_value)) * 100

            return {
                "asset_allocation": asset_allocation,
                "allocation_percentages": allocation_percentages,
                "total_investment_value": float(total_investment_value)
            }

    def _update_portfolio_value(self, portfolio_id: str):
        """更新投資組合總值"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 計算組合總市值
            cursor.execute("""
                SELECT SUM(market_value) as total_value
                FROM holdings
                WHERE portfolio_id = ?
            """, (portfolio_id,))

            result = cursor.fetchone()
            total_value = result["total_value"] if result["total_value"] else 0

            # 更新組合記錄
            cursor.execute("""
                UPDATE portfolios
                SET total_value = ?, updated_at = CURRENT_TIMESTAMP
                WHERE portfolio_id = ?
            """, (total_value, portfolio_id))

            conn.commit()

    def search_customers_by_criteria(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """根據條件搜尋客戶"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            where_clauses = []
            params = []

            if "risk_level" in criteria:
                where_clauses.append("risk_level = ?")
                params.append(criteria["risk_level"])

            if "min_age" in criteria:
                where_clauses.append("age >= ?")
                params.append(criteria["min_age"])

            if "max_age" in criteria:
                where_clauses.append("age <= ?")
                params.append(criteria["max_age"])

            if "min_income" in criteria:
                where_clauses.append("annual_income >= ?")
                params.append(criteria["min_income"])

            where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

            query = f"""
                SELECT customer_id, name, age, risk_level, annual_income, employment_status
                FROM customers
                {where_clause}
                ORDER BY created_at DESC
            """

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def close(self):
        """關閉資料庫連接"""
        # SQLite 使用 context manager，不需要額外關閉
        logger.info("資料庫連接已關閉")