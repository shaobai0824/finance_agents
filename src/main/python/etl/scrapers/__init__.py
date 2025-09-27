"""
爬蟲模組集合

包含所有網站特化的爬蟲實作
"""

from .law_moj_scraper import LawMojScraper, scrape as law_moj_scrape
from .cnyes_scraper import CnyesScraper, scrape as cnyes_scrape

__all__ = [
    "LawMojScraper",
    "CnyesScraper",
    "law_moj_scrape",
    "cnyes_scrape"
]