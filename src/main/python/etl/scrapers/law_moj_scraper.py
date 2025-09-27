"""
全國法規資料庫爬蟲 (law.moj.gov.tw)

專為法律合規專家設計的權威法規資料爬蟲
優先級：第一級（核心基石）
技術難度：低（靜態頁面）
"""

import re
from typing import List, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from datetime import datetime

from ..base_scraper import BaseScraper, ScrapedArticle, extract_text_from_html


class LawMojScraper(BaseScraper):
    """全國法規資料庫爬蟲

    爬取重點：
    - 法律條文
    - 法規修正歷史
    - 施行細則
    - 法規解釋
    """

    def __init__(self, config):
        super().__init__(config)
        self.base_url = "https://law.moj.gov.tw"
        self.expert_domain = "legal_compliance"

        # 法規分類對應
        self.law_categories = {
            "金融法規": ["銀行法", "證券交易法", "保險法", "金融控股公司法"],
            "稅務法規": ["所得稅法", "營業稅法", "遺產及贈與稅法"],
            "投資法規": ["投資型保險商品管理規則", "境外基金管理辦法"]
        }

    def scrape(self) -> List[ScrapedArticle]:
        """執行法規資料爬蟲"""
        self.logger.info(f"開始爬取 {self.name} - 全國法規資料庫")

        articles = []

        try:
            # 1. 爬取主要金融相關法規
            financial_laws = self._scrape_financial_laws()
            articles.extend(financial_laws)

            # 2. 爬取最新法規異動
            recent_updates = self._scrape_recent_updates()
            articles.extend(recent_updates)

            self.logger.info(f"成功爬取 {len(articles)} 筆法規資料")

        except Exception as e:
            self.logger.error(f"爬蟲執行失敗: {e}", exc_info=True)

        return articles

    def _scrape_financial_laws(self) -> List[ScrapedArticle]:
        """爬取金融相關法規"""
        articles = []

        for category, law_names in self.law_categories.items():
            self.logger.info(f"爬取法規分類: {category}")

            for law_name in law_names:
                try:
                    law_articles = self._scrape_law_by_name(law_name, category)
                    articles.extend(law_articles)
                except Exception as e:
                    self.logger.warning(f"爬取法規 {law_name} 失敗: {e}")

        return articles

    def _scrape_law_by_name(self, law_name: str, category: str) -> List[ScrapedArticle]:
        """根據法規名稱爬取具體條文"""
        search_url = f"{self.base_url}/LawClass/LawSearchContent.aspx"

        # 構建搜尋參數
        search_params = {
            "ty": "ALL",
            "cc": "1,2,3,4,5",
            "kw": law_name
        }

        # 取得搜尋結果頁面
        search_page = self.session.get(search_url, params=search_params)
        if search_page.status_code != 200:
            return []

        soup = BeautifulSoup(search_page.content, 'html.parser')

        # 找到法規連結
        law_links = self._extract_law_links(soup)

        articles = []
        for link in law_links[:5]:  # 限制每個法規最多取5個版本
            try:
                article = self._scrape_law_content(link, law_name, category)
                if article:
                    articles.append(article)
            except Exception as e:
                self.logger.warning(f"爬取法規內容失敗 {link}: {e}")

        return articles

    def _extract_law_links(self, soup: BeautifulSoup) -> List[str]:
        """從搜尋結果頁面提取法規連結"""
        links = []

        # 尋找搜尋結果中的法規連結
        result_links = soup.find_all('a', href=re.compile(r'LawAll\.aspx\?pcode='))

        for link in result_links:
            href = link.get('href')
            if href:
                full_url = urljoin(self.base_url, href)
                links.append(full_url)

        return links

    def _scrape_law_content(self, url: str, law_name: str, category: str) -> Optional[ScrapedArticle]:
        """爬取具體法規內容"""
        content = self.get_page_content(url)
        if not content:
            return None

        soup = BeautifulSoup(content, 'html.parser')

        # 提取法規標題
        title_element = soup.find('span', {'id': 'ctl00_ContentPlaceHolder1_lblLawName'})
        title = title_element.get_text().strip() if title_element else law_name

        # 提取法規內容
        content_element = soup.find('div', {'id': 'ctl00_ContentPlaceHolder1_divLawArticle'})
        if not content_element:
            return None

        # 清理並提取純文字
        law_text = extract_text_from_html(str(content_element))

        # 提取施行日期
        date_element = soup.find('span', {'id': 'ctl00_ContentPlaceHolder1_lblActDate'})
        publish_date = None
        if date_element:
            date_text = date_element.get_text().strip()
            publish_date = self._parse_taiwan_date(date_text)

        # 建立文章物件
        article = ScrapedArticle(
            title=title,
            content=self.clean_text(law_text),
            url=url,
            publish_date=publish_date,
            tags=[category, "法規", law_name],
            source_website="law.moj.gov.tw",
            expert_domain=self.expert_domain
        )

        return article

    def _scrape_recent_updates(self) -> List[ScrapedArticle]:
        """爬取最新法規異動"""
        articles = []

        # 法規異動查詢頁面
        updates_url = f"{self.base_url}/LawClass/LawSearchNo.aspx"

        try:
            content = self.get_page_content(updates_url)
            if not content:
                return articles

            soup = BeautifulSoup(content, 'html.parser')

            # 找到最新異動清單
            update_links = soup.find_all('a', href=re.compile(r'LawAll\.aspx'))

            for link in update_links[:10]:  # 限制最新10筆
                try:
                    href = link.get('href')
                    full_url = urljoin(self.base_url, href)

                    article = self._scrape_law_content(full_url, "法規異動", "法規更新")
                    if article:
                        articles.append(article)

                except Exception as e:
                    self.logger.warning(f"爬取法規異動失敗: {e}")

        except Exception as e:
            self.logger.error(f"爬取最新法規異動失敗: {e}")

        return articles

    def _parse_taiwan_date(self, date_str: str) -> Optional[datetime]:
        """解析台灣民國年份日期

        Args:
            date_str: 如 "中華民國110年01月01日"

        Returns:
            解析後的 datetime 物件
        """
        if not date_str:
            return None

        try:
            # 提取民國年份
            year_match = re.search(r'(\d+)年', date_str)
            month_match = re.search(r'(\d+)月', date_str)
            day_match = re.search(r'(\d+)日', date_str)

            if year_match and month_match and day_match:
                roc_year = int(year_match.group(1))
                month = int(month_match.group(1))
                day = int(day_match.group(1))

                # 民國年轉西元年
                ad_year = roc_year + 1911

                return datetime(ad_year, month, day)

        except (ValueError, AttributeError) as e:
            self.logger.warning(f"解析台灣日期失敗: {date_str}, 錯誤: {e}")

        return None

    def _parse_article_list(self, content: str) -> List[str]:
        """解析文章清單頁面（基類要求實作）"""
        soup = BeautifulSoup(content, 'html.parser')
        links = []

        for link in soup.find_all('a', href=re.compile(r'LawAll\.aspx')):
            href = link.get('href')
            if href:
                full_url = urljoin(self.base_url, href)
                links.append(full_url)

        return links

    def _parse_article_detail(self, url: str, content: str) -> Optional[ScrapedArticle]:
        """解析文章詳細頁面（基類要求實作）"""
        return self._scrape_law_content(url, "法規條文", "法規")


def scrape(config: dict) -> List[dict]:
    """爬蟲入口函數，供 ETL 流程調用

    Args:
        config: 爬蟲設定

    Returns:
        爬取結果的字典清單
    """
    with LawMojScraper(config) as scraper:
        articles = scraper.scrape()
        return [article.to_dict() for article in articles]


# 測試函數
def test_scraper():
    """測試爬蟲功能"""
    test_config = {
        "name": "全國法規資料庫",
        "expert_domain": "legal_compliance",
        "request_delay": (2, 4),
        "max_retries": 3
    }

    print("🏛️  測試全國法規資料庫爬蟲...")

    with LawMojScraper(test_config) as scraper:
        articles = scraper.scrape()

        print(f"✅ 成功爬取 {len(articles)} 筆法規資料")

        # 顯示前3筆結果
        for i, article in enumerate(articles[:3], 1):
            print(f"\n📋 法規 {i}:")
            print(f"   標題: {article.title}")
            print(f"   URL: {article.url}")
            print(f"   內容長度: {len(article.content)} 字符")
            print(f"   標籤: {', '.join(article.tags)}")


if __name__ == "__main__":
    test_scraper()