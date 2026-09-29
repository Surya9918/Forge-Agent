"""
Google Gemini provider for ForgeAgent.
"""

import os
import json
import requests
from typing import List, Type, Optional
from forgeagent.llm.base import LLMProvider, ChatMessage, LLMResponse, T
from forgeagent.observability.logger import get_logger

logger = get_logger("forgeagent.llm.google")


class GoogleProvider(LLMProvider):
    def __init__(self, model: str = "gemini-2.0-flash", api_key: Optional[str] = None, **kwargs):
        super().__init__(model=model, **kwargs)
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")

    def generate(self, messages: List[ChatMessage], **kwargs) -> LLMResponse:
        if not self.api_key:
            logger.warning("No GEMINI_API_KEY found, falling back to simulated output")
            return LLMResponse(content="[Simulation: GEMINI_API_KEY not configured]", model=self.model)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        contents = []
        for m in messages:
            role = "model" if m.role == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": m.content}]})

        body = {
            "contents": contents,
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_tokens,
            }
        }
        resp = requests.post(url, json=body, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()

        text = ""
        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                text = parts[0].get("text", "")

        usage = data.get("usageMetadata", {})
        prompt_toks = usage.get("promptTokenCount", 0)
        resp_toks = usage.get("candidatesTokenCount", 0)
        self.total_prompt_tokens += prompt_toks
        self.total_completion_tokens += resp_toks

        return LLMResponse(
            content=text,
            tokens_prompt=prompt_toks,
            tokens_completion=resp_toks,
            total_tokens=prompt_toks + resp_toks,
            model=self.model
        )

    def generate_structured(self, messages: List[ChatMessage], schema: Type[T], **kwargs) -> T:
        system_instruction = f"\nReturn strictly valid JSON matching this JSON Schema:\n{json.dumps(schema.model_json_schema())}"
        enhanced_messages = list(messages)
        enhanced_messages[-1] = ChatMessage(
            role=enhanced_messages[-1].role,
            content=enhanced_messages[-1].content + system_instruction
        )
        resp = self.generate(enhanced_messages, **kwargs)
        cleaned = resp.content.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        return schema.model_validate_json(cleaned.strip())
