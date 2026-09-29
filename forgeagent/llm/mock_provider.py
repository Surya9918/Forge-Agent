"""
Mock LLM Provider for hermetic testing, offline benchmarks, and fallback evaluation.
"""

import json
from typing import List, Dict, Any, Type, Optional, Callable
from forgeagent.llm.base import LLMProvider, ChatMessage, LLMResponse, T
from forgeagent.compat import model_from_dict, model_construct


class MockProvider(LLMProvider):
    def __init__(
        self,
        model: str = "mock-model",
        custom_responder: Optional[Callable[[List[ChatMessage]], str]] = None,
        **kwargs
    ):
        super().__init__(model=model, **kwargs)
        self.custom_responder = custom_responder
        self.call_history: List[List[ChatMessage]] = []

    def generate(self, messages: List[ChatMessage], **kwargs) -> LLMResponse:
        self.call_history.append(messages)
        self.total_prompt_tokens += 100
        self.total_completion_tokens += 150

        if self.custom_responder:
            text = self.custom_responder(messages)
            return LLMResponse(
                content=text,
                tokens_prompt=100,
                tokens_completion=150,
                total_tokens=250,
                model=self.model,
            )

        last_msg = messages[-1].content if messages else ""

        if "Plan" in last_msg or "plan" in last_msg or "requirement" in last_msg.lower():
            content = json.dumps({
                "project": "task-manager",
                "description": "High-level software project plan",
                "stack": {"frontend": "React", "backend": "Node.js", "database": "PostgreSQL"},
                "tasks": [
                    {"id": "task-1", "title": "Setup project structure", "description": "Initialize package.json and layout", "target_files": ["package.json"], "dependencies": []},
                    {"id": "task-2", "title": "Implement core domain", "description": "Create business logic and routes", "target_files": ["app.py"], "dependencies": ["task-1"]},
                    {"id": "task-3", "title": "Add test suite", "description": "Write comprehensive unit tests", "target_files": ["tests/test_app.py"], "dependencies": ["task-2"]}
                ],
                "acceptance_criteria": ["Project builds cleanly", "All unit tests pass", "Git commits created"]
            })
        elif "fix" in last_msg.lower() or "repair" in last_msg.lower():
            content = json.dumps({
                "analysis": "Identified syntax error in test assertion",
                "file_path": "test_app.py",
                "fixed_content": "# Fixed implementation\ndef test_add():\n    assert 1 + 1 == 2\n",
                "explanation": "Corrected assertion condition to ensure test passes",
                "confidence": 0.95
            })
        elif "review" in last_msg.lower():
            content = "# Code Review Report\n\n- Correctness: High\n- Security: No exposed secrets detected\n- Performance: Optimal\n- Tests: 100% passing"
        else:
            content = "Mock response from ForgeAgent LLM Provider"

        return LLMResponse(
            content=content,
            tokens_prompt=100,
            tokens_completion=150,
            total_tokens=250,
            model=self.model,
        )

    def generate_structured(self, messages: List[ChatMessage], schema: Type[T], **kwargs) -> T:
        self.call_history.append(messages)
        self.total_prompt_tokens += 100
        self.total_completion_tokens += 150

        if self.custom_responder:
            text = self.custom_responder(messages)
            try:
                data = json.loads(text)
                return model_from_dict(schema, data)
            except Exception:
                pass

        schema_name = schema.__name__
        if schema_name == "DevelopmentPlan":
            data = {
                "project": "task-manager",
                "description": "High-level software project plan",
                "stack": {"frontend": "React", "backend": "Node.js", "database": "PostgreSQL"},
                "tasks": [
                    {"id": "task-1", "title": "Setup project structure", "description": "Init", "target_files": ["package.json"], "dependencies": []},
                    {"id": "task-2", "title": "Implement core", "description": "Logic", "target_files": ["app.py"], "dependencies": ["task-1"]}
                ],
                "acceptance_criteria": ["Project builds"]
            }
        elif schema_name == "TaskImplementation":
            data = {
                "task_id": "mock-task-id",
                "actions": [
                    {
                        "file_path": "tests/test_app.py",
                        "action": "write",
                        "content": "import unittest\nclass TestApp(unittest.TestCase):\n    def test_mock(self): pass\n",
                        "explanation": "Mock implemented"
                    },
                    {
                        "file_path": "tests/__init__.py",
                        "action": "write",
                        "content": "",
                        "explanation": "Init"
                    }
                ],
                "notes": "Mock implemented"
            }
        elif schema_name == "RepairPatch":
            data = {
                "analysis": "Syntax error",
                "file_path": "tests/test_app.py",
                "fixed_content": "import unittest\nclass TestApp(unittest.TestCase):\n    def test_add(self):\n        self.assertEqual(1, 1)\n",
                "explanation": "Fixed assertion",
                "confidence": 0.95
            }
        else:
            data = {}
            
        return model_from_dict(schema, data)
