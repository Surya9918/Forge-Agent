"""
Base abstraction for ForgeAgent Tools.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from forgeagent.config.models import ForgeConfig
from forgeagent.observability.logger import get_logger

logger = get_logger("forgeagent.tools")


class ToolResult(BaseModel):
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseTool(ABC):
    name: str = ""
    description: str = ""
    parameters_schema: Dict[str, Any] = {}

    def __init__(self, config: Optional[ForgeConfig] = None):
        self.config = config or ForgeConfig()

    def execute(self, **kwargs) -> ToolResult:
        """Permission-checked and audited execution wrapper."""
        action_name = self.name
        if not self.config.is_action_permitted(action_name):
            logger.warning(f"Action '{action_name}' blocked pending approval under mode {self.config.agent.mode}")
            return ToolResult(
                success=False,
                error=f"Permission Denied: '{action_name}' requires human approval in {self.config.agent.mode} mode.",
                metadata={"action": action_name, "requires_approval": True}
            )

        try:
            return self._run(**kwargs)
        except Exception as e:
            logger.error(f"Tool {self.name} raised error: {e}", exc_info=True)
            return ToolResult(success=False, error=str(e))

    @abstractmethod
    def _run(self, **kwargs) -> ToolResult:
        pass
