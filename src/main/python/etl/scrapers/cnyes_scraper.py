"""
?…äº¨ç¶²çˆ¬??(cnyes.com)

å°ˆç‚º?‘è??†æ?å°ˆå®¶?‡ç?è²¡è??ƒå?å®¶è¨­è¨ˆç??³æ??‘è??°è??¬èŸ²
?ªå?ç´šï?ç¬¬ä?ç´šï??³æ??•æ?ï¼??€è¡“é›£åº¦ï?ä¸­ï??¨å??•æ?è¼‰å…¥ï¼?"""

import re
import json
from typing import List, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

from ..base_scraper import BaseScraper, ScrapedArticle, extract_text_from_html


class CnyesScraper(BaseScraper):
    """?…äº¨ç¶²çˆ¬??
    ?¬å??é?ï¼?    - ?°è‚¡?°è?
    - ç¾è‚¡?°è?
    - ?ºé??•è?
    - ?†è²¡è¦å?
    - å¸‚å ´?†æ?
    """

    def __init__(self, config):
        super().__init__(config)
        self.base_url = "https://news.cnyes.com"
        self.expert_domain = config.get("expert_domain", "financial_analysis")

        # ?°è??†é?å°æ?å°ˆå®¶?˜å?
        self.news_categories = {
            "financial_analysis": {
                "?°è‚¡": "https://news.cnyes.com/news/cat/tw_stock",
                "ç¾è‚¡": "https://news.cnyes.com/news/cat/us_stock",
                "?¨ç??¡å?": "https://news.cnyes.com/news/cat/global_stock",
                "å¤–åŒ¯": "https://news.cnyes.com/news/cat/forex",
                "?Ÿç‰©??: "https://news.cnyes.com/news/cat/commodity"
            },
            "financial_planning": {
                "?ºé?": "https://news.cnyes.com/news/cat/fund",
                "?†è²¡": "https://news.cnyes.com/news/cat/wealth",
                "ä¿éšª": "https://news.cnyes.com/news/cat/insurance",
                "?¿åœ°??: "https://news.cnyes.com/news/cat/house"
            }
        }

    def scrape(self) -> List[ScrapedArticle]:
        """?·è??…äº¨ç¶²æ–°?çˆ¬??""
        self.logger.info(f"?‹å??¬å? {self.name} - ?…äº¨ç¶?)

        articles = []

        try:
            # ?¹æ?å°ˆå®¶?˜å??¸æ??°è??†é?
            categories = self.news_categories.get(self.expert_domain, {})

            for category_name, category_url in categories.items():
                self.logger.info(f"?¬å??°è??†é?: {category_name}")

                try:
                    category_articles = self._scrape_news_category(category_url, category_name)
                    articles.extend(category_articles)
                except Exception as e:
                    self.logger.warning(f"?¬å??†é? {category_name} å¤±æ?: {e}")

            self.logger.info(f"?å??¬å? {len(articles)} ç¯‡æ–°??)

        except Exception as e:
            self.logger.error(f"?¬èŸ²?·è?å¤±æ?: {e}", exc_info=True)

        return articles

    def _scrape_news_category(self, category_url: str, category_name: str) -> List[ScrapedArticle]:
        """?¬å??¹å??†é??„æ–°??""
        articles = []

        # ?–å??†é??é¢
        content = self.get_page_content(category_url, use_selenium=True)
        if not content:
            return articles

        # ?å??°è?æ¸…å–®
        news_links = self._parse_article_list(content)

        # ?åˆ¶æ¯å€‹å?é¡æ?å¤šçˆ¬??0ç¯‡æ–°??        for link in news_links[:20]:
            try:
                article = self._scrape_news_article(link, category_name)
                if article:
                    articles.append(article)
            except Exception as e:
                self.logger.warning(f"?¬å??°è?å¤±æ? {link}: {e}")

        return articles

    def _scrape_news_article(self, url: str, category: str) -> Optional[ScrapedArticle]:
        """?¬å??®ç??°è??‡ç?"""
        content = self.get_page_content(url)
        if not content:
            return None

        return self._parse_article_detail(url, content, category)

    def _parse_article_list(self, content: str) -> List[str]:
        """è§???°è?æ¸…å–®?é¢ï¼Œæ??–æ–°?é€??"""
        soup = BeautifulSoup(content, 'html.parser')
        links = []

        # ?¹æ?1: å°‹æ‰¾?°è?æ¸…å–®å®¹å™¨
        news_containers = soup.find_all('div', class_=re.compile(r'.*news.*item.*|.*article.*item.*'))

        for container in news_containers:
            link_element = container.find('a', href=re.compile(r'/news/id/'))
            if link_element:
                href = link_element.get('href')
                if href:
                    full_url = urljoin(self.base_url, href)
                    links.append(full_url)

        # ?¹æ?2: ?´æ¥å°‹æ‰¾?°è????
        if not links:
            news_links = soup.find_all('a', href=re.compile(r'/news/id/\d+'))
            for link in news_links:
                href = link.get('href')
                if href:
                    full_url = urljoin(self.base_url, href)
                    links.append(full_url)

        # ?»é?ä¸¦è???        return list(set(links))

    def _parse_article_detail(self, url: str, content: str, category: str = "") -> Optional[ScrapedArticle]:
        """è§???°è?è©³ç´°?é¢"""
        soup = BeautifulSoup(content, 'html.parser')

        # ?å?æ¨™é?
        title = self._extract_title(soup)
        if not title:
            return None

        # ?å??§å®¹
        article_content = self._extract_content(soup)
        if not article_content:
            return None

        # ?å??¼å??¥æ?
        publish_date = self._extract_publish_date(soup)

        # ?å?ä½œè€?        author = self._extract_author(soup)

        # ?å?æ¨™ç±¤
        tags = self._extract_tags(soup, category)

        # å»ºç??‡ç??©ä»¶
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
        """?å??‡ç?æ¨™é?"""
        # å¸¸è??„æ?é¡Œé¸?‡å™¨
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
                if title and len(title) > 5:  # ?æ¿¾å¤ªçŸ­?„æ?é¡?                    return title

        return None

    def _extract_content(self, soup: BeautifulSoup) -> Optional[str]:
        """?å??‡ç??§å®¹"""
        # å¸¸è??„å…§å®¹é¸?‡å™¨
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
                # ç§»é™¤å»???Œä??¸é??ƒç?
                for unwanted in content_element.select('.ad, .advertisement, .social-share, .related-news'):
                    unwanted.decompose()

                content_text = extract_text_from_html(str(content_element))
                if content_text and len(content_text) > 100:  # ?æ¿¾å¤ªçŸ­?„å…§å®?                    return content_text

        return None

    def _extract_publish_date(self, soup: BeautifulSoup) -> Optional[datetime]:
        """?å??¼å??¥æ?"""
        # å¸¸è??„æ—¥?Ÿé¸?‡å™¨
        date_selectors = [
            'time[datetime]',
            '.publish-time',
            '.date',
            '[data-qa="publish-time"]'
        ]

        for selector in date_selectors:
            date_element = soup.select_one(selector)
            if date_element:
                # ?—è©¦å¾?datetime å±¬æ€§å?å¾?                datetime_attr = date_element.get('datetime')
                if datetime_attr:
                    return self._parse_iso_date(datetime_attr)

                # ?—è©¦å¾æ?å­—å…§å®¹å?å¾?                date_text = date_element.get_text().strip()
                if date_text:
                    return self._parse_chinese_date(date_text)

        return None

    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """?å?ä½œè€?""
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
                # æ¸…ç?ä½œè€…å?ç¨?                author_text = re.sub(r'è¨˜è€…|ç·¨è¼¯|ä½œè€…[:ï¼š]?', '', author_text)
                if author_text:
                    return author_text

        return None

    def _extract_tags(self, soup: BeautifulSoup, category: str) -> List[str]:
        """?å??‡ç?æ¨™ç±¤"""
        tags = [category] if category else []

        # å°‹æ‰¾æ¨™ç±¤?ƒç?
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
        """è§?? ISO ?¼å??¥æ?"""
        try:
            # ?•ç?å¸¸è???ISO ?¼å?
            if 'T' in date_str:
                date_str = date_str.split('T')[0]

            return datetime.fromisoformat(date_str.replace('Z', ''))
        except ValueError:
            return None

    def _parse_chinese_date(self, date_str: str) -> Optional[datetime]:
        """è§??ä¸­æ??¥æ??¼å?"""
        # ç§»é™¤å¤šé??‡å?
        date_str = re.sub(r'?¼å??‚é?[:ï¼š]?|?´æ–°?‚é?[:ï¼š]?', '', date_str)

        # ?—è©¦è§???¸å??‚é?
        if '?†é??? in date_str:
            minutes = re.search(r'(\d+)?†é???, date_str)
            if minutes:
                return datetime.now() - timedelta(minutes=int(minutes.group(1)))

        if 'å°æ??? in date_str:
            hours = re.search(r'(\d+)å°æ???, date_str)
            if hours:
                return datetime.now() - timedelta(hours=int(hours.group(1)))

        # ?—è©¦è§??çµ•å??‚é?
        return self.parse_date(date_str)


def scrape(config: dict) -> List[dict]:
    """?¬èŸ²?¥å£?½æ•¸ï¼Œä? ETL æµç?èª¿ç”¨

    Args:
        config: ?¬èŸ²è¨­å?

    Returns:
        ?¬å?çµæ??„å??¸æ???    """
    with CnyesScraper(config) as scraper:
        articles = scraper.scrape()
        return [article.to_dict() for article in articles]


# æ¸¬è©¦?½æ•¸
def test_scraper():
    """æ¸¬è©¦?¬èŸ²?Ÿèƒ½"""
    # æ¸¬è©¦?‘è??†æ?å°ˆå®¶?ç½®
    test_config_analyst = {
        "name": "?…äº¨ç¶??‘è??†æ?",
        "expert_domain": "financial_analysis",
        "request_delay": (2, 4),
        "max_retries": 3,
        "selenium_browser": "chrome"
    }

    print("?? æ¸¬è©¦?…äº¨ç¶²çˆ¬??- ?‘è??†æ?å°ˆå®¶...")

    with CnyesScraper(test_config_analyst) as scraper:
        articles = scraper.scrape()

        print(f"???å??¬å? {len(articles)} ç¯‡é??æ–°??)

        # é¡¯ç¤º??ç¯‡ç???        for i, article in enumerate(articles[:3], 1):
            print(f"\n?“° ?°è? {i}:")
            print(f"   æ¨™é?: {article.title}")
            print(f"   ä½œè€? {article.author}")
            print(f"   ?¼å??‚é?: {article.publish_date}")
            print(f"   ?§å®¹?·åº¦: {len(article.content)} å­—ç¬¦")
            print(f"   æ¨™ç±¤: {', '.join(article.tags)}")


if __name__ == "__main__":
    test_scraper()
