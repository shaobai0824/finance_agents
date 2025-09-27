# Finance Agents ETL 自動化爬蟲系統

## 🎯 系統概述

基於 ETL.md 規劃建立的完整自動化爬蟲與向量化系統，為 Finance Agents 多代理人理財諮詢系統提供持續更新的知識庫。

### 🏗️ 系統架構

```
Finance Agents ETL System
├── 基礎爬蟲框架 (BaseScraper)
├── 網站特化爬蟲模組
│   ├── 全國法規資料庫 (LawMojScraper)    - 法律合規專家
│   ├── 鉅亨網 (CnyesScraper)             - 金融分析/理財規劃專家
│   ├── 公開資訊觀測站 (MOPSScraper)       - 金融分析專家 [待實作]
│   └── Mr. Market (MrMarketScraper)      - 理財規劃專家 [待實作]
├── ETL 流程管理器 (ETLManager)
├── 自動化排程系統
├── 向量化與資料庫載入
└── 監控與測試系統
```

## 📊 **網站與專家配對分析**

根據 ETL.md 評估，以下是各網站對專家代理人的適合性：

### 🥇 **第一優先級 - 核心基石**
- **全國法規資料庫** (law.moj.gov.tw) ➜ **法律合規專家** ⭐⭐⭐⭐⭐
- **公開資訊觀測站** (mops.twse.com.tw) ➜ **金融分析專家** ⭐⭐⭐⭐⭐

### 🥈 **第二優先級 - 即時動態**
- **鉅亨網** (cnyes.com) ➜ **金融分析專家 + 理財規劃專家** ⭐⭐⭐⭐
- **金管會** (fsc.gov.tw) ➜ **法律合規專家** ⭐⭐⭐⭐

### 🥉 **第三優先級 - 深度觀點**
- **Mr. Market 市場先生** (rich01.com) ➜ **理財規劃專家** ⭐⭐⭐⭐⭐

## 🚀 **快速開始**

### 1. 安裝依賴
```bash
pip install -r requirements_etl.txt
```

### 2. 測試系統
```bash
python test_etl_system.py
```

### 3. 檢視可用資料來源
```bash
python run_etl.py --list
```

### 4. 測試單一爬蟲
```bash
python run_etl.py --test "全國法規資料庫"
```

### 5. 執行完整 ETL 流程
```bash
python run_etl.py --full
```

### 6. 設定自動化排程
```bash
python setup_scheduler.py
```

## 📁 **檔案結構**

```
ETL System/
├── src/main/python/etl/
│   ├── __init__.py                   # ETL 模組初始化
│   ├── base_scraper.py              # 基礎爬蟲抽象類別
│   ├── etl_manager.py               # ETL 流程管理器
│   └── scrapers/
│       ├── __init__.py              # 爬蟲模組集合
│       ├── law_moj_scraper.py       # 全國法規資料庫爬蟲
│       └── cnyes_scraper.py         # 鉅亨網爬蟲
├── etl_config.yaml                  # ETL 設定檔
├── run_etl.py                       # ETL 主執行腳本
├── setup_scheduler.py               # 排程設定工具
├── test_etl_system.py              # 系統測試腳本
├── requirements_etl.txt             # 依賴套件清單
└── ETL_SYSTEM_README.md            # 本說明文件
```

## ⚙️ **設定檔說明**

### etl_config.yaml 主要設定
```yaml
global_settings:
  chunk_size: 500                    # 文檔分塊大小
  max_articles_per_source: 30        # 每個來源最大文章數
  request_delay: [2, 4]              # 請求延遲範圍

sources:
  - name: "全國法規資料庫"
    module: "src.main.python.etl.scrapers.law_moj_scraper"
    expert_domain: "legal_compliance"
    enabled: true
    schedule: "0 3 * * 0"            # 每週日凌晨3點
```

## 🤖 **已實作爬蟲模組**

### 1. 全國法規資料庫爬蟲 (LawMojScraper)
- **目標網站**: https://law.moj.gov.tw/
- **專家領域**: 法律合規專家
- **爬取內容**: 金融法規、稅務法規、投資法規
- **技術特色**: 台灣民國年份日期解析、法規條文結構化處理
- **執行頻率**: 每週日凌晨3點

### 2. 鉅亨網爬蟲 (CnyesScraper)
- **目標網站**: https://news.cnyes.com/
- **專家領域**: 金融分析專家 + 理財規劃專家
- **爬取內容**: 台股/美股新聞、基金理財資訊
- **技術特色**: Selenium 動態載入、多分類智慧路由
- **執行頻率**: 每日多次 (6:00, 14:00, 22:00)

