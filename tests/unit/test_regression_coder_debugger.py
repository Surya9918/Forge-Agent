import unittest
import tempfile
from pathlib import Path
from forgeagent.config.models import ForgeConfig
from forgeagent.llm.mock_provider import MockProvider
from forgeagent.tools.registry import ToolRegistry
from forgeagent.state.state import TaskState
from forgeagent.domain.models import PlanTask, DevelopmentPlan, CodeAction, TaskImplementation, RepairPatch
from forgeagent.agents.coder import CoderAgent
from forgeagent.agents.debugger import DebuggerAgent


class TestRegressionCoderDebugger(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.workspace = self.tmpdir.name
        self.config = ForgeConfig()
        self.llm = MockProvider()
        self.tools = ToolRegistry(self.workspace, self.config)
        self.state = TaskState(task_id="reg-1", project_id="regression-proj")

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_coder_always_has_actions_iterable(self):
        coder = CoderAgent(llm_provider=self.llm, tool_registry=self.tools, config=self.config)
        task = PlanTask(id="task-reg-1", title="Build service", description="Service implementation")
        plan = DevelopmentPlan(project="reg-proj")

        impl = coder.run(self.state, task, plan)
        self.assertTrue(hasattr(impl, "actions"))
        self.assertIsInstance(impl.actions, list)
        self.assertTrue(len(impl.actions) > 0)
        for act in impl.actions:
            self.assertTrue(hasattr(act, "file_path"))
            self.assertTrue(hasattr(act, "content"))

    def test_debugger_always_has_file_path_and_applies_fix(self):
        # Create an initially broken file
        broken_file = Path(self.workspace) / "test_app.py"
        broken_file.write_text("def test_broken(): assert 1 == 2\n")

        debugger = DebuggerAgent(llm_provider=self.llm, tool_registry=self.tools, config=self.config)
        healed = debugger.run(self.state, test_output="AssertionError: 1 == 2 in test_broken")
        self.assertTrue(healed)
        self.assertIn("test_app.py", self.state.changed_files)

        # Verify fixed file content was written
        repaired_content = broken_file.read_text()
        self.assertIn("assertEqual(1, 1)", repaired_content)


if __name__ == "__main__":
    unittest.main()
