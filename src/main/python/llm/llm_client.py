"""
LLM 客戶端模組
支援 OpenAI GPT 和 Anthropic Claude 模型
"""

import os
import asyncio
from typing import Dict, Any, List, Optional, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass
import logging

# 條件匯入 - 如果沒安裝套件不會報錯
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

@dataclass
class LLMResponse:
    """LLM 回應資料結構"""
    content: str
    model: str
    usage: Dict[str, Any]
    finish_reason: str
    response_time: float

class BaseLLMClient(ABC):
    """LLM 客戶端基類"""

    @abstractmethod
    async def generate_response(self, prompt: str, **kwargs) -> LLMResponse:
        """生成回應"""
        pass

class OpenAIClient(BaseLLMClient):
    """OpenAI GPT 客戶端"""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not installed. Run: pip install openai")

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided")

        self.model = model
        self.client = openai.AsyncOpenAI(api_key=self.api_key)
        self.logger = logging.getLogger(__name__)

    async def generate_response(self, prompt: str = None, messages: List[Dict[str, str]] = None, **kwargs) -> LLMResponse:
        """生成 OpenAI 回應

        支援兩種調用方式：
        1. 簡單模式：generate_response(prompt="your query")
        2. 對話模式：generate_response(messages=[...])

        Linus 實用主義：向後兼容，不破壞現有代碼
        """
        import time
        start_time = time.time()

        try:
            # 避免參數重複：從 kwargs 中移除已處理的參數
            api_kwargs = kwargs.copy()
            max_tokens = api_kwargs.pop("max_tokens", 1000)
            temperature = api_kwargs.pop("temperature", 0.7)
            # 移除 model 參數以避免重複（使用實例初始化時的 model）
            api_kwargs.pop("model", None)

            # 決定使用哪種模式
            if messages:
                # 對話模式：使用完整的 messages 列表
                chat_messages = messages
            elif prompt:
                # 簡單模式：將 prompt 轉換為單個 user message
                chat_messages = [{"role": "user", "content": prompt}]
            else:
                raise ValueError("Either 'prompt' or 'messages' must be provided")

            self.logger.info(f"Calling OpenAI API with model={self.model}, messages={len(chat_messages)}, max_tokens={max_tokens}")
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=chat_messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **api_kwargs
            )

            response_time = time.time() - start_time
            self.logger.info(f"OpenAI API returned in {response_time:.2f}s")

            return LLMResponse(
                content=response.choices[0].message.content,
                model=response.model,
                usage=response.usage.dict() if response.usage else {},
                finish_reason=response.choices[0].finish_reason,
                response_time=response_time
            )

        except Exception as e:
            self.logger.error(f"OpenAI API error: {e}")
            import traceback
            traceback.print_exc()
            raise

class AnthropicClient(BaseLLMClient):
    """Anthropic Claude 客戶端"""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-sonnet-20240229"):
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("Anthropic library not installed. Run: pip install anthropic")

        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key not provided")

        self.model = model
        self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
        self.logger = logging.getLogger(__name__)

    async def generate_response(self, prompt: str, **kwargs) -> LLMResponse:
        """生成 Anthropic 回應"""
        import time
        start_time = time.time()

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=kwargs.get("max_tokens", 1000),
                temperature=kwargs.get("temperature", 0.7),
                messages=[{"role": "user", "content": prompt}]
            )

            response_time = time.time() - start_time

            return LLMResponse(
                content=response.content[0].text,
                model=response.model,
                usage=response.usage.dict() if hasattr(response, 'usage') else {},
                finish_reason=response.stop_reason or "stop",
                response_time=response_time
            )

        except Exception as e:
            self.logger.error(f"Anthropic API error: {e}")
            raise

