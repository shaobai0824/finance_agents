AI 理財顧問爬蟲開發優先級建議書
緒論
本文件旨在為 AI 個人理財顧問系統的知識庫爬蟲開發提供一份明確的優先級與策略建議。目標是依據資料的權威性、價值性與技術可行性，分階段建立一個穩定、高效且合規的資料擷取流程，以最大化開發資源的效益。

第一優先級：核心基石 (Core Foundation)
此階段的目標是獲取絕對權威且不可替代的「事實來源 (Source of Truth)」。這些資料是系統合法合規與提供正確資訊的基礎，且網站結構相對穩定，爬取成功率高。

1. 全國法規資料庫
對應代理人：法律專家

網站：https://law.moj.gov.tw/

優點：

絕對權威：所有法律問題的最終依據，資料準確無誤。

結構穩定：政府網站，版面結構極少變動，爬蟲程式碼維護成本低。

反爬性弱：作為公開資訊平台，通常不會有複雜的反爬蟲機制。

內容乾淨：頁面內容主要是純文字的法條，無廣告或複雜腳本干擾。

缺點與挑戰：

資料量龐大，需要設計好資料庫結構來儲存法規、條文、修正歷史之間的關聯。

技術建議：

使用 Python Requests + BeautifulSoup 即可高效完成。這是一個標準的靜態網頁爬取組合，開發速度快。

2. 公開資訊觀測站 (MOPS)
對應代理人：金融專家

網站：https://mops.twse.com.tw/

優點：

絕對獨家：所有台灣上市櫃公司的第一手財報、營收、重大訊息的唯一官方來源，資料價值極高。

高度結構化：資料多以表格形式呈現，一旦成功解析，資料乾淨且易於使用。

缺點與挑戰：

爬取難度極高：這是清單中最具挑戰性的網站。它使用複雜的 HTML <table> 結構、POST 表單提交、Session 管理，並且有防止機器人訪問的機制。

維護成本高：網站的查詢介面或回傳格式偶有變動，需要持續監控與維護爬蟲。

技術建議：

強烈建議使用 Selenium 或 Playwright。這些瀏覽器自動化工具能模擬使用者操作（點擊按鈕、填寫表單），是處理這類複雜網站的最佳方案。需要投入較多時間進行開發與除錯。

第二優先級：即時動態與市場脈動 (Real-time Dynamics)
此階段目標是獲取高時效性的市場新聞與分析，讓 AI 的建議能跟上市場變化。這些是商業網站，爬取時需更加謹慎。

3. 鉅亨網 (Anue)
對應代理人：金融專家、理財專家

網站：https://news.cnyes.com/

優點：

高時效性：24 小時發布新聞，是獲取市場即時資訊的絕佳來源。

內容廣泛：涵蓋台股、美股、外匯、基金、加密貨幣等多種主題。

文章結構統一：新聞內頁的 HTML 結構通常很一致，易於解析文章標題、時間與內文。

缺點與挑戰：

可能有反爬機制：作為大型商業網站，可能會偵測請求頻率，需要設定合理的延遲 (delay) 與偽裝請求標頭 (User-Agent)。

廣告與非內容元素：需要仔細清洗 HTML，過濾掉廣告、推薦連結等雜訊。

動態載入：部分列表頁可能使用 JavaScript 動態載入內容（如無限滾動），需要分析其背後的 API 或使用瀏覽器自動化工具。

技術建議：

文章內頁可嘗試 Requests + BeautifulSoup。若列表頁為動態載入，則需使用 Selenium 或直接 F12 分析 XHR 網路請求來找到後端 API。

4. 金融監督管理委員會 (主網站)
對應代理人：法律專家、金融專家

網站：https://www.fsc.gov.tw/

優點：

權威解釋：提供法規的解釋令 (函釋) 與新聞稿，是理解法規在實務上如何應用的關鍵。

監管動向：可了解最新的金融監管政策與趨勢。

缺點與挑戰：

網站資訊架構較複雜，內容散落在「新聞稿」、「法令規章」等多個不同單元，需要為每個單元客製化爬取邏輯。

技術建議：

Requests + BeautifulSoup 應可勝任。關鍵在於前期花時間分析網站地圖，找出需要爬取的各個目標頁面。

第三優先級：深度觀點與通識教育 (In-depth Views & Education)
此階段目標是豐富知識庫的深度與廣度，提供更貼近一般人的理財教育內容。這些網站多為部落格或內容平台，爬取時需注意版權問題。

5. Mr. Market 市場先生
對應代理人：理財專家

網站：https://rich01.com/

優點：

高品質教學內容：文章結構清晰、深入淺出，非常適合作為理財通識知識庫。

網站結構單純：標準的部落格形式，爬取文章列表與內文相對簡單。

缺點與挑戰：

版權與歸屬：爬取內容時，必須在 RAG 系統的輸出中明確標示引用來源，尊重原作者的智慧財產權。

非結構化：內容是長篇文章，需要依賴強大的文本分塊 (Chunking) 策略來優化 RAG 效果。

技術建議：

Requests + BeautifulSoup 即可。

