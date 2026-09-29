"""
Anthropic Claude provider for ForgeAgent.
"""

import os
import json
import requests
from typing import List, Type, Optional
from forgeagent.llm.base import LLMProvider, ChatMessage, LLMResponse, T


class AnthropicProvider(LLMProvider):
    def __init__(self, model: str = "claude-3-5-sonnet-20241022", api_key: Optional[str] = None, **kwargs):
        super().__init__(model=model, **kwargs)
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")

    def generate(self, messages: List[ChatMessage], **kwargs) -> LLMResponse:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        system_msg = ""
        user_messages = []
        for m in messages:
            if m.role == "system":
                system_msg += m.content + "\n"
            else:
                user_messages.append({"role": m.role, "content": m.content})

        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": user_messages,
        }
        if system_msg.strip():
            payload["system"] = system_msg.strip()

        resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()

        text = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                text += block.get("text", "")

        usage = data.get("usage", {})
        prompt_tokens = usage.get("input_tokens", 0)
        completion_tokens = usage.get("output_tokens", 0)

        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens

        return LLMResponse(
            content=text,
            tokens_prompt=prompt_tokens,
            tokens_completion=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            model=self.model,
        )

    def generate_structured(self, messages: List[ChatMessage], schema: Type[T], **kwargs) -> T:
        prompt_schema = f"\nOutput ONLY valid JSON matching this schema:\n{json.dumps(schema.model_json_schema())}"
        msgs = list(messages)
        msgs[-1] = ChatMessage(role=msgs[-1].role, content=msgs[-1].content + prompt_schema)
        resp = self.generate(msgs, **kwargs)
        text = resp.content.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return schema.model_validate_json(text.strip())
