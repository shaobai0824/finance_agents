#!/usr/bin/env python3
"""
ETL 排程設定腳本

設定定時任務執行 ETL 流程
支援 Windows 工作排程器 和 Linux Cron
"""

import os
import sys
import platform
import subprocess
from pathlib import Path
import yaml


def load_config(config_path: str = "etl_config.yaml") -> dict:
    """載入 ETL 設定檔"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"❌ 載入設定檔失敗: {e}")
        sys.exit(1)


def setup_windows_scheduler(config: dict):
    """設定 Windows 工作排程器"""
    print("🪟 設定 Windows 工作排程器...")

    project_root = Path(__file__).parent.absolute()
    python_path = sys.executable
    script_path = project_root / "run_etl.py"
    config_path = project_root / "etl_config.yaml"

    sources = config.get("sources", [])
    enabled_sources = [s for s in sources if s.get("enabled", False)]

    if not enabled_sources:
        print("❌ 沒有啟用的資料來源")
        return

    print(f"📋 將建立 {len(enabled_sources)} 個排程任務:")

    for source in enabled_sources:
        source_name = source.get("name", "Unknown")
        schedule = source.get("schedule", "")
        priority = source.get("priority", 1)

        if not schedule or schedule == "Manual":
            print(f"   ⏭️  跳過手動執行的來源: {source_name}")
            continue

        # 轉換 Cron 格式到 Windows 排程格式
        windows_schedule = convert_cron_to_windows(schedule)
        if not windows_schedule:
            print(f"   ⚠️  無法轉換排程格式: {source_name} ({schedule})")
            continue

        # 建立任務名稱
        task_name = f"FinanceAgents_ETL_{source_name.replace(' ', '_')}"

        # 建構 schtasks 命令
        cmd = [
            "schtasks", "/create",
            "/tn", task_name,
            "/tr", f'"{python_path}" "{script_path}" --test "{source_name}" --config "{config_path}"',
            "/sc", windows_schedule["frequency"],
            "/f"  # 強制覆蓋現有任務
        ]

        # 添加額外的時間參數
        if windows_schedule.get("time"):
            cmd.extend(["/st", windows_schedule["time"]])

        if windows_schedule.get("days"):
            cmd.extend(["/d", windows_schedule["days"]])

        try:
            # 執行命令
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='cp950')

            if result.returncode == 0:
                print(f"   ✅ 成功建立任務: {task_name}")
                print(f"      排程: {schedule} -> {windows_schedule['description']}")
            else:
                print(f"   ❌ 建立任務失敗: {task_name}")
                print(f"      錯誤: {result.stderr}")

        except Exception as e:
            print(f"   ❌ 執行 schtasks 失敗: {e}")

    print("\n🎯 Windows 排程設定完成")
    print("💡 可以在「工作排程器」中查看和管理這些任務")


def setup_linux_cron(config: dict):
    """設定 Linux Cron 任務"""
    print("🐧 設定 Linux Cron 任務...")

    project_root = Path(__file__).parent.absolute()
    python_path = sys.executable
    script_path = project_root / "run_etl.py"
    config_path = project_root / "etl_config.yaml"

    sources = config.get("sources", [])
    enabled_sources = [s for s in sources if s.get("enabled", False)]

    if not enabled_sources:
        print("❌ 沒有啟用的資料來源")
        return

    # 建立 cron 任務內容
    cron_lines = []
    cron_lines.append("# Finance Agents ETL 自動化任務")
    cron_lines.append(f"# 由 {__file__} 於 {datetime.now()} 自動生成")
    cron_lines.append("")

    for source in enabled_sources:
        source_name = source.get("name", "Unknown")
        schedule = source.get("schedule", "")

        if not schedule or schedule == "Manual":
            print(f"   ⏭️  跳過手動執行的來源: {source_name}")
            continue

        # 建構 cron 任務
        log_file = project_root / "logs" / f"etl_{source_name.replace(' ', '_').lower()}.log"
        cron_command = (
            f'{schedule} '
            f'{python_path} "{script_path}" --test "{source_name}" --config "{config_path}" '
            f'>> "{log_file}" 2>&1'
        )

        cron_lines.append(f"# {source_name}")
        cron_lines.append(cron_command)
        cron_lines.append("")

    # 將 cron 任務寫入暫存檔
    cron_file = project_root / "finance_agents_cron.txt"
    with open(cron_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(cron_lines))

    print(f"📄 Cron 任務已寫入: {cron_file}")
    print("\n📋 請手動執行以下命令來安裝 cron 任務:")
    print(f"   crontab {cron_file}")
    print("\n💡 或者將以下內容添加到現有的 crontab:")
    print("-" * 50)
    for line in cron_lines:
        print(line)
    print("-" * 50)


def convert_cron_to_windows(cron_expression: str) -> dict:
    """將 Cron 表達式轉換為 Windows 任務排程格式

    Args:
        cron_expression: Cron 表達式 (例如: "0 6 * * *")

    Returns:
        Windows 排程格式字典
    """
    try:
        parts = cron_expression.strip().split()
        if len(parts) != 5:
            return None

        minute, hour, day, month, weekday = parts

        # 基本的時間格式
        time_str = f"{hour.zfill(2)}:{minute.zfill(2)}"

        # 每日執行
        if day == "*" and month == "*" and weekday == "*":
            return {
                "frequency": "daily",
                "time": time_str,
                "description": f"每日 {time_str}"
            }

        # 週執行
        if day == "*" and month == "*" and weekday != "*":
            weekday_map = {
                "0": "SUN", "1": "MON", "2": "TUE", "3": "WED",
                "4": "THU", "5": "FRI", "6": "SAT"
            }

            if weekday in weekday_map:
                return {
                    "frequency": "weekly",
                    "time": time_str,
                    "days": weekday_map[weekday],
                    "description": f"每週{weekday_map[weekday]} {time_str}"
                }

        # 月執行
        if day != "*" and month == "*" and weekday == "*":
            return {
                "frequency": "monthly",
                "time": time_str,
                "description": f"每月{day}日 {time_str}"
            }

        return None

    except Exception:
        return None


def remove_windows_tasks():
    """移除所有 FinanceAgents ETL 相關的 Windows 任務"""
    print("🗑️  移除現有的 Windows 排程任務...")

    try:
        # 列出所有任務
        result = subprocess.run(
            ["schtasks", "/query", "/fo", "csv"],
            capture_output=True, text=True, encoding='cp950'
        )

        if result.returncode != 0:
            print("❌ 無法查詢現有任務")
            return

        # 尋找 FinanceAgents 相關任務
        lines = result.stdout.split('\n')
        finance_tasks = [
            line.split(',')[0].strip('"')
            for line in lines
            if "FinanceAgents_ETL" in line
        ]

        if not finance_tasks:
            print("✅ 沒有找到現有的 FinanceAgents ETL 任務")
            return

        # 刪除找到的任務
        for task_name in finance_tasks:
            try:
                delete_result = subprocess.run(
                    ["schtasks", "/delete", "/tn", task_name, "/f"],
                    capture_output=True, text=True, encoding='cp950'
                )

                if delete_result.returncode == 0:
                    print(f"   ✅ 已刪除任務: {task_name}")
                else:
                    print(f"   ❌ 刪除任務失敗: {task_name}")

            except Exception as e:
                print(f"   ❌ 刪除任務時發生錯誤: {task_name}, {e}")

    except Exception as e:
        print(f"❌ 操作失敗: {e}")


def main():
    """主函數"""
    import argparse
    from datetime import datetime

    parser = argparse.ArgumentParser(description="設定 Finance Agents ETL 自動化排程")
    parser.add_argument("--config", "-c", default="etl_config.yaml", help="設定檔路徑")
    parser.add_argument("--remove", "-r", action="store_true", help="移除現有排程任務")
    parser.add_argument("--dry-run", "-d", action="store_true", help="僅顯示將建立的任務，不實際執行")

    args = parser.parse_args()

    print("⚙️  Finance Agents ETL 排程設定工具")
    print("=" * 50)

    # 移除現有任務
    if args.remove:
        if platform.system() == "Windows":
            remove_windows_tasks()
        else:
            print("💡 Linux 系統請手動執行: crontab -r")
        return

    # 載入設定
    config = load_config(args.config)

    # 顯示將建立的任務
    sources = config.get("sources", [])
    enabled_sources = [s for s in sources if s.get("enabled", False)]

    print(f"📋 發現 {len(enabled_sources)} 個啟用的資料來源:")
    for source in enabled_sources:
        name = source.get("name")
        schedule = source.get("schedule", "Manual")
        priority = source.get("priority", 0)
        print(f"   - {name} (優先級 {priority}, 排程: {schedule})")

    if args.dry_run:
        print("\n🔍 Dry run 模式，未實際建立任務")
        return

    # 根據作業系統設定排程
    if platform.system() == "Windows":
        setup_windows_scheduler(config)
    elif platform.system() == "Linux":
        setup_linux_cron(config)
    else:
        print(f"❌ 不支援的作業系統: {platform.system()}")
        print("💡 請手動設定定時任務")


if __name__ == "__main__":
    main()