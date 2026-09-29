"""
Secure Local Process Sandbox with workspace boundary enforcement, timeouts, and sanitized environment.
"""

import os
import time
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from forgeagent.sandbox.base import SandboxRunner, CommandResult
from forgeagent.observability.redactor import redact_secrets
from forgeagent.observability.logger import get_logger

logger = get_logger("forgeagent.sandbox.local")


class LocalProcessSandbox(SandboxRunner):
    def __init__(self, workspace_root: str, default_timeout: int = 120):
        self.workspace_root = Path(workspace_root).resolve()
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        self.default_timeout = default_timeout

    def run_command(
        self,
        command: str,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout_seconds: Optional[int] = None
    ) -> CommandResult:
        timeout = timeout_seconds or self.default_timeout

        target_cwd = Path(cwd).resolve() if cwd else self.workspace_root
        # Enforce workspace boundary check
        try:
            target_cwd.relative_to(self.workspace_root)
        except ValueError:
            logger.warning(f"Boundary breach attempted: {target_cwd} outside {self.workspace_root}")
            return CommandResult(
                command=command,
                exit_code=-1,
                stdout="",
                stderr=f"Security Violation: cwd '{target_cwd}' is outside workspace '{self.workspace_root}'",
                duration_ms=0,
            )

        # Build clean environment scrubbed of parent secrets
        clean_env = os.environ.copy()
        for secret_key in ["GITHUB_TOKEN", "GH_TOKEN", "GEMINI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "AWS_SECRET_ACCESS_KEY"]:
            clean_env.pop(secret_key, None)

        if env:
            clean_env.update(env)

        start_time = time.time()
        try:
            process = subprocess.run(
                command,
                shell=True,
                cwd=str(target_cwd),
                env=clean_env,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            duration_ms = int((time.time() - start_time) * 1000)
            return CommandResult(
                command=command,
                exit_code=process.returncode,
                stdout=redact_secrets(process.stdout),
                stderr=redact_secrets(process.stderr),
                duration_ms=duration_ms,
                timed_out=False,
            )
        except subprocess.TimeoutExpired as e:
            duration_ms = int((time.time() - start_time) * 1000)
            stdout = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
            stderr = e.stderr.decode() if isinstance(e.stderr, bytes) else (e.stderr or "")
            return CommandResult(
                command=command,
                exit_code=-1,
                stdout=redact_secrets(stdout),
                stderr=f"Execution timed out after {timeout} seconds. {redact_secrets(stderr)}",
                duration_ms=duration_ms,
                timed_out=True,
            )
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return CommandResult(
                command=command,
                exit_code=-1,
                stdout="",
                stderr=str(e),
                duration_ms=duration_ms,
            )

    def cleanup(self) -> None:
        pass
