#!/usr/bin/env python3
"""
Finance Agents ETL 主執行腳本

自動化爬蟲與向量化流程的入口點
支援單一來源測試、完整流程執行、排程管理
"""

import asyncio
import argparse
import logging
import sys
import yaml
from datetime import datetime
from pathlib import Path
from typing import Optional, List

# 添加專案路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.main.python.etl.etl_manager import ETLManager


def setup_logging(config: dict):
    """設定日誌系統"""
    log_config = config.get("logging", {})

    # 建立日誌目錄
    log_file = log_config.get("file", "./logs/etl.log")
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # 設定日誌格式
    log_format = log_config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    log_level = getattr(logging, log_config.get("level", "INFO"))

    # 配置 root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    # 設定第三方庫日誌級別
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("selenium").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)


def load_config(config_path: str) -> dict:
    """載入設定檔"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 合併全域設定到各個來源
        global_settings = config.get("global_settings", {})
        for source in config.get("sources", []):
            source_config = source.get("config", {})
            for key, value in global_settings.items():
                if key not in source_config:
                    source_config[key] = value
            source["config"] = source_config

        return config

    except Exception as e:
        print(f"❌ 載入設定檔失敗: {config_path}, 錯誤: {e}")
        sys.exit(1)


async def run_full_etl(config_path: str):
    """執行完整 ETL 流程"""
    print("🚀 啟動 Finance Agents ETL 自動化流程")
    print("=" * 60)

    # 載入設定
    config = load_config(config_path)
    setup_logging(config)

    logger = logging.getLogger("main")
    logger.info("開始執行完整 ETL 流程")

    try:
        # 建立 ETL 管理器
        etl_manager = ETLManager(config)

        # 執行 ETL 流程
        stats = await etl_manager.run_full_etl()

        # 顯示結果
        print("\n🎉 ETL 流程執行完成")
        print("📊 執行統計:")
        print(f"   ✅ 爬取文章: {stats['total_scraped']}")
        print(f"   🔧 處理文檔: {stats['total_processed']}")
        print(f"   📤 載入向量: {stats['total_loaded']}")

        if stats['failed_sources']:
            print(f"   ❌ 失敗來源: {len(stats['failed_sources'])}")
            for failed in stats['failed_sources']:
                print(f"      - {failed['name']}: {failed['error']}")

        duration = stats['end_time'] - stats['start_time']
        print(f"   ⏱️  執行時間: {duration}")

        logger.info("ETL 流程執行完成")
        return True

    except Exception as e:
        logger.error(f"ETL 流程執行失敗: {e}", exc_info=True)
        print(f"❌ ETL 流程執行失敗: {e}")
        return False


async def test_single_source(config_path: str, source_name: str):
    """測試單一資料來源"""
    print(f"🧪 測試資料來源: {source_name}")
    print("=" * 60)

    # 載入設定
    config = load_config(config_path)
    setup_logging(config)

    logger = logging.getLogger("test")
    logger.info(f"開始測試資料來源: {source_name}")

    try:
        # 建立 ETL 管理器
        etl_manager = ETLManager(config)

        # 測試單一來源
        stats = await etl_manager.test_single_source(source_name)

        # 顯示結果
        print(f"\n✅ 測試完成: {source_name}")
        print("📊 測試統計:")
        print(f"   📥 爬取文章: {stats['total_scraped']}")
        print(f"   🔧 處理文檔: {stats['total_processed']}")
        print(f"   📤 載入向量: {stats['total_loaded']}")

        if stats['failed_sources']:
            print(f"   ❌ 測試失敗: {stats['failed_sources'][0]['error']}")

        duration = stats['end_time'] - stats['start_time']
        print(f"   ⏱️  執行時間: {duration}")

        logger.info(f"資料來源測試完成: {source_name}")
        return True

    except Exception as e:
        logger.error(f"測試資料來源失敗: {e}", exc_info=True)
        print(f"❌ 測試失敗: {e}")
        return False


def list_sources(config_path: str):
    """列出所有可用的資料來源"""
    config = load_config(config_path)

    print("📋 可用的資料來源:")
    print("=" * 60)

    sources = config.get("sources", [])
    if not sources:
        print("❌ 沒有設定任何資料來源")
        return

    enabled_count = 0
    for i, source in enumerate(sources, 1):
        name = source.get("name", "Unknown")
        module = source.get("module", "Unknown")
        domain = source.get("expert_domain", "Unknown")
        enabled = source.get("enabled", False)
        priority = source.get("priority", 0)
        schedule = source.get("schedule", "Manual")

        status = "✅ 啟用" if enabled else "⏸️  停用"
        if enabled:
            enabled_count += 1

        print(f"{i:2d}. {name}")
        print(f"    狀態: {status}")
        print(f"    專家領域: {domain}")
        print(f"    優先級: {priority}")
        print(f"    排程: {schedule}")
        print(f"    模組: {module}")
        print()

    print(f"📊 總計: {len(sources)} 個來源，{enabled_count} 個啟用")


async def run_by_priority(config_path: str, priority: int):
    """依優先級執行 ETL"""
    print(f"🎯 執行優先級 {priority} 的資料來源")
    print("=" * 60)

    config = load_config(config_path)
    setup_logging(config)

    # 篩選指定優先級的來源
    filtered_sources = [
        source for source in config.get("sources", [])
        if source.get("priority") == priority and source.get("enabled", True)
    ]

    if not filtered_sources:
        print(f"❌ 沒有找到優先級 {priority} 的啟用資料來源")
        return False

    # 建立新的設定，只包含篩選的來源
    filtered_config = config.copy()
    filtered_config["sources"] = filtered_sources

    print(f"📋 將執行 {len(filtered_sources)} 個資料來源:")
    for source in filtered_sources:
        print(f"   - {source.get('name')}")

    # 執行 ETL
    etl_manager = ETLManager(filtered_config)
    stats = await etl_manager.run_full_etl()

    # 顯示結果
    print(f"\n🎉 優先級 {priority} ETL 執行完成")
    print("📊 執行統計:")
    print(f"   ✅ 爬取文章: {stats['total_scraped']}")
    print(f"   🔧 處理文檔: {stats['total_processed']}")
    print(f"   📤 載入向量: {stats['total_loaded']}")

    return True


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description="Finance Agents ETL 自動化爬蟲系統",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  python run_etl.py --full                          # 執行完整 ETL 流程
  python run_etl.py --test "全國法規資料庫"          # 測試單一資料來源
  python run_etl.py --list                          # 列出所有資料來源
  python run_etl.py --priority 1                    # 執行優先級 1 的來源
  python run_etl.py --config custom_config.yaml     # 使用自訂設定檔
        """
    )

    parser.add_argument(
        "--config", "-c",
        default="etl_config.yaml",
        help="設定檔路徑 (預設: etl_config.yaml)"
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--full", "-f",
        action="store_true",
        help="執行完整 ETL 流程"
    )
    group.add_argument(
        "--test", "-t",
        metavar="SOURCE_NAME",
        help="測試單一資料來源"
    )
    group.add_argument(
        "--list", "-l",
        action="store_true",
        help="列出所有可用的資料來源"
    )
    group.add_argument(
        "--priority", "-p",
        type=int,
        metavar="PRIORITY",
        help="依優先級執行 ETL (1=最高優先級)"
    )

    args = parser.parse_args()

    # 檢查設定檔是否存在
    if not Path(args.config).exists():
        print(f"❌ 設定檔不存在: {args.config}")
        sys.exit(1)

    # 執行對應的操作
    try:
        if args.full:
            success = asyncio.run(run_full_etl(args.config))
            sys.exit(0 if success else 1)

        elif args.test:
            success = asyncio.run(test_single_source(args.config, args.test))
            sys.exit(0 if success else 1)

        elif args.list:
            list_sources(args.config)
            sys.exit(0)

        elif args.priority is not None:
            success = asyncio.run(run_by_priority(args.config, args.priority))
            sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n⚠️  使用者中斷執行")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 執行失敗: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()