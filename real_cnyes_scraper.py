#!/usr/bin/env python3
"""
真實鉅亨網財經新聞爬蟲
- 真正從 cnyes.com 爬取實際財經新聞
- 解析HTML內容提取標題、內容、時間等資訊
- 儲存為JSON格式
"""

import requests
import json
import time
import os
from datetime import datetime
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import urllib.parse

class RealCnyesScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

        # 鉅亨網分類頁面
        self.categories = {
            "台股": "https://news.cnyes.com/news/cat/tw_stock",
            "美股": "https://news.cnyes.com/news/cat/us_stock",
            "基金": "https://news.cnyes.com/news/cat/fund",
            "理財": "https://news.cnyes.com/news/cat/wealth",
            "外匯": "https://news.cnyes.com/news/cat/forex",
            "國際": "https://news.cnyes.com/news/cat/wd_stock"
        }

    def scrape_category_page(self, category: str, url: str, max_articles: int = 5) -> List[Dict]:
        """爬取分類頁面的新聞列表"""
        print(f"正在爬取 {category} 分類: {url}")

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'

            soup = BeautifulSoup(response.text, 'html.parser')
            articles = []

            # 尋找新聞連結 - 鉅亨網的新聞連結格式
            news_links = []

            # 方法1: 尋找包含新聞ID的連結
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if href and '/news/id/' in href:
                    if href.startswith('/'):
                        href = 'https://news.cnyes.com' + href
                    news_links.append(href)

            # 去重並限制數量
            news_links = list(set(news_links))[:max_articles]

            print(f"找到 {len(news_links)} 個新聞連結")

            for i, link in enumerate(news_links):
                print(f"正在處理第 {i+1}/{len(news_links)} 篇新聞...")
                article = self.scrape_article(link, category)
                if article:
                    articles.append(article)
                time.sleep(2)  # 避免過於頻繁請求

            return articles

        except Exception as e:
            print(f"爬取 {category} 分類失敗: {e}")
            return []

    def scrape_article(self, url: str, category: str) -> Dict:
        """爬取單篇新聞內容"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'

            soup = BeautifulSoup(response.text, 'html.parser')

            # 提取標題
            title = ""
            title_selectors = [
                'h1.news-title',
                'h1',
                '.news-title',
                '.title',
                '[class*="title"]'
            ]

            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = title_elem.get_text().strip()
                    break

            # 提取內容
            content = ""
            content_selectors = [
                '.news-content',
                '.article-content',
                '.content',
                '[class*="content"]',
                '.news-body'
            ]

            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # 移除不需要的元素
                    for unwanted in content_elem.find_all(['script', 'style', 'iframe', 'ins']):
                        unwanted.decompose()
                    content = content_elem.get_text().strip()
                    break

            # 提取發布時間
            publish_time = ""
            time_selectors = [
                '.news-time',
                '.publish-time',
                '.time',
                '[class*="time"]',
                '.date'
            ]

            for selector in time_selectors:
                time_elem = soup.select_one(selector)
                if time_elem:
                    publish_time = time_elem.get_text().strip()
                    break

            if not title or not content:
                print(f"無法提取完整內容: {url}")
                return None

            # 清理內容
            content = self.clean_content(content)

            article = {
                "title": title,
                "content": content,
                "url": url,
                "category": category,
                "publish_time": publish_time,
                "scrape_time": datetime.now().isoformat(),
                "source": "cnyes.com"
            }

            print(f"成功爬取: {title[:50]}...")
            return article

        except Exception as e:
            print(f"爬取文章失敗 {url}: {e}")
            return None

    def clean_content(self, content: str) -> str:
        """清理文章內容"""
        # 移除多餘空白
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        content = '\n'.join(lines)

        # 移除常見的廣告或無關內容
        unwanted_phrases = [
            "訂閱",
            "廣告",
            "相關新聞",
            "延伸閱讀",
            "更多新聞",
            "分享",
            "按讚",
            "留言"
        ]

        for phrase in unwanted_phrases:
            content = content.replace(phrase, "")

        return content.strip()

    def scrape_all_categories(self, max_articles_per_category: int = 3) -> List[Dict]:
        """爬取所有分類的新聞"""
        all_articles = []

        for category, url in self.categories.items():
            print(f"\n開始爬取 {category} 分類...")
            articles = self.scrape_category_page(category, url, max_articles_per_category)
            all_articles.extend(articles)
            print(f"{category} 分類完成，共 {len(articles)} 篇文章")
            time.sleep(3)  # 分類間間隔

        return all_articles

    def save_to_json(self, articles: List[Dict], filename: str = None) -> str:
        """儲存為JSON檔案"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"real_cnyes_news_{timestamp}.json"

        # 確保data目錄存在
        data_dir = "data"
        os.makedirs(data_dir, exist_ok=True)

        filepath = os.path.join(data_dir, filename)

        # 建立JSON結構
        json_data = {
            "metadata": {
                "source": "cnyes.com",
                "scrape_time": datetime.now().isoformat(),
                "total_articles": len(articles),
                "categories": list(set(article["category"] for article in articles)),
                "scraper": "RealCnyesScraper"
            },
            "articles": articles
        }

        # 儲存檔案
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)

        print(f"\n新聞已儲存至: {filepath}")
        return filepath


def main():
    """主執行函數"""
    print("真實鉅亨網新聞爬蟲")
    print("=" * 50)

    scraper = RealCnyesScraper()

    try:
        # 爬取所有分類的新聞
        articles = scraper.scrape_all_categories(max_articles_per_category=3)

        if articles:
            # 儲存為JSON
            json_file = scraper.save_to_json(articles)

            # 顯示結果
            print(f"\n爬取完成！")
            print(f"總共爬取: {len(articles)} 篇新聞")

            # 按分類統計
            category_count = {}
            for article in articles:
                category = article["category"]
                category_count[category] = category_count.get(category, 0) + 1

            print("\n分類統計:")
            for category, count in category_count.items():
                print(f"- {category}: {count} 篇")

            print(f"\nJSON檔案: {json_file}")

            # 顯示前3篇新聞標題
            print("\n範例新聞:")
            for i, article in enumerate(articles[:3], 1):
                print(f"{i}. [{article['category']}] {article['title']}")
                print(f"   內容預覽: {article['content'][:100]}...")
                print()
        else:
            print("未能爬取到任何新聞")

    except Exception as e:
        print(f"爬取過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()