import unittest
import tempfile
from forgeagent.config.models import ForgeConfig
from forgeagent.llm.mock_provider import MockProvider
from forgeagent.agents.orchestrator import AgentOrchestrator
from forgeagent.state.state import AgentPhase


class TestIdempotency(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.workspace = self.tmpdir.name

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_repeated_run_idempotency(self):
        config = ForgeConfig()
        config.project.workspace = self.workspace
        llm = MockProvider()
        orchestrator = AgentOrchestrator(
            config=config,
            workspace_root=self.workspace,
            llm_provider=llm
        )

        req = "Build an idempotent data processor"
        # First execution
        state1 = orchestrator.run(requirement=req, project_name="idempotent-app")
        self.assertEqual(state1.phase, AgentPhase.COMPLETED)
        commit1 = state1.commit_sha

        # Second execution on the same project
        state2 = orchestrator.run(requirement=req, project_name="idempotent-app")
        self.assertEqual(state2.phase, AgentPhase.COMPLETED)
        self.assertIsNotNone(state2.commit_sha)


if __name__ == "__main__":
    unittest.main()
