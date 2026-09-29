"""
Base abstraction for LLM providers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Type, TypeVar
from pydantic import BaseModel, Field


class MessageRole(str):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ChatMessage(BaseModel):
    role: str
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None


class LLMResponse(BaseModel):
    content: str
    raw: Any = None
    tokens_prompt: int = 0
    tokens_completion: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    model: str = ""
    finish_reason: str = "stop"


T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    def __init__(self, model: str, temperature: float = 0.2, max_tokens: int = 8192, timeout: int = 60):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0

    @abstractmethod
    def generate(self, messages: List[ChatMessage], **kwargs) -> LLMResponse:
        """Synchronously generate text response."""
        pass

    @abstractmethod
    def generate_structured(self, messages: List[ChatMessage], schema: Type[T], **kwargs) -> T:
        """Generate validated Pydantic model response."""
        pass

    def get_token_usage(self) -> Dict[str, int]:
        return {
            "prompt_tokens": self.total_prompt_tokens,
            "completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_prompt_tokens + self.total_completion_tokens,
        }
