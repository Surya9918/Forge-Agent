"""
ForgeAgent: Autonomous Software Engineering inside Antigravity.
Production-ready plugin, MCP server, and agent orchestration system.
"""

__version__ = "0.2.0"
__product__ = "ForgeAgent"
__tagline__ = "Autonomous Software Engineering inside Antigravity."

from forgeagent.config.models import ForgeConfig, AutonomyMode
from forgeagent.agents.orchestrator import AgentOrchestrator
from forgeagent.antigravity.mcp_server import ForgeMCPServer

__all__ = [
    "__version__",
    "__product__",
    "__tagline__",
    "ForgeConfig",
    "AutonomyMode",
    "AgentOrchestrator",
    "ForgeMCPServer",
]
