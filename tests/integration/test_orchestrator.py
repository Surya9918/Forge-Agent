import unittest
import tempfile
from pathlib import Path
from forgeagent.config.models import ForgeConfig
from forgeagent.llm.mock_provider import MockProvider
from forgeagent.agents.orchestrator import AgentOrchestrator
from forgeagent.state.state import AgentPhase


class TestOrchestratorIntegration(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.workspace = self.tmpdir.name
        self.config = ForgeConfig()
        self.config.project.workspace = self.workspace
        self.llm = MockProvider()
        self.orchestrator = AgentOrchestrator(
            config=self.config,
            workspace_root=self.workspace,
            llm_provider=self.llm
        )

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_full_autonomous_lifecycle(self):
        req = "Build a lightweight key-value cache CLI"
        state = self.orchestrator.run(requirement=req, project_name="kv-cache")

        self.assertEqual(state.phase, AgentPhase.COMPLETED)
        self.assertTrue(state.project_id, "kv-cache")
        self.assertIsNotNone(state.branch)

        # Verify Antigravity artifacts were generated
        artifacts_dir = Path(self.workspace) / ".agents" / "artifacts"
        self.assertTrue((artifacts_dir / "implementation_plan.md").is_file())
        self.assertTrue((artifacts_dir / "walkthrough.md").is_file())
        self.assertTrue((artifacts_dir / "verification_report.md").is_file())

        # Verify Git repo was initialized
        git_dir = Path(self.workspace) / ".git"
        self.assertTrue(git_dir.is_dir())


if __name__ == "__main__":
    unittest.main()
