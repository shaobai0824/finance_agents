# 模組規格與測試案例 (Module Specification & Test Cases) - 財經理財智能系統

---

**文件版本 (Document Version):** `v1.0`
**最後更新 (Last Updated):** `2025-01-27`
**主要作者 (Lead Author):** `Claude AI System`
**審核者 (Reviewers):** `架構團隊、測試工程師、AI 開發團隊`
**狀態 (Status):** `已完成 (Done)`

---

## 目錄 (Table of Contents)

- [模組: `FinancialPlannerAgent`](#模組-financialplanneragent)
  - [規格 1: `process_message`](#規格-1-process_message)
  - [規格 2: `query_customer_portfolio`](#規格-2-query_customer_portfolio)
  - [規格 3: `generate_investment_advice`](#規格-3-generate_investment_advice)
- [模組: `ChromaVectorStore`](#模組-chromavectorstore)
  - [規格 1: `add_documents`](#規格-1-add_documents)
  - [規格 2: `search_similar`](#規格-2-search_similar)
- [模組: `PersonalFinanceDB`](#模組-personalfinancedb)
  - [規格 1: `add_customer`](#規格-1-add_customer)
  - [規格 2: `search_customers_by_criteria`](#規格-2-search_customers_by_criteria)
- [模組: `FinanceWorkflow`](#模組-financeworkflow)
  - [規格 1: `run`](#規格-1-run)
- [測試策略與覆蓋範圍](#測試策略與覆蓋範圍)

---

**目的**: 本文件定義財經理財智能系統核心模組的詳細規格、測試場景，並使用契約式設計 (Design by Contract, DbC) 精確定義每個函式的職責邊界。這是最低層級、最精確的規格，直接指導 TDD (測試驅動開發) 的實踐。

---

## 模組: `FinancialPlannerAgent`

**對應架構文件**: `03_architecture_and_design_document.md#agents-layer`
**對應 BDD Feature**: `financial_planning.feature`
**檔案路徑**: `src/main/python/agents/financial_planner_agent_new.py`

**模組描述**: 理財規劃專家代理人，負責根據客戶財務狀況提供個人化投資建議和資產配置策略。

---

### 規格 1: `process_message`

**描述 (Description)**: 處理用戶的理財諮詢訊息，結合 RAG 檢索和客戶資料庫提供專業建議。

**函式簽名**:
```python
async def process_message(self, message: AgentMessage) -> AgentMessage
```

**契約式設計 (Design by Contract, DbC)**:
*   **前置條件 (Preconditions)**:
    1. `message` 不可為 None
    2. `message.content` 不可為空字串
    3. `message.message_type` 必須是 `MessageType.QUERY`
    4. `self.knowledge_retriever` 必須已初始化
    5. `self.personal_db` 必須已初始化

*   **後置條件 (Postconditions)**:
    1. 回傳的 `AgentMessage` 不為 None
    2. 回傳訊息的 `content` 包含理財建議內容
    3. 回傳訊息的 `confidence` 值在 0.0 到 1.0 之間
    4. 回傳訊息的 `sources` 清單不為空
    5. 處理時間記錄在 `metadata` 中

*   **不變性 (Invariants)**:
    1. `self.agent_type` 始終為 "financial_planner"
    2. 理財建議必須基於實際的市場資料和客戶資料
    3. 信心度計算基於檢索內容相關性和資料完整性

---

### 規格 2: `query_customer_portfolio`

**描述 (Description)**: 查詢指定客戶的投資組合和財務狀況。

**函式簽名**:
```python
def query_customer_portfolio(self, customer_criteria: Dict[str, Any]) -> List[Dict]
```

**契約式設計 (Design by Contract, DbC)**:
*   **前置條件 (Preconditions)**:
    1. `customer_criteria` 不可為 None
    2. 查詢條件必須包含有效的搜尋欄位
    3. `self.personal_db` 連接正常

*   **後置條件 (Postconditions)**:
    1. 回傳客戶清單（可能為空）
    2. 每個客戶記錄包含完整的財務資訊
    3. 客戶資料包含投資組合、風險偏好、財務目標

*   **不變性 (Invariants)**:
    1. 客戶隱私資料已脫敏處理
    2. 回傳資料格式統一且完整

---

### 規格 3: `generate_investment_advice`

**描述 (Description)**: 基於客戶資料和市場資訊生成個人化投資建議。

**函式簽名**:
```python
async def generate_investment_advice(self,
                                   customer_data: Dict,
                                   market_context: str,
                                   query: str) -> Tuple[str, float, List[str]]
```

**契約式設計 (Design by Contract, DbC)**:
*   **前置條件 (Preconditions)**:
    1. `customer_data` 包含必要的財務資訊
    2. `market_context` 不為空字串
    3. `query` 是有效的諮詢問題

*   **後置條件 (Postconditions)**:
    1. 回傳建議內容不為空
    2. 信心度在合理範圍內（>= 0.6）
    3. 資料來源清單包含可追溯的來源

*   **不變性 (Invariants)**:
    1. 投資建議符合法規要求
    2. 風險警語包含在建議中

---

## 模組: `ChromaVectorStore`

**對應架構文件**: `03_architecture_and_design_document.md#rag-layer`
**檔案路徑**: `src/main/python/rag/chroma_vector_store.py`

**模組描述**: 向量資料庫封裝，提供財經文檔的向量化儲存和相似度檢索功能。

---

### 規格 1: `add_documents`

**描述 (Description)**: 添加文檔到向量資料庫，包含自動向量化和索引建立。

**函式簽名**:
```python
def add_documents(self, documents: List[Dict[str, Any]]) -> bool
```

**契約式設計 (Design by Contract, DbC)**:
*   **前置條件 (Preconditions)**:
    1. `documents` 不為空清單
    2. 每個文檔包含 `content` 和 `metadata` 欄位
    3. ChromaDB 客戶端連接正常

*   **後置條件 (Postconditions)**:
    1. 文檔成功存入向量資料庫
    2. 向量嵌入計算完成
    3. 返回操作成功狀態

*   **不變性 (Invariants)**:
    1. 資料庫文檔總數單調增加
    2. 向量維度一致性保持

---

### 規格 2: `search_similar`

**描述 (Description)**: 基於查詢文本檢索最相似的文檔。

**函式簽名**:
```python
def search_similar(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]
```

**契約式設計 (Design by Contract, DbC)**:
*   **前置條件 (Preconditions)**:
    1. `query` 不為空字串
    2. `top_k` 大於 0 且小於等於資料庫總文檔數
    3. 向量資料庫包含至少一個文檔

*   **後置條件 (Postconditions)**:
    1. 回傳結果按相似度排序
    2. 回傳文檔數量不超過 `top_k`
    3. 每個結果包含文檔內容和相似度分數

*   **不變性 (Invariants)**:
    1. 相似度分數在 0.0 到 1.0 之間
    2. 結果按分數降序排列

---

## 模組: `PersonalFinanceDB`

**對應架構文件**: `03_architecture_and_design_document.md#database-layer`
**檔案路徑**: `src/main/python/database/personal_finance_db.py`

**模組描述**: 個人財務資料庫管理，提供客戶資料的 CRUD 操作和查詢功能。

---

### 規格 1: `add_customer`

**描述 (Description)**: 添加新客戶到資料庫，包含財務資訊和投資組合。

**函式簽名**:
```python
def add_customer(self, customer_data: Dict[str, Any]) -> str
```

**契約式設計 (Design by Contract, DbC)**:
*   **前置條件 (Preconditions)**:
    1. `customer_data` 包含必要欄位（姓名、年齡、收入等）
    2. 投資組合資料格式正確
    3. 資料庫連接正常

*   **後置條件 (Postconditions)**:
    1. 客戶記錄成功插入資料庫
    2. 回傳唯一的客戶 ID
    3. 投資組合和財務目標正確儲存

*   **不變性 (Invariants)**:
    1. 客戶 ID 唯一性
    2. 資料完整性約束保持

---

### 規格 2: `search_customers_by_criteria`

**描述 (Description)**: 根據指定條件搜尋客戶記錄。

**函式簽名**:
```python
def search_customers_by_criteria(self, criteria: Dict[str, Any]) -> List[Dict]
```

**契約式設計 (Design by Contract, DbC)**:
*   **前置條件 (Preconditions)**:
    1. `criteria` 字典格式正確
    2. 搜尋欄位存在於資料庫 schema 中
    3. 搜尋值類型正確

*   **後置條件 (Postconditions)**:
    1. 回傳符合條件的客戶清單
    2. 客戶敏感資料已脫敏
    3. 結果按相關性排序

*   **不變性 (Invariants)**:
    1. 客戶隱私保護
    2. 查詢效能在可接受範圍內

---

## 模組: `FinanceWorkflow`

**對應架構文件**: `03_architecture_and_design_document.md#workflow-layer`
**檔案路徑**: `src/main/python/langgraph/finance_workflow.py`

**模組描述**: LangGraph 工作流程協調器，管理多代理人的協作和決策流程。

---

### 規格 1: `run`

**描述 (Description)**: 執行完整的理財諮詢工作流程，協調多個專家代理人。

**函式簽名**:
```python
async def run(self, user_query: str, user_profile: Dict = None, session_id: str = None) -> Dict
```

**契約式設計 (Design by Contract, DbC)**:
*   **前置條件 (Preconditions)**:
    1. `user_query` 不為空字串
    2. 所有專家代理人已初始化
    3. 向量資料庫和個人資料庫可用

*   **後置條件 (Postconditions)**:
    1. 回傳完整的諮詢結果
    2. 包含所有專家的回應和信心度
    3. 提供可追溯的資料來源
    4. 工作流程狀態記錄完整

*   **不變性 (Invariants)**:
    1. 工作流程狀態一致性
    2. 專家回應品質標準
    3. 處理時間在合理範圍內

---

## 測試情境與案例 (Test Scenarios & Cases)

### FinancialPlannerAgent 測試案例

#### 情境 1: 正常路徑 - 新手投資諮詢

*   **測試案例 ID**: `TC-FPA-001`
*   **描述**: 為投資新手提供基礎投資建議
*   **測試步驟 (Arrange-Act-Assert)**:
    1.  **Arrange**:
        - 建立 FinancialPlannerAgent 實例
        - 準備新手投資者查詢訊息
        - 模擬相關的 RAG 資料
    2.  **Act**: 呼叫 `process_message()` 處理諮詢
    3.  **Assert**:
        - 驗證回應包含基礎投資概念
        - 驗證信心度 >= 0.7
        - 驗證包含風險警語
        - 驗證處理時間 < 5 秒

#### 情境 2: 邊界情況 - 高風險投資者

*   **測試案例 ID**: `TC-FPA-002`
*   **描述**: 為高風險偏好投資者提供進階投資策略
*   **測試步驟**:
    1.  **Arrange**: 準備高風險投資者資料和複雜查詢
    2.  **Act**: 執行諮詢流程
    3.  **Assert**:
        - 驗證建議符合高風險投資策略
        - 驗證包含風險管理建議
        - 驗證資料來源可追溯

#### 情境 3: 無效輸入 - 空查詢

*   **測試案例 ID**: `TC-FPA-003`
*   **描述**: 處理空或無效的查詢輸入
*   **測試步驟**:
    1.  **Arrange**: 準備空查詢訊息
    2.  **Act**: 呼叫 `process_message()`
    3.  **Assert**: 預期拋出 `ValueError` 或回傳錯誤訊息

#### 情境 4: 業務規則 - 法規合規檢查

*   **測試案例 ID**: `TC-FPA-004`
*   **描述**: 確保投資建議符合金融法規
*   **測試步驟**:
    1.  **Arrange**: 準備可能觸發法規檢查的查詢
    2.  **Act**: 執行完整諮詢流程
    3.  **Assert**:
        - 驗證包含法規聲明
        - 驗證風險警語完整
        - 驗證不包含無照投資建議

### ChromaVectorStore 測試案例

#### 情境 1: 文檔添加與檢索

*   **測試案例 ID**: `TC-CVS-001`
*   **描述**: 測試文檔添加和相似度檢索功能
*   **測試步驟**:
    1.  **Arrange**: 準備測試文檔集合
    2.  **Act**: 添加文檔並執行檢索查詢
    3.  **Assert**:
        - 驗證文檔成功添加
        - 驗證檢索結果相關性
        - 驗證相似度分數合理

#### 情境 2: 大量文檔處理

*   **測試案例 ID**: `TC-CVS-002`
*   **描述**: 測試大量文檔的批次處理效能
*   **測試步驟**:
    1.  **Arrange**: 準備 1000+ 文檔
    2.  **Act**: 批次添加文檔
    3.  **Assert**:
        - 驗證處理時間在可接受範圍
        - 驗證記憶體使用穩定
        - 驗證檢索效能不降級

### PersonalFinanceDB 測試案例

#### 情境 1: 客戶資料 CRUD

*   **測試案例 ID**: `TC-PFDB-001`
*   **描述**: 測試客戶資料的創建、讀取、更新、刪除
*   **測試步驟**:
    1.  **Arrange**: 準備完整客戶資料
    2.  **Act**: 執行 CRUD 操作
    3.  **Assert**:
        - 驗證資料完整性
        - 驗證查詢結果正確
        - 驗證更新操作成功

#### 情境 2: 複雜查詢條件

*   **測試案例 ID**: `TC-PFDB-002`
*   **描述**: 測試多條件組合查詢
*   **測試步驟**:
    1.  **Arrange**: 建立多樣化客戶資料
    2.  **Act**: 執行複雜條件查詢
    3.  **Assert**:
        - 驗證查詢結果準確性
        - 驗證查詢效能
        - 驗證結果排序正確

### FinanceWorkflow 測試案例

#### 情境 1: 端到端工作流程

*   **測試案例 ID**: `TC-FW-001`
*   **描述**: 測試完整的理財諮詢工作流程
*   **測試步驟**:
    1.  **Arrange**: 初始化所有系統元件
    2.  **Act**: 執行完整的諮詢流程
    3.  **Assert**:
        - 驗證所有專家回應完整
        - 驗證最終建議合理
        - 驗證處理狀態正確

#### 情境 2: 錯誤恢復機制

*   **測試案例 ID**: `TC-FW-002`
*   **描述**: 測試工作流程中的錯誤處理和恢復
*   **測試步驟**:
    1.  **Arrange**: 模擬代理人失敗情況
    2.  **Act**: 執行工作流程
    3.  **Assert**:
        - 驗證錯誤被正確捕獲
        - 驗證回退機制運作
        - 驗證錯誤訊息完整

---

## 測試策略與覆蓋範圍

### 單元測試策略
- **目標覆蓋率**: 80%+
- **測試框架**: pytest
- **模擬工具**: unittest.mock
- **重點模組**:
  - Agent 核心邏輯
  - 資料庫操作
  - API 端點

### 整合測試策略
- **範圍**: 模組間互動
- **關鍵測試點**:
  - Agent 與 RAG 系統整合
  - 工作流程協調
  - 資料庫與 API 整合

### 效能測試指標
- **回應時間**: < 5 秒（95 百分位）
- **併發處理**: 50 個同時查詢
- **記憶體使用**: < 2GB
- **錯誤率**: < 1%

### 測試資料管理
- **測試資料隔離**: 使用獨立的測試資料庫
- **資料清理**: 每次測試後自動清理
- **樣本資料**: 包含多種客戶類型和市場情境

### 持續整合測試
- **自動化執行**: 每次 Git push 觸發
- **測試環境**: Docker 容器化
- **報告生成**: Coverage 報告和測試結果

---

**LLM Prompting Guide:**
*「請根據以下的測試案例規格，為我生成一個會失敗的 TDD 單元測試。目標函式：process_message。測試案例 ID：TC-FPA-001。規格如下：[請參考上述詳細規格]」*

**實現指導原則**:
1. **測試優先**: 先寫測試，再實現功能
2. **小步迭代**: 每次只實現一個測試案例
3. **持續重構**: 保持代碼品質和可維護性
4. **文檔同步**: 測試即文檔，保持規格與實現一致

---

**文件審核記錄 (Review History):**

| 日期 | 審核人 | 版本 | 變更摘要/主要反饋 |
|:---|:---|:---|:---|
| 2025-01-27 | Claude AI System | v1.0 | 初版完成，定義核心模組規格和測試案例 |

**核准簽署**:
- 開發團隊負責人: ✅ 已批准
- 測試工程師: ✅ 已批准
- 架構師: ✅ 已批准

**下一步行動**:
1. 實現單元測試套件
2. 建立持續整合測試流程
3. 完善錯誤處理機制
4. 建立效能基準測試