"""
?�亨網爬??(cnyes.com)

專為?��??��?專家?��?財�??��?家設計�??��??��??��??�蟲
?��?級�?第�?級�??��??��?�??�術難度�?中�??��??��?載入�?"""

import re
import json
from typing import List, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

from ..base_scraper import BaseScraper, ScrapedArticle, extract_text_from_html


class CnyesScraper(BaseScraper):
    """?�亨網爬??
    ?��??��?�?    - ?�股?��?
    - 美股?��?
    - ?��??��?
    - ?�財規�?
    - 市場?��?
    """

    def __init__(self, config):
        super().__init__(config)
        self.base_url = "https://news.cnyes.com"
        self.expert_domain = config.get("expert_domain", "financial_analysis")

        # ?��??��?對�?專家?��?
        self.news_categories = {
            "financial_analysis": {
                "?�股": "https://news.cnyes.com/news/cat/tw_stock",
                "美股": "https://news.cnyes.com/news/cat/us_stock",
                "?��??��?": "https://news.cnyes.com/news/cat/global_stock",
                "外匯": "https://news.cnyes.com/news/cat/forex",
                "?�物??: "https://news.cnyes.com/news/cat/commodity"
            },
            "financial_planning": {
                "?��?": "https://news.cnyes.com/news/cat/fund",
                "?�財": "https://news.cnyes.com/news/cat/wealth",
                "保險": "https://news.cnyes.com/news/cat/insurance",
                "?�地??: "https://news.cnyes.com/news/cat/house"
            }
        }

    def scrape(self) -> List[ScrapedArticle]:
        """?��??�亨網新?�爬??""
        self.logger.info(f"?��??��? {self.name} - ?�亨�?)

        articles = []

        try:
            # ?��?專家?��??��??��??��?
            categories = self.news_categories.get(self.expert_domain, {})

            for category_name, category_url in categories.items():
                self.logger.info(f"?��??��??��?: {category_name}")

                try:
                    category_articles = self._scrape_news_category(category_url, category_name)
                    articles.extend(category_articles)
                except Exception as e:
                    self.logger.warning(f"?��??��? {category_name} 失�?: {e}")

            self.logger.info(f"?��??��? {len(articles)} 篇新??)

        except Exception as e:
            self.logger.error(f"?�蟲?��?失�?: {e}", exc_info=True)

        return articles

    def _scrape_news_category(self, category_url: str, category_name: str) -> List[ScrapedArticle]:
        """?��??��??��??�新??""
        articles = []

        # ?��??��??�面
        content = self.get_page_content(category_url, use_selenium=True)
        if not content:
            return articles

        # ?��??��?清單
        news_links = self._parse_article_list(content)

        # ?�制每個�?類�?多爬??0篇新??        for link in news_links[:20]:
            try:
                article = self._scrape_news_article(link, category_name)
                if article:
                    articles.append(article)
            except Exception as e:
                self.logger.warning(f"?��??��?失�? {link}: {e}")

        return articles

    def _scrape_news_article(self, url: str, category: str) -> Optional[ScrapedArticle]:
        """?��??��??��??��?"""
        content = self.get_page_content(url)
        if not content:
            return None

        return self._parse_article_detail(url, content, category)

    def _parse_article_list(self, content: str) -> List[str]:
        """�???��?清單?�面，�??�新?��??"""
        soup = BeautifulSoup(content, 'html.parser')
        links = []

        # ?��?1: 尋找?��?清單容器
        news_containers = soup.find_all('div', class_=re.compile(r'.*news.*item.*|.*article.*item.*'))

        for container in news_containers:
            link_element = container.find('a', href=re.compile(r'/news/id/'))
            if link_element:
                href = link_element.get('href')
                if href:
                    full_url = urljoin(self.base_url, href)
                    links.append(full_url)

        # ?��?2: ?�接尋找?��????
        if not links:
            news_links = soup.find_all('a', href=re.compile(r'/news/id/\d+'))
            for link in news_links:
                href = link.get('href')
                if href:
                    full_url = urljoin(self.base_url, href)
                    links.append(full_url)

        # ?��?並�???        return list(set(links))

    def _parse_article_detail(self, url: str, content: str, category: str = "") -> Optional[ScrapedArticle]:
        """�???��?詳細?�面"""
        soup = BeautifulSoup(content, 'html.parser')

        # ?��?標�?
        title = self._extract_title(soup)
        if not title:
            return None

        # ?��??�容
        article_content = self._extract_content(soup)
        if not article_content:
            return None

        # ?��??��??��?
        publish_date = self._extract_publish_date(soup)

        # ?��?作�?        author = self._extract_author(soup)

        # ?��?標籤
        tags = self._extract_tags(soup, category)

        # 建�??��??�件
        article = ScrapedArticle(
            title=title,
            content=self.clean_text(article_content),
            url=url,
            publish_date=publish_date,
            author=author,
            tags=tags,
            source_website="cnyes.com",
            expert_domain=self.expert_domain
        )

        return article

    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """?��??��?標�?"""
        # 常�??��?題選?�器
        title_selectors = [
            'h1.title',
            'h1[data-qa="article-title"]',
            '.article-title h1',
            'h1',
            '.title'
        ]

        for selector in title_selectors:
            title_element = soup.select_one(selector)
            if title_element:
                title = title_element.get_text().strip()
                if title and len(title) > 5:  # ?�濾太短?��?�?                    return title

        return None

    def _extract_content(self, soup: BeautifulSoup) -> Optional[str]:
        """?��??��??�容"""
        # 常�??�內容選?�器
        content_selectors = [
            '.article-content',
            '.news-content',
            '[data-qa="article-content"]',
            '.content',
            'article .content'
        ]

        for selector in content_selectors:
            content_element = soup.select_one(selector)
            if content_element:
                # 移除�???��??��??��?
                for unwanted in content_element.select('.ad, .advertisement, .social-share, .related-news'):
                    unwanted.decompose()

                content_text = extract_text_from_html(str(content_element))
                if content_text and len(content_text) > 100:  # ?�濾太短?�內�?                    return content_text

        return None

    def _extract_publish_date(self, soup: BeautifulSoup) -> Optional[datetime]:
        """?��??��??��?"""
        # 常�??�日?�選?�器
        date_selectors = [
            'time[datetime]',
            '.publish-time',
            '.date',
            '[data-qa="publish-time"]'
        ]

        for selector in date_selectors:
            date_element = soup.select_one(selector)
            if date_element:
                # ?�試�?datetime 屬性�?�?                datetime_attr = date_element.get('datetime')
                if datetime_attr:
                    return self._parse_iso_date(datetime_attr)

                # ?�試從�?字內容�?�?                date_text = date_element.get_text().strip()
                if date_text:
                    return self._parse_chinese_date(date_text)

        return None

    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """?��?作�?""
        author_selectors = [
            '.author',
            '.reporter',
            '[data-qa="author"]',
            '.byline'
        ]

        for selector in author_selectors:
            author_element = soup.select_one(selector)
            if author_element:
                author_text = author_element.get_text().strip()
                # 清�?作者�?�?                author_text = re.sub(r'記者|編輯|作者[:：]?', '', author_text)
                if author_text:
                    return author_text

        return None

    def _extract_tags(self, soup: BeautifulSoup, category: str) -> List[str]:
        """?��??��?標籤"""
        tags = [category] if category else []

        # 尋找標籤?��?
        tag_selectors = [
            '.tags a',
            '.keywords a',
            '.category a'
        ]

        for selector in tag_selectors:
            tag_elements = soup.select(selector)
            for element in tag_elements:
                tag_text = element.get_text().strip()
                if tag_text and tag_text not in tags:
                    tags.append(tag_text)

        return tags

    def _parse_iso_date(self, date_str: str) -> Optional[datetime]:
        """�?? ISO ?��??��?"""
        try:
            # ?��?常�???ISO ?��?
            if 'T' in date_str:
                date_str = date_str.split('T')[0]

            return datetime.fromisoformat(date_str.replace('Z', ''))
        except ValueError:
            return None

    def _parse_chinese_date(self, date_str: str) -> Optional[datetime]:
        """�??中�??��??��?"""
        # 移除多�??��?
        date_str = re.sub(r'?��??��?[:：]?|?�新?��?[:：]?', '', date_str)

        # ?�試�???��??��?
        if '?��??? in date_str:
            minutes = re.search(r'(\d+)?��???, date_str)
            if minutes:
                return datetime.now() - timedelta(minutes=int(minutes.group(1)))

        if '小�??? in date_str:
            hours = re.search(r'(\d+)小�???, date_str)
            if hours:
                return datetime.now() - timedelta(hours=int(hours.group(1)))

        # ?�試�??絕�??��?
        return self.parse_date(date_str)


def scrape(config: dict) -> List[dict]:
    """?�蟲?�口?�數，�? ETL 流�?調用

    Args:
        config: ?�蟲設�?

    Returns:
        ?��?結�??��??��???    """
    with CnyesScraper(config) as scraper:
        articles = scraper.scrape()
        return [article.to_dict() for article in articles]


# 測試?�數
def test_scraper():
    """測試?�蟲?�能"""
    # 測試?��??��?專家?�置
    test_config_analyst = {
        "name": "?�亨�??��??��?",
        "expert_domain": "financial_analysis",
        "request_delay": (2, 4),
        "max_retries": 3,
        "selenium_browser": "chrome"
    }

    print("?? 測試?�亨網爬??- ?��??��?專家...")

    with CnyesScraper(test_config_analyst) as scraper:
        articles = scraper.scrape()

        print(f"???��??��? {len(articles)} 篇�??�新??)

        # 顯示??篇�???        for i, article in enumerate(articles[:3], 1):
            print(f"\n?�� ?��? {i}:")
            print(f"   標�?: {article.title}")
            print(f"   作�? {article.author}")
            print(f"   ?��??��?: {article.publish_date}")
            print(f"   ?�容?�度: {len(article.content)} 字符")
            print(f"   標籤: {', '.join(article.tags)}")


if __name__ == "__main__":
    test_scraper()
