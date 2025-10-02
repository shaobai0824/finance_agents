#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新聞爬取定時排程系統

功能：
1. 每日定時自動爬取鉅亨網新聞
2. 自動去重並載入向量資料庫
3. 記錄執行日誌
4. 支援手動觸發
5. 支援配置不同的排程時間

遵循 Linus 哲學：
- 簡潔：清晰的排程邏輯
- 實用：解決實際的自動化需求
- 好品味：統一的錯誤處理
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import json

# 添加專案路徑
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src" / "main" / "python"))

from dotenv import load_dotenv
load_dotenv()

from src.main.python.etl.auto_news_pipeline import run_auto_scrape_and_load

# 配置日誌
log_dir = project_root / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "news_scheduler.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class NewsScheduler:
    """新聞爬取定時排程器"""

    def __init__(self, config: dict = None):
        """初始化排程器

        Args:
            config: 配置字典
                - hour: 每日執行時間（小時，0-23）
                - minute: 每日執行時間（分鐘，0-59）
                - articles_per_category: 每個分類爬取的文章數
                - collection_name: 向量資料庫集合名稱
        """
        self.config = config or {}

        # 預設配置
        self.hour = self.config.get('hour', 9)  # 預設每天早上9點
        self.minute = self.config.get('minute', 0)
        self.articles_per_category = self.config.get('articles_per_category', 20)
        self.collection_name = self.config.get(
            'collection_name',
            'finance_knowledge_optimal'
        )

        # 初始化排程器
        self.scheduler = BlockingScheduler()

        # 結果歷史記錄
        self.history_file = log_dir / "execution_history.json"
        self.execution_history = self._load_history()

    def _load_history(self) -> list:
        """載入執行歷史"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"載入執行歷史失敗: {e}")
                return []
        return []

    def _save_history(self):
        """儲存執行歷史"""
        try:
            # 只保留最近30天的記錄
            recent_history = self.execution_history[-30:]

            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(recent_history, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"儲存執行歷史失敗: {e}")

    def scheduled_job(self):
        """定時任務：爬取新聞並載入"""
        logger.info("=" * 80)
        logger.info(f"開始執行定時爬取任務 - {datetime.now()}")
        logger.info("=" * 80)

        try:
            # 執行自動化流程
            result = run_auto_scrape_and_load(
                articles_per_category=self.articles_per_category,
                collection_name=self.collection_name
            )

            # 記錄結果
            self.execution_history.append(result)
            self._save_history()

            # 輸出結果摘要
            logger.info("=" * 80)
            logger.info("定時任務執行完成")
            logger.info("=" * 80)
            logger.info(f"成功: {result.get('success')}")
            logger.info(f"爬取文章數: {result.get('scraped_count')}")
            logger.info(f"載入文檔塊數: {result.get('loaded_count')}")

            if result.get('error'):
                logger.error(f"錯誤: {result.get('error')}")

        except Exception as e:
            logger.error(f"定時任務執行失敗: {e}")
            import traceback
            traceback.print_exc()

            # 記錄失敗
            error_result = {
                "success": False,
                "error": str(e),
                "start_time": datetime.now().isoformat(),
                "end_time": datetime.now().isoformat()
            }
            self.execution_history.append(error_result)
            self._save_history()

    def start(self):
        """啟動排程器"""
        # 添加定時任務
        trigger = CronTrigger(hour=self.hour, minute=self.minute)

        self.scheduler.add_job(
            self.scheduled_job,
            trigger=trigger,
            id='daily_news_scrape',
            name='每日新聞爬取',
            replace_existing=True
        )

        logger.info(f"排程器已啟動，每日 {self.hour:02d}:{self.minute:02d} 執行新聞爬取")
        logger.info(f"每個分類爬取 {self.articles_per_category} 篇文章")
        logger.info(f"目標集合: {self.collection_name}")
        logger.info("按 Ctrl+C 停止排程器")

        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("排程器已停止")
            self.scheduler.shutdown()

    def run_once(self):
        """手動執行一次（不啟動排程）"""
        logger.info("手動執行爬取任務（不啟動排程）")
        self.scheduled_job()

    def show_history(self, limit: int = 10):
        """顯示執行歷史

        Args:
            limit: 顯示最近的記錄數
        """
        logger.info(f"\n最近 {limit} 次執行記錄：\n")

        recent = self.execution_history[-limit:]

        for i, record in enumerate(reversed(recent), 1):
            logger.info(f"記錄 {i}:")
            logger.info(f"  時間: {record.get('start_time')}")
            logger.info(f"  成功: {record.get('success')}")
            logger.info(f"  爬取數: {record.get('scraped_count', 0)}")
            logger.info(f"  載入數: {record.get('loaded_count', 0)}")

            if record.get('error'):
                logger.info(f"  錯誤: {record.get('error')}")

            logger.info("")


def main():
    """主函數"""
    import argparse

    parser = argparse.ArgumentParser(
        description='新聞爬取定時排程系統'
    )

    parser.add_argument(
        '--mode',
        choices=['schedule', 'once', 'history'],
        default='schedule',
        help='執行模式：schedule=啟動排程，once=執行一次，history=查看歷史'
    )

    parser.add_argument(
        '--hour',
        type=int,
        default=9,
        help='每日執行時間（小時，0-23），預設 9'
    )

    parser.add_argument(
        '--minute',
        type=int,
        default=0,
        help='每日執行時間（分鐘，0-59），預設 0'
    )

    parser.add_argument(
        '--articles',
        type=int,
        default=20,
        help='每個分類爬取的文章數，預設 20'
    )

    parser.add_argument(
        '--collection',
        type=str,
        default='finance_knowledge_optimal',
        help='向量資料庫集合名稱'
    )

    args = parser.parse_args()

    # 配置
    config = {
        'hour': args.hour,
        'minute': args.minute,
        'articles_per_category': args.articles,
        'collection_name': args.collection
    }

    # 初始化排程器
    scheduler = NewsScheduler(config)

    # 執行對應模式
    if args.mode == 'schedule':
        scheduler.start()
    elif args.mode == 'once':
        scheduler.run_once()
    elif args.mode == 'history':
        scheduler.show_history(limit=10)


if __name__ == "__main__":
    main()
