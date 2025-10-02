# 📅 新聞爬蟲排程設定指南

## 🎯 快速開始

### 方案選擇

| 使用場景 | 推薦方案 | 設定步驟 |
|---------|---------|---------|
| **測試/開發** | APScheduler | 執行 Python 腳本 |
| **Windows 生產** | Windows 工作排程器 | 執行 setup_windows_scheduler.bat |
| **Linux 生產** | systemd + cron | 手動設定 systemd service |

---

## 🪟 方案 1：Windows 工作排程器（推薦）

### 優點
- ✅ Windows 內建，無需額外軟體
- ✅ 開機自動啟動
- ✅ 系統級排程，穩定可靠
- ✅ GUI 管理介面

### 設定步驟

#### 1. 自動設定（推薦）

```batch
# 右鍵點擊，選擇「以系統管理員身分執行」
setup_windows_scheduler.bat
```

系統會詢問：
- 執行小時 (0-23，預設 9)
- 執行分鐘 (0-59，預設 0)

#### 2. 手動設定

1. 開啟「工作排程器」(Task Scheduler)
2. 點擊「建立基本工作」
3. 設定：
   - 名稱：CnyesNewsScraper
   - 觸發程序：每日
   - 時間：09:00（或你想要的時間）
   - 動作：啟動程式
   - 程式：`run_daily_scrape.bat` 的完整路徑

### 管理指令

```batch
# 查看排程狀態
schtasks /query /tn "CnyesNewsScraper"

# 立即執行一次
schtasks /run /tn "CnyesNewsScraper"

# 停用排程
schtasks /change /tn "CnyesNewsScraper" /disable

# 啟用排程
schtasks /change /tn "CnyesNewsScraper" /enable

# 刪除排程
schtasks /delete /tn "CnyesNewsScraper" /f
```

### 查看日誌

```batch
# 日誌位置
logs\scraper_YYYYMMDD.log

# 範例
logs\scraper_20251002.log
```

---

## 🐍 方案 2：APScheduler（Python 原生）

### 優點
- ✅ 已經實作完成
- ✅ Python 程式碼控制
- ✅ 靈活配置

### 缺點
- ❌ 需要保持 Python 進程運行
- ❌ 關機/重啟會停止

### 使用方法

#### 執行一次（測試）
```bash
python src/main/python/etl/news_scheduler.py --mode once --articles 10
```

#### 啟動排程（需保持運行）
```bash
# 每天早上 9:00，每個分類 20 篇
python src/main/python/etl/news_scheduler.py --mode schedule --hour 9 --minute 0 --articles 20
```

#### 查看歷史
```bash
python src/main/python/etl/news_scheduler.py --mode history
```

---

## 🐧 方案 3：Linux systemd（Linux 生產環境）

### 1. 創建 systemd service 檔案

```bash
sudo nano /etc/systemd/system/cnyes-scraper.service
```

內容：
```ini
[Unit]
Description=Cnyes News Scraper
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/project
Environment="PATH=/path/to/project/finance_agents_env/bin"
ExecStart=/path/to/project/finance_agents_env/bin/python src/main/python/etl/news_scheduler.py --mode once --articles 20
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

### 2. 創建 cron 定時任務

```bash
crontab -e
```

添加：
```bash
# 每天早上 9:00 執行
0 9 * * * systemctl start cnyes-scraper.service
```

### 3. 管理指令

```bash
# 啟用服務
sudo systemctl enable cnyes-scraper.service

# 立即執行
sudo systemctl start cnyes-scraper.service

# 查看狀態
sudo systemctl status cnyes-scraper.service

# 查看日誌
sudo journalctl -u cnyes-scraper.service -f
```

---

## 🐳 方案 4：Docker + Cron（容器化部署）

### 1. 創建 Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    cron \
    && rm -rf /var/lib/apt/lists/*

# 複製專案
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 設定 cron
RUN echo "0 9 * * * cd /app && python src/main/python/etl/news_scheduler.py --mode once --articles 20 >> /app/logs/cron.log 2>&1" > /etc/cron.d/scraper-cron
RUN chmod 0644 /etc/cron.d/scraper-cron
RUN crontab /etc/cron.d/scraper-cron

CMD ["cron", "-f"]
```

### 2. 使用 Docker Compose

```yaml
version: '3.8'

services:
  scraper:
    build: .
    container_name: cnyes-scraper
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./chroma_db:/app/chroma_db
    env_file:
      - .env
    restart: unless-stopped
```

