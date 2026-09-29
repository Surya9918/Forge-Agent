"""
Ollama Local Model Provider for on-device inference.
"""

import os
import json
import requests
from typing import List, Type, Optional
from forgeagent.llm.base import LLMProvider, ChatMessage, LLMResponse, T


class OllamaProvider(LLMProvider):
    def __init__(self, model: str = "qwen2.5-coder:7b", base_url: Optional[str] = None, **kwargs):
        super().__init__(model=model, **kwargs)
        self.base_url = base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

    def generate(self, messages: List[ChatMessage], **kwargs) -> LLMResponse:
        url = f"{self.base_url.rstrip('/')}/api/chat"
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {"temperature": self.temperature}
        }
        resp = requests.post(url, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        content = data.get("message", {}).get("content", "")
        prompt_tokens = data.get("prompt_eval_count", 0)
        completion_tokens = data.get("eval_count", 0)

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