6. 經濟日報 / 工商時報
對應代理人：金融專家

網站：https://money.udn.com/ / https://ctee.com.tw/

優點：

深度產業分析：提供比即時新聞更有深度的產業報導與評論。

缺點與挑戰：

付費牆 (Paywall)：許多深度報導是會員專屬，免費爬蟲只能抓取到部分內容或摘要。

技術建議：

僅針對免費內容進行爬取，使用 Requests + BeautifulSoup。若要存取付費內容，則需考慮合法的訂閱方案與 API 存取。

自動化 RAG 知識庫 ETL 流程設計書
1. 緒論
1.1. 文件目的
本文件旨在提供一套完整、穩定且可擴展的自動化 ETL 流程設計方案。該流程負責定期從指定的資料來源（如新聞網站、法規資料庫）擷取資訊，進行處理與轉換，最終載入至 MongoDB 向量資料庫，以持續更新 AI 理財顧問的 RAG 知識庫。

1.2. 設計目標
自動化 (Automation)：整個流程應無需人工干預，可依預定排程自動執行。

可靠性 (Reliability)：具備完善的錯誤處理與重試機制，確保單一來源的失敗不會中斷整個流程。

可維護性 (Maintainability)：程式碼結構清晰、模組化，易於新增或修改資料來源。

冪等性 (Idempotency)：重複執行同一任務應產生相同的結果，避免在資料庫中產生重複資料。

可觀測性 (Observability)：具備詳細的日誌記錄，便於追蹤執行狀態與排查問題。

2. 系統架構
我們設計一個由排程器觸發的主執行腳本，該腳本根據設定檔動態載入對應的爬蟲模組，並依序執行擷取、轉換、載入的完整流程。

圖一：自動化 ETL 流程架構圖

排程器 (Scheduler)：

方案：使用 Linux 系統內建的 Cron 來設定定時任務。例如，設定在每日凌晨 3 點執行主腳本。

優點：簡單、穩定、無須額外安裝複雜的服務。對於中小型專案是最佳選擇。

主執行腳本 (main_etl.py)：

整個流程的總指揮。

負責讀取設定檔 (config.yaml)，獲取所有要處理的資料來源清單。

依序為每個資料來源呼叫對應的爬蟲與處理模組。

統一管理日誌記錄與錯誤處理。

爬蟲模組 (Scraper Modules)：

模組化設計：每個網站對應一個獨立的 Python 檔案（例如 mops_scraper.py, anue_scraper.py）。

統一介面：所有爬蟲模組都實作一個共同的 scrape() 函數，回傳一個標準化的資料結構（例如 list[dict]）。

數據轉換層 (Transformer)：

負責將爬取到的原始資料進行清洗、分塊 (Chunking)，並轉換為向量。

數據載入層 (Loader)：

負責將處理好的向量化資料寫入 MongoDB，並處理重複資料的更新邏輯。

3. 核心組件詳細設計
3.1. 設定檔 (config.yaml)
使用 YAML 格式的設定檔來管理所有資料來源，讓新增來源時完全不需要修改主程式碼。

# config.yaml
mongodb_uri: "mongodb+srv://<user>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority"
embedding_model_name: "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

sources:
  - name: "全國法規資料庫"
    module: "scrapers.law_moj_scraper"
    target_collection: "legal_statutes"
    enabled: true
    # ... 其他該爬蟲需要的參數 ...

  - name: "鉅亨網-台股新聞"
    module: "scrapers.anue_scraper"
    target_collection: "financial_news"
    enabled: true
    base_url: "[https://news.cnyes.com/news/cat/tw_stock](https://news.cnyes.com/news/cat/tw_stock)"

  - name: "公開資訊觀測站"
    module: "scrapers.mops_scraper"
    target_collection: "financial_reports"
    enabled: false # 暫時停用

3.2. 數據處理流程
Step 1: 擷取 (Extract)
每個爬蟲模組的核心是 scrape() 函數。它的職責是：

爬取目標網站。

解析 HTML，提取所需欄位（標題、日期、內容、URL）。

回傳一個包含多篇文章的列表，每篇文章是一個字典。URL 是每篇文章的唯一標識符。

Step 2: 轉換 (Transform)
此階段包含多個子步驟：

清洗 (Clean)：去除 HTML 標籤、廣告、多餘的空白字元。

分塊 (Chunk)：使用 LangChain 的 RecursiveCharacterTextSplitter 將長文本切分成適合 RAG 的小塊。

向量化 (Embed)：將每個文本塊轉換為向量。為了效率，應該批次處理 (in batches)。

Step 3: 載入 (Load)
此階段的關鍵是實現冪等性，防止重複插入。

生成唯一 ID：對每篇文章的來源 URL 進行 HASH（例如 SHA-256）運算，產生一個唯一的 _id。

使用 upsert 操作：

在寫入 MongoDB 時，使用 update_one 方法並將 upsert 參數設為 True。

系統會用這個 _id 檢查資料庫中是否已存在該篇文章。

如果存在：只更新內容（也許文章被編輯過）。

