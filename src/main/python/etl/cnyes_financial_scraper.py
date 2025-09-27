"""
鉅亨網財經資料爬蟲系統 (改良版)

實作 Linus 哲學：
1. 簡潔執念：專注財經新聞的高效爬取
2. 好品味：結構化的資料提取和清理
3. 實用主義：專為理財專家系統設計
4. Never break userspace：穩定的JSON輸出格式
"""

import asyncio
import aiohttp
import logging
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import time
import os
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class FinancialArticle:
    """財經文章資料結構"""
    title: str
    content: str
    url: str
    category: str
    publish_date: str
    author: str
    tags: List[str]
    summary: str
    source: str = "cnyes.com"
    scrape_time: str = ""
    expert_domain: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return asdict(self)

    def to_vector_format(self) -> Dict[str, Any]:
        """轉換為向量資料庫格式"""
        return {
            "content": f"{self.title}\n\n{self.summary}\n\n{self.content}",
            "metadata": {
                "title": self.title,
                "url": self.url,
                "category": self.category,
                "publish_date": self.publish_date,
                "author": self.author,
                "tags": ", ".join(self.tags) if self.tags else "",
                "source": self.source,
                "expert_domain": self.expert_domain,
                "scrape_time": self.scrape_time
            },
            "source": f"鉅亨網 - {self.category}"
        }


