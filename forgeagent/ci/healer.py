"""
CI Self-Healing Engine: monitors remote or local CI runs, analyzes logs, and executes automatic repairs.
"""

from typing import Dict, Any, Optional, List
from forgeagent.github.client import GitHubClient
from forgeagent.llm.base import LLMProvider, ChatMessage
from forgeagent.tools.registry import ToolRegistry
from forgeagent.state.state import TaskState
from forgeagent.events.bus import bus
from forgeagent.events.events import ForgeEvent, EventType
from forgeagent.observability.logger import get_logger

logger = get_logger("forgeagent.ci.healer")


class CIHealer:
    def __init__(
        self,
        github_client: GitHubClient,
        llm_provider: LLMProvider,
        tool_registry: ToolRegistry,
        max_attempts: int = 5
    ):
        self.github_client = github_client
        self.llm_provider = llm_provider
        self.tool_registry = tool_registry
        self.max_attempts = max_attempts

    def monitor_and_heal(self, state: TaskState, repo_name: str, branch: str) -> bool:
        bus.emit(ForgeEvent(
            event_type=EventType.CI_STARTED,
            task_id=state.task_id,
            project_id=state.project_id,
            message=f"Monitoring CI pipeline for branch {branch} in {repo_name}"
        ))

        attempts = 0
        while attempts < self.max_attempts:
            status = self.github_client.get_ci_status(repo=repo_name, branch_or_sha=branch)
            runs = status.get("workflow_runs", [])
            if not runs:
                logger.info("No workflow runs found yet; assuming initial pass")
                bus.emit(ForgeEvent(
                    event_type=EventType.CI_PASSED,
                    task_id=state.task_id,
                    project_id=state.project_id,
                    message="CI passed (no active failures reported)"
                ))
                return True

            latest_run = runs[0]
            conclusion = latest_run.get("conclusion")
            if conclusion == "success":
                bus.emit(ForgeEvent(
                    event_type=EventType.CI_PASSED,
                    task_id=state.task_id,
                    project_id=state.project_id,
                    message=f"CI workflow succeeded: {latest_run.get('html_url', '')}"
                ))
                return True
            elif conclusion in ["failure", "timed_out"]:
                attempts += 1
                bus.emit(ForgeEvent(
                    event_type=EventType.CI_FAILED,
                    task_id=state.task_id,
                    project_id=state.project_id,
                    message=f"CI failed on attempt {attempts}/{self.max_attempts}. Starting CI Self-Healing."
                ))

                # Fetch logs and diagnose
                run_id = latest_run.get("id", 0)
                logs = self.github_client.get_workflow_logs(repo=repo_name, run_id=run_id)
                self._apply_ci_repair(state, logs, branch)
            else:
                # Still running or queued
                break

        return False

    def _apply_ci_repair(self, state: TaskState, ci_logs: str, branch: str) -> None:
        bus.emit(ForgeEvent(
            event_type=EventType.FIX_STARTED,
            task_id=state.task_id,
            project_id=state.project_id,
            message="Analyzing CI logs for automated repair"
        ))

        prompt = f"""You are the CI/CD Debugger Agent.
The continuous integration build failed with the following logs:
{ci_logs[-2000:]}

Diagnose the root cause and provide the exact file change needed to repair this failure.
Output format:
FILE: <file_path>
CODE:
<full updated file content>
"""
        messages = [ChatMessage(role="user", content=prompt)]
        resp = self.llm_provider.generate(messages)

        # Parse and write repair
        content = resp.content
        if "FILE:" in content and "CODE:" in content:
            file_part = content.split("FILE:")[1].split("CODE:")[0].strip()
            code_part = content.split("CODE:")[1].strip()
            if code_part.startswith("```"):
                code_part = code_part.split("\n", 1)[1]
            if code_part.endswith("```"):
                code_part = code_part.rsplit("\n", 1)[0]

            self.tool_registry.execute_tool("write_file", file_path=file_part, content=code_part)
            self.tool_registry.execute_tool("git_add")
            self.tool_registry.execute_tool("git_commit", message=f"fix(ci): auto-heal build failure in {file_part}")
            self.tool_registry.execute_tool("git_push", branch=branch)

            bus.emit(ForgeEvent(
                event_type=EventType.FIX_APPLIED,
                task_id=state.task_id,
                project_id=state.project_id,
                message=f"Applied CI self-healing fix to {file_part} and pushed to {branch}"
            ))
