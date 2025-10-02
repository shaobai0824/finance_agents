"""
爬蟲模組集合

包含所有網站特化的爬蟲實作
"""

from .law_moj_scraper import LawMojScraper, scrape as law_moj_scrape
# 舊的 cnyes_scraper.py 有編碼問題，已由 cnyes_auto_scraper.py 替代
from .cnyes_auto_scraper import CnyesAutoScraper, scrape as cnyes_auto_scrape

__all__ = [
    "LawMojScraper",
    "CnyesAutoScraper",
    "law_moj_scrape",
    "cnyes_auto_scrape"
]