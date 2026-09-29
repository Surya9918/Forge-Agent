"""
Planner Agent: transforms user requirements into structured task plans and acceptance criteria.
"""

import json
import uuid
from typing import List, Dict, Any, Optional
from forgeagent.agents.base import BaseAgent
from forgeagent.llm.base import ChatMessage
from forgeagent.state.state import TaskState, AgentPhase
from forgeagent.compat import model_to_dict
from forgeagent.events.bus import bus
from forgeagent.events.events import ForgeEvent, EventType
from forgeagent.domain.models import PlanTask, DevelopmentPlan


class PlannerAgent(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(name="Planner", **kwargs)

    def run(self, state: Optional[TaskState], requirement: str = "") -> DevelopmentPlan:
        if state is None:
            state = TaskState(task_id=str(uuid.uuid4())[:8], project_id="plan-project")

        state.phase = AgentPhase.PLANNING
        state.status_message = "Analyzing requirement and formulating development plan"
        req = requirement or state.requirement

        bus.emit(ForgeEvent(
            event_type=EventType.PLAN_CREATED,
            task_id=state.task_id,
            project_id=state.project_id,
            message=f"Planning requirement: '{req[:60]}...'"
        ))

        prompt = f"""You are the Principal Software Architect & Planner Agent for ForgeAgent.
Analyze the following user requirement and produce a structured, production-grade engineering plan.

User Requirement:
"{req}"

Break the work into concrete, verifiable tasks.
Provide a clean JSON response matching this schema:
{{
  "project": "project-slug",
  "description": "high-level project purpose",
  "stack": {{
    "frontend": "framework or none",
    "backend": "framework or python/node",
    "database": "database or none",
    "test_runner": "unittest/pytest/npm"
  }},
  "tasks": [
    {{
      "id": "task-1",
      "title": "Setup project and dependencies",
      "description": "Initialize package files, configs, and directory layout",
      "target_files": ["requirements.txt", "README.md"],
      "dependencies": []
    }},
    {{
      "id": "task-2",
      "title": "Implement core application domain",
      "description": "Implement models, business logic, and API/CLI",
      "target_files": ["app.py"],
      "dependencies": ["task-1"]
    }},
    {{
      "id": "task-3",
      "title": "Implement comprehensive test suite",
      "description": "Write automated unit tests verifying functionality",
      "target_files": ["tests/test_app.py"],
      "dependencies": ["task-2"]
    }}
  ],
  "acceptance_criteria": [
    "Clean build without syntax errors",
    "All unit tests pass",
    "Git repository initialized with clean history"
  ]
}}
"""
        messages = [ChatMessage(role="user", content=prompt)]
        plan = self.llm.generate_structured(messages, DevelopmentPlan)

        state.metadata["plan"] = model_to_dict(plan)
        state.metadata["total_tasks"] = len(plan.tasks)
        return plan
