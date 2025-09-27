"""
FinancialPlannerAgent with LLM - 理財規劃專家 (使用真實 LLM)

實作 Linus 哲學：
1. 簡潔執念：專注個人理財規劃，避免複雜投資建議
2. 好品味：基於使用者風險偏好的客製化建議
3. 實用主義：提供具體可行的理財方案
4. Never break userspace：穩定的理財建議格式
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from .llm_base_agent import LLMBaseAgent
from .base_agent import AgentType, MessageType


class FinancialPlannerAgentLLM(LLMBaseAgent):
    """理財規劃專家代理人 (使用真實 LLM)

    特色：
    - 使用 GPT-4o-mini 生成個人化理財建議
    - 結合 RAG 檢索的理財知識
    - 整合個人財務資料庫
    - 專業的理財規劃提示詞
    """

    def __init__(self, name: str = "理財規劃專家", knowledge_retriever=None, personal_db=None):
        super().__init__(
            agent_type=AgentType.FINANCIAL_PLANNER,
            name=name,
            use_rag=True,
            knowledge_retriever=knowledge_retriever,
            personal_db=personal_db
        )

        # 理財規劃專業領域
        self.planning_domains = {
            "investment_planning": "投資規劃",
            "retirement_planning": "退休規劃",
            "risk_management": "風險管理",
            "savings_planning": "儲蓄規劃",
            "tax_planning": "稅務規劃",
            "estate_planning": "遺產規劃"
        }

        # 風險等級配置
        self.risk_profiles = {
            "conservative": {
                "name": "保守型",
                "stock_allocation": "20-40%",
                "bond_allocation": "40-60%",
                "cash_allocation": "20-40%",
                "description": "追求資本保值，接受較低報酬"
            },
            "moderate": {
                "name": "穩健型",
                "stock_allocation": "40-70%",
                "bond_allocation": "20-40%",
                "cash_allocation": "10-20%",
                "description": "平衡風險與報酬"
            },
            "aggressive": {
                "name": "積極型",
                "stock_allocation": "70-90%",
                "bond_allocation": "5-20%",
                "cash_allocation": "5-15%",
                "description": "追求高報酬，能承受較大波動"
            }
        }

    async def _build_prompt(self,
                          query: str,
                          knowledge_results: List[Dict],
                          personal_context: Dict[str, Any]) -> str:
        """構建理財規劃專業提示詞"""

        # 分析查詢領域
        planning_domain = self._classify_planning_domain(query)
        domain_name = self.planning_domains.get(planning_domain, "綜合理財規劃")

        # 格式化知識上下文
        knowledge_context = self._format_knowledge_context(knowledge_results)

        # 格式化個人財務上下文
        personal_info = ""
        if personal_context.get("has_customer_data"):
            sample_customer = personal_context.get("sample_customer", {})
            if sample_customer:
                personal_info = f"""
個人財務資料參考：
- 年齡: {sample_customer.get('age', '30')} 歲
- 風險承受度: {sample_customer.get('risk_tolerance', 'moderate')}
- 投資經驗: {sample_customer.get('investment_experience', 'beginner')}
- 財務目標: {', '.join(sample_customer.get('financial_goals', ['財富累積']))}
"""

        prompt = f"""你是一位專業的認證理財規劃師 (CFP)，請根據以下資訊提供專業的{domain_name}建議：

用戶查詢：{query}

相關理財知識：
{knowledge_context}

{personal_info}

請提供結構化的理財規劃建議，包含：

📊 **{domain_name}分析**

🎯 **個人財務評估**
- 根據提供的資訊分析客戶需求
- 評估風險承受度和投資時間軸
- 識別關鍵的理財目標

📈 **資產配置建議**
- 基於風險偏好的具體配置比例
- 適合的投資工具和產品推薦
- 分階段實施的時程安排

💡 **具體行動方案**
1. **短期行動** (1-6個月)：立即可執行的步驟
2. **中期規劃** (6個月-2年)：逐步建立的投資組合
3. **長期目標** (2年以上)：達成財務目標的策略

