"""
StateManager - LangGraph 狀態管理

實作 Linus 哲學：
1. 好品味：簡潔的狀態結構，避免冗餘欄位
2. 資料結構優先：狀態是工作流程的核心，設計要清晰
3. Never break userspace：狀態格式穩定，向後兼容
4. 簡潔執念：狀態轉換邏輯清晰，無複雜條件
"""

from typing import Dict, Any, List, Optional, TypedDict, Annotated
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """工作流程狀態枚舉"""
    PENDING = "pending"           # 等待開始
    ROUTING = "routing"           # 路由分析中
    PROCESSING = "processing"     # 專家處理中
    COORDINATING = "coordinating" # 協調整合中
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"            # 執行失敗


class FinanceState(TypedDict):
    """理財諮詢工作流程狀態

    Linus 哲學：好品味的資料結構
    - 所有必要資訊集中在一個地方
    - 欄位命名清晰，無歧義
    - 型別明確，便於靜態檢查
    """
    # 基本資訊
    session_id: str
    user_query: str
    timestamp: str
    status: str

    # 路由資訊
    required_experts: List[str]
    routing_confidence: float
    routing_metadata: Dict[str, Any]

    # 專家回應
    expert_responses: Dict[str, Dict[str, Any]]
    expert_sources: Dict[str, List[str]]

    # 最終結果
    final_response: Optional[str]
    confidence_score: Optional[float]
    response_sources: Optional[List[str]]

    # 執行資訊
    execution_log: List[Dict[str, Any]]
    error_messages: List[str]

    # 使用者資料（可選）
    user_profile: Optional[Dict[str, Any]]
    user_financial_data: Optional[Dict[str, Any]]


