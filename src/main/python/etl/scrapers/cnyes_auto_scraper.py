#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
鉅亨網自動化爬蟲系統

整合功能：
1. 多分類爬取（台股、美股、科技、基金、外匯、期貨）
2. 自動去重（檢查 content_hash）
3. 時間提取（支援 <time datetime=""> 格式）
4. 自動載入向量資料庫
5. 定時排程支援

遵循 Linus 哲學：
- 簡潔：統一的爬蟲介面
- 實用：解決實際的自動化需求
- 好品味：避免重複，重用現有組件
"""

import re
import hashlib
from typing import List, Optional, Dict, Any
from datetime import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from ..base_scraper import BaseScraper, ScrapedArticle, extract_text_from_html


class CnyesAutoScraper(BaseScraper):
    """鉅亨網自動化爬蟲

    支援分類：
    - 台股
    - 美股
    - 科技
    - 基金
    - 外匯
    - 期貨
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = "https://m.cnyes.com"

        # 所有支援的分類（手機版 URL，依用戶需求）
        self.news_categories = {
            "台股": "https://m.cnyes.com/news/cat/tw_stock",
            "美股": "https://m.cnyes.com/news/cat/wd_stock",
            "科技": "https://m.cnyes.com/news/cat/tech",
            "基金": "https://m.cnyes.com/news/cat/fund",
            "外匯": "https://m.cnyes.com/news/cat/forex",
            "理財": "https://m.cnyes.com/news/cat/tw_money"
        }

        # 每個分類爬取的新聞數量
        self.articles_per_category = config.get("articles_per_category", 20)

        # 已知的 content_hash（用於去重）
        self.existing_hashes = set()

    def set_existing_hashes(self, hashes: List[str]):
        """設定已存在的文章 hash（用於去重）"""
        self.existing_hashes = set(hashes)
        self.logger.info(f"已載入 {len(hashes)} 個現有文章 hash 用於去重")

    def scrape(self) -> List[ScrapedArticle]:
        """執行爬蟲"""
        self.logger.info(f"開始爬取鉅亨網新聞 - {self.name}")

        all_articles = []

        for category_name, category_url in self.news_categories.items():
            self.logger.info(f"爬取分類：{category_name}")

            try:
                category_articles = self._scrape_news_category(
                    category_url,
                    category_name
                )

                # 去重過濾
                new_articles = [
                    article for article in category_articles
                    if article._generate_content_hash() not in self.existing_hashes
                ]

                if len(category_articles) > len(new_articles):
                    self.logger.info(
                        f"分類 {category_name} 過濾掉 {len(category_articles) - len(new_articles)} 篇重複文章"
                    )

                all_articles.extend(new_articles)

            except Exception as e:
                self.logger.warning(f"爬取分類 {category_name} 失敗: {e}")

        self.logger.info(f"共爬取 {len(all_articles)} 篇新文章")
        return all_articles

    def _scrape_news_category(self, category_url: str, category_name: str) -> List[ScrapedArticle]:
        """爬取特定分類的新聞"""
        articles = []

        # 獲取分類頁面
        content = self.get_page_content(category_url, use_selenium=True)
        if not content:
            return articles

        # 解析文章清單（返回包含 url 和 title 的字典列表）
        news_items = self._parse_article_list(content)

        # 限制爬取數量
        for item in news_items[:self.articles_per_category]:
            try:
                article = self._scrape_news_article(
                    item['url'],
                    category_name,
                    preloaded_title=item.get('title')
                )
                if article:
                    articles.append(article)
            except Exception as e:
                self.logger.warning(f"爬取文章失敗 {item['url']}: {e}")

        return articles

    def _scrape_news_article(
        self,
        url: str,
        category: str,
        preloaded_title: Optional[str] = None
    ) -> Optional[ScrapedArticle]:
        """爬取單篇新聞"""
        content = self.get_page_content(url)
        if not content:
            return None

        return self._parse_article_detail(url, content, category, preloaded_title)

    def _parse_article_list(self, content: str) -> List[Dict[str, str]]:
        """解析文章清單頁面（手機版）

        Linus 哲學：簡潔執念 - 從 <a> 標籤的 title 屬性提取標題

        Returns:
            包含 url 和 title 的字典列表
        """
        soup = BeautifulSoup(content, 'html.parser')
        articles = []
        seen_urls = set()

        # 方法1：優先尋找有 title 屬性的 <a> 標籤（手機版特徵）
        news_links_with_title = soup.find_all('a', attrs={'title': True, 'href': re.compile(r'/news/id/\d+')})

        for link in news_links_with_title:
            href = link.get('href')
            title = link.get('title', '').strip()

            if href and title and len(title) > 5:
                full_url = urljoin(self.base_url, href)

                # 去重
                if full_url not in seen_urls:
                    articles.append({
                        'url': full_url,
                        'title': title
                    })
                    seen_urls.add(full_url)

        # 方法2：若方法1沒找到，嘗試一般連結
        if not articles:
            news_links = soup.find_all('a', href=re.compile(r'/news/id/\d+'))
            for link in news_links:
                href = link.get('href')
                if href:
                    full_url = urljoin(self.base_url, href)
                    if full_url not in seen_urls:
                        articles.append({
                            'url': full_url,
                            'title': None  # 稍後從詳細頁面提取
                        })
                        seen_urls.add(full_url)

        self.logger.info(f"找到 {len(articles)} 個新聞連結 ({sum(1 for a in articles if a['title'])} 個含標題)")
        return articles

    def _parse_article_detail(
        self,
        url: str,
        content: str,
        category: str = "",
        preloaded_title: Optional[str] = None
    ) -> Optional[ScrapedArticle]:
        """解析文章詳細頁面"""
        soup = BeautifulSoup(content, 'html.parser')

        # 提取標題（優先使用從列表頁預載的標題）
        title = preloaded_title if preloaded_title else self._extract_title(soup)
        if not title:
            return None

        # 提取內容
        article_content = self._extract_content(soup)
        if not article_content:
            return None

        # 提取發布時間（支援 <time datetime=""> 格式）
        publish_date = self._extract_publish_date(soup)

        # 提取作者
        author = self._extract_author(soup)

        # 提取標籤
        tags = self._extract_tags(soup, category)

        # 判斷專家領域
        expert_domain = self._determine_expert_domain(category, title, article_content)

        # 建立文章物件
        article = ScrapedArticle(
            title=title,
            content=self.clean_text(article_content),
            url=url,
            publish_date=publish_date,
            author=author,
            tags=tags,
            source_website="cnyes.com",
            expert_domain=expert_domain
        )

        return article

    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """提取標題

        Linus 哲學：實用主義 - 找第一個 h1，大多數新聞網站都這樣設計
        """
        # 優先尋找 h1
        h1 = soup.find('h1')
        if h1:
            title = h1.get_text().strip()
            if title and len(title) > 5:
                self.logger.debug(f"找到標題: {title[:50]}...")
                return title

        # 備用：從 meta og:title 提取
        meta_title = soup.find('meta', property='og:title')
        if meta_title and meta_title.get('content'):
            title = meta_title['content'].strip()
            if title and len(title) > 5:
                self.logger.debug(f"從 meta 找到標題: {title[:50]}...")
                return title

        # 最後備用：從 title 標籤提取
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text().strip()
            if title and len(title) > 5:
                self.logger.debug(f"從 title 標籤找到: {title[:50]}...")
                return title

        self.logger.warning("無法找到標題")
        return None

    def _extract_content(self, soup: BeautifulSoup) -> Optional[str]:
        """提取內容

        Linus 哲學：好品味 - 優先使用標準標籤，沒有特殊情況
        """
        # 方法1：找 article 標籤
        article = soup.find('article')
        if article:
            # 移除不需要的元素
            for unwanted in article.select('.ad, .advertisement, .social-share, .related-news, script, style'):
                unwanted.decompose()

            content_text = extract_text_from_html(str(article))
            if content_text and len(content_text) > 100:
                self.logger.debug(f"從 article 標籤提取內容：{len(content_text)} 字符")
                return content_text

        # 方法2：找包含 'content' 的 div
        content_divs = soup.find_all('div', class_=re.compile(r'.*content.*', re.I))
        for div in content_divs:
            # 移除不需要的元素
            for unwanted in div.select('.ad, .advertisement, .social-share, .related-news, script, style'):
                unwanted.decompose()

            content_text = extract_text_from_html(str(div))
            if content_text and len(content_text) > 100:
                self.logger.debug(f"從 content div 提取內容：{len(content_text)} 字符")
                return content_text

        # 方法3：從所有 <p> 標籤提取
        paragraphs = soup.find_all('p')
        if paragraphs:
            combined_text = '\n'.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
            if combined_text and len(combined_text) > 100:
                self.logger.debug(f"從 p 標籤提取內容：{len(combined_text)} 字符")
                return combined_text

        self.logger.warning("無法找到文章內容")
        return None

    def _extract_publish_date(self, soup: BeautifulSoup) -> Optional[datetime]:
        """提取發布時間

        支援格式：
        - <time datetime="2025-10-02T05:21:24.000Z">2025-10-02 13:21</time>
        - <p class="alr4vq1"><time datetime="...">...</time></p>
        """
        # 方法1: 尋找 time[datetime] 標籤
        time_element = soup.find('time', attrs={'datetime': True})
        if time_element:
            datetime_attr = time_element.get('datetime')
            if datetime_attr:
                return self._parse_iso_datetime(datetime_attr)

        # 方法2: 其他日期選擇器
        date_selectors = [
            '.publish-time',
            '.date',
            '[data-qa="publish-time"]'
        ]

        for selector in date_selectors:
            date_element = soup.select_one(selector)
            if date_element:
                # 檢查是否包含 time 子元素
                time_elem = date_element.find('time', attrs={'datetime': True})
                if time_elem:
                    datetime_attr = time_elem.get('datetime')
                    if datetime_attr:
                        return self._parse_iso_datetime(datetime_attr)

                # 嘗試從文字內容解析
                date_text = date_element.get_text().strip()
                if date_text:
                    return self._parse_chinese_date(date_text)

        return None

    def _parse_iso_datetime(self, datetime_str: str) -> Optional[datetime]:
        """解析 ISO 格式日期時間

        支援格式：
        - 2025-10-02T05:21:24.000Z
        - 2025-10-02T05:21:24Z
        - 2025-10-02T05:21:24
        """
        try:
            # 移除末尾的 'Z'（表示 UTC）
            if datetime_str.endswith('Z'):
                datetime_str = datetime_str[:-1]

            # 移除毫秒部分（如果有）
            if '.' in datetime_str:
                datetime_str = datetime_str.split('.')[0]

            # 解析 ISO 格式
            return datetime.fromisoformat(datetime_str)
        except ValueError:
            self.logger.warning(f"無法解析 ISO 日期: {datetime_str}")
            return None

    def _parse_chinese_date(self, date_str: str) -> Optional[datetime]:
        """解析中文日期格式"""
        # 移除常見前綴
        date_str = re.sub(r'發布時間[:：]?|更新時間[:：]?', '', date_str).strip()

        # 嘗試解析相對時間
        if '分鐘前' in date_str:
            minutes = re.search(r'(\d+)分鐘前', date_str)
            if minutes:
                from datetime import timedelta
                return datetime.now() - timedelta(minutes=int(minutes.group(1)))

        if '小時前' in date_str:
            hours = re.search(r'(\d+)小時前', date_str)
            if hours:
                from datetime import timedelta
                return datetime.now() - timedelta(hours=int(hours.group(1)))

        # 嘗試解析絕對日期
        return self.parse_date(date_str)

    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """提取作者"""
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
                # 清理作者名稱
                author_text = re.sub(r'記者|編輯|作者[:：]?', '', author_text)
                if author_text:
                    return author_text

        return None

    def _extract_tags(self, soup: BeautifulSoup, category: str) -> List[str]:
        """提取標籤"""
        tags = [category] if category else []

        # 尋找標籤元素
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

    def _determine_expert_domain(
        self,
        category: str,
        title: str,
        content: str
    ) -> str:
        """判斷專家領域"""
        content_lower = (title + " " + content + " " + category).lower()

        # 理財規劃關鍵字
        planning_keywords = [
            "投資", "理財", "基金", "保險", "資產配置",
            "退休", "儲蓄", "財富管理"
        ]

        # 金融分析關鍵字
        analysis_keywords = [
            "股票", "股市", "台股", "美股", "市場", "分析",
            "漲跌", "技術分析", "走勢", "匯率", "外匯", "期貨"
        ]

        # 法律專家關鍵字
        legal_keywords = [
            "法規", "稅務", "法律", "合規", "政策", "監管"
        ]

        # 計算匹配分數
        planning_score = sum(
            1 for keyword in planning_keywords
            if keyword in content_lower
        )
        analysis_score = sum(
            1 for keyword in analysis_keywords
            if keyword in content_lower
        )
        legal_score = sum(
            1 for keyword in legal_keywords
            if keyword in content_lower
        )

        # 判斷主要領域
        if analysis_score >= planning_score and analysis_score >= legal_score:
            return "financial_analysis"
        elif legal_score > planning_score and legal_score > analysis_score:
            return "legal_compliance"
        else:
            return "financial_planning"


