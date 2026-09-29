"""
Debugger Agent: implements the autonomous self-healing repair loop.
"""

from typing import List, Dict, Any, Optional
from forgeagent.agents.base import BaseAgent
from forgeagent.domain.models import RepairPatch
from forgeagent.llm.base import ChatMessage
from forgeagent.state.state import TaskState, AgentPhase
from forgeagent.events.bus import bus
from forgeagent.events.events import ForgeEvent, EventType
from forgeagent.intelligence.analyzer import RepoAnalyzer


class DebuggerAgent(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(name="Debugger", **kwargs)

    def run(self, state: TaskState, test_output: str, previous_attempts: Optional[List[str]] = None) -> bool:
        state.phase = AgentPhase.HEALING
        state.iteration += 1

        if state.iteration > state.max_iterations:
            state.phase = AgentPhase.BLOCKED
            state.status_message = f"Exceeded maximum repair iterations ({state.max_iterations}). Human escalation required."
            bus.emit(ForgeEvent(
                event_type=EventType.AGENT_BLOCKED,
                task_id=state.task_id,
                project_id=state.project_id,
                message=state.status_message,
                payload={"iteration": state.iteration, "max_iterations": state.max_iterations}
            ))
            return False

        bus.emit(ForgeEvent(
            event_type=EventType.FIX_STARTED,
            task_id=state.task_id,
            project_id=state.project_id,
            message=f"Starting repair attempt {state.iteration}/{state.max_iterations}"
        ))

        # Retrieve git diff and recent failure context
        diff_res = self.tools.execute_tool("git_diff")
        git_diff = diff_res.data if diff_res.success else ""

        analyzer = RepoAnalyzer(self.tools.workspace_root)
        repo_summary = analyzer.analyze()

        prompt = f"""You are the Principal Debugger Agent for ForgeAgent.
A build or test failure occurred during automated verification.

Test Output / Stack Trace:
{test_output[-2500:]}

Recent Git Diff:
{git_diff[-1500:] if git_diff else "No staged git diff."}

Recent Changed Files:
{state.changed_files}

Previous Repair Attempts:
{previous_attempts or "None"}

Analyze the failure, identify the exact broken file, and generate the complete fixed file content.
Do NOT delete tests or suppress errors.
Provide a clean JSON response matching:
{{
  "analysis": "Root cause explanation",
  "file_path": "path/to/broken_file.py",
  "fixed_content": "Complete corrected content of the file",
  "explanation": "Why this change fixes the error",
  "confidence": 0.95
}}
"""
        messages = [ChatMessage(role="user", content=prompt)]
        patch = self.llm.generate_structured(messages, RepairPatch)

        if patch.confidence < 0.4:
            state.phase = AgentPhase.BLOCKED
            state.status_message = f"Debugger confidence too low ({patch.confidence:.2f}) to apply fix safely. Human escalation required."
            bus.emit(ForgeEvent(
                event_type=EventType.AGENT_BLOCKED,
                task_id=state.task_id,
                project_id=state.project_id,
                message=state.status_message
            ))
            return False

        # Apply fix
        write_res = self.tools.execute_tool("write_file", file_path=patch.file_path, content=patch.fixed_content)
        if not write_res.success:
            return False

        if patch.file_path not in state.changed_files:
            state.changed_files.append(patch.file_path)

        bus.emit(ForgeEvent(
            event_type=EventType.FIX_APPLIED,
            task_id=state.task_id,
            project_id=state.project_id,
            message=f"Applied fix to {patch.file_path}: {patch.explanation}",
            payload={"file": patch.file_path, "iteration": state.iteration}
        ))
        return True
