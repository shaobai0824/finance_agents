"""
LegalExpertAgent with LLM - 法律專家 (使用真實 LLM)

實作 Linus 哲學：
1. 簡潔執念：直接回答法規問題，避免冗長解釋
2. 好品味：準確引用法條和實務見解
3. 實用主義：提供可操作的合規建議
4. Never break userspace：一致的法律意見格式
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from .llm_base_agent import LLMBaseAgent
from .base_agent import AgentType, MessageType


class LegalExpertAgentLLM(LLMBaseAgent):
    """法律專家代理人 (使用真實 LLM)

    特色：
    - 使用 GPT-4o-mini 生成專業法律建議
    - 專注金融投資相關法規
    - 不使用 RAG，純依據法律知識
    - 提供準確的法條引用和實務建議
    """

    def __init__(self, name: str = "法律專家", knowledge_retriever=None):
        super().__init__(
            agent_type=AgentType.LEGAL_EXPERT,
            name=name,
            use_rag=False,  # 法律專家不使用 RAG
            knowledge_retriever=None
        )

        # 金融法規專業領域
        self.legal_domains = {
            "securities_law": "證券交易法",
            "banking_law": "銀行法",
            "insurance_law": "保險法",
            "trust_law": "信託法",
            "tax_law": "稅法",
            "consumer_protection": "消費者保護法",
            "money_laundering": "洗錢防制法",
            "personal_data": "個人資料保護法"
        }

        # 常見法規問題類型
        self.legal_categories = {
            "investment_regulations": "投資法規",
            "financial_disclosure": "資訊揭露",
            "investor_protection": "投資人保護",
            "compliance_requirements": "合規要求",
            "risk_warnings": "風險警語",
            "licensing_requirements": "執照要求"
        }

    async def _build_prompt(self,
                          query: str,
                          knowledge_results: List[Dict],
                          personal_context: Dict[str, Any]) -> str:
        """構建法律專家專業提示詞"""

        # 分析法律問題類型
        legal_category = self._classify_legal_category(query)
        category_name = self.legal_categories.get(legal_category, "一般法律諮詢")

        prompt = f"""你是一位專精金融法規的執業律師，請根據台灣相關法規回答以下問題：

法律諮詢問題：{query}

問題類型：{category_name}

請提供專業的法律意見，包含：

⚖️ **法律分析**

📋 **相關法規**
- 明確引用適用的法條條文
- 說明法規的立法目的和規範範圍
- 提及相關的主管機關和執法單位

🔍 **實務見解**
- 基於法規條文的解釋和適用
- 參考主管機關的函釋和實務作法
- 說明可能的法律風險和後果

💡 **合規建議**
- 具體的遵法措施和注意事項
- 建議的內控制度和程序
- 預防法律風險的最佳做法

⚠️ **風險提醒**
- 違反相關法規的法律責任
- 可能面臨的行政處分或刑責
- 民事責任和賠償風險

📝 **建議行動**
- 立即應採取的合規措施
- 後續應持續注意的法規變動
- 必要時尋求專業法律諮詢的時機

要求：
1. 引用的法條要準確，包含條文內容
2. 分析要客觀中立，避免主觀判斷
3. 建議要具體可行，符合實務操作
4. 使用繁體中文，採用法律專業用語
5. 結構清晰，重點明確
6. 包含適當的免責聲明

請基於台灣現行法規和實務，提供專業的法律意見。"""

        return prompt

    def _classify_legal_category(self, query: str) -> str:
        """分類法律問題類型"""
        query_lower = query.lower()

        # 投資法規
        if any(keyword in query_lower for keyword in
               ["投資", "證券", "股票", "基金", "期貨", "選擇權"]):
            return "investment_regulations"

        # 資訊揭露
        elif any(keyword in query_lower for keyword in
                 ["揭露", "公告", "說明書", "公開", "資訊"]):
            return "financial_disclosure"

        # 投資人保護
        elif any(keyword in query_lower for keyword in
                 ["投資人", "保護", "權益", "申訴", "糾紛"]):
            return "investor_protection"

        # 合規要求
        elif any(keyword in query_lower for keyword in
                 ["合規", "法規", "規定", "要求", "義務"]):
            return "compliance_requirements"

        # 風險警語
        elif any(keyword in query_lower for keyword in
                 ["風險", "警語", "聲明", "告知"]):
            return "risk_warnings"

        # 執照要求
        elif any(keyword in query_lower for keyword in
                 ["執照", "許可", "登記", "核准", "資格"]):
            return "licensing_requirements"

        # 預設為一般投資法規
        else:
            return "investment_regulations"

    async def _generate_fallback_response(self, prompt: str) -> str:
        """LLM 不可用時的降級回應"""
        return """⚖️ **法律意見**

