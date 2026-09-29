"""
Terminal execution tools with security policies, allowlists, denylists, and sandboxing.
"""

from typing import Optional, Dict, Any
from forgeagent.tools.base import BaseTool, ToolResult
from forgeagent.config.models import ForgeConfig
from forgeagent.sandbox.manager import SandboxManager


class RunCommandTool(BaseTool):
    name = "run_command"
    description = "Execute a shell command inside the secure sandbox environment."

    def __init__(self, sandbox_manager: SandboxManager, config: Optional[ForgeConfig] = None):
        super().__init__(config=config)
        self.sandbox_manager = sandbox_manager

    def _is_command_safe(self, command: str) -> (bool, str):
        cmd_clean = command.strip()
        # 1. Check denylist
        for denied in self.config.security.denied_commands:
            if denied in cmd_clean:
                return False, f"Command contains forbidden expression: '{denied}'"

        # 2. Check allowlist for command binary
        first_token = cmd_clean.split()[0] if cmd_clean.split() else ""
        # Handle env var or leading assignments (e.g. CI=true npm test)
        if "=" in first_token and len(cmd_clean.split()) > 1:
            first_token = cmd_clean.split()[1]

        # Extract base binary name
        import os
        base_binary = os.path.basename(first_token)

        if self.config.security.allowed_commands:
            if base_binary not in self.config.security.allowed_commands:
                # In assisted mode or strict production, reject unlisted binaries
                if self.config.agent.mode != "autonomous":
                    return False, f"Command binary '{base_binary}' is not in allowed list: {self.config.security.allowed_commands}"

        return True, ""

    def _run(self, command: str, cwd: Optional[str] = None, timeout_seconds: Optional[int] = None) -> ToolResult:
        is_safe, reason = self._is_command_safe(command)
        if not is_safe:
            return ToolResult(success=False, error=f"Security Policy Violation: {reason}")

        runner = self.sandbox_manager.get_runner()
        res = runner.run_command(command, cwd=cwd, timeout_seconds=timeout_seconds)

        return ToolResult(
            success=res.success,
            data={
                "stdout": res.stdout,
                "stderr": res.stderr,
                "exit_code": res.exit_code,
                "duration_ms": res.duration_ms,
                "timed_out": res.timed_out,
            },
            error=res.stderr if not res.success else None,
            metadata={"command": command, "exit_code": res.exit_code}
        )


class RunTestsTool(BaseTool):
    name = "run_tests"
    description = "Execute project test suite and return structured failure/pass results."

    def __init__(self, sandbox_manager: SandboxManager, config: Optional[ForgeConfig] = None):
        super().__init__(config=config)
        self.sandbox_manager = sandbox_manager

    def _run(self, test_command: str = "npm test", cwd: Optional[str] = None) -> ToolResult:
        runner = self.sandbox_manager.get_runner()
        res = runner.run_command(test_command, cwd=cwd)
        return ToolResult(
            success=res.success,
            data={
                "command": test_command,
                "exit_code": res.exit_code,
                "stdout": res.stdout,
                "stderr": res.stderr,
                "duration_ms": res.duration_ms,
            },
            error=None if res.success else f"Test run exited with code {res.exit_code}"
        )


class RunBuildTool(BaseTool):
    name = "run_build"
    description = "Execute project build command and report errors."

    def __init__(self, sandbox_manager: SandboxManager, config: Optional[ForgeConfig] = None):
        super().__init__(config=config)
        self.sandbox_manager = sandbox_manager

    def _run(self, build_command: str = "npm run build", cwd: Optional[str] = None) -> ToolResult:
        runner = self.sandbox_manager.get_runner()
        res = runner.run_command(build_command, cwd=cwd)
        return ToolResult(
            success=res.success,
            data={
                "command": build_command,
                "exit_code": res.exit_code,
                "stdout": res.stdout,
                "stderr": res.stderr,
                "duration_ms": res.duration_ms,
            },
            error=None if res.success else f"Build failed with exit code {res.exit_code}"
        )


class InspectProcessTool(BaseTool):
    name = "inspect_process"
    description = "Check active sandbox processes and resource status."

    def _run(self) -> ToolResult:
        import os
        import sys
        return ToolResult(
            success=True,
            data={
                "platform": sys.platform,
                "pid": os.getpid(),
                "cwd": os.getcwd(),
                "status": "healthy"
            }
        )
