import unittest
import tempfile
from forgeagent.config.models import ForgeConfig
from forgeagent.llm.mock_provider import MockProvider
from forgeagent.tools.registry import ToolRegistry
from forgeagent.state.state import TaskState
from forgeagent.agents.planner import PlannerAgent
from forgeagent.agents.architect import ArchitectAgent
from forgeagent.agents.coder import CoderAgent, PlanTask
from forgeagent.agents.tester import TesterAgent
from forgeagent.agents.debugger import DebuggerAgent
from forgeagent.agents.reviewer import ReviewerAgent


class TestAgents(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.workspace = self.tmpdir.name
        self.config = ForgeConfig()
        self.llm = MockProvider()
        self.tools = ToolRegistry(self.workspace, self.config)
        self.state = TaskState(task_id="test-1", project_id="unit-test-proj")

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_planner_agent(self):
        planner = PlannerAgent(llm_provider=self.llm, tool_registry=self.tools, config=self.config)
        plan = planner.run(self.state, requirement="Build a calculator CLI")
        self.assertTrue(len(plan.tasks) > 0)
        self.assertEqual(plan.project, "task-manager")

    def test_architect_agent(self):
        planner = PlannerAgent(llm_provider=self.llm, tool_registry=self.tools, config=self.config)
        plan = planner.run(self.state, requirement="Build a calculator CLI")
        architect = ArchitectAgent(llm_provider=self.llm, tool_registry=self.tools, config=self.config)
        arch_doc = architect.run(self.state, plan)
        self.assertTrue(len(arch_doc) > 0)
        self.assertIn("architecture", self.state.artifacts)

    def test_debugger_agent(self):
        debugger = DebuggerAgent(llm_provider=self.llm, tool_registry=self.tools, config=self.config)
        healed = debugger.run(self.state, test_output="AssertionError: 1 != 2")
        self.assertTrue(healed)
        self.assertEqual(self.state.iteration, 1)


if __name__ == "__main__":
    unittest.main()
