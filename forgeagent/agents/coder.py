"""
Coding Agent: reads existing codebase context and implements tasks incrementally.
"""

from typing import List, Dict, Any
from forgeagent.agents.base import BaseAgent
from forgeagent.domain.models import PlanTask, DevelopmentPlan, CodeAction, TaskImplementation
from forgeagent.llm.base import ChatMessage
from forgeagent.state.state import TaskState, AgentPhase
from forgeagent.intelligence.analyzer import RepoAnalyzer
from forgeagent.events.bus import bus
from forgeagent.events.events import ForgeEvent, EventType


class CoderAgent(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(name="Coder", **kwargs)

    def run(self, state: TaskState, task: PlanTask, plan: DevelopmentPlan) -> TaskImplementation:
        state.phase = AgentPhase.IMPLEMENTATION
        state.status_message = f"Implementing task: {task.title}"

        bus.emit(ForgeEvent(
            event_type=EventType.TASK_STARTED,
            task_id=state.task_id,
            project_id=state.project_id,
            message=f"Starting implementation of '{task.title}'"
        ))

        analyzer = RepoAnalyzer(self.tools.workspace_root)
        existing_context = analyzer.get_context_for_task([task.title] + task.target_files)

        prompt = f"""You are the Senior Software Engineer (Coder Agent) for ForgeAgent.
Implement the following engineering task adhering to best practices and project conventions.

Project: {plan.project}
Task ID: {task.id}
Title: {task.title}
Description: {task.description}
Target Files: {task.target_files}

Existing Code Context:
{existing_context or "No relevant existing files yet (greenfield)."}

Return a structured TaskImplementation JSON matching this schema:
{{
  "task_id": "{task.id}",
  "actions": [
    {{
      "file_path": "path/to/file",
      "action": "write",
      "content": "Full source code here...",
      "explanation": "Why this code was written"
    }}
  ],
  "notes": "Implementation summary"
}}
"""
        messages = [ChatMessage(role="user", content=prompt)]
        implementation = self.llm.generate_structured(messages, TaskImplementation)

        # Apply each code action
        for act in implementation.actions:
            if act.action in ["write", "create"]:
                res = self.tools.execute_tool("write_file", file_path=act.file_path, content=act.content)
                if act.file_path not in state.changed_files:
                    state.changed_files.append(act.file_path)
                bus.emit(ForgeEvent(
                    event_type=EventType.FILE_CREATED,
                    task_id=state.task_id,
                    project_id=state.project_id,
                    message=f"Created/Updated {act.file_path}: {act.explanation}"
                ))
            elif act.action == "delete":
                self.tools.execute_tool("delete_file", file_path=act.file_path)

        bus.emit(ForgeEvent(
            event_type=EventType.TASK_COMPLETED,
            task_id=state.task_id,
            project_id=state.project_id,
            message=f"Completed task '{task.title}'"
        ))
        return implementation
