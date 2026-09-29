"""
OpenAI & OpenAI-compatible provider for ForgeAgent.
"""

import os
import json
import requests
from typing import List, Type, Optional
from forgeagent.llm.base import LLMProvider, ChatMessage, LLMResponse, T


class OpenAIProvider(LLMProvider):
    def __init__(self, model: str = "gpt-4o", api_key: Optional[str] = None, base_url: Optional[str] = None, **kwargs):
        super().__init__(model=model, **kwargs)
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.base_url = base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")

    def generate(self, messages: List[ChatMessage], **kwargs) -> LLMResponse:
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()

        choice = data["choices"][0]
        content = choice["message"]["content"]
        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)

        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens

        return LLMResponse(
            content=content,
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