def scrape(config: dict) -> List[dict]:
    """爬蟲入口函數，供 ETL 流程調用

    Args:
        config: 爬蟲設定

    Returns:
        爬取結果的字典清單
    """
    with CnyesAutoScraper(config) as scraper:
        articles = scraper.scrape()
        return [article.to_dict() for article in articles]


# 測試函數
def test_scraper():
    """測試爬蟲功能"""
    test_config = {
        "name": "鉅亨網自動爬蟲",
        "articles_per_category": 5,  # 測試時只爬5篇
        "request_delay": (2, 4),
        "max_retries": 3,
        "selenium_browser": "chrome"
    }

    print("=== 測試鉅亨網自動化爬蟲 ===\n")

    with CnyesAutoScraper(test_config) as scraper:
        articles = scraper.scrape()

        print(f"\n共爬取 {len(articles)} 篇新聞\n")

        # 顯示前3篇
        for i, article in enumerate(articles[:3], 1):
            print(f"文章 {i}:")
            print(f"  標題: {article.title}")
            print(f"  分類: {', '.join(article.tags)}")
            print(f"  作者: {article.author}")
            print(f"  發布時間: {article.publish_date}")
            print(f"  專家領域: {article.expert_domain}")
            print(f"  內容長度: {len(article.content)} 字符")
            print(f"  URL: {article.url}")
            print(f"  Hash: {article._generate_content_hash()}")
            print()


if __name__ == "__main__":
    test_scraper()