### 3. 部署

```bash
# 構建並啟動
docker-compose up -d

# 查看日誌
docker-compose logs -f

# 手動執行一次
docker-compose exec scraper python src/main/python/etl/news_scheduler.py --mode once --articles 20
```

---

## 🔧 爬蟲測試與調試

### 測試前準備

1. **安裝 ChromeDriver**（Selenium 需要）

```bash
# 方法 1：使用 webdriver-manager（推薦）
pip install webdriver-manager

# 方法 2：手動下載
# 下載：https://chromedriver.chromium.org/
# 放置：C:\Program Files\ChromeDriver\chromedriver.exe
# 添加到 PATH
```

2. **驗證環境**

```bash
# 測試 ChromeDriver
chromedriver --version

# 測試 Python 環境
python -c "from selenium import webdriver; print('OK')"
```

### 測試步驟

#### 1. 快速測試（1篇文章）

```bash
python test_auto_scraper.py
```

#### 2. 完整測試（指定文章數）

```bash
# 每個分類 5 篇
python src/main/python/etl/news_scheduler.py --mode once --articles 5
```

#### 3. 檢查結果

```bash
# 查看日誌
type logs\news_scheduler.log

# 查看執行歷史
python src/main/python/etl/news_scheduler.py --mode history

# 檢查資料庫
python diagnose_rag.py
```

### 常見問題排除

#### 問題 1：ChromeDriver 錯誤

**錯誤訊息**：
```
selenium.common.exceptions.WebDriverException: 'chromedriver' executable needs to be in PATH
```

**解決方法**：
```bash
# 安裝 webdriver-manager
pip install webdriver-manager

# 修改爬蟲配置（如需要）
```

#### 問題 2：爬取 0 篇文章

**可能原因**：
1. 網站結構改變（需更新選擇器）
2. IP 被封鎖（需要代理）
3. Selenium 配置問題

**調試步驟**：
```bash
# 1. 測試網站是否可訪問
curl -I https://news.cnyes.com

# 2. 檢查 Selenium 日誌
# 查看爬蟲日誌中的詳細錯誤

# 3. 手動測試選擇器（使用瀏覽器開發者工具）
```

#### 問題 3：記憶體不足

**解決方法**：
```python
# 調整配置
scraper_config = {
    'articles_per_category': 10,  # 減少爬取數量
    'request_delay': (3, 5),      # 增加延遲
}
```

---

## 📊 監控與維護

### 日誌位置

```
logs/
├── news_scheduler.log         # 排程器日誌
├── scraper_20251002.log       # 每日爬蟲日誌
└── execution_history.json     # 執行歷史
```

### 定期檢查

```bash
# 每週檢查
1. 查看日誌：有無錯誤
2. 檢查資料庫：資料是否增長
3. 測試檢索：RAG 是否正常

# 指令
dir logs\scraper_*.log
python diagnose_rag.py
```

### 調整配置

修改 `run_daily_scrape.bat`：
```batch
REM 調整爬取數量
"%PYTHON_ENV%" src\main\python\etl\news_scheduler.py --mode once --articles 30

REM 使用不同集合
"%PYTHON_ENV%" src\main\python\etl\news_scheduler.py --mode once --articles 20 --collection my_collection
```

---

## 🎯 最佳實踐

### 1. 開發環境
- 使用 APScheduler 測試
- 小批量爬取（5-10 篇/分類）
- 頻繁查看日誌

### 2. 生產環境
- Windows：工作排程器
- Linux：systemd + cron
- Docker：容器化部署

### 3. 爬蟲禮儀
- 設定合理延遲（2-5秒）
- 限制並發請求
- 遵守 robots.txt
- 避免高峰時段

### 4. 資料品質
- 定期檢查去重效果
- 監控資料增長速度
- 驗證 RAG 檢索品質

---

## 📞 技術支援

### 問題回報

遇到問題時，請提供：
1. 錯誤訊息（完整）
2. 日誌檔案（相關部分）
3. 執行環境（OS、Python 版本）
4. 執行指令

### 相關文件

- 爬蟲實作：`src/main/python/etl/scrapers/cnyes_auto_scraper.py`
- 整合流程：`src/main/python/etl/auto_news_pipeline.py`
- 排程器：`src/main/python/etl/news_scheduler.py`
