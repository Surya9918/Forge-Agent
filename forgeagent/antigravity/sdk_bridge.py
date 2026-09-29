"""
Google Antigravity Python SDK (`google-antigravity`) Bridge.
Provides programmatic registration for Antigravity Agent tools, subagents, and lifecycle hooks.
"""

from typing import Dict, Any, Callable
from forgeagent.agents.orchestrator import AgentOrchestrator
from forgeagent.config.loader import load_config


class AntigravitySDKBridge:
    def __init__(self, workspace_root: str = "./workspace"):
        self.config = load_config()
        self.config.project.workspace = workspace_root
        self.orchestrator = AgentOrchestrator(self.config, workspace_root=workspace_root)

    def get_antigravity_tools(self) -> Dict[str, Callable]:
        """
        Export callable functions compatible with Google Antigravity SDK custom tools registration:
        e.g., `agent = Agent(config, tools=bridge.get_antigravity_tools().values())`
        """
        def forge_plan(requirement: str, project_name: str = "app") -> str:
            """Plan software engineering project requirement."""
            plan = self.orchestrator.planner.run(None, requirement=requirement)
            return plan.model_dump_json(indent=2)

        def forge_develop(requirement: str, project_name: str = "app") -> str:
            """Autonomously develop, test, fix, and commit code for requirement."""
            state = self.orchestrator.run(requirement=requirement, project_name=project_name)
            return f"Completed in phase {state.phase} with {state.tests.passed} tests passed."

        def forge_test_and_heal() -> str:
            """Run automated self-healing loop on tests."""
            state = self.orchestrator.state_manager.load_latest()
            if not state:
                return "No active state to test."
            summary = self.orchestrator.tester.run(state)
            while summary.failed > 0 and state.iteration < self.config.agent.max_iterations:
                self.orchestrator.debugger.run(state, test_output=summary.output)
                summary = self.orchestrator.tester.run(state)
            return f"Verification finished: {summary.passed} passed, {summary.failed} failed."

        return {
            "forge_plan": forge_plan,
            "forge_develop": forge_develop,
            "forge_test_and_heal": forge_test_and_heal,
        }
