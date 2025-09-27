# 財經理財智能系統 Docker 配置
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# 複製需求檔案
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式檔案
COPY src/ ./src/
COPY data/ ./data/
COPY *.py ./
COPY *.md ./

# 建立資料目錄
RUN mkdir -p /app/chroma_db /app/logs

# 設定環境變數
ENV PYTHONPATH=/app/src/main/python
ENV CHROMA_DB_PATH=/app/chroma_db
ENV LOG_LEVEL=INFO

# 暴露連接埠
EXPOSE 8000

# 健康檢查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# 啟動指令
CMD ["python", "-m", "uvicorn", "src.main.python.api.main:app", "--host", "0.0.0.0", "--port", "8000"]