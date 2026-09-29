"""
Central Tool Registry for ForgeAgent managing tool discovery, schemas, and execution.
"""

from typing import Dict, Any, List, Optional
from forgeagent.tools.base import BaseTool, ToolResult
from forgeagent.config.models import ForgeConfig
from forgeagent.sandbox.manager import SandboxManager
from forgeagent.git.engine import GitEngine
from forgeagent.github.client import GitHubClient

from forgeagent.tools.filesystem import (
    ReadFileTool, WriteFileTool, EditFileTool, DeleteFileTool, ListDirectoryTool, SearchCodeTool
)
from forgeagent.tools.terminal import (
    RunCommandTool, RunTestsTool, RunBuildTool, InspectProcessTool
)
from forgeagent.git.tools import (
    GitStatusTool, GitDiffTool, GitLogTool, GitBranchTool,
    GitCheckoutTool, GitAddTool, GitCommitTool, GitPushTool
)
from forgeagent.github.tools import (
    GitHubCreateRepoTool, GitHubGetRepoTool, GitHubCreateBranchTool,
    GitHubCreatePRTool, GitHubGetPRTool, GitHubGetCIStatusTool, GitHubGetWorkflowLogsTool
)


class ToolRegistry:
    def __init__(
        self,
        workspace_root: str,
        config: Optional[ForgeConfig] = None,
        sandbox_manager: Optional[SandboxManager] = None,
        git_engine: Optional[GitEngine] = None,
        github_client: Optional[GitHubClient] = None
    ):
        self.workspace_root = workspace_root
        self.config = config or ForgeConfig()
        self.sandbox_manager = sandbox_manager or SandboxManager(workspace_root, self.config.sandbox)
        self.git_engine = git_engine or GitEngine(workspace_root, self.config.git)
        self.github_client = github_client or GitHubClient(self.config.github)

        self._tools: Dict[str, BaseTool] = {}
        self._register_default_tools()

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "parameters_schema": t.parameters_schema,
            }
            for t in self._tools.values()
        ]

    def execute_tool(self, tool_name: str, **kwargs) -> ToolResult:
        tool = self.get_tool(tool_name)
        if not tool:
            return ToolResult(success=False, error=f"Unknown tool: '{tool_name}'")
        return tool.execute(**kwargs)

    def _register_default_tools(self) -> None:
        # Filesystem tools
        self.register(ReadFileTool(self.workspace_root, self.config))
        self.register(WriteFileTool(self.workspace_root, self.config))
        self.register(EditFileTool(self.workspace_root, self.config))
        self.register(DeleteFileTool(self.workspace_root, self.config))
        self.register(ListDirectoryTool(self.workspace_root, self.config))
        self.register(SearchCodeTool(self.workspace_root, self.config))

        # Terminal & execution tools
        self.register(RunCommandTool(self.sandbox_manager, self.config))
        self.register(RunTestsTool(self.sandbox_manager, self.config))
        self.register(RunBuildTool(self.sandbox_manager, self.config))
        self.register(InspectProcessTool(self.config))

        # Git tools
        self.register(GitStatusTool(self.git_engine, self.config))
        self.register(GitDiffTool(self.git_engine, self.config))
        self.register(GitLogTool(self.git_engine, self.config))
        self.register(GitBranchTool(self.git_engine, self.config))
        self.register(GitCheckoutTool(self.git_engine, self.config))
        self.register(GitAddTool(self.git_engine, self.config))
        self.register(GitCommitTool(self.git_engine, self.config))
        self.register(GitPushTool(self.git_engine, self.config))

        # GitHub tools
        self.register(GitHubCreateRepoTool(self.github_client, self.config))
        self.register(GitHubGetRepoTool(self.github_client, self.config))
        self.register(GitHubCreateBranchTool(self.github_client, self.config))
        self.register(GitHubCreatePRTool(self.github_client, self.config))
        self.register(GitHubGetPRTool(self.github_client, self.config))
        self.register(GitHubGetCIStatusTool(self.github_client, self.config))
        self.register(GitHubGetWorkflowLogsTool(self.github_client, self.config))
