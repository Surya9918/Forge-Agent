"""
Sandbox Manager governing sandbox provisioning, security policies, and resource limits.
"""

from typing import Optional
from forgeagent.config.models import SandboxConfig
from forgeagent.sandbox.base import SandboxRunner
from forgeagent.sandbox.local_sandbox import LocalProcessSandbox
from forgeagent.sandbox.docker_sandbox import DockerSandbox


class SandboxManager:
    def __init__(self, workspace_root: str, config: Optional[SandboxConfig] = None):
        self.workspace_root = workspace_root
        self.config = config or SandboxConfig()
        self._runner: Optional[SandboxRunner] = None

    def get_runner(self) -> SandboxRunner:
        if self._runner is not None:
            return self._runner

        if self.config.runtime == "docker":
            self._runner = DockerSandbox(
                workspace_root=self.workspace_root,
                default_timeout=self.config.timeout_seconds,
                memory_limit_mb=self.config.memory_limit_mb,
                cpu_limit=self.config.cpu_limit,
            )
        else:
            self._runner = LocalProcessSandbox(
                workspace_root=self.workspace_root,
                default_timeout=self.config.timeout_seconds,
            )
        return self._runner

    def cleanup(self) -> None:
        if self._runner:
            self._runner.cleanup()
            self._runner = None
