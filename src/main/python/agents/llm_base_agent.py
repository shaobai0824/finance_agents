"""
LLM Base Agent - 所有使用 LLM 的 Agent 的基礎類別
提供統一的 LLM 調用介面和錯誤處理
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
from abc import abstractmethod

from .base_agent import BaseAgent, AgentMessage, AgentType, MessageType

try:
    from ..llm import generate_llm_response, is_llm_configured, LLMResponse
except ImportError:
    # 允許在測試環境中使用絕對導入
    try:
        from llm import generate_llm_response, is_llm_configured, LLMResponse
    except ImportError:
        # 模擬函數用於測試
        async def generate_llm_response(prompt, **kwargs):
            return type('MockResponse', (), {
                'content': '模擬 LLM 回應',
                'model': 'mock',
                'usage': {},
                'finish_reason': 'stop',
                'response_time': 0.1
            })()

        def is_llm_configured():
            return False

        LLMResponse = type('LLMResponse', (), {})


class LLMBaseAgent(BaseAgent):
    """使用 LLM 的 Agent 基礎類別"""

    def __init__(self,
                 agent_type: AgentType,
                 name: str,
                 use_rag: bool = True,
                 knowledge_retriever=None,
                 personal_db=None):
        super().__init__(
            agent_type=agent_type,
            name=name,
            use_rag=use_rag,
            knowledge_retriever=knowledge_retriever
        )

        self.personal_db = personal_db
        self.logger = logging.getLogger(__name__)

        # LLM 配置
        self.llm_config = {
            "max_tokens": 1000,
            "temperature": 0.3,  # 較低溫度確保專業性
            "model": "gpt-4o-mini"
        }

    async def process_message(self, message: AgentMessage) -> AgentMessage:
        """處理訊息的通用流程"""
        try:
            query = message.content.strip()

            # 1. RAG 檢索相關資訊
            knowledge_results = []
            if self.use_rag and self.knowledge_retriever:
                knowledge_results = await self._retrieve_knowledge(query, max_results=8)

            # 2. 查詢個人資料庫（如果需要）
            personal_context = await self._get_personal_context(query)

            # 3. 構建專業提示詞
            prompt = await self._build_prompt(query, knowledge_results, personal_context)

            # 4. 使用 LLM 生成回應
            response_content = await self._generate_llm_response(prompt)

            # 5. 後處理回應
            final_content = self._post_process_response(response_content)

            # 6. 計算信心度
            confidence = self._calculate_confidence(query, knowledge_results)

            # 7. 建立回應
            response = self.create_response(
                content=final_content,
                metadata={
                    "llm_model": self.llm_config["model"],
                    "knowledge_used": len(knowledge_results),
                    "personal_context_used": bool(personal_context),
                    "agent_type": self.agent_type.value,
                    "processing_time": datetime.now().isoformat()
                },
                sources=self._extract_sources(knowledge_results),
                confidence=confidence
            )

            self.log_interaction(message, response)
            return response

        except Exception as e:
            self.logger.error(f"Error processing message in {self.name}: {e}")
            return self.create_error_response(
                f"處理過程中發生錯誤：{str(e)}",
                metadata={"error_type": "llm_processing_error"}
            )

    async def _get_personal_context(self, query: str) -> Dict[str, Any]:
        """獲取個人財務相關上下文"""
        if not self.personal_db:
            return {}

        try:
            # 根據查詢決定是否需要個人財務資料
            if any(keyword in query.lower() for keyword in
                   ["我的", "個人", "客戶", "組合", "資產", "財務狀況"]):

                # 模擬查詢客戶資料（實際應用中會有具體的客戶 ID）
                customers = self.personal_db.search_customers_by_criteria({})
                if customers:
                    return {
                        "has_customer_data": True,
                        "customer_count": len(customers),
                        "sample_customer": customers[0] if customers else None
                    }

            return {}
        except Exception as e:
            self.logger.error(f"Error getting personal context: {e}")
            return {}

    async def _generate_llm_response(self, prompt: str) -> str:
        """使用 LLM 生成回應"""
        if not is_llm_configured():
            self.logger.warning("LLM not configured, using fallback response")
            return await self._generate_fallback_response(prompt)

        try:
            response = await generate_llm_response(
                prompt=prompt,
                **self.llm_config
            )
            return response.content

        except Exception as e:
            self.logger.error(f"LLM generation failed: {e}")
            return await self._generate_fallback_response(prompt)

    @abstractmethod
    async def _build_prompt(self,
                          query: str,
                          knowledge_results: List[Dict],
                          personal_context: Dict[str, Any]) -> str:
        """構建專業提示詞 - 每個 Agent 需要實現"""
        pass

    @abstractmethod
    async def _generate_fallback_response(self, prompt: str) -> str:
        """LLM 不可用時的降級回應 - 每個 Agent 需要實現"""
        pass

    def _post_process_response(self, response: str) -> str:
        """後處理回應內容"""
        # 確保包含必要的風險警語
        if "風險" not in response and "投資" in response:
            response += "\n\n⚠️ **投資風險提醒**\n投資有風險，請謹慎評估個人財務狀況。過往績效不代表未來表現。"

        # 確保包含免責聲明
        if "僅供參考" not in response:
            response += "\n\n*本分析僅供參考，不構成投資建議。投資決策請自行判斷。*"

        return response

    def _calculate_confidence(self, query: str, knowledge_results: List[Dict]) -> float:
        """計算回應信心度"""
        base_confidence = 0.7

        # 根據檢索結果數量調整
        if len(knowledge_results) >= 5:
            base_confidence += 0.1
        elif len(knowledge_results) >= 3:
            base_confidence += 0.05

        # 根據查詢明確度調整
        if len(query) > 10:
            base_confidence += 0.05

        # 如果使用真實 LLM，提高信心度
        if is_llm_configured():
            base_confidence += 0.15

        return min(base_confidence, 0.95)

    def _format_knowledge_context(self, knowledge_results: List[Dict]) -> str:
        """格式化知識檢索結果"""
        if not knowledge_results:
            return "暫無相關資訊"

        context_parts = []
        for i, result in enumerate(knowledge_results[:6], 1):
            title = result.get('metadata', {}).get('title', f'資料 {i}')
            content = result.get('content', '')[:200]
            context_parts.append(f"{i}. {title}: {content}")

        return "\n".join(context_parts)

    def get_llm_status(self) -> Dict[str, Any]:
        """獲取 LLM 狀態資訊"""
        return {
            "llm_configured": is_llm_configured(),
            "model": self.llm_config["model"],
            "agent_name": self.name,
            "agent_type": self.agent_type.value,
            "use_rag": self.use_rag,
            "has_personal_db": bool(self.personal_db)
        }