如果不存在：則插入這筆新資料。

這樣，即使爬蟲重複抓到同一篇文章，資料庫也只會有一筆紀錄。

3.3. 排程與部署 (Cron + Docker)
最好的部署方式是將整個 ETL 流程打包成一個 Docker 映像檔。

Dockerfile.etl

FROM python:3.11-slim

WORKDIR /app

# 安裝系統依賴 (例如 cron)
RUN apt-get update && apt-get install -y cron

# 複製專案檔案
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# 設定 Cron Job
# 建立 crontab 檔案，內容是 "0 3 * * * python /app/main_etl.py >> /var/log/cron.log 2>&1"
# 這表示每天凌晨 3:00 執行，並將標準輸出與錯誤導向日誌檔
RUN echo "0 3 * * * python /app/main_etl.py >> /var/log/cron.log 2>&1" > /etc/cron.d/etl-cron
RUN chmod 0644 /etc/cron.d/etl-cron
RUN crontab /etc/cron.d/etl-cron

# 啟動 cron 服務並保持前景執行
CMD ["cron", "-f"]

執行容器
只需要一行指令即可啟動這個自動化服務：
docker run -d --name rag-etl-worker my-etl-image

4. 程式碼範例 (main_etl.py)
這是一個簡化但結構完整的主執行腳本，展示了上述設計思想。

import yaml
import logging
import importlib
from pathlib import Path
from pymongo import MongoClient, UpdateOne
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import SentenceTransformerEmbeddings

# --- 1. 初始化設定 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_config():
    """載入設定檔"""
    config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def get_db_connection(config):
    """建立資料庫連線"""
    client = MongoClient(config['mongodb_uri'])
    return client.get_database("rag_knowledge_base")

# --- 2. 核心 ETL 函數 ---
def transform_and_embed(articles: list[dict], embedding_model):
    """轉換資料並生成向量"""
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    
    processed_chunks = []
    for article in articles:
        if not article.get('content'):
            continue
            
        chunks = text_splitter.split_text(article['content'])
        for i, chunk_text in enumerate(chunks):
            processed_chunks.append({
                "source_url": article['url'],
                "title": article['title'],
                "publish_date": article.get('date'),
                "chunk_sequence": i,
                "text": chunk_text
            })

    # 批次生成向量以提高效率
    texts_to_embed = [chunk['text'] for chunk in processed_chunks]
    if not texts_to_embed:
        return []
        
    vectors = embedding_model.embed_documents(texts_to_embed)
    
    for i, chunk in enumerate(processed_chunks):
        chunk['vector_embedding'] = vectors[i]
        
    return processed_chunks

def load_to_mongodb(db, collection_name: str, data: list[dict]):
    """使用 upsert 載入資料至 MongoDB"""
    if not data:
        logging.info(f"集合 [{collection_name}] 沒有新資料需要載入。")
        return 0

    collection = db[collection_name]
    
    # 準備 bulk write 操作
    operations = []
    for item in data:
        # 使用 URL 和 chunk 序號生成唯一 ID
        unique_id = f"{item['source_url']}_{item['chunk_sequence']}"
        
        # 準備 upsert 操作
        operations.append(UpdateOne(
            {"_id": unique_id},
            {"$set": item},
            upsert=True
        ))
        
    result = collection.bulk_write(operations)
    return result.upserted_count

# --- 3. 主執行流程 ---
def main():
    logging.info("開始執行自動化 ETL 流程...")
    config = load_config()
    db = get_db_connection(config)
    embedding_model = SentenceTransformerEmbeddings(model_name=config['embedding_model_name'])

    for source in config['sources']:
        if not source['enabled']:
            logging.info(f"跳過已停用的資料來源: {source['name']}")
            continue

        logging.info(f"--- 正在處理資料來源: {source['name']} ---")
        try:
            # 動態載入爬蟲模組
            scraper_module = importlib.import_module(source['module'])
            
            # Step 1: 擷取 (Extract)
            logging.info("開始擷取資料...")
            raw_articles = scraper_module.scrape(config=source) # 傳入該來源的特定設定
            logging.info(f"成功擷取 {len(raw_articles)} 篇文章。")

            # Step 2: 轉換 (Transform)
            logging.info("開始轉換資料並生成向量...")
            vectorized_data = transform_and_embed(raw_articles, embedding_model)
            logging.info(f"成功將文章轉換為 {len(vectorized_data)} 個文本塊。")

            # Step 3: 載入 (Load)
            logging.info("開始載入資料至資料庫...")
            upserted_count = load_to_mongodb(db, source['target_collection'], vectorized_data)
            logging.info(f"成功新增 {upserted_count} 筆資料至集合 [{source['target_collection']}]。")

        except Exception as e:
            logging.error(f"處理資料來源 [{source['name']}] 時發生錯誤: {e}", exc_info=True)
            # 在此可以加入錯誤通知機制，例如發送 Email 或 Slack 通知
            continue # 即使一個來源失敗，也繼續處理下一個

    logging.info("所有資料來源處理完畢，ETL 流程結束。")

if __name__ == "__main__":
    main()
