"""
訊息資料模型

Linus 哲學：簡潔的資料結構，所有訊息統一格式
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class MessageRole(Enum):
    """訊息角色"""
    SYSTEM = "system"      # 系統提示
    USER = "user"          # 使用者輸入
    ASSISTANT = "assistant" # AI 回應


@dataclass
class ConversationMessage:
    """對話訊息

    Linus 好品味：
    - 所有必要資訊集中在一個結構
    - 可直接轉換為 OpenAI message 格式
    - 無冗餘欄位
    """
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)

    # 可選的元數據
    metadata: Dict[str, Any] = field(default_factory=dict)

    # AI 回應特有欄位
    expert_type: Optional[str] = None
    confidence: Optional[float] = None
    sources: List[str] = field(default_factory=list)

    def to_openai_format(self) -> Dict[str, str]:
        """轉換為 OpenAI API 格式

        Linus 實用主義：直接對接 OpenAI，無額外轉換
        """
        return {
            "role": self.role.value,
            "content": self.content
        }

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式 (用於儲存)"""
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "expert_type": self.expert_type,
            "confidence": self.confidence,
            "sources": self.sources
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationMessage':
        """從字典建立訊息"""
        return cls(
            role=MessageRole(data["role"]),
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
            expert_type=data.get("expert_type"),
            confidence=data.get("confidence"),
            sources=data.get("sources", [])
        )