class CnyesFinancialScraper:
    """鉅亨網財經資料爬蟲"""

    def __init__(self):
        self.base_url = "https://news.cnyes.com"
        self.session = None

        # 財經分類對應表
        self.categories = {
            "台股": {
                "url": "https://news.cnyes.com/news/cat/tw_stock",
                "expert_domain": "financial_analysis",
                "keywords": ["台股", "上市", "股價", "漲跌", "成交量"]
            },
            "美股": {
                "url": "https://news.cnyes.com/news/cat/us_stock",
                "expert_domain": "financial_analysis",
                "keywords": ["美股", "道瓊", "納斯達克", "S&P500", "Fed"]
            },
            "基金": {
                "url": "https://news.cnyes.com/news/cat/fund",
                "expert_domain": "financial_planning",
                "keywords": ["基金", "投信", "淨值", "配息", "ETF"]
            },
            "理財": {
                "url": "https://news.cnyes.com/news/cat/wealth",
                "expert_domain": "financial_planning",
                "keywords": ["理財", "投資", "資產配置", "退休", "保險"]
            },
            "外匯": {
                "url": "https://news.cnyes.com/news/cat/forex",
                "expert_domain": "financial_analysis",
                "keywords": ["外匯", "匯率", "美元", "央行", "升息"]
            },
            "債券": {
                "url": "https://news.cnyes.com/news/cat/bond",
                "expert_domain": "financial_planning",
                "keywords": ["債券", "公債", "殖利率", "信評", "企業債"]
            }
        }

        # HTTP headers
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }

    async def __aenter__(self):
        """異步上下文管理器進入"""
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=10)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器退出"""
        if self.session:
            await self.session.close()

    async def scrape_financial_news(self, max_articles_per_category: int = 20) -> List[FinancialArticle]:
        """爬取財經新聞"""
        logger.info("開始爬取鉅亨網財經新聞...")

        all_articles = []

        for category_name, category_info in self.categories.items():
            logger.info(f"爬取類別: {category_name}")

            try:
                articles = await self._scrape_category(
                    category_name,
                    category_info,
                    max_articles_per_category
                )
                all_articles.extend(articles)
                logger.info(f"類別 {category_name} 完成，爬取 {len(articles)} 篇文章")

                # 避免過於頻繁的請求
                await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"爬取類別 {category_name} 失敗: {e}")
                continue

        logger.info(f"總共爬取 {len(all_articles)} 篇財經文章")
        return all_articles

    async def _scrape_category(self, category_name: str, category_info: Dict, max_articles: int) -> List[FinancialArticle]:
        """爬取特定類別的新聞"""
        articles = []
        category_url = category_info["url"]

        try:
            # 獲取類別頁面
            async with self.session.get(category_url) as response:
                if response.status != 200:
                    logger.warning(f"類別頁面 {category_name} 回應異常: {response.status}")
                    return articles

                html_content = await response.text()

            # 解析文章連結
            article_links = self._extract_article_links(html_content)

            # 限制文章數量
            article_links = article_links[:max_articles]

            # 爬取每篇文章
            for link in article_links:
                try:
                    article = await self._scrape_article(link, category_name, category_info)
                    if article:
                        articles.append(article)

                    # 控制請求頻率
                    await asyncio.sleep(1)

                except Exception as e:
                    logger.warning(f"爬取文章失敗 {link}: {e}")
                    continue

        except Exception as e:
            logger.error(f"爬取類別 {category_name} 時發生錯誤: {e}")

        return articles

    def _extract_article_links(self, html_content: str) -> List[str]:
        """從類別頁面提取文章連結"""
        soup = BeautifulSoup(html_content, 'html.parser')
        links = []

        # 多種選擇器策略
        selectors = [
            'a[href*="/news/id/"]',
            '.news-item a',
            '.article-item a',
            'article a',
            '.title a'
        ]

        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                href = element.get('href')
                if href and '/news/id/' in href:
                    full_url = urljoin(self.base_url, href)
                    if full_url not in links:
                        links.append(full_url)

        logger.debug(f"提取到 {len(links)} 個文章連結")
        return links

    async def _scrape_article(self, url: str, category: str, category_info: Dict) -> Optional[FinancialArticle]:
        """爬取單篇文章"""
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return None

                html_content = await response.text()

            # 解析文章內容
            soup = BeautifulSoup(html_content, 'html.parser')

            # 提取標題
            title = self._extract_title(soup)
            if not title:
                return None

            # 提取內容
            content = self._extract_content(soup)
            if not content or len(content) < 100:
                return None

            # 提取其他資訊
            publish_date = self._extract_publish_date(soup)
            author = self._extract_author(soup)
            tags = self._extract_tags(soup, category_info["keywords"])
            summary = self._generate_summary(content)

            # 建立文章物件
            article = FinancialArticle(
                title=title,
                content=content,
                url=url,
                category=category,
                publish_date=publish_date,
                author=author or "鉅亨網編輯",
                tags=tags,
                summary=summary,
                expert_domain=category_info["expert_domain"],
                scrape_time=datetime.now().isoformat()
            )

            logger.debug(f"成功爬取文章: {title[:50]}...")
            return article

        except Exception as e:
            logger.warning(f"爬取文章失敗 {url}: {e}")
            return None

    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """提取文章標題"""
        selectors = [
            'h1.title',
            'h1[data-qa="article-title"]',
            '.article-title h1',
            '.news-title h1',
            'h1',
            '.title',
            '[data-qa="headline"]'
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text().strip()
                if title and len(title) > 5:
                    return self._clean_text(title)

        return None

    def _extract_content(self, soup: BeautifulSoup) -> Optional[str]:
        """提取文章內容"""
        selectors = [
            '.article-content',
            '.news-content',
            '[data-qa="article-content"]',
            '.content',
            'article .content',
            '.post-content',
            '.entry-content'
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                # 移除不需要的元素
                for unwanted in element.select('.ad, .advertisement, .social-share, .related-news, .tags, .author-info'):
                    unwanted.decompose()

                # 提取純文字
                content = element.get_text(separator='\n').strip()
                content = self._clean_text(content)

                if content and len(content) > 100:
                    return content

        return None

    def _extract_publish_date(self, soup: BeautifulSoup) -> str:
        """提取發布日期"""
        selectors = [
            'time[datetime]',
            '.publish-time',
            '.date',
            '[data-qa="publish-time"]',
            '.meta-time'
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                # 嘗試從 datetime 屬性獲取
                datetime_attr = element.get('datetime')
                if datetime_attr:
                    try:
                        # 解析 ISO 格式日期
                        parsed_date = datetime.fromisoformat(datetime_attr.replace('Z', '+00:00'))
                        return parsed_date.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        pass

                # 從文字內容解析
                date_text = element.get_text().strip()
                if date_text:
                    parsed_date = self._parse_chinese_date(date_text)
                    if parsed_date:
                        return parsed_date.strftime('%Y-%m-%d %H:%M:%S')

        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def _extract_author(self, soup: BeautifulSoup) -> Optional[str]:
        """提取作者"""
        selectors = [
            '.author',
            '.reporter',
            '[data-qa="author"]',
            '.byline',
            '.meta-author'
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                author_text = element.get_text().strip()
                # 清理作者名稱
                author_text = re.sub(r'記者|編輯|作者|撰稿[:：]?', '', author_text).strip()
                if author_text:
                    return author_text

        return None

    def _extract_tags(self, soup: BeautifulSoup, category_keywords: List[str]) -> List[str]:
        """提取標籤"""
        tags = category_keywords.copy()

        # 從頁面提取標籤
        tag_selectors = [
            '.tags a',
            '.keywords a',
            '.category a',
            '.tag-list a'
        ]

        for selector in tag_selectors:
            elements = soup.select(selector)
            for element in elements:
                tag_text = element.get_text().strip()
                if tag_text and tag_text not in tags:
                    tags.append(tag_text)

        # 限制標籤數量
        return tags[:10]

    def _generate_summary(self, content: str, max_length: int = 200) -> str:
        """生成文章摘要"""
        # 取前幾句話作為摘要
        sentences = re.split(r'[。！？]', content)
        summary = ""

        for sentence in sentences:
            if len(summary + sentence) <= max_length:
                summary += sentence + "。"
            else:
                break

        return summary.strip() or content[:max_length] + "..."

    def _clean_text(self, text: str) -> str:
        """清理文字"""
        # 移除多餘的空白和換行
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n+', '\n', text)

        # 移除特殊字符
        text = re.sub(r'[^\w\s\u4e00-\u9fff。，！？：；「」『』（）\[\]%-]', '', text)

        return text.strip()

    def _parse_chinese_date(self, date_str: str) -> Optional[datetime]:
        """解析中文日期格式"""
        # 移除多餘文字
        date_str = re.sub(r'發布時間|更新時間[:：]?', '', date_str).strip()

        # 相對時間處理
        if '分鐘前' in date_str:
            minutes = re.search(r'(\d+)分鐘前', date_str)
            if minutes:
                return datetime.now() - timedelta(minutes=int(minutes.group(1)))

        if '小時前' in date_str:
            hours = re.search(r'(\d+)小時前', date_str)
            if hours:
                return datetime.now() - timedelta(hours=int(hours.group(1)))

        if '天前' in date_str:
            days = re.search(r'(\d+)天前', date_str)
            if days:
                return datetime.now() - timedelta(days=int(days.group(1)))

        # 嘗試解析具體日期格式
        date_patterns = [
            r'(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2})',
            r'(\d{4})/(\d{2})/(\d{2})\s+(\d{2}):(\d{2})',
            r'(\d{2})/(\d{2})/(\d{4})\s+(\d{2}):(\d{2})'
        ]

        for pattern in date_patterns:
            match = re.search(pattern, date_str)
            if match:
                try:
                    if len(match.groups()) == 5:
                        year, month, day, hour, minute = match.groups()
                        return datetime(int(year), int(month), int(day), int(hour), int(minute))
                except:
                    continue

        return None

    def save_to_json(self, articles: List[FinancialArticle], filename: str = None) -> str:
        """儲存為JSON檔案"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"cnyes_financial_news_{timestamp}.json"

        # 確保資料夾存在
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data")
        os.makedirs(data_dir, exist_ok=True)

        filepath = os.path.join(data_dir, filename)

        # 轉換為字典格式
        articles_data = [article.to_dict() for article in articles]

        # 建立完整的JSON結構
        output_data = {
            "scrape_info": {
                "source": "cnyes.com",
                "scrape_time": datetime.now().isoformat(),
                "total_articles": len(articles_data),
                "categories": list(self.categories.keys())
            },
            "articles": articles_data
        }

        # 儲存JSON檔案
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        logger.info(f"財經新聞已儲存至: {filepath}")
        return filepath


