"""
ETL (Extract, Transform, Load) 自動化爬蟲系統

專為 Finance Agents 設計的知識庫更新系統：
- 基礎爬蟲框架
- 網站特化爬蟲模組
- 自動化排程管理
- 向量化與資料庫載入
"""

from .base_scraper import BaseScraper
from .etl_manager import ETLManager

__all__ = [
    "BaseScraper",
    "ETLManager"
]