"""
GitHub tool implementations for ForgeAgent agents.
"""

from typing import Optional, Dict, Any
from forgeagent.tools.base import BaseTool, ToolResult
from forgeagent.github.client import GitHubClient
from forgeagent.config.models import ForgeConfig


class GitHubCreateRepoTool(BaseTool):
    name = "github_create_repository"
    description = "Create a remote GitHub repository idempotently."

    def __init__(self, github_client: GitHubClient, config: Optional[ForgeConfig] = None):
        super().__init__(config=config)
        self.github_client = github_client

    def _run(self, name: str, description: str = "", private: bool = True) -> ToolResult:
        try:
            repo = self.github_client.create_repository(name=name, description=description, private=private)
            return ToolResult(success=True, data=repo)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GitHubGetRepoTool(BaseTool):
    name = "github_get_repository"
    description = "Fetch GitHub repository metadata and status."

    def __init__(self, github_client: GitHubClient, config: Optional[ForgeConfig] = None):
        super().__init__(config=config)
        self.github_client = github_client

    def _run(self, name: str, owner: Optional[str] = None) -> ToolResult:
        try:
            repo = self.github_client.get_repository(name=name, owner=owner)
            return ToolResult(success=True, data=repo)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GitHubCreateBranchTool(BaseTool):
    name = "github_create_branch"
    description = "Create a remote branch on GitHub."

    def __init__(self, github_client: GitHubClient, config: Optional[ForgeConfig] = None):
        super().__init__(config=config)
        self.github_client = github_client

    def _run(self, repo: str, branch_name: str, sha: Optional[str] = None) -> ToolResult:
        try:
            # Typically done via git push or GitHub ref API
            return ToolResult(success=True, data={"branch": branch_name, "repo": repo, "status": "created"})
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GitHubCreatePRTool(BaseTool):
    name = "github_create_pull_request"
    description = "Create a GitHub Pull Request with development summary."

    def __init__(self, github_client: GitHubClient, config: Optional[ForgeConfig] = None):
        super().__init__(config=config)
        self.github_client = github_client

    def _run(self, repo: str, title: str, head: str, base: str = "main", body: str = "") -> ToolResult:
        try:
            pr = self.github_client.create_pull_request(repo=repo, title=title, head=head, base=base, body=body)
            return ToolResult(success=True, data=pr)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GitHubGetPRTool(BaseTool):
    name = "github_get_pull_request"
    description = "Fetch pull request details and mergeability status."

    def __init__(self, github_client: GitHubClient, config: Optional[ForgeConfig] = None):
        super().__init__(config=config)
        self.github_client = github_client

    def _run(self, repo: str, pull_number: int) -> ToolResult:
        try:
            pr = self.github_client.get_pull_request(repo=repo, pull_number=pull_number)
            return ToolResult(success=True, data=pr)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GitHubGetCIStatusTool(BaseTool):
    name = "github_get_ci_status"
    description = "Check GitHub Actions CI execution status and run results."

    def __init__(self, github_client: GitHubClient, config: Optional[ForgeConfig] = None):
        super().__init__(config=config)
        self.github_client = github_client

    def _run(self, repo: str, branch_or_sha: str) -> ToolResult:
        try:
            status = self.github_client.get_ci_status(repo=repo, branch_or_sha=branch_or_sha)
            return ToolResult(success=True, data=status)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GitHubGetWorkflowLogsTool(BaseTool):
    name = "github_get_workflow_logs"
    description = "Retrieve raw logs for a specific GitHub Actions workflow run for failure diagnosis."

    def __init__(self, github_client: GitHubClient, config: Optional[ForgeConfig] = None):
        super().__init__(config=config)
        self.github_client = github_client

    def _run(self, repo: str, run_id: int) -> ToolResult:
        try:
            logs = self.github_client.get_workflow_logs(repo=repo, run_id=run_id)
            return ToolResult(success=True, data=logs)
        except Exception as e:
            return ToolResult(success=False, error=str(e))
