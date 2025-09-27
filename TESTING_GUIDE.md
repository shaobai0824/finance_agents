# 財經理財系統功能測試指南

## 🎯 系統概覽

本系統包含以下核心功能：
1. **真實新聞爬取**：從鉅亨網爬取最新財經新聞
2. **向量資料庫**：儲存和檢索財經資料
3. **理財專家Agents**：3種專業理財advisor
4. **個人資料庫**：模擬客戶財務狀況
5. **RAG檢索系統**：智能知識檢索

---

## 🧪 測試步驟

### **步驟 1：測試真實新聞爬蟲**
```bash
# 爬取最新鉅亨網新聞（約需2-3分鐘）
python real_cnyes_scraper.py
```

**預期結果**：
- 爬取15篇左右的真實新聞
- 生成 `data/real_cnyes_news_YYYYMMDD_HHMMSS.json` 檔案
- 顯示各分類的新聞數量統計

**檢查項目**：
- ✅ 是否有真實的URL（如：`https://news.cnyes.com/news/id/6169813`）
- ✅ 是否有完整的新聞內容（非Lorem ipsum）
- ✅ 是否有正確的分類（台股、美股、基金等）

---

### **步驟 2：測試向量資料庫整合**
```bash
# 將真實新聞載入向量資料庫
python integrate_real_cnyes_data.py
```

**預期結果**：
- 自動載入最新的JSON檔案
- 成功載入到ChromaDB向量資料庫
- 顯示檢索測試結果

**檢查項目**：
- ✅ 是否成功載入所有新聞
- ✅ 檢索測試是否找到相關新聞
- ✅ 標籤系統是否正常工作

---

### **步驟 3：測試整合理財系統**
```bash
# 測試完整的理財諮詢系統
python test_integrated_finance_system.py
```

**預期結果**：
- 初始化個人資料庫和RAG系統
- 理財專家能查詢客戶財產狀況
- 提供個人化投資建議

**檢查項目**：
- ✅ 理財專家是否能成功初始化
- ✅ 是否能查詢到客戶資料
- ✅ 回應信心度是否合理（>60%）

---

### **步驟 4：測試基金資料載入**
```bash
# 載入基金投資產品到向量資料庫
python -m src.main.python.etl.fund_data_ingestion
```

**預期結果**：
- 載入16個基金產品到向量資料庫
- 顯示基金產品統計資訊

---

## 🔍 快速驗證測試

### **方法 1：一鍵完整測試**
```bash
# 執行完整測試流程
python -c "
import subprocess
import sys

print('=== 財經理財系統完整測試 ===')

tests = [
    ('爬取真實新聞', 'python real_cnyes_scraper.py'),
    ('整合向量資料庫', 'python integrate_real_cnyes_data.py'),
    ('測試理財系統', 'python test_integrated_finance_system.py')
]

for name, cmd in tests:
    print(f'\n[開始] {name}...')
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f'[成功] {name}')
        else:
            print(f'[失敗] {name}: {result.stderr[:200]}')
    except Exception as e:
        print(f'[錯誤] {name}: {e}')

print('\n=== 測試完成 ===')
"
```

### **方法 2：檢查系統狀態**
```bash
# 檢查各組件狀態
python -c "
import sys
import os
sys.path.append(os.path.join('.', 'src', 'main', 'python'))

print('=== 系統狀態檢查 ===')

# 檢查向量資料庫
try:
    from rag import ChromaVectorStore
    store = ChromaVectorStore()
    collections = store.client.list_collections()
    print(f'向量資料庫集合:')
    for col in collections:
        print(f'  - {col.name}: {col.count()} 個文檔')
except Exception as e:
    print(f'向量資料庫錯誤: {e}')

# 檢查個人資料庫
try:
    from database import PersonalFinanceDB
    db = PersonalFinanceDB()
    customers = db.search_customers_by_criteria({})
    print(f'\n個人資料庫: {len(customers)} 個客戶')
except Exception as e:
    print(f'個人資料庫錯誤: {e}')

# 檢查資料檔案
import glob
news_files = glob.glob('data/real_cnyes_news_*.json')
print(f'\n真實新聞檔案: {len(news_files)} 個')
for file in news_files:
    print(f'  - {file}')
"
```

---

## 📊 進階功能測試

