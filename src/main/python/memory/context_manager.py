"""
上下文管理器

職責：
1. Token 計算
2. 滑動窗口管理
3. 自動摘要（未來擴展）

Linus 簡潔：現在用最簡單的策略，未來再優化
"""

from typing import List
import logging

logger = logging.getLogger(__name__)


class ContextManager:
    """上下文管理器

    Linus 簡潔：現在用最簡單的策略，未來再優化
    """

    def __init__(
        self,
        max_tokens: int = 4000,
        enable_summarization: bool = False,
        model: str = "gpt-4"
    ):
        self.max_tokens = max_tokens
        self.enable_summarization = enable_summarization
        self.model = model

        # Token 編碼器（延遲載入）
        self._encoding = None

    @property
    def encoding(self):
        """延遲載入 tiktoken 編碼器"""
        if self._encoding is None:
            try:
                import tiktoken
                try:
                    self._encoding = tiktoken.encoding_for_model(self.model)
                except:
                    self._encoding = tiktoken.get_encoding("cl100k_base")
            except ImportError:
                logger.warning("tiktoken not installed, using approximate token counting")
                self._encoding = None
        return self._encoding

    def count_tokens(self, text: str) -> int:
        """計算文本的 token 數

        如果 tiktoken 不可用，使用近似計算（英文 ~4 字元 = 1 token）
        """
        if self.encoding:
            return len(self.encoding.encode(text))
        else:
            # 近似計算：中文 ~1.5 字 = 1 token，英文 ~4 字元 = 1 token
            # 簡化為總字元數 / 3
            return len(text) // 3

    def count_messages_tokens(
        self,
        messages: List['ConversationMessage']  # type: ignore
    ) -> int:
        """計算訊息列表的總 token 數"""
        total = 0
        for msg in messages:
            # OpenAI 計算方式：role + content + 格式 overhead
            total += self.count_tokens(msg.content)
            total += 4  # role + formatting overhead
        return total

    def get_managed_context(
        self,
        messages: List['ConversationMessage']  # type: ignore
    ) -> List['ConversationMessage']:  # type: ignore
        """獲取管理後的上下文

        Linus 簡潔：現在用最簡單的截斷策略
        未來可以加入：
        1. 智能摘要
        2. 重要訊息保留
        3. 語意壓縮
        """
        if not messages:
            return []

        total_tokens = self.count_messages_tokens(messages)

        # 如果未超過限制，直接返回
        if total_tokens <= self.max_tokens:
            return messages

        # 超過限制：從後往前保留訊息
        logger.warning(
            f"Context exceeded {self.max_tokens} tokens ({total_tokens}), "
            f"truncating..."
        )

        result = []
        current_tokens = 0

        # 從最新的訊息開始保留
        for msg in reversed(messages):
            msg_tokens = self.count_tokens(msg.content) + 4
            if current_tokens + msg_tokens > self.max_tokens:
                break
            result.insert(0, msg)
            current_tokens += msg_tokens

        logger.info(f"Kept {len(result)}/{len(messages)} messages ({current_tokens} tokens)")
        return result