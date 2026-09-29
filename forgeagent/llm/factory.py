"""
Factory for creating LLMProvider instances based on ForgeConfig.
"""

from forgeagent.config.models import LLMConfig
from forgeagent.llm.base import LLMProvider
from forgeagent.llm.mock_provider import MockProvider
from forgeagent.llm.google_provider import GoogleProvider
from forgeagent.llm.openai_provider import OpenAIProvider
from forgeagent.llm.anthropic_provider import AnthropicProvider
from forgeagent.llm.ollama_provider import OllamaProvider


def get_llm_provider(config: LLMConfig) -> LLMProvider:
    provider_name = config.provider.lower().strip()
    if provider_name in ["google", "gemini"]:
        return GoogleProvider(
            model=config.model,
            api_key=config.api_key,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            timeout=config.timeout_seconds,
        )
    elif provider_name in ["openai", "chatgpt"]:
        return OpenAIProvider(
            model=config.model,
            api_key=config.api_key,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            timeout=config.timeout_seconds,
        )
    elif provider_name in ["anthropic", "claude"]:
        return AnthropicProvider(
            model=config.model,
            api_key=config.api_key,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            timeout=config.timeout_seconds,
        )
    elif provider_name in ["ollama", "local"]:
        return OllamaProvider(
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            timeout=config.timeout_seconds,
        )
    else:
        return MockProvider(
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            timeout=config.timeout_seconds,
        )