class MockLLMClient(BaseLLMClient):
    """模擬 LLM 客戶端（用於測試和開發）"""

    def __init__(self, model: str = "mock-llm"):
        self.model = model
        self.logger = logging.getLogger(__name__)

    async def generate_response(self, prompt: str, **kwargs) -> LLMResponse:
        """生成模擬回應"""
        import time
        import asyncio

        start_time = time.time()

        # 模擬 API 延遲
        await asyncio.sleep(0.5)

        # 根據 prompt 關鍵字生成不同回應
        if "投資" in prompt or "股票" in prompt:
            content = "基於您的查詢，我建議採用分散投資策略，並定期檢視投資組合。請注意投資有風險，需謹慎評估。"
        elif "理財" in prompt:
            content = "理財規劃應該根據個人風險承受度和財務目標制定。建議先建立緊急基金，再考慮投資。"
        else:
            content = "感謝您的查詢。基於可用資訊，我提供以上分析供您參考。投資決策請謹慎考量。"

        response_time = time.time() - start_time

        return LLMResponse(
            content=content,
            model=self.model,
            usage={"prompt_tokens": len(prompt), "completion_tokens": len(content)},
            finish_reason="stop",
            response_time=response_time
        )

class LLMManager:
    """LLM 管理器 - 統一管理不同的 LLM 客戶端"""

    def __init__(self):
        self.clients: Dict[str, BaseLLMClient] = {}
        self.default_client = None
        self.logger = logging.getLogger(__name__)

        # 自動初始化可用的客戶端
        self._initialize_clients()

    def _initialize_clients(self):
        """初始化可用的 LLM 客戶端"""

        # 嘗試初始化 OpenAI
        try:
            if os.getenv("OPENAI_API_KEY"):
                self.clients["openai"] = OpenAIClient()
                if not self.default_client:
                    self.default_client = "openai"
                self.logger.info("OpenAI client initialized")
        except Exception as e:
            self.logger.warning(f"Failed to initialize OpenAI client: {e}")

        # 嘗試初始化 Anthropic
        try:
            if os.getenv("ANTHROPIC_API_KEY"):
                self.clients["anthropic"] = AnthropicClient()
                if not self.default_client:
                    self.default_client = "anthropic"
                self.logger.info("Anthropic client initialized")
        except Exception as e:
            self.logger.warning(f"Failed to initialize Anthropic client: {e}")

        # 如果沒有真實 LLM，使用模擬客戶端
        if not self.clients:
            self.clients["mock"] = MockLLMClient()
            self.default_client = "mock"
            self.logger.info("Using mock LLM client (no API keys provided)")

    async def generate_response(self,
                              prompt: str = None,
                              messages: List[Dict[str, str]] = None,
                              client_name: Optional[str] = None,
                              **kwargs) -> LLMResponse:
        """生成回應

        支援兩種模式：
        1. prompt 模式：generate_response(prompt="...")
        2. messages 模式：generate_response(messages=[...])
        """
        client_name = client_name or self.default_client

        if client_name not in self.clients:
            raise ValueError(f"LLM client '{client_name}' not available")

        return await self.clients[client_name].generate_response(prompt=prompt, messages=messages, **kwargs)

    def get_available_clients(self) -> List[str]:
        """取得可用的客戶端清單"""
        return list(self.clients.keys())

    def is_real_llm_available(self) -> bool:
        """檢查是否有真實的 LLM 可用"""
        return any(name != "mock" for name in self.clients.keys())

# 全域 LLM 管理器實例
llm_manager = LLMManager()

# 便利函數
async def generate_llm_response(prompt: str = None, messages: List[Dict[str, str]] = None, **kwargs) -> LLMResponse:
    """便利函數 - 生成 LLM 回應

    支援兩種模式：
    1. generate_llm_response(prompt="query")
    2. generate_llm_response(messages=[...])
    """
    return await llm_manager.generate_response(prompt=prompt, messages=messages, **kwargs)

def is_llm_configured() -> bool:
    """檢查是否已配置 LLM（包括 Mock LLM）"""
    return len(llm_manager.clients) > 0

def is_real_llm_configured() -> bool:
    """檢查是否已配置真實的 LLM（不包括 Mock）"""
    return llm_manager.is_real_llm_available()