📋 **相關法規**
根據證券交易法及相關法規，投資活動應遵循以下規範：

1. **資訊揭露義務**：依證券交易法規定，提供正確完整資訊
2. **適合性原則**：評估客戶風險承受度，推薦適當商品
3. **利益衝突管理**：避免損害客戶權益的利益衝突

💡 **合規建議**
- 確保所有投資建議符合相關法規要求
- 提供完整的風險警語和商品說明
- 建立完善的客戶資料和交易記錄

⚠️ **風險提醒**
- 違反證券法規可能面臨行政處分
- 未善盡告知義務可能承擔民事責任
- 建議定期關注法規異動

*注意：此為一般性法律資訊，不構成具體法律建議。個案問題請諮詢專業律師。*

**免責聲明**：本意見僅供參考，不構成正式法律建議。具體個案請諮詢執業律師。"""

    async def provide_legal_opinion(self, legal_question: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """提供法律意見"""
        try:
            # 使用 LLM 生成法律意見
            legal_opinion = await self._generate_llm_response(
                await self._build_prompt(legal_question, [], context or {})
            )

            return {
                "legal_opinion": legal_opinion,
                "confidence": 0.90,  # 法律意見通常有較高信心度
                "sources": ["台灣相關法規", "主管機關函釋", "法律實務"],
                "disclaimer": "本意見僅供參考，不構成正式法律建議",
                "consultation_recommended": "重要決策建議諮詢專業律師"
            }

        except Exception as e:
            self.logger.error(f"Error providing legal opinion: {e}")
            return {
                "legal_opinion": "無法提供法律意見，請諮詢專業律師",
                "confidence": 0.0,
                "sources": [],
                "error": str(e)
            }

    def check_compliance_requirements(self, business_type: str, activity: str) -> Dict[str, Any]:
        """檢查合規要求"""
        try:
            # 基本合規檢查項目
            compliance_items = {
                "投資顧問": [
                    "投資顧問事業設置標準",
                    "投資顧問事業管理規則",
                    "證券投資顧問事業負責人與業務人員管理規則"
                ],
                "證券經紀": [
                    "證券商設置標準",
                    "證券商管理規則",
                    "證券商業務員管理規則"
                ],
                "投信投顧": [
                    "證券投資信託及顧問法",
                    "證券投資信託事業管理規則",
                    "證券投資顧問事業管理規則"
                ]
            }

            return {
                "business_type": business_type,
                "activity": activity,
                "applicable_regulations": compliance_items.get(business_type, []),
                "recommendation": "請依據具體業務內容諮詢主管機關或專業律師"
            }

        except Exception as e:
            self.logger.error(f"Error checking compliance: {e}")
            return {"error": str(e)}

    def get_legal_capabilities(self) -> Dict[str, Any]:
        """獲取法律專業能力描述"""
        return {
            "supported_domains": list(self.legal_domains.values()),
            "legal_categories": list(self.legal_categories.values()),
            "llm_configured": self.get_llm_status()["llm_configured"],
            "specializations": [
                "證券交易法",
                "銀行法規",
                "投資人保護",
                "金融合規",
                "風險警語要求"
            ],
            "services": [
                "法規諮詢",
                "合規檢查",
                "風險評估",
                "法律意見書",
                "合規建議"
            ],
            "disclaimer": "提供一般性法律資訊，不取代專業律師諮詢"
        }