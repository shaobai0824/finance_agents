"""
BaseAgent - 所有代理人的基礎類別（整合 LLM 功能）

實作 Linus 哲學：
1. 好品味：簡潔的代理人介面，消除特殊情況
2. 實用主義：專注解決實際理財問題
3. Never break userspace：穩定的 API 契約
4. 簡潔執念：每個代理人只做一件事並做好
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime

# 信心度計算系統
try:
    from ..evaluation.confidence_calculator import confidence_calculator, ConfidenceMetrics
except ImportError:
    # 測試環境降級
    confidence_calculator = None
    ConfidenceMetrics = None

# LLM 相關導入
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

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """代理人類型枚舉"""
    MANAGER = "manager"
    FINANCIAL_PLANNER = "financial_planner"
    FINANCIAL_ANALYST = "financial_analyst"
    LEGAL_EXPERT = "legal_expert"


class MessageType(Enum):
    """訊息類型枚舉"""
    QUERY = "query"           # 使用者查詢
    RESPONSE = "response"     # 代理人回應
    ROUTE = "route"          # 路由決策
    ROUTING = "routing"      # 路由處理中
    DATA = "data"            # 資料查詢結果
    ERROR = "error"          # 錯誤訊息


@dataclass
class AgentMessage:
    """代理人間傳遞的訊息格式

    Linus 哲學：好品味的資料結構設計
    - 簡潔：只包含必要欄位
    - 一致：所有代理人使用相同格式
    - 可擴展：metadata 支援未來擴展
    """
    agent_type: AgentType
    message_type: MessageType
    content: str
    metadata: Optional[Dict[str, Any]] = None
    sources: Optional[List[str]] = None  # 資料來源追蹤
    confidence: Optional[float] = None   # 信心度評分

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "agent_type": self.agent_type.value,
            "message_type": self.message_type.value,
            "content": self.content,
            "metadata": self.metadata or {},
            "sources": self.sources or [],
            "confidence": self.confidence
        }


class BaseAgent(ABC):
    """所有理財代理人的基礎類別（整合 LLM 功能）

    實作 Linus 的核心原則：
    1. 好品味：統一的代理人介面，無特殊情況
    2. Never break userspace：穩定的 API 契約
    3. 簡潔執念：每個代理人專注單一職責
    4. 實用主義：所有代理人都使用 LLM，無例外
    """

    def __init__(self,
                 agent_type: AgentType,
                 name: str,
                 use_rag: bool = True,
                 knowledge_retriever=None,
                 personal_db=None):
        """初始化代理人

        Args:
            agent_type: 代理人類型
            name: 代理人名稱
            use_rag: 是否使用 RAG 系統
            knowledge_retriever: 知識檢索器（可選）
            personal_db: 個人資料庫（可選）
        """
        self.agent_type = agent_type
        self.name = name
        self.use_rag = use_rag
        self.knowledge_retriever = knowledge_retriever
        self.personal_db = personal_db
        self.logger = logging.getLogger(f"{__name__}.{name}")
        self.last_retrieved_docs = []  # 儲存最後檢索的 RAG 文件

        # LLM 配置
        self.llm_config = {
            "max_tokens": 1000,
            "temperature": 0.3,  # 較低溫度確保專業性
            "model": "gpt-4o-mini"
        }

        # 專家系統提示詞
        self.system_prompt = self._get_system_prompt()

    @abstractmethod
    def _get_system_prompt(self) -> str:
        """取得專家系統提示詞

        每個專家必須定義自己的系統提示詞
        """
        pass

    @abstractmethod
    async def _build_prompt(self,
                          query: str,
                          knowledge_results: List[Dict],
                          personal_context: Dict[str, Any],
                          user_profile: Dict[str, Any] = None) -> str:
        """構建專業提示詞 - 每個 Agent 需要實現

        Args:
            query: 使用者查詢
            knowledge_results: RAG 檢索結果
            personal_context: 從資料庫查詢的個人財務上下文
            user_profile: 使用者提供的個人資料 (age, risk_tolerance, etc.)
        """
        pass

    @abstractmethod
    async def _generate_fallback_response(self, prompt: str) -> str:
        """LLM 不可用時的降級回應 - 每個 Agent 需要實現"""
        pass

    async def process_message(self, message: AgentMessage) -> AgentMessage:
        """處理訊息的通用流程"""
        try:
            query = message.content.strip()

            # 提取對話歷史（如果有）
            conversation_history = message.metadata.get("conversation_history", [])

            # 提取使用者個人資料（從 API 傳入）
            user_profile = message.metadata.get("user_profile")

            # 1. RAG 檢索相關資訊
            knowledge_results = []
            if self.use_rag and self.knowledge_retriever:
                knowledge_results = await self._retrieve_knowledge(query, max_results=8)

            # 2. 查詢個人資料庫（如果需要）
            personal_context = await self._get_personal_context(query)

            # 3. 構建專業提示詞（傳入 user_profile）
            prompt = await self._build_prompt(query, knowledge_results, personal_context, user_profile)

            # 4. 使用 LLM 生成回應（傳入對話歷史）
            response_content = await self._generate_llm_response(prompt, conversation_history)

            # 5. 後處理回應
            final_content = self._post_process_response(response_content)

            # 6. 計算智能信心度
            confidence_metrics = await self._calculate_smart_confidence(
                query, final_content, knowledge_results, personal_context
            )
            confidence = confidence_metrics.overall_confidence if confidence_metrics else self._calculate_fallback_confidence(query, knowledge_results)

            # 7. 建立回應
            response = self.create_response(
                content=final_content,
                metadata={
                    "llm_model": self.llm_config["model"],
                    "knowledge_used": len(knowledge_results),
                    "personal_context_used": bool(personal_context),
                    "agent_type": self.agent_type.value,
                    "processing_time": datetime.now().isoformat(),
                    # 新增信心度詳細指標
                    "confidence_metrics": confidence_metrics.to_dict() if confidence_metrics and hasattr(confidence_metrics, 'to_dict') else {
                        "relevance_score": confidence_metrics.relevance_score if confidence_metrics else 0.0,
                        "response_quality": confidence_metrics.response_quality if confidence_metrics else 0.0,
                        "knowledge_coverage": confidence_metrics.knowledge_coverage if confidence_metrics else 0.0,
                        "domain_expertise": confidence_metrics.domain_expertise if confidence_metrics else 0.0
                    }
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
                metadata={"error_type": "processing_error"}
            )

    async def process_message_stream(self, message: AgentMessage):
        """處理訊息並流式輸出回應（真正的流式處理）

        這是真正的流式處理實作，直接從 LLM 逐塊輸出，
        讓使用者在 3-5 秒內看到第一個字，而不是等待 20 秒

        Yields:
            str: 逐塊生成的回應內容
        """
        try:
            query = message.content.strip()
            conversation_history = message.metadata.get("conversation_history", [])
            user_profile = message.metadata.get("user_profile")

            # 1. RAG 檢索相關資訊（快速，1-2秒）
            knowledge_results = []
            if self.use_rag and self.knowledge_retriever:
                knowledge_results = await self._retrieve_knowledge(query, max_results=8)
                # 儲存最後檢索的文件，供外部訪問
                self.last_retrieved_docs = knowledge_results

            # 2. 查詢個人資料庫（快速）
            personal_context = await self._get_personal_context(query)

            # 3. 構建專業提示詞（快速，傳入 user_profile）
            prompt = await self._build_prompt(query, knowledge_results, personal_context, user_profile)

            # 4. 流式生成回應（這裡開始流式輸出，3-5 秒內第一個 token）
            async for chunk in self._generate_llm_response_stream(prompt, conversation_history):
                yield chunk

        except Exception as e:
            self.logger.error(f"Error in stream processing in {self.name}: {e}")
            yield f"❌ 處理過程中發生錯誤：{str(e)}"

    @abstractmethod
    async def can_handle(self, query: str) -> float:
        """評估是否能處理特定查詢

        Args:
            query: 使用者查詢內容

        Returns:
            float: 處理能力評分 (0.0-1.0)
        """
        pass

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

    async def _generate_llm_response(
        self,
        prompt: str,
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        """使用 LLM 生成回應

        Args:
            prompt: 當前查詢的提示詞
            conversation_history: 對話歷史（OpenAI 格式）

        Linus 實用主義：直接使用 OpenAI messages 格式，無額外轉換
        """
        if not is_llm_configured():
            self.logger.warning("No LLM client available, using fallback response")
            return await self._generate_fallback_response(prompt)

        try:
            # 構建完整的 messages
            messages = []

            # 1. 添加系統提示
            messages.append({
                "role": "system",
                "content": self.system_prompt
            })

            # 2. 添加對話歷史（如果有）
            if conversation_history:
                messages.extend(conversation_history)
                self.logger.info(f"Using {len(conversation_history)} historical messages")

            # 3. 添加當前查詢
            messages.append({
                "role": "user",
                "content": prompt
            })

            # 使用 messages 格式呼叫 LLM
            self.logger.info(f"Calling LLM with {len(messages)} messages...")
            response = await generate_llm_response(
                messages=messages,
                **self.llm_config
            )
            self.logger.info(f"LLM response received: {len(response.content)} chars")
            return response.content

        except Exception as e:
            self.logger.error(f"LLM generation failed: {e}")
            return await self._generate_fallback_response(prompt)

    async def _generate_llm_response_stream(
        self,
        prompt: str,
        conversation_history: List[Dict[str, str]] = None
    ):
        """使用 LLM 生成流式回應（真正的流式處理）

        這個方法會直接從 OpenAI API 逐塊接收 token，
        讓使用者在 3-5 秒內看到第一個字，而不是等待完整回應

        Args:
            prompt: 當前查詢的提示詞
            conversation_history: 對話歷史（OpenAI 格式）

        Yields:
            str: 逐塊生成的內容
        """
        if not is_llm_configured():
            self.logger.warning("No LLM client available, using fallback response")
            fallback = await self._generate_fallback_response(prompt)
            # 模擬流式輸出降級回應
            chunk_size = 10
            for i in range(0, len(fallback), chunk_size):
                yield fallback[i:i+chunk_size]
            return

        try:
            # 構建完整的 messages（同普通模式）
            messages = []

            # 1. 添加系統提示
            messages.append({
                "role": "system",
                "content": self.system_prompt
            })

            # 2. 添加對話歷史（如果有）
            if conversation_history:
                messages.extend(conversation_history)
                self.logger.info(f"[Stream] Using {len(conversation_history)} historical messages")

            # 3. 添加當前查詢
            messages.append({
                "role": "user",
                "content": prompt
            })

            # 使用流式 API 呼叫 LLM
            self.logger.info(f"[Stream] Calling LLM stream with {len(messages)} messages...")

            # 導入 LLM manager 的流式方法
            from ..llm import llm_manager

            if not llm_manager or not llm_manager.default_client:
                raise Exception("LLM client not available")

            # 獲取默認客戶端
            client = llm_manager.clients.get(llm_manager.default_client)
            if not client:
                raise Exception(f"LLM client '{llm_manager.default_client}' not found")

            # 調用流式生成方法
            async for chunk in client.generate_response_stream(
                messages=messages,
                **self.llm_config
            ):
                yield chunk

            self.logger.info(f"[Stream] LLM stream completed")

        except Exception as e:
            self.logger.error(f"LLM stream generation failed: {e}")
            # 錯誤時輸出降級訊息
            fallback = await self._generate_fallback_response(prompt)
            yield fallback

    async def _retrieve_knowledge(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """檢索相關知識（如果啟用 RAG）

        Args:
            query: 查詢內容
            max_results: 最大結果數

        Returns:
            檢索結果清單
        """
        if not self.use_rag or not self.knowledge_retriever:
            return []

        try:
            # 根據代理人類型進行專業領域檢索
            domain_map = {
                AgentType.FINANCIAL_ANALYST: "financial_analysis",
                AgentType.FINANCIAL_PLANNER: "financial_planning",
                AgentType.LEGAL_EXPERT: "legal_compliance"
            }

            expert_domain = domain_map.get(self.agent_type, "general")

            # 僅限金融和理財專家使用 RAG
            if expert_domain in ["financial_analysis", "financial_planning"]:
                from ..rag.knowledge_retriever import ExpertDomain

                domain_enum_map = {
                    "financial_analysis": ExpertDomain.FINANCIAL_ANALYSIS,
                    "financial_planning": ExpertDomain.FINANCIAL_PLANNING
                }

                domain_enum = domain_enum_map.get(expert_domain, ExpertDomain.GENERAL)
                results = await self.knowledge_retriever.retrieve_for_expert(
                    query=query,
                    expert_domain=domain_enum,
                    max_results=max_results
                )

                # 信心度過濾：只保留相似度 >= 0.25 的結果（平衡設定）
                MIN_CONFIDENCE_THRESHOLD = 0.25
                filtered_results = [
                    result for result in results
                    if result.confidence >= MIN_CONFIDENCE_THRESHOLD
                ]

                if len(filtered_results) < len(results):
                    self.logger.info(
                        f"Filtered out {len(results) - len(filtered_results)} low-confidence results "
                        f"(threshold: {MIN_CONFIDENCE_THRESHOLD})"
                    )

                return [result.to_dict() for result in filtered_results]

        except Exception as e:
            self.logger.warning(f"知識檢索失敗: {e}")

        return []

    def _post_process_response(self, response: str) -> str:
        """後處理回應內容"""
        # 確保包含必要的風險警語
        if "風險" not in response and "投資" in response:
            response += "\n\n⚠️ **投資風險提醒**\n投資有風險，請謹慎評估個人財務狀況。過往績效不代表未來表現。"

        # 確保包含免責聲明
        if "僅供參考" not in response:
            response += "\n\n*本分析僅供參考，不構成投資建議。投資決策請自行判斷。*"

        return response

    async def _calculate_smart_confidence(
        self,
        query: str,
        response_content: str,
        knowledge_results: List[Dict],
        personal_context: Dict[str, Any]
    ) -> Optional[ConfidenceMetrics]:
        """使用智能信心度計算系統

        Linus 哲學：好品味的設計
        - 用智能演算法替代硬編碼規則
        - 基於多維度分析而非簡單加成
        """
        if not confidence_calculator:
            return None

        try:
            return await confidence_calculator.calculate_confidence(
                query=query,
                response_content=response_content,
                knowledge_results=knowledge_results,
                agent_type=self.agent_type.value,
                personal_context=personal_context
            )
        except Exception as e:
            self.logger.warning(f"Smart confidence calculation failed: {e}")
            return None

    def _calculate_fallback_confidence(self, query: str, knowledge_results: List[Dict]) -> float:
        """降級信心度計算（原有邏輯的改進版）

        當智能計算失敗時使用，但仍比原版更精確
        """
        # 基礎分數：根據是否有知識檢索
        if knowledge_results:
            base_confidence = 0.5 + (min(len(knowledge_results), 5) * 0.08)  # 0.5-0.9
        else:
            base_confidence = 0.4  # 無知識檢索降低基礎分數

        # 查詢複雜度調整（比原版更精確）
        query_complexity = min(len(query.split()), 10) / 10  # 詞數複雜度
        base_confidence += query_complexity * 0.1

        # LLM 可用性加成
        if is_llm_configured():
            base_confidence += 0.1
        else:
            base_confidence *= 0.8  # 無 LLM 時大幅降低

        return min(0.9, max(0.2, base_confidence))  # 擴大範圍到 0.2-0.9

    def _extract_sources(self, knowledge_results: List[Dict]) -> List[str]:
        """提取資料來源"""
        sources = []
        for result in knowledge_results:
            source = result.get("source")
            if source and source not in sources:
                sources.append(source)
        return sources

    def _format_knowledge_context(self, knowledge_results: List[Dict[str, Any]]) -> str:
        """格式化知識檢索結果為上下文

        Args:
            knowledge_results: 知識檢索結果

        Returns:
            格式化後的上下文文字
        """
        if not knowledge_results:
            return ""

        context_parts = ["相關知識參考："]

        for i, result in enumerate(knowledge_results, 1):
            content = result.get("content", "").strip()
            source = result.get("source", "未知來源")
            confidence = result.get("confidence", 0)

            context_parts.append(
                f"\n{i}. 來源：{source} (信心度: {confidence:.1%})\n"
                f"   內容：{content[:300]}{'...' if len(content) > 300 else ''}"
            )

        return "\n".join(context_parts)

    def create_response(
        self,
        content: str,
        message_type: MessageType = MessageType.RESPONSE,
        metadata: Optional[Dict[str, Any]] = None,
        sources: Optional[List[str]] = None,
        confidence: Optional[float] = None
    ) -> AgentMessage:
        """建立回應訊息的便利方法

        Linus 哲學：好品味的便利方法，減少重複代碼
        """
        return AgentMessage(
            agent_type=self.agent_type,
            message_type=message_type,
            content=content,
            metadata=metadata,
            sources=sources,
            confidence=confidence
        )

    def create_error_response(
        self,
        error_message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentMessage:
        """建立錯誤回應"""
        return self.create_response(
            content=error_message,
            message_type=MessageType.ERROR,
            metadata=metadata,
            confidence=0.0
        )

    def log_interaction(self, input_message: AgentMessage, output_message: AgentMessage):
        """記錄代理人互動（用於審計追蹤）"""
        self.logger.info(
            f"Agent {self.name} processed message: "
            f"input_type={input_message.message_type.value}, "
            f"output_confidence={output_message.confidence}, "
            f"sources={len(output_message.sources or [])}"
        )

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

    def __str__(self) -> str:
        return f"{self.name}({self.agent_type.value})"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.name}>"