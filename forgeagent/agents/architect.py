"""
Architect Agent: produces formal architectural specifications and persists them to docs/architecture.md.
"""

from pathlib import Path
from forgeagent.agents.base import BaseAgent
from forgeagent.agents.planner import DevelopmentPlan
from forgeagent.llm.base import ChatMessage
from forgeagent.state.state import TaskState, AgentPhase
from forgeagent.events.bus import bus
from forgeagent.events.events import ForgeEvent, EventType


class ArchitectAgent(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(name="Architect", **kwargs)

    def run(self, state: TaskState, plan: DevelopmentPlan) -> str:
        state.phase = AgentPhase.ARCHITECTURE
        state.status_message = "Designing system architecture and technical specifications"

        prompt = f"""You are the Lead Systems Architect for ForgeAgent.
Based on the plan below, generate a comprehensive architectural specification in Markdown.

Plan:
Project: {plan.project}
Description: {plan.description}
Stack: {plan.stack}
Tasks: {[t.title for t in plan.tasks]}
Acceptance Criteria: {plan.acceptance_criteria}

Your architecture document MUST cover:
1. Executive Summary & Problem Domain
2. System Architecture & Component Diagram
3. Complete Directory Structure
4. Data Models & Database Schemas
5. API Specifications & Data Contracts
6. Security Requirements & Threat Mitigation
7. Testing & Verification Strategy
8. Deployment & CI/CD Pipeline
9. Architectural Decisions & Tradeoffs
"""
        messages = [ChatMessage(role="user", content=prompt)]
        resp = self.llm.generate(messages)
        arch_content = resp.content

        # Write to docs/architecture.md
        self.tools.execute_tool("write_file", file_path="docs/architecture.md", content=arch_content)
        state.artifacts["architecture"] = "docs/architecture.md"

        bus.emit(ForgeEvent(
            event_type=EventType.ARCHITECTURE_CREATED,
            task_id=state.task_id,
            project_id=state.project_id,
            message="System architecture document created at docs/architecture.md"
        ))
        return arch_content
