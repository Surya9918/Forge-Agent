"""
Event definitions for ForgeAgent.
"""

from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class EventType(str, Enum):
    PROJECT_CREATED = "PROJECT_CREATED"
    PLAN_CREATED = "PLAN_CREATED"
    ARCHITECTURE_CREATED = "ARCHITECTURE_CREATED"
    TASK_STARTED = "TASK_STARTED"
    TASK_COMPLETED = "TASK_COMPLETED"
    FILE_CREATED = "FILE_CREATED"
    FILE_MODIFIED = "FILE_MODIFIED"
    COMMAND_STARTED = "COMMAND_STARTED"
    COMMAND_COMPLETED = "COMMAND_COMPLETED"
    TEST_STARTED = "TEST_STARTED"
    TEST_FAILED = "TEST_FAILED"
    TEST_PASSED = "TEST_PASSED"
    FIX_STARTED = "FIX_STARTED"
    FIX_APPLIED = "FIX_APPLIED"
    COMMIT_CREATED = "COMMIT_CREATED"
    PUSH_COMPLETED = "PUSH_COMPLETED"
    CI_STARTED = "CI_STARTED"
    CI_FAILED = "CI_FAILED"
    CI_PASSED = "CI_PASSED"
    PR_CREATED = "PR_CREATED"
    PROJECT_COMPLETED = "PROJECT_COMPLETED"
    AGENT_BLOCKED = "AGENT_BLOCKED"
    HUMAN_APPROVAL_REQUESTED = "HUMAN_APPROVAL_REQUESTED"
    HUMAN_APPROVAL_GRANTED = "HUMAN_APPROVAL_GRANTED"
    HUMAN_APPROVAL_DENIED = "HUMAN_APPROVAL_DENIED"


class ForgeEvent(BaseModel):
    event_type: EventType
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    task_id: Optional[str] = None
    project_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    message: str = ""
