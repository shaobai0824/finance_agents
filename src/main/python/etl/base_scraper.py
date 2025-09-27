"""
BaseScraper - 基礎爬蟲抽象類別

實作 Linus 哲學：
1. 簡潔執念：統一的爬蟲介面，避免重複代碼
2. 好品味：一致的錯誤處理和日誌記錄
3. 實用主義：專注解決實際的資料擷取需求
4. Never break userspace：穩定的 API，向後兼容
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging
import time
import random
import requests
from datetime import datetime
from dataclasses import dataclass
import hashlib
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class ScrapedArticle:
    """爬取文章的標準化資料結構

    Linus 哲學：好品味的資料結構
    - 統一的格式，便於後續處理
    - 包含必要的元資料
    - 支援來源追蹤
    """
    title: str
    content: str
    url: str
    publish_date: Optional[datetime] = None
    author: Optional[str] = None
    tags: List[str] = None
    source_website: str = ""
    expert_domain: str = ""

    def __post_init__(self):
        if self.tags is None:
            self.tags = []

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "title": self.title,
            "content": self.content,
            "url": self.url,
            "publish_date": self.publish_date.isoformat() if self.publish_date else None,
            "author": self.author,
            "tags": self.tags,
            "source_website": self.source_website,
            "expert_domain": self.expert_domain,
            "scraped_at": datetime.now().isoformat(),
            "content_hash": self._generate_content_hash()
        }

    def _generate_content_hash(self) -> str:
        """生成內容 hash，用於重複檢測"""
        content_str = f"{self.title}{self.content}{self.url}"
        return hashlib.md5(content_str.encode()).hexdigest()


class BaseScraper(ABC):
    """基礎爬蟲抽象類別

    所有具體爬蟲都應繼承此類
    """

    def __init__(self, config: Dict[str, Any]):
        """初始化爬蟲

        Args:
            config: 爬蟲設定字典
        """
        self.config = config
        self.name = config.get("name", self.__class__.__name__)
        self.expert_domain = config.get("expert_domain", "general")
        self.max_retries = config.get("max_retries", 3)
        self.request_delay = config.get("request_delay", (1, 3))  # 隨機延遲範圍
        self.timeout = config.get("timeout", 30)

        # 設定日誌
        self.logger = logging.getLogger(f"etl.{self.name}")

        # HTTP 會話設定
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.get('user_agent',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            )
        })

        # Selenium 驅動器（延遲初始化）
        self._driver = None

    @abstractmethod
    def scrape(self) -> List[ScrapedArticle]:
        """執行爬蟲，返回文章清單

        這是每個具體爬蟲必須實作的方法

        Returns:
            爬取到的文章清單
        """
        pass

    @abstractmethod
    def _parse_article_list(self, content: str) -> List[str]:
        """解析文章清單頁面，提取文章連結

        Args:
            content: 頁面 HTML 內容

        Returns:
            文章 URL 清單
        """
        pass

    @abstractmethod
    def _parse_article_detail(self, url: str, content: str) -> Optional[ScrapedArticle]:
        """解析文章詳細頁面

        Args:
            url: 文章 URL
            content: 頁面 HTML 內容

        Returns:
            解析後的文章物件，解析失敗返回 None
        """
        pass

    def get_page_content(self, url: str, use_selenium: bool = False) -> Optional[str]:
        """取得頁面內容

        Args:
            url: 目標 URL
            use_selenium: 是否使用 Selenium（用於動態載入頁面）

        Returns:
            頁面 HTML 內容，失敗返回 None
        """
        for attempt in range(self.max_retries):
            try:
                if use_selenium:
                    content = self._get_content_with_selenium(url)
                else:
                    content = self._get_content_with_requests(url)

                if content:
                    self.logger.debug(f"成功取得頁面內容: {url}")
                    return content

            except Exception as e:
                self.logger.warning(f"取得頁面內容失敗 (嘗試 {attempt + 1}/{self.max_retries}): {url}, 錯誤: {e}")

                # 失敗後等待再重試
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # 指數退避
                    time.sleep(wait_time)

        self.logger.error(f"無法取得頁面內容: {url}")
        return None

    def _get_content_with_requests(self, url: str) -> Optional[str]:
        """使用 requests 取得頁面內容"""
        self._random_delay()

        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        response.encoding = response.apparent_encoding  # 自動檢測編碼

        return response.text

    def _get_content_with_selenium(self, url: str) -> Optional[str]:
        """使用 Selenium 取得頁面內容"""
        if not self._driver:
            self._init_selenium_driver()

        self._driver.get(url)

        # 等待頁面載入完成
        WebDriverWait(self._driver, self.timeout).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # 額外等待動態內容載入
        time.sleep(2)

        return self._driver.page_source

    def _init_selenium_driver(self):
        """初始化 Selenium 驅動器"""
        browser = self.config.get("selenium_browser", "chrome").lower()

        if browser == "chrome":
            options = ChromeOptions()
            options.add_argument("--headless")  # 無頭模式
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument(f"--user-agent={self.session.headers['User-Agent']}")

            self._driver = webdriver.Chrome(options=options)

        elif browser == "firefox":
            options = FirefoxOptions()
            options.add_argument("--headless")
            options.set_preference("general.useragent.override", self.session.headers['User-Agent'])

            self._driver = webdriver.Firefox(options=options)

        else:
            raise ValueError(f"不支援的瀏覽器: {browser}")

        self.logger.info(f"已初始化 {browser} Selenium 驅動器")

    def _random_delay(self):
        """隨機延遲，避免被反爬蟲機制偵測"""
        if isinstance(self.request_delay, tuple):
            delay = random.uniform(*self.request_delay)
        else:
            delay = self.request_delay

        time.sleep(delay)

    def clean_text(self, text: str) -> str:
        """清理文字內容

        Args:
            text: 原始文字

        Returns:
            清理後的文字
        """
        if not text:
            return ""

        # 移除多餘空白和換行
        text = ' '.join(text.split())

        # 移除常見的廣告文字模式
        ad_patterns = [
            "※ 本網站及資訊不構成投資建議",
            "※ 投資人應審慎考量本身之投資風險",
            "廣告",
            "贊助商廣告",
            "相關新聞",
            "延伸閱讀"
        ]

        for pattern in ad_patterns:
            text = text.replace(pattern, "")

        return text.strip()

    def parse_date(self, date_str: str) -> Optional[datetime]:
        """解析日期字串

        Args:
            date_str: 日期字串

        Returns:
            解析後的 datetime 物件，失敗返回 None
        """
        if not date_str:
            return None

        # 常見的日期格式
        date_formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%Y/%m/%d %H:%M:%S",
            "%Y/%m/%d %H:%M",
            "%Y/%m/%d",
            "%m-%d %H:%M",
            "%m/%d %H:%M"
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue

        self.logger.warning(f"無法解析日期格式: {date_str}")
        return None

    def __enter__(self):
        """上下文管理器進入"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出，清理資源"""
        self.cleanup()

    def cleanup(self):
        """清理資源"""
        if self._driver:
            try:
                self._driver.quit()
                self.logger.info("已關閉 Selenium 驅動器")
            except Exception as e:
                self.logger.warning(f"關閉 Selenium 驅動器時發生錯誤: {e}")

        if self.session:
            self.session.close()


# 工具函數
def extract_text_from_html(html_content: str, selector: str = None) -> str:
    """從 HTML 中提取純文字

    Args:
        html_content: HTML 內容
        selector: CSS 選擇器（可選）

    Returns:
        提取的純文字
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # 移除腳本和樣式標籤
    for script in soup(["script", "style", "nav", "footer", "aside"]):
        script.decompose()

    if selector:
        element = soup.select_one(selector)
        text = element.get_text() if element else ""
    else:
        text = soup.get_text()

    # 清理文字
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = ' '.join(chunk for chunk in chunks if chunk)

    return text