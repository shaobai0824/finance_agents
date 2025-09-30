"""
Memory Module - 對話記憶管理

實作 Linus 哲學：
1. 簡潔的資料結構 - 統一的訊息格式
2. 實用主義 - 直接對接 OpenAI API
3. Never break userspace - 向後兼容的設計
"""

from .message_models import ConversationMessage, MessageRole
from .context_manager import ContextManager
from .conversation_memory import ConversationMemory

__all__ = [
    "ConversationMessage",
    "MessageRole",
    "ContextManager",
    "ConversationMemory",
]