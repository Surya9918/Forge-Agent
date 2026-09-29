"""
Antigravity LLM provider for ForgeAgent.
This provider uses the native Antigravity Gemini integration
instead of requiring external API keys.
"""

import json
from typing import List, Type, Any
from pydantic import BaseModel
from forgeagent.llm.base import LLMProvider, ChatMessage, LLMResponse, T
from forgeagent.observability.logger import get_logger

logger = get_logger("forgeagent.llm.antigravity")


class AntigravityProvider(LLMProvider):
    def __init__(self, model: str = "gemini-2.0-flash", **kwargs):
        super().__init__(model=model, **kwargs)
        # Initialize the Antigravity SDK client
        import google_antigravity as agy
        self.client = agy.Client()

    def generate(self, messages: List[ChatMessage], **kwargs) -> LLMResponse:
        logger.info(f"Generating content using Antigravity native Gemini: {self.model}")
        
        try:
            # Format messages for Antigravity SDK
            agy_messages = [{"role": m.role, "content": m.content} for m in messages]
            
            # Call native platform LLM
            response = self.client.llm.generate(
                model=self.model,
                messages=agy_messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            
            # Update usage
            self.total_prompt_tokens += response.usage.prompt_tokens
            self.total_completion_tokens += response.usage.completion_tokens
            
            return LLMResponse(
                content=response.text,
                tokens_prompt=response.usage.prompt_tokens,
                tokens_completion=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
                model=self.model
            )
        except Exception as e:
            logger.error(f"Antigravity generation failed: {e}")
            raise

    def generate_structured(self, messages: List[ChatMessage], schema: Type[T], **kwargs) -> T:
        logger.info(f"Generating structured content using Antigravity native Gemini: {self.model}")
        
        try:
            agy_messages = [{"role": m.role, "content": m.content} for m in messages]
            response = self.client.llm.generate_structured(
                model=self.model,
                messages=agy_messages,
                response_schema=schema.model_json_schema(),
                temperature=self.temperature,
            )
            return schema.model_validate_json(response.text)
        except Exception as e:
            logger.error(f"Antigravity structured generation failed: {e}")
            raise
