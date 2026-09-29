"""
Base Agent class for ForgeAgent.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from forgeagent.config.models import ForgeConfig
from forgeagent.llm.base import LLMProvider
from forgeagent.tools.registry import ToolRegistry
from forgeagent.state.state import TaskState
from forgeagent.observability.logger import get_logger


class BaseAgent(ABC):
    def __init__(
        self,
        name: str,
        llm_provider: LLMProvider,
        tool_registry: ToolRegistry,
        config: Optional[ForgeConfig] = None
    ):
        self.name = name
        self.llm = llm_provider
        self.tools = tool_registry
        self.config = config or ForgeConfig()
        self.logger = get_logger(f"forgeagent.agents.{name.lower()}")

    @abstractmethod
    def run(self, state: TaskState, **kwargs) -> Any:
        pass
