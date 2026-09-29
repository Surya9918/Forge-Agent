"""
Real End-to-End Autonomous Software Engineering Verification.
Executes full real pipeline: Plan -> Scaffold -> Real Code -> Real Test Execution ->
Failure Injection -> Autonomous Self-Healing -> Verified Retest -> Real Git Init & Commit ->
Antigravity Artifacts Generation.
"""

import unittest
import tempfile
import subprocess
from pathlib import Path
from typing import List

from forgeagent.config.models import ForgeConfig, AutonomyMode
from forgeagent.llm.base import LLMProvider, ChatMessage, LLMResponse, T
from forgeagent.domain.models import PlanTask, DevelopmentPlan, CodeAction, TaskImplementation, RepairPatch
from forgeagent.agents.orchestrator import AgentOrchestrator
from forgeagent.state.state import AgentPhase


class RealE2EProvider(LLMProvider):
    """
    Deterministic provider generating real executable Python code and real repairs
    for the Python CLI Calculator project.
    """
    def __init__(self):
        super().__init__(model="real-e2e-engine")
        self.intentionally_inject_bug = True

    def generate(self, messages: List[ChatMessage], **kwargs) -> LLMResponse:
        last = messages[-1].content
        if "architect" in last.lower():
            return LLMResponse(content="# Calculator Architecture\n\n- CLI Interface\n- Math Operations\n- Test Suite")
        elif "review" in last.lower():
            return LLMResponse(content="# Code Review\n\n- Correctness: Verified\n- Tests: Passing\n- Status: Approved")
        return LLMResponse(content="OK")

    def generate_structured(self, messages: List[ChatMessage], schema: type, **kwargs):
        schema_name = getattr(schema, "__name__", "")
        if schema_name == "DevelopmentPlan":
            return DevelopmentPlan(
                project="calculator-cli",
                description="Production-grade CLI calculator in Python",
                stack={"backend": "python", "test_runner": "unittest"},
                tasks=[
                    PlanTask(
                        id="task-1",
                        title="Implement Calculator Logic and Tests",
                        description="Implement add, subtract, multiply, divide and unit tests",
                        target_files=["calculator.py", "tests/test_calculator.py"],
                        dependencies=[]
                    )
                ],
                acceptance_criteria=["All math operations work", "Unit tests pass"]
            )
        elif schema_name == "TaskImplementation":
            # Real executable Python code
            calc_code = """class Calculator:
    @staticmethod
    def add(a: float, b: float) -> float:
        # Intentionally injected bug: subtraction instead of addition
        return a - b

    @staticmethod
    def multiply(a: float, b: float) -> float:
        return a * b
"""
            test_code = """import unittest
from calculator import Calculator

class TestCalculator(unittest.TestCase):
    def test_add(self):
        self.assertEqual(Calculator.add(2, 3), 5)

    def test_multiply(self):
        self.assertEqual(Calculator.multiply(4, 5), 20)

if __name__ == '__main__':
    unittest.main()
"""
            return TaskImplementation(
                task_id="task-1",
                actions=[
                    CodeAction(file_path="calculator.py", action="write", content=calc_code, explanation="Calculator implementation"),
                    CodeAction(file_path="tests/__init__.py", action="write", content="", explanation="Package init"),
                    CodeAction(file_path="tests/test_calculator.py", action="write", content=test_code, explanation="Calculator test suite"),
                ],
                notes="Generated initial calculator code with intentional defect for self-healing validation",
                status="completed"
            )
        elif schema_name == "RepairPatch":
            # Real repair patch correcting the bug
            repaired_calc_code = """class Calculator:
    @staticmethod
    def add(a: float, b: float) -> float:
        return a + b

    @staticmethod
    def multiply(a: float, b: float) -> float:
        return a * b
"""
            return RepairPatch(
                file_path="calculator.py",
                operation="replace",
                fixed_content=repaired_calc_code,
                analysis="Root cause: Calculator.add was performing subtraction (a - b) instead of addition (a + b).",
                explanation="Fixed addition arithmetic operator.",
                confidence=0.99
            )
        raise ValueError(f"Unknown schema requested: {schema}")


class TestRealPipelineE2E(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.workspace = self.tmpdir.name

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_real_autonomous_pipeline_with_self_healing(self):
        config = ForgeConfig()
        config.project.name = "real-calc"
        config.project.workspace = self.workspace
        config.agent.mode = AutonomyMode.AUTONOMOUS
        config.agent.max_iterations = 5

        provider = RealE2EProvider()
        orchestrator = AgentOrchestrator(
            config=config,
            workspace_root=self.workspace,
            llm_provider=provider
        )

        # Execute full autonomous loop
        state = orchestrator.run(
            requirement="Build a Python CLI calculator supporting addition and multiplication with automated tests",
            project_name="real-calc"
        )

        # 1. Verify pipeline reached COMPLETED state
        self.assertEqual(state.phase, AgentPhase.COMPLETED)
        self.assertEqual(state.status_message, "All tasks autonomously completed and verified.")

        # 2. Verify self-healing triggered and succeeded
        self.assertGreaterEqual(state.iteration, 1, "Self-healing loop should have run at least 1 iteration to fix injected bug")
        self.assertEqual(state.tests.failed, 0, "All tests must pass after self-healing")
        self.assertGreaterEqual(state.tests.passed, 2, "Both test_add and test_multiply must pass")

        # 3. Verify real files were written to workspace
        ws = Path(self.workspace)
        calc_path = ws / "calculator.py"
        test_path = ws / "tests" / "test_calculator.py"
        self.assertTrue(calc_path.is_file(), "calculator.py must exist")
        self.assertTrue(test_path.is_file(), "test_calculator.py must exist")

        # 4. Verify repaired file content works when executed with real Python interpreter
        repaired_text = calc_path.read_text(encoding="utf-8")
        self.assertIn("return a + b", repaired_text, "calculator.py must contain the repaired addition logic")

        # Run real unittest in real subprocess to double check independent pass
        import sys
        proc = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
            cwd=str(ws),
            capture_output=True,
            text=True
        )
        self.assertEqual(proc.returncode, 0, f"Real unittest execution failed:\n{proc.stderr}\n{proc.stdout}")
        self.assertIn("Ran 2 tests", proc.stderr + proc.stdout)
        self.assertIn("OK", proc.stderr + proc.stdout)

        # 5. Verify real Git repository was initialized and committed
        self.assertTrue((ws / ".git").is_dir(), "Real Git repository must be initialized")
        git_log = subprocess.run(
            ["git", "log", "--oneline"],
            cwd=str(ws),
            capture_output=True,
            text=True
        )
        self.assertEqual(git_log.returncode, 0)
        self.assertIn("feat(real-calc): complete autonomous implementation", git_log.stdout)

        # 6. Verify real Antigravity Artifacts were written to disk
        artifacts_dir = ws / ".agents" / "artifacts"
        self.assertTrue(artifacts_dir.is_dir())
        self.assertTrue((artifacts_dir / "implementation_plan.md").is_file())
        self.assertTrue((artifacts_dir / "walkthrough.md").is_file())
        self.assertTrue((artifacts_dir / "verification_report.md").is_file())

        plan_content = (artifacts_dir / "implementation_plan.md").read_text()
        self.assertIn("calculator-cli", plan_content)
        self.assertIn("Implement Calculator Logic and Tests", plan_content)

        verif_content = (artifacts_dir / "verification_report.md").read_text()
        self.assertIn("PASSED", verif_content)


if __name__ == "__main__":
    unittest.main()
