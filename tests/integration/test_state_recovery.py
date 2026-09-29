import unittest
import tempfile
from pathlib import Path
from forgeagent.config.models import ForgeConfig
from forgeagent.llm.mock_provider import MockProvider
from forgeagent.agents.orchestrator import AgentOrchestrator
from forgeagent.state.state import TaskState, AgentPhase
from forgeagent.state.persistence import StateManager


class TestStateRecovery(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.workspace = self.tmpdir.name

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_state_persistence_and_recovery(self):
        config = ForgeConfig()
        config.project.workspace = self.workspace
        state_mgr = StateManager(f"{self.workspace}/.forge/state")

        # 1. Simulate an interrupted task
        interrupted_state = TaskState(
            task_id="task-crash-1",
            project_id="recoverable-proj",
            requirement="Build a microservice",
            phase=AgentPhase.TESTING,
            iteration=2,
            branch="forgeagent/recoverable-proj"
        )
        saved_path = state_mgr.save(interrupted_state)
        self.assertTrue(saved_path.is_file())

        # 2. Simulate process restart by instantiating a completely fresh orchestrator
        recovered_state = state_mgr.load("task-crash-1")
        self.assertIsNotNone(recovered_state)
        self.assertEqual(recovered_state.task_id, "task-crash-1")
        self.assertEqual(recovered_state.phase, AgentPhase.TESTING)
        self.assertEqual(recovered_state.iteration, 2)

        latest_state = state_mgr.load_latest()
        self.assertIsNotNone(latest_state)
        self.assertEqual(latest_state.task_id, "task-crash-1")


if __name__ == "__main__":
    unittest.main()
