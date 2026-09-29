"""
Docker-based sandbox runner for isolated container execution.
"""

import shutil
import subprocess
from typing import Dict, Any, Optional
from forgeagent.sandbox.base import SandboxRunner, CommandResult
from forgeagent.sandbox.local_sandbox import LocalProcessSandbox
from forgeagent.observability.logger import get_logger

logger = get_logger("forgeagent.sandbox.docker")


class DockerSandbox(SandboxRunner):
    def __init__(
        self,
        workspace_root: str,
        image: str = "python:3.11-slim",
        default_timeout: int = 120,
        memory_limit_mb: int = 2048,
        cpu_limit: float = 2.0
    ):
        self.workspace_root = workspace_root
        self.image = image
        self.default_timeout = default_timeout
        self.memory_limit_mb = memory_limit_mb
        self.cpu_limit = cpu_limit
        self.docker_available = shutil.which("docker") is not None
        self._fallback_runner = LocalProcessSandbox(workspace_root, default_timeout)

    def run_command(
        self,
        command: str,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout_seconds: Optional[int] = None
    ) -> CommandResult:
        if not self.docker_available:
            logger.info("Docker binary not found; falling back to secure LocalProcessSandbox")
            return self._fallback_runner.run_command(command, cwd=cwd, env=env, timeout_seconds=timeout_seconds)

        # Docker execution container invocation
        docker_cmd = (
            f"docker run --rm -v {self.workspace_root}:/workspace -w /workspace "
            f"--memory={self.memory_limit_mb}m --cpus={self.cpu_limit} "
            f"{self.image} sh -c {subprocess.list2cmdline([command])}"
        )
        return self._fallback_runner.run_command(docker_cmd, cwd=self.workspace_root, timeout_seconds=timeout_seconds)

    def cleanup(self) -> None:
        self._fallback_runner.cleanup()