class StateManager:
    """狀態管理器

    負責管理 LangGraph 工作流程的狀態轉換
    """

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.StateManager")

    def create_initial_state(
        self,
        session_id: str,
        user_query: str,
        user_profile: Optional[Dict[str, Any]] = None
    ) -> FinanceState:
        """建立初始狀態

        Linus 哲學：簡潔的初始化，所有預設值明確
        """
        return FinanceState(
            session_id=session_id,
            user_query=user_query,
            timestamp=datetime.now().isoformat(),
            status=WorkflowStatus.PENDING.value,

            required_experts=[],
            routing_confidence=0.0,
            routing_metadata={},

            expert_responses={},
            expert_sources={},

            final_response=None,
            confidence_score=None,
            response_sources=None,

            execution_log=[],
            error_messages=[],

            user_profile=user_profile,
            user_financial_data=None
        )

    def update_routing_info(
        self,
        state: FinanceState,
        required_experts: List[str],
        confidence: float,
        metadata: Dict[str, Any]
    ) -> FinanceState:
        """更新路由資訊"""
        state["required_experts"] = required_experts
        state["routing_confidence"] = confidence
        state["routing_metadata"] = metadata
        state["status"] = WorkflowStatus.ROUTING.value

        # 記錄執行日誌
        self._add_execution_log(state, "routing", {
            "experts_count": len(required_experts),
            "confidence": confidence,
            "experts": required_experts
        })

        return state

    def add_expert_response(
        self,
        state: FinanceState,
        expert_type: str,
        response_content: str,
        metadata: Dict[str, Any],
        sources: List[str],
        confidence: float
    ) -> FinanceState:
        """添加專家回應

        Linus 哲學：避免特殊情況
        - 統一的專家回應格式
        - 無論什麼專家都用相同的資料結構
        """
        state["expert_responses"][expert_type] = {
            "content": response_content,
            "metadata": metadata,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat()
        }

        state["expert_sources"][expert_type] = sources
        state["status"] = WorkflowStatus.PROCESSING.value

        # 記錄執行日誌
        self._add_execution_log(state, "expert_response", {
            "expert_type": expert_type,
            "confidence": confidence,
            "sources_count": len(sources)
        })

        return state

    def set_final_response(
        self,
        state: FinanceState,
        final_response: str,
        confidence_score: float,
        sources: List[str]
    ) -> FinanceState:
        """設定最終回應"""
        state["final_response"] = final_response
        state["confidence_score"] = confidence_score
        state["response_sources"] = sources
        state["status"] = WorkflowStatus.COMPLETED.value

        # 記錄執行日誌
        self._add_execution_log(state, "final_response", {
            "confidence": confidence_score,
            "sources_count": len(sources),
            "response_length": len(final_response)
        })

        return state

    def add_error(self, state: FinanceState, error_message: str) -> FinanceState:
        """添加錯誤訊息"""
        state["error_messages"].append(error_message)
        if state["status"] != WorkflowStatus.FAILED.value:
            state["status"] = WorkflowStatus.FAILED.value

        # 記錄執行日誌
        self._add_execution_log(state, "error", {
            "error_message": error_message,
            "total_errors": len(state["error_messages"])
        })

        return state

    def is_routing_complete(self, state: FinanceState) -> bool:
        """檢查路由是否完成"""
        return (
            len(state["required_experts"]) > 0 and
            state["routing_confidence"] > 0.0
        )

    def are_all_experts_responded(self, state: FinanceState) -> bool:
        """檢查所有專家是否都已回應"""
        required_experts = set(state["required_experts"])
        responded_experts = set(state["expert_responses"].keys())
        return required_experts.issubset(responded_experts)

    def get_pending_experts(self, state: FinanceState) -> List[str]:
        """取得尚未回應的專家清單"""
        required_experts = set(state["required_experts"])
        responded_experts = set(state["expert_responses"].keys())
        return list(required_experts - responded_experts)

    def calculate_overall_confidence(self, state: FinanceState) -> float:
        """計算整體信心度

        Linus 哲學：簡單的演算法勝過複雜的理論
        - 基於路由信心度和專家信心度的加權平均
        - 避免複雜的數學公式
        """
        if not state["expert_responses"]:
            return state["routing_confidence"]

        expert_confidences = [
            resp["confidence"]
            for resp in state["expert_responses"].values()
        ]

        if not expert_confidences:
            return state["routing_confidence"]

        # 簡單平均，路由信心度權重 20%，專家信心度權重 80%
        routing_weight = 0.2
        expert_weight = 0.8

        avg_expert_confidence = sum(expert_confidences) / len(expert_confidences)
        overall_confidence = (
            routing_weight * state["routing_confidence"] +
            expert_weight * avg_expert_confidence
        )

        return min(1.0, max(0.0, overall_confidence))

    def _add_execution_log(
        self,
        state: FinanceState,
        action: str,
        details: Dict[str, Any]
    ) -> None:
        """添加執行日誌"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details
        }
        state["execution_log"].append(log_entry)

    def update_session_state(self, session_id: str, state: FinanceState) -> None:
        """更新會話狀態（用於持久化存儲）

        Linus 哲學：簡潔的狀態管理
        - 當前為內存存儲，未來可擴展為資料庫
        - 統一的狀態更新介面
        """
        # 記錄狀態更新日誌
        self.logger.info(f"Session {session_id} state updated: status={state['status']}")

        # 在實際生產環境中，這裡可以：
        # 1. 存儲到資料庫
        # 2. 發送狀態更新事件
        # 3. 更新緩存
        # 目前僅記錄日誌
        pass

    def get_state_summary(self, state: FinanceState) -> Dict[str, Any]:
        """取得狀態摘要（用於監控和除錯）"""
        return {
            "session_id": state["session_id"],
            "status": state["status"],
            "required_experts": state["required_experts"],
            "responded_experts": list(state["expert_responses"].keys()),
            "overall_confidence": self.calculate_overall_confidence(state),
            "has_final_response": state["final_response"] is not None,
            "error_count": len(state["error_messages"]),
            "execution_steps": len(state["execution_log"])
        }