🛡️ **風險管理**
- 投資風險的控制措施
- 保險需求評估
- 緊急備用金建議

📋 **定期檢視計劃**
- 建議的檢視頻率
- 調整的時機和條件
- 重要的績效指標

要求：
1. 建議要具體可行，避免抽象概念
2. 提供明確的數字和比例
3. 考慮台灣的金融環境和法規
4. 使用繁體中文，語調專業但易懂
5. 包含適當的風險警語
6. 結構清晰，使用 Markdown 格式

請基於專業知識和提供的資訊，給出個人化的理財規劃建議。"""

        return prompt

    def _classify_planning_domain(self, query: str) -> str:
        """分類理財規劃領域"""
        query_lower = query.lower()

        # 投資規劃
        if any(keyword in query_lower for keyword in
               ["投資", "資產配置", "投資組合", "基金", "股票", "債券"]):
            return "investment_planning"

        # 退休規劃
        elif any(keyword in query_lower for keyword in
                 ["退休", "養老", "退休金", "退休準備"]):
            return "retirement_planning"

        # 風險管理
        elif any(keyword in query_lower for keyword in
                 ["保險", "風險", "保障", "意外"]):
            return "risk_management"

        # 儲蓄規劃
        elif any(keyword in query_lower for keyword in
                 ["儲蓄", "存款", "緊急基金", "現金流"]):
            return "savings_planning"

        # 稅務規劃
        elif any(keyword in query_lower for keyword in
                 ["稅", "節稅", "稅務", "扣除額"]):
            return "tax_planning"

        # 預設為投資規劃
        else:
            return "investment_planning"

    async def _generate_fallback_response(self, prompt: str) -> str:
        """LLM 不可用時的降級回應"""
        return """📊 **個人投資建議**

**基於您的風險偏好（穩健型），建議資產配置：**
• 股票類投資：50%
• 債券類投資：40%
• 現金與約當現金：10%

**具體執行建議：**
1. 分批進場投資，避免單次大額投入
2. 定期定額投資優質基金或ETF
3. 每季檢視投資組合並適度調整
4. 保持3-6個月生活費的緊急備用金

**注意事項：**
- 投資有風險，請謹慎評估個人財務狀況
- 建議分散投資，不要集中單一標的

*注意：此為預設理財建議模板，建議配置 LLM API 以獲得更詳細的個人化分析。*"""

    def query_customer_portfolio(self, customer_criteria: Dict[str, Any]) -> List[Dict]:
        """查詢客戶投資組合"""
        if not self.personal_db:
            return []

        try:
            return self.personal_db.search_customers_by_criteria(customer_criteria)
        except Exception as e:
            self.logger.error(f"Error querying customer portfolio: {e}")
            return []

    async def generate_investment_advice(self,
                                       customer_data: Dict,
                                       market_context: str,
                                       query: str) -> tuple[str, float, List[str]]:
        """生成投資建議"""
        try:
            # 構建包含客戶資料的提示詞
            prompt = f"""基於以下客戶資料和市場環境，提供投資建議：

客戶資料：{customer_data}
市場環境：{market_context}
具體問題：{query}

請提供具體的投資建議和風險評估。"""

            response_content = await self._generate_llm_response(prompt)
            confidence = 0.85 if response_content else 0.6
            sources = ["理財專家知識庫", "個人財務規劃準則", "投資組合理論"]

            return response_content, confidence, sources

        except Exception as e:
            self.logger.error(f"Error generating investment advice: {e}")
            return "無法生成投資建議，請稍後再試。", 0.3, []

    def get_planning_capabilities(self) -> Dict[str, Any]:
        """獲取理財規劃能力描述"""
        return {
            "supported_domains": list(self.planning_domains.values()),
            "risk_profiles": list(self.risk_profiles.keys()),
            "llm_configured": self.get_llm_status()["llm_configured"],
            "features": [
                "個人化資產配置",
                "風險評估分析",
                "退休規劃建議",
                "稅務優化策略",
                "保險需求分析"
            ],
            "data_sources": [
                "RAG 理財知識庫",
                "個人財務資料庫",
                "市場資訊"
            ]
        }