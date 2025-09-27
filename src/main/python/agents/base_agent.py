"""
BaseAgent - 所有代理人的基礎類別

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
    """所有理財代理人的基礎類別

    實作 Linus 的三個核心原則：
    1. 好品味：統一的代理人介面，無特殊情況
    2. Never break userspace：穩定的 API 契約
    3. 簡潔執念：每個代理人專注單一職責
    """

    def __init__(self, agent_type: AgentType, name: str, use_rag: bool = True, knowledge_retriever=None):
        """初始化代理人

        Args:
            agent_type: 代理人類型
            name: 代理人名稱
            use_rag: 是否使用 RAG 系統
            knowledge_retriever: 知識檢索器（可選）
        """
        self.agent_type = agent_type
        self.name = name
        self.use_rag = use_rag
        self.knowledge_retriever = knowledge_retriever
        self.logger = logging.getLogger(f"{__name__}.{name}")

        # 專家系統提示詞
        self.system_prompt = self._get_system_prompt()

    @abstractmethod
    def _get_system_prompt(self) -> str:
        """取得專家系統提示詞

        每個專家必須定義自己的系統提示詞
        """
        if self.agent_type == AgentType.FINANCIAL_ANALYST:
            return "你是一個金融分析師，負責分析金融市場的走勢和趨勢。"
        elif self.agent_type == AgentType.FINANCIAL_PLANNER:
            return "你是一個金融規劃師，負責規劃金融市場的投資策略。"
        elif self.agent_type == AgentType.LEGAL_EXPERT:
            return "你是一個法律專家，負責分析法律問題和提供法律建議。"
        elif self.agent_type == AgentType.MANAGER:
            return "你是一個管理代理人，負責協調其他專家和回答問題。"
       

    @abstractmethod
    async def process_message(self, message: AgentMessage) -> AgentMessage:
        """處理接收到的訊息

        Args:
            message: 接收到的訊息

        Returns:
            AgentMessage: 處理後的回應訊息

        Raises:
            ValueError: 當訊息格式不正確時
        """
        pass

    @abstractmethod
    async def can_handle(self, query: str) -> float:
        """評估是否能處理特定查詢

        Args:
            query: 使用者查詢內容

        Returns:
            float: 處理能力評分 (0.0-1.0)
        """
        pass

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

                return [result.to_dict() for result in results]

        except Exception as e:
            self.logger.warning(f"知識檢索失敗: {e}")

        return []

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

    def log_interaction(self, input_message: AgentMessage, output_message: AgentMessage):
        """記錄代理人互動（用於審計追蹤）"""
        self.logger.info(
            f"Agent {self.name} processed message: "
            f"input_type={input_message.message_type.value}, "
            f"output_confidence={output_message.confidence}, "
            f"sources={len(output_message.sources or [])}"
        )

    def __str__(self) -> str:
        return f"{self.name}({self.agent_type.value})"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.name}>"