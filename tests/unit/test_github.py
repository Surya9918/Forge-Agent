import unittest
from forgeagent.github.client import GitHubClient


class TestGitHubClient(unittest.TestCase):
    def setUp(self):
        self.client = GitHubClient(token="mock-token")

    def test_simulated_repo_create_and_get(self):
        repo = self.client.create_repository(name="test-repo", description="Testing", private=True)
        self.assertEqual(repo["name"], "test-repo")
        self.assertTrue(repo["private"])

        fetched = self.client.get_repository("test-repo")
        self.assertEqual(fetched["name"], "test-repo")

    def test_simulated_pr_create(self):
        pr = self.client.create_pull_request(repo="test-repo", title="feat: test feature", head="feat/test", base="main")
        self.assertEqual(pr["title"], "feat: test feature")
        self.assertEqual(pr["number"], 1)

    def test_simulated_ci_status(self):
        ci = self.client.get_ci_status("test-repo", "feat/test")
        self.assertEqual(ci["conclusion"], "success")


if __name__ == "__main__":
    unittest.main()
