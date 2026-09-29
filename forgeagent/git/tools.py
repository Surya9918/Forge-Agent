"""
Git tool wrappers for agent orchestration.
"""

from typing import Optional, List
from forgeagent.tools.base import BaseTool, ToolResult
from forgeagent.git.engine import GitEngine
from forgeagent.config.models import ForgeConfig


class GitStatusTool(BaseTool):
    name = "git_status"
    description = "Get status of Git working tree, staged/unstaged changes, and current branch."

    def __init__(self, git_engine: GitEngine, config: Optional[ForgeConfig] = None):
        super().__init__(config=config)
        self.git_engine = git_engine

    def _run(self) -> ToolResult:
        try:
            status = self.git_engine.get_status()
            return ToolResult(success=True, data=status)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GitDiffTool(BaseTool):
    name = "git_diff"
    description = "View git diff for working tree or staged changes."

    def __init__(self, git_engine: GitEngine, config: Optional[ForgeConfig] = None):
        super().__init__(config=config)
        self.git_engine = git_engine

    def _run(self, staged: bool = False) -> ToolResult:
        try:
            diff = self.git_engine.get_diff(staged=staged)
            return ToolResult(success=True, data=diff)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GitLogTool(BaseTool):
    name = "git_log"
    description = "Retrieve recent commit history."

    def __init__(self, git_engine: GitEngine, config: Optional[ForgeConfig] = None):
        super().__init__(config=config)
        self.git_engine = git_engine

    def _run(self, limit: int = 10) -> ToolResult:
        try:
            commits = self.git_engine.get_log(limit=limit)
            return ToolResult(success=True, data=commits)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GitBranchTool(BaseTool):
    name = "git_branch"
    description = "Create a new git branch."

    def __init__(self, git_engine: GitEngine, config: Optional[ForgeConfig] = None):
        super().__init__(config=config)
        self.git_engine = git_engine

    def _run(self, branch_name: str, checkout: bool = True) -> ToolResult:
        try:
            msg = self.git_engine.create_branch(branch_name, checkout=checkout)
            return ToolResult(success=True, data=msg)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GitCheckoutTool(BaseTool):
    name = "git_checkout"
    description = "Switch active Git branch."

    def __init__(self, git_engine: GitEngine, config: Optional[ForgeConfig] = None):
        super().__init__(config=config)
        self.git_engine = git_engine

    def _run(self, branch_name: str) -> ToolResult:
        try:
            msg = self.git_engine.checkout_branch(branch_name)
            return ToolResult(success=True, data=msg)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GitAddTool(BaseTool):
    name = "git_add"
    description = "Stage files for commit."

    def __init__(self, git_engine: GitEngine, config: Optional[ForgeConfig] = None):
        super().__init__(config=config)
        self.git_engine = git_engine

    def _run(self, paths: Optional[List[str]] = None) -> ToolResult:
        try:
            msg = self.git_engine.stage_files(paths)
            return ToolResult(success=True, data=msg)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GitCommitTool(BaseTool):
    name = "git_commit"
    description = "Commit staged changes with a conventional commit message."

    def __init__(self, git_engine: GitEngine, config: Optional[ForgeConfig] = None):
        super().__init__(config=config)
        self.git_engine = git_engine

    def _run(self, message: str) -> ToolResult:
        try:
            sha = self.git_engine.commit(message)
            return ToolResult(success=True, data={"commit_sha": sha, "message": message})
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GitPushTool(BaseTool):
    name = "git_push"
    description = "Push committed changes to remote repository."

    def __init__(self, git_engine: GitEngine, config: Optional[ForgeConfig] = None):
        super().__init__(config=config)
        self.git_engine = git_engine

    def _run(self, remote: str = "origin", branch: Optional[str] = None, force: bool = False) -> ToolResult:
        try:
            msg = self.git_engine.push(remote=remote, branch=branch, force=force)
            return ToolResult(success=True, data=msg)
        except Exception as e:
            return ToolResult(success=False, error=str(e))
