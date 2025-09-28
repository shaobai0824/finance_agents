#!/usr/bin/env python3
"""
簡化的 API 啟動器，避免模組導入問題
"""

import os
import sys
from pathlib import Path

# 添加專案路徑到 Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src" / "main" / "python"))

from dotenv import load_dotenv

load_dotenv()

# 現在導入 FastAPI 模組
try:
    import uvicorn

    from src.main.python.api.main import app

    print("Success: API module imported")
    print("Starting API server...")

    # 啟動服務器
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,  # 使用不同端口避免衝突
        reload=False,  # 關閉自動重載避免問題
        log_level="info"
    )

except ImportError as e:
    print(f"Import error: {e}")
    print("Please check module path and dependencies")
except Exception as e:
    print(f"Startup failed: {e}")