### **測試 1：理財專家對話測試**
```bash
python -c "
import asyncio
import sys
import os
sys.path.append(os.path.join('.', 'src', 'main', 'python'))

from agents.financial_planner_agent_new import FinancialPlannerAgent
from agents.base_agent import AgentMessage, MessageType
from rag import ChromaVectorStore, KnowledgeRetriever

async def test_agent_chat():
    print('=== 理財專家對話測試 ===')

    try:
        # 初始化理財專家
        vector_store = ChromaVectorStore()
        knowledge_retriever = KnowledgeRetriever(vector_store)
        agent = FinancialPlannerAgent('理財專家', knowledge_retriever=knowledge_retriever)

        # 測試問題
        questions = [
            '最近有什麼值得投資的標的嗎？',
            '小米股票怎麼樣？',
            '退休理財有什麼建議？'
        ]

        for question in questions:
            print(f'\n問題：{question}')
            message = AgentMessage(
                agent_type=agent.agent_type,
                message_type=MessageType.QUERY,
                content=question
            )

            response = await agent.process_message(message)
            print(f'回應：{response.content[:150]}...')
            print(f'信心度：{response.confidence:.1%}')

    except Exception as e:
        print(f'測試失敗：{e}')

asyncio.run(test_agent_chat())
"
```

### **測試 2：新聞檢索測試**
```bash
python -c "
import sys
import os
sys.path.append(os.path.join('.', 'src', 'main', 'python'))

print('=== 新聞檢索功能測試 ===')

try:
    from rag import ChromaVectorStore
    store = ChromaVectorStore()
    collection = store.client.get_collection('financial_news')

    test_queries = ['台積電', '小米', 'TikTok', '美股', '基金投資']

    for query in test_queries:
        print(f'\n搜尋：{query}')
        results = collection.query(query_texts=[query], n_results=2)

        if results['documents'][0]:
            for i, metadata in enumerate(results['metadatas'][0]):
                print(f'  {i+1}. {metadata[\"title\"]}')
                print(f'     來源：{metadata[\"url\"]}')
        else:
            print('  未找到結果')

except Exception as e:
    print(f'檢索測試失敗：{e}')
"
```

---

## 🛠 疑難排解

### **常見問題**

**Q1: 爬蟲無法獲取新聞**
```bash
# 檢查網路連線和網站狀態
curl -I https://news.cnyes.com/news/cat/tw_stock
```

**Q2: 向量資料庫連接失敗**
```bash
# 重新初始化ChromaDB
python -c "
from rag import ChromaVectorStore
store = ChromaVectorStore()
print('ChromaDB狀態：', '正常' if store.client else '異常')
"
```

**Q3: 理財專家回應信心度過低**
```bash
# 檢查RAG知識庫內容
python -c "
from rag import ChromaVectorStore
store = ChromaVectorStore()
collections = store.client.list_collections()
total_docs = sum(col.count() for col in collections)
print(f'知識庫總文檔數：{total_docs}')
if total_docs < 10:
    print('建議：載入更多資料到向量資料庫')
"
```

---

## 📈 效能監控

### **系統效能檢查**
```bash
python -c "
import time
import sys
import os
sys.path.append(os.path.join('.', 'src', 'main', 'python'))

print('=== 系統效能檢查 ===')

# 測試向量檢索速度
try:
    start_time = time.time()
    from rag import ChromaVectorStore
    store = ChromaVectorStore()
    collection = store.client.get_collection('financial_news')
    results = collection.query(query_texts=['投資'], n_results=5)
    end_time = time.time()

    print(f'向量檢索時間：{end_time - start_time:.2f} 秒')
    print(f'檢索結果數量：{len(results[\"documents\"][0])}')

except Exception as e:
    print(f'效能檢查失敗：{e}')
"
```

---

## ✅ 測試檢查清單

完成以下測試後，系統應該能夠：

- [ ] 成功爬取真實的鉅亨網新聞
- [ ] 將新聞載入向量資料庫
- [ ] 向量檢索能找到相關新聞
- [ ] 理財專家能提供投資建議
- [ ] 個人資料庫功能正常
- [ ] 基金產品資料完整
- [ ] 系統整合測試通過
- [ ] 回應時間在合理範圍內（<5秒）

**通過標準**：
- 所有核心功能正常運作
- 理財專家回應信心度 > 60%
- 新聞爬取成功率 > 80%
- 向量檢索響應時間 < 2秒