"""
FinancialAnalystAgent with Real LLM Integration - 金融分析專家 (真實 LLM 版本)

實作 Linus 哲學：
1. 簡潔執念：專注市場分析和投資決策支援
2. 好品味：基於數據的客觀分析結論
3. 實用主義：提供可操作的投資建議
4. Never break userspace：一致的分析報告格式
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import re
import logging

from .base_agent import BaseAgent, AgentMessage, AgentType, MessageType
from .llm_base_agent import LLMBaseAgent
from ..llm import generate_llm_response, is_llm_configured


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

    async def process_message(self, message: AgentMessage) -> AgentMessage:
        """處理訊息並生成專業金融分析"""
        try:
            query = message.content.strip()

            # 1. RAG 檢索相關市場資訊
            knowledge_results = await self._retrieve_knowledge(query, max_results=8)
            knowledge_context = self._format_knowledge_context(knowledge_results)

            # 2. 分析查詢類型
            analysis_domain = self._classify_analysis_domain(query)

            # 3. 使用 LLM 生成專業分析
            analysis_report = await self._generate_llm_analysis(
                query, analysis_domain, knowledge_context
            )

            # 4. 計算信心度
            confidence = self._calculate_confidence(query, knowledge_results)

            # 5. 建立回應
            response = self.create_response(
                content=analysis_report,
                metadata={
                    "analysis_domain": analysis_domain,
                    "knowledge_used": len(knowledge_results),
                    "analysis_time": datetime.now().isoformat(),
                    "agent_type": "financial_analyst_llm",
                    "llm_configured": is_llm_configured()
                },
                sources=self._extract_sources(knowledge_results),
                confidence=confidence
            )

            self.log_interaction(message, response)
            return response

        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return self.create_error_response(
                f"分析過程中發生錯誤：{str(e)}",
                metadata={"error_type": "processing_error"}
            )

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

    async def _generate_llm_analysis(self,
                                   query: str,
                                   analysis_domain: str,
                                   knowledge_context: str) -> str:
        """使用 LLM 生成專業金融分析"""

        # 如果沒有配置 LLM，使用預設模板
        if not is_llm_configured():
            return await self._generate_template_analysis(query, analysis_domain)

        # 構建專業的提示詞
        prompt = self._build_analysis_prompt(query, analysis_domain, knowledge_context)

        try:
            # 調用 LLM 生成分析
            llm_response = await generate_llm_response(
                prompt,
                max_tokens=1200,
                temperature=0.3  # 較低溫度確保專業性
            )

            # 後處理：確保包含必要的風險警語
            analysis = self._post_process_analysis(llm_response.content)

            return analysis

        except Exception as e:
            self.logger.error(f"LLM generation failed: {e}")
            # 降級到模板回應
            return await self._generate_template_analysis(query, analysis_domain)

    def _build_analysis_prompt(self,
                             query: str,
                             analysis_domain: str,
                             knowledge_context: str) -> str:
        """構建專業的金融分析提示詞"""

        domain_name = self.analysis_domains.get(analysis_domain, "市場分析")

        prompt = f"""你是一位專業的金融分析師，請根據以下資訊提供專業的{domain_name}：

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

        return prompt

    async def _generate_template_analysis(self, query: str, analysis_domain: str) -> str:
        """生成模板分析（LLM 不可用時的降級方案）"""
        domain_name = self.analysis_domains.get(analysis_domain, "市場分析")

        return f"""📈 **{domain_name}報告**

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

    def _post_process_analysis(self, analysis: str) -> str:
        """後處理分析內容，確保包含必要警語"""

        # 確保包含風險警語
        if "風險提醒" not in analysis and "投資風險" not in analysis:
            analysis += "\n\n⚠️ **投資風險提醒**\n- 投資有風險，請謹慎評估個人財務狀況\n- 過往績效不代表未來表現\n- 建議分散投資，不要集中單一標的"

        # 確保包含免責聲明
        if "本分析僅供參考" not in analysis:
            analysis += "\n\n*本分析僅供參考，不構成投資建議。投資決策請自行判斷。*"

        return analysis

    def _format_knowledge_context(self, knowledge_results: List[Dict]) -> str:
        """格式化知識檢索結果為上下文"""
        if not knowledge_results:
            return "暫無相關市場資訊"

        context_parts = []
        for i, result in enumerate(knowledge_results[:6], 1):
            title = result.get('metadata', {}).get('title', f'市場資訊 {i}')
            content = result.get('content', '')[:300]  # 限制長度
            context_parts.append(f"{i}. {title}: {content}")

        return "\n".join(context_parts)

    def _calculate_confidence(self, query: str, knowledge_results: List[Dict]) -> float:
        """計算分析信心度"""
        base_confidence = 0.7

        # 根據檢索結果數量調整
        if len(knowledge_results) >= 5:
            base_confidence += 0.1
        elif len(knowledge_results) >= 3:
            base_confidence += 0.05

        # 根據查詢明確度調整
        if len(query) > 10 and any(keyword in query for keyword in
                                 ["分析", "建議", "投資", "股票", "基金"]):
            base_confidence += 0.05

        # 如果使用真實 LLM，提高信心度
        if is_llm_configured():
            base_confidence += 0.1

        return min(base_confidence, 0.95)  # 最高 95%

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