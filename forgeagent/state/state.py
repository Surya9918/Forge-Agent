"""
State machine and state representations for ForgeAgent tasks.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class AgentPhase(str, Enum):
    IDLE = "idle"
    PLANNING = "planning"
    ARCHITECTURE = "architecture"
    IMPLEMENTATION = "implementation"
    TESTING = "testing"
    HEALING = "healing"
    REVIEW = "review"
    GIT_OPERATIONS = "git_operations"
    GITHUB_PR = "github_pr"
    CI_MONITORING = "ci_monitoring"
    CI_HEALING = "ci_healing"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    PAUSED = "paused"


class TestSummary(BaseModel):
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    total: int = 0
    output: str = ""
    exit_code: int = 0


class TaskState(BaseModel):
    task_id: str
    project_id: str
    requirement: str = ""
    phase: AgentPhase = AgentPhase.IDLE
    status_message: str = "Initialized"
    iteration: int = 0
    max_iterations: int = 10
    branch: Optional[str] = None
    commit_sha: Optional[str] = None
    pr_number: Optional[int] = None
    pr_url: Optional[str] = None
    tests: TestSummary = Field(default_factory=TestSummary)
    changed_files: List[str] = Field(default_factory=list)
    artifacts: Dict[str, str] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tokens_used: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def update_timestamp(self) -> None:
        self.updated_at = datetime.now(timezone.utc).isoformat()
