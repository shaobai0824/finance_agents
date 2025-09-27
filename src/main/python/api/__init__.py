"""
FastAPI 後端 API 模組

提供理財諮詢服務的 RESTful API：
- main: FastAPI 應用主程式
- models: API 資料模型
- routes: API 路由定義
- services: 業務邏輯服務
"""

from .main import app

__all__ = ["app"]