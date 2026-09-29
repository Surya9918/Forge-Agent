import unittest
import tempfile
from pathlib import Path
from forgeagent.git.engine import GitEngine
from forgeagent.config.models import GitConfig


class TestGitEngine(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.workspace = self.tmpdir.name
        self.engine = GitEngine(self.workspace)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_init_and_status(self):
        self.engine.initialize_repository()
        self.assertTrue(self.engine.is_repo())

        status = self.engine.get_status()
        self.assertTrue(status["is_repo"])

    def test_commit_and_log(self):
        self.engine.initialize_repository()
        test_file = Path(self.workspace) / "file.txt"
        test_file.write_text("content")

        self.engine.stage_files()
        sha = self.engine.commit("feat: initial test commit")
        self.assertTrue(len(sha) > 0)

        logs = self.engine.get_log(limit=5)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["message"], "feat: initial test commit")

    def test_protected_branch_force_push_blocked(self):
        self.engine.initialize_repository()
        with self.assertRaises(PermissionError):
            self.engine.push(branch="main", force=True)


if __name__ == "__main__":
    unittest.main()
