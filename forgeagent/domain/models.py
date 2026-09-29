"""
Canonical Domain Models for ForgeAgent.
Unifies Planner, Coder, Debugger, and Orchestrator contracts.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class PlanTask(BaseModel):
    id: str
    title: str
    description: str
    target_files: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    status: str = "pending"


class DevelopmentPlan(BaseModel):
    project: str
    description: str = ""
    stack: Dict[str, str] = Field(default_factory=dict)
    tasks: List[PlanTask] = Field(default_factory=list)
    acceptance_criteria: List[str] = Field(default_factory=list)


class CodeAction(BaseModel):
    file_path: str
    action: str = "write"  # write, edit, delete, append
    content: str = ""
    old_content: Optional[str] = None
    explanation: str = ""


class TaskImplementation(BaseModel):
    task_id: str
    actions: List[CodeAction] = Field(default_factory=list)
    notes: str = ""
    status: str = "completed"


class RepairPatch(BaseModel):
    file_path: str
    operation: str = "replace"  # replace, edit, append, delete
    fixed_content: str = ""
    old_content: Optional[str] = None
    analysis: str = ""
    explanation: str = ""
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)

    @property
    def is_valid(self) -> bool:
        return bool(self.file_path and (self.fixed_content or self.operation == "delete"))