## 🔄 **ETL 流程詳解**

### Extract (擷取)
1. 動態載入爬蟲模組
2. 執行網站特化爬蟲
3. 標準化資料格式
4. 錯誤處理與重試機制

### Transform (轉換)
1. 文字清理與正規化
2. 智慧分塊 (Chunking)
3. 元資料萃取與豐富化
4. 重複內容檢測

### Load (載入)
1. 批次向量化處理
2. ChromaDB 冪等性寫入
3. 元資料索引建立
4. 統計資訊更新

## 📅 **自動化排程**

### Windows 系統
```bash
# 設定 Windows 工作排程器
python setup_scheduler.py

# 移除現有排程
python setup_scheduler.py --remove
```

### Linux 系統
```bash
# 生成 Cron 設定
python setup_scheduler.py

# 手動安裝 Cron 任務
crontab finance_agents_cron.txt
```

### 排程策略
- **高頻更新**: 鉅亨網新聞 (每日3次)
- **中頻更新**: 法規資料 (每週1次)
- **低頻更新**: 深度文章 (每週1次)

## 🧪 **測試與驗證**

### 完整系統測試
```bash
python test_etl_system.py
```

測試項目包括：
- ✅ 設定檔載入
- ✅ 向量資料庫連接
- ✅ 法規爬蟲功能
- ✅ 鉅亨網爬蟲功能
- ✅ ETL管理器基本功能
- ✅ 向量搜尋功能

### 單元測試
```bash
# 測試法規爬蟲
python src/main/python/etl/scrapers/law_moj_scraper.py

# 測試鉅亨網爬蟲
python src/main/python/etl/scrapers/cnyes_scraper.py
```

## 📈 **效能與監控**

### 效能指標
- **併發處理**: 支援2個同時資料來源
- **記憶體限制**: 512MB
- **請求頻率**: 30次/分鐘
- **重試機制**: 最多3次重試

### 監控功能
- **執行統計**: 爬取/處理/載入數量
- **錯誤追蹤**: 失敗來源與原因記錄
- **效能監控**: 執行時間與資源使用
- **日誌系統**: 分級日誌與檔案輪換

## 🔒 **安全與合規**

### 網路爬蟲倫理
- ✅ 遵守 robots.txt
- ✅ 合理請求延遲
- ✅ 使用者代理輪換
- ✅ 頻率限制機制

### 資料處理
- ✅ 內容去識別化
- ✅ 來源標註與追蹤
- ✅ 重複內容檢測
- ✅ 敏感資訊過濾

## 🚧 **待實作功能**

### 高優先級
1. **公開資訊觀測站爬蟲** (mops_scraper.py)
   - 技術難度極高
   - 需要複雜的表單處理
   - 建議使用 Playwright

2. **金管會法規爬蟲** (fsc_scraper.py)
   - 新聞稿與法令規章
   - 多頁面結構分析

### 中優先級
3. **Mr. Market 爬蟲** (mrmarket_scraper.py)
   - 理財教育內容
   - 標準部落格結構

4. **通知系統**
   - Email/Slack 通知
   - 錯誤警報機制

### 低優先級
5. **進階功能**
   - 增量更新機制
   - 資料版本管理
   - A/B 測試框架

## 💡 **使用建議**

### 開發環境
1. 先執行完整系統測試
2. 測試單一爬蟲功能
3. 檢查向量資料庫狀態
4. 逐步啟用自動化排程

### 生產環境
1. 設定 Docker 容器化部署
2. 配置日誌監控系統
3. 建立備份與恢復機制
4. 設定效能警報閾值

### 疑難排解
- **Chrome WebDriver 錯誤**: 執行 `webdriver-manager chrome --download`
- **編碼問題**: 確保所有檔案使用 UTF-8 編碼
- **權限問題**: 檢查 ChromaDB 目錄寫入權限
- **網路問題**: 檢查防火牆與代理設定

## 🎉 **總結**

已成功建立完整的自動化 ETL 爬蟲系統，實現：

✅ **完整的爬蟲框架** - 統一介面，易於擴展
✅ **專家領域配對** - 精準的內容分類與路由
✅ **自動化排程** - 無人值守的定時執行
✅ **向量化整合** - 無縫對接 RAG 知識庫
✅ **監控與測試** - 完善的品質保證機制

系統已準備好為 Finance Agents 提供持續更新的高品質知識庫！