async def main():
    """主執行函數"""
    print("鉅亨網財經資料爬蟲系統")
    print("=" * 50)

    try:
        async with CnyesFinancialScraper() as scraper:
            # 爬取財經新聞
            articles = await scraper.scrape_financial_news(max_articles_per_category=15)

            if articles:
                # 儲存為JSON
                json_file = scraper.save_to_json(articles)

                # 顯示統計資訊
                print(f"\n[成功] 爬取完成！")
                print(f"總文章數: {len(articles)}")

                # 按類別統計
                category_stats = {}
                for article in articles:
                    category = article.category
                    category_stats[category] = category_stats.get(category, 0) + 1

                print(f"\n類別統計:")
                for category, count in category_stats.items():
                    print(f"  {category}: {count} 篇")

                print(f"\nJSON檔案: {json_file}")

                # 顯示範例文章
                print(f"\n範例文章:")
                for i, article in enumerate(articles[:3], 1):
                    print(f"\n{i}. 標題: {article.title}")
                    print(f"   類別: {article.category}")
                    print(f"   作者: {article.author}")
                    print(f"   日期: {article.publish_date}")
                    print(f"   摘要: {article.summary[:100]}...")

            else:
                print("[錯誤] 未能爬取到任何文章")

    except Exception as e:
        print(f"[錯誤] 爬蟲執行失敗: {e}")
        logger.error(f"爬蟲執行失敗: {e}", exc_info=True)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    asyncio.run(main())