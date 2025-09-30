"""
對話記憶管理器

Linus 哲學：
1. 簡潔執念：清晰的 API，無複雜邏輯
2. 資料結構優先：訊息列表是核心
3. Never break userspace：穩定的介面
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from .message_models import ConversationMessage, MessageRole
from .context_manager import ContextManager

logger = logging.getLogger(__name__)


class ConversationMemory:
    """對話記憶管理器

    職責：
    1. 儲存對話歷史（內存）
    2. 提供歷史查詢
    3. 格式化給 LLM 使用
    4. 自動管理記憶容量
    """

    def __init__(
        self,
        session_id: str,
        max_turns: int = 10,              # 最多保留 N 輪對話
        max_context_tokens: int = 4000,   # 最大上下文 tokens
        enable_summarization: bool = False # 啟用自動摘要（未來擴展）
    ):
        self.session_id = session_id
        self.max_turns = max_turns
        self.max_context_tokens = max_context_tokens
        self.enable_summarization = enable_summarization

        # 核心資料結構：訊息列表
        self.messages: List[ConversationMessage] = []

        # 上下文管理器
        self.context_manager = ContextManager(
            max_tokens=max_context_tokens,
            enable_summarization=enable_summarization
        )

        # 統計資訊
        self.total_turns = 0
        self.created_at = datetime.now()
        self.last_activity = datetime.now()

    def add_message(
        self,
        role: MessageRole,
        content: str,
        **kwargs
    ) -> None:
        """添加訊息到歷史

        Linus 簡潔：統一的添加介面，無特殊情況
        """
        message = ConversationMessage(
            role=role,
            content=content,
            **kwargs
        )

        self.messages.append(message)
        self.last_activity = datetime.now()

        # 一輪對話 = 一個 user + 一個 assistant
        if role == MessageRole.ASSISTANT:
            self.total_turns += 1

        # 自動管理容量
        self._manage_capacity()

        logger.debug(f"Added message: role={role.value}, length={len(content)}")

    def get_recent_messages(
        self,
        n_turns: Optional[int] = None
    ) -> List[ConversationMessage]:
        """獲取最近 N 輪對話

        Args:
            n_turns: 輪數，None = 全部

        Returns:
            訊息列表（由舊到新）
        """
        if n_turns is None:
            return self.messages.copy()

        # 一輪 = user + assistant，所以 * 2
        n_messages = n_turns * 2
        return self.messages[-n_messages:] if len(self.messages) > n_messages else self.messages.copy()

    def get_context_for_llm(
        self,
        include_system_prompt: bool = True,
        system_prompt: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """格式化歷史給 LLM 使用

        Linus 實用主義：直接返回 OpenAI 格式

        Returns:
            OpenAI messages 格式列表
        """
        messages = []

        # 添加系統提示
        if include_system_prompt:
            prompt = system_prompt or self._get_default_system_prompt()
            messages.append({
                "role": "system",
                "content": prompt
            })

        # 添加對話歷史
        recent_messages = self.context_manager.get_managed_context(
            self.messages
        )

        for msg in recent_messages:
            messages.append(msg.to_openai_format())

        return messages

    def get_history_summary(self) -> str:
        """獲取對話歷史摘要（用於顯示/日誌）"""
        if not self.messages:
            return "無對話歷史"

        user_messages = [m for m in self.messages if m.role == MessageRole.USER]
        assistant_messages = [m for m in self.messages if m.role == MessageRole.ASSISTANT]

        return (
            f"會話 {self.session_id}:\n"
            f"- 總輪數: {self.total_turns}\n"
            f"- 使用者訊息: {len(user_messages)}\n"
            f"- AI 回應: {len(assistant_messages)}\n"
            f"- 建立時間: {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"- 最後活動: {self.last_activity.strftime('%Y-%m-%d %H:%M:%S')}"
        )

    def clear(self) -> None:
        """清除所有歷史"""
        self.messages.clear()
        self.total_turns = 0
        logger.info(f"Session {self.session_id} memory cleared")

    def _manage_capacity(self) -> None:
        """管理記憶容量

        Linus 簡潔：簡單的策略勝過複雜的演算法
        - 超過 max_turns：刪除最舊的一輪
        - 超過 token 限制：觸發摘要（如果啟用）
        """
        # 策略 1：限制輪數
        if self.total_turns > self.max_turns:
            # 刪除最舊的一輪（user + assistant）
            self._remove_oldest_turn()

        # 策略 2：Token 限制（由 ContextManager 處理）
        # 在 get_context_for_llm() 時自動處理

    def _remove_oldest_turn(self) -> None:
        """刪除最舊的一輪對話"""
        if len(self.messages) >= 2:
            # 假設第一條是 user，第二條是 assistant
            removed = self.messages[:2]
            self.messages = self.messages[2:]
            logger.debug(f"Removed oldest turn: {len(removed)} messages")

    def _get_default_system_prompt(self) -> str:
        """預設系統提示"""
        return (
            "你是一個專業的理財諮詢助手，擅長投資建議、市場分析和法規諮詢。"
            "請根據使用者的問題和對話歷史，提供專業、個人化的建議。"
        )

    def to_dict(self) -> Dict[str, Any]:
        """序列化（用於儲存到資料庫）"""
        return {
            "session_id": self.session_id,
            "messages": [msg.to_dict() for msg in self.messages],
            "total_turns": self.total_turns,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationMemory':
        """反序列化"""
        memory = cls(session_id=data["session_id"])
        memory.messages = [
            ConversationMessage.from_dict(msg_data)
            for msg_data in data["messages"]
        ]
        memory.total_turns = data["total_turns"]
        memory.created_at = datetime.fromisoformat(data["created_at"])
        memory.last_activity = datetime.fromisoformat(data["last_activity"])
        return memory