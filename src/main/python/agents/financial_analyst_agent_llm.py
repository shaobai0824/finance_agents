"""
FinancialAnalystAgent with Real LLM Integration - 金融分析專家 (真實 LLM 版本)

實作 Linus 哲學：
1. 簡潔執念：專注市場分析和投資決策支援
2. 好品味：基於數據的客觀分析結論
3. 實用主義：提供可操作的投資建議
4. Never break userspace：一致的分析報告格式
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from .base_agent import AgentMessage, AgentType, BaseAgent, MessageType
from .llm_base_agent import LLMBaseAgent

try:
    from ..llm import generate_llm_response, is_llm_configured
except ImportError:
    try:
        from llm import generate_llm_response, is_llm_configured
    except ImportError:
        async def generate_llm_response(prompt, **kwargs):
            return type('MockResponse', (), {'content': '模擬回應', 'model': 'mock'})()
        def is_llm_configured():
            return False


class FinancialAnalystAgentLLM(LLMBaseAgent):
    """金融分析專家代理人 (使用真實 LLM)

    特色：
    - 使用真實的 LLM (OpenAI/Anthropic) 生成分析
    - 結合 RAG 檢索的市場資訊
    - 專業的金融分析提示詞
    - 結構化的分析報告輸出
    """

    def __init__(self, name: str = "金融分析專家", knowledge_retriever=None):
        super().__init__(
            agent_type=AgentType.FINANCIAL_ANALYST,
            name=name,
            use_rag=True,
            knowledge_retriever=knowledge_retriever
        )

        self.logger = logging.getLogger(__name__)

        # 檢查 LLM 配置
        if not is_llm_configured():
            self.logger.warning("No LLM configured, falling back to template responses")

        # 分析專業領域
        self.analysis_domains = {
            "technical_analysis": "技術分析",
            "fundamental_analysis": "基本面分析",
            "market_analysis": "市場分析",
            "risk_assessment": "風險評估",
            "sector_analysis": "產業分析"
        }

    async def _build_prompt(self,
                          query: str,
                          knowledge_results: List[Dict],
                          personal_context: Dict[str, Any]) -> str:
        """構建金融分析專業提示詞"""

        # 分析查詢類型
        analysis_domain = self._classify_analysis_domain(query)
        domain_name = self.analysis_domains.get(analysis_domain, "市場分析")

        # 格式化知識上下文
        knowledge_context = self._format_knowledge_context(knowledge_results)

        return f"""你是一位專業的金融分析師，請根據以下資訊提供專業的{domain_name}：

用戶查詢：{query}

相關市場資訊：
{knowledge_context}

請提供結構化的分析報告，包含：

📈 **{domain_name}報告**

📊 **當前市場狀況**
- 基於提供的市場資訊進行客觀分析
- 結合歷史趨勢和當前狀況

💡 **關鍵發現**
1. **核心觀點**：基於數據的客觀判斷
2. **風險因子**：識別主要風險和不確定性
3. **機會分析**：潛在的投資機會

📋 **專業建議**
- 具體可執行的投資策略
- 適合的投資時機和方法
- 風險控制措施

⚠️ **風險提醒**
- 投資風險警語
- 市場不確定性提醒

分析要求：
1. 保持客觀專業，基於事實和數據
2. 避免過度樂觀或悲觀的預測
3. 提供具體可行的建議
4. 使用繁體中文回應
5. 格式要清晰易讀，使用適當的 Markdown 標記
"""

    async def _generate_fallback_response(self, prompt: str) -> str:
        """LLM 不可用時的金融分析降級回應"""
        return """📈 **市場分析報告**

📊 **當前市場狀況**
- 基於最新市場資訊進行分析
- 考量總體經濟環境影響
- 結合歷史數據比較

💡 **關鍵發現**
1. **趨勢判斷**：根據技術指標和基本面數據分析
2. **風險評估**：識別主要風險因子和不確定性
3. **機會點**：潛在投資機會和進場時機

📋 **投資建議**
- 建議採用分散投資策略
- 定期檢視投資組合表現
- 根據風險承受度調整配置

⚠️ **風險提醒**
- 投資有風險，過往績效不代表未來表現
- 建議分散投資，控制單一標的投資比重
- 定期檢視投資組合，適時調整策略

*注意：此為預設分析模板，建議配置 LLM API 以獲得更詳細的個人化分析。*
"""

    def _get_system_prompt(self) -> str:
        """金融分析專家的系統提示詞"""
        return """你是專業的金融分析師，專精於股票、債券、基金等金融商品的深度分析研究。

# 專業領域
- 技術分析：價格走勢、技術指標、交易訊號分析
- 基本面分析：財務報表、公司估值、產業研究
- 市場分析：總體經濟、政策影響、市場趨勢
- 投資策略：選股邏輯、進出場時機、風險控制

# 分析框架
1. **數據驅動**: 基於客觀數據和歷史資料進行分析
2. **多角度分析**: 結合技術面、基本面、總體面觀點
3. **風險評估**: 識別並量化投資風險
4. **實務導向**: 提供可執行的投資建議

# 回應格式
📈 **市場/個股分析**
- 當前狀況評估
- 關鍵技術/基本面指標
- 趨勢判斷與預測

📊 **數據解讀**
- 重要財務/技術指標說明
- 同業或歷史比較
- 異常狀況分析

💡 **投資建議**
- 進出場時機建議
- 目標價位設定
- 停損停利策略

⚠️ **風險警示**
- 主要風險因子識別
- 市場不確定性提醒
- 建議風險控制措施

🔍 **後續觀察重點**
- 需關注的關鍵指標
- 重要時間節點提醒

注意：分析基於現有資料，市場具不確定性，投資前請審慎評估。

我會結合檢索到的最新市場資訊和歷史數據來提供專業分析。"""

    async def can_handle(self, query: str) -> float:
        """評估是否能處理金融分析相關查詢"""
        query_lower = query.lower()

        # 計算金融分析關鍵字匹配度
        analysis_keywords = [
            "技術分析", "基本面分析", "市場分析", "股票分析", "投資分析",
            "財報分析", "產業分析", "趨勢分析", "K線", "移動平均", "RSI", "MACD",
            "本益比", "ROE", "營收", "獲利", "股價淨值比", "技術指標",
            "stock", "market", "analysis", "economic", "trend", "data",
            "分析", "股票", "投資", "市場", "技術", "基本面", "財報",
            "本益比", "趨勢", "指標", "價格", "評估"
        ]

        keyword_count = sum(1 for keyword in analysis_keywords if keyword in query_lower)
        keyword_score = min(keyword_count / 6, 1.0) * 0.6

        # 數據/指標相關詞彙加分
        data_terms = ["數據", "指標", "比率", "報酬率", "績效", "走勢", "價格"]
        data_count = sum(1 for term in data_terms if term in query)
        data_score = min(data_count / 3, 1.0) * 0.3

        # 具體性評分（是否提及具體股票、數據等）
        specificity_indicators = ["股票代號", "公司名稱", "具體數字", "時間範圍"]
        has_specific = any(
            indicator in query for indicator in ["2330", "台積電", "%", "元", "年", "月"]
        )
        specificity_score = 0.1 if has_specific else 0

        final_score = keyword_score + data_score + specificity_score

        self.logger.debug(
            f"金融分析專家能力評分: {final_score:.2f} "
            f"(關鍵字: {keyword_score:.2f}, 數據導向: {data_score:.2f}, 具體性: {specificity_score:.2f})"
        )

        return min(final_score, 1.0)

    def _classify_analysis_domain(self, query: str) -> str:
        """分類分析領域"""
        query_lower = query.lower()

        # 技術分析關鍵字
        if any(keyword in query_lower for keyword in
               ["技術分析", "k線", "移動平均", "macd", "rsi", "支撐", "壓力", "趨勢"]):
            return "technical_analysis"

        # 基本面分析關鍵字
        elif any(keyword in query_lower for keyword in
                 ["基本面", "財報", "本益比", "roe", "營收", "獲利", "財務"]):
            return "fundamental_analysis"

        # 風險評估關鍵字
        elif any(keyword in query_lower for keyword in
                 ["風險", "波動", "風險評估", "投資風險"]):
            return "risk_assessment"

        # 產業分析關鍵字
        elif any(keyword in query_lower for keyword in
                 ["產業", "類股", "板塊", "sector", "行業"]):
            return "sector_analysis"

        # 預設為市場分析
        else:
            return "market_analysis"


    def get_analysis_capabilities(self) -> Dict[str, Any]:
        """取得分析能力描述"""
        return {
            "supported_domains": list(self.analysis_domains.values()),
            "llm_configured": is_llm_configured(),
            "features": [
                "技術分析",
                "基本面分析",
                "市場分析",
                "風險評估",
                "產業分析"
            ],
            "data_sources": "RAG 檢索 + 即時市場資訊"
        }