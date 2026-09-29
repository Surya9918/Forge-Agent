"""
Tester Agent: orchestrates build & test execution and structures pass/fail metrics.
"""

import re
from pathlib import Path
from forgeagent.agents.base import BaseAgent
from forgeagent.state.state import TaskState, TestSummary, AgentPhase
from forgeagent.intelligence.detector import ProjectDetector
from forgeagent.events.bus import bus
from forgeagent.events.events import ForgeEvent, EventType


class TesterAgent(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(name="Tester", **kwargs)

    def run(self, state: TaskState) -> TestSummary:
        state.phase = AgentPhase.TESTING
        state.status_message = "Running build and test verification"

        bus.emit(ForgeEvent(
            event_type=EventType.TEST_STARTED,
            task_id=state.task_id,
            project_id=state.project_id,
            message="Discovering and executing project tests"
        ))

        stack = ProjectDetector.detect(Path(self.tools.workspace_root))

        # 1. Run build if command present
        if stack.build_command and not stack.build_command.startswith("echo"):
            build_res = self.tools.execute_tool("run_build", build_command=stack.build_command)
            if not build_res.success:
                state.tests = TestSummary(
                    passed=0,
                    failed=1,
                    total=1,
                    output=f"Build Failed:\n{build_res.error or build_res.data.get('stderr')}",
                    exit_code=build_res.data.get("exit_code", 1) if build_res.data else 1
                )
                bus.emit(ForgeEvent(
                    event_type=EventType.TEST_FAILED,
                    task_id=state.task_id,
                    project_id=state.project_id,
                    message="Build step failed"
                ))
                return state.tests

        # 2. Run tests
        test_cmd = stack.test_command
        test_res = self.tools.execute_tool("run_tests", test_command=test_cmd)

        out = (test_res.data.get("stdout", "") if test_res.data else "") + "\n" + (test_res.data.get("stderr", "") if test_res.data else "")
        exit_code = test_res.data.get("exit_code", 0) if test_res.data else 0

        # Parse test metrics from stdout/stderr
        summary = self._parse_test_output(out, exit_code)
        state.tests = summary

        if summary.failed > 0 or not test_res.success:
            bus.emit(ForgeEvent(
                event_type=EventType.TEST_FAILED,
                task_id=state.task_id,
                project_id=state.project_id,
                message=f"Tests failed: {summary.failed} failure(s) detected",
                payload={"passed": summary.passed, "failed": summary.failed}
            ))
        else:
            bus.emit(ForgeEvent(
                event_type=EventType.TEST_PASSED,
                task_id=state.task_id,
                project_id=state.project_id,
                message=f"All tests passed: {summary.passed} passed",
                payload={"passed": summary.passed}
            ))

        return summary

    def _parse_test_output(self, output: str, exit_code: int) -> TestSummary:
        passed = 0
        failed = 0
        total = 0

        # Python unittest: Ran X tests in Ys ... OK or FAILED (failures=A, errors=B)
        ran_match = re.search(r"Ran (\d+) tests?", output)
        if ran_match:
            total = int(ran_match.group(1))
            fail_match = re.search(r"FAILED \((?:failures=(\d+))?(?:, )?(?:errors=(\d+))?\)", output)
            if fail_match:
                f_count = int(fail_match.group(1) or 0)
                e_count = int(fail_match.group(2) or 0)
                failed = f_count + e_count
                passed = max(0, total - failed)
            else:
                passed = total
                failed = 0
        # Jest / Vitest: Tests: X passed, Y failed, Z total
        elif "Tests:" in output:
            p_match = re.search(r"(\d+) passed", output)
            f_match = re.search(r"(\d+) failed", output)
            passed = int(p_match.group(1)) if p_match else 0
            failed = int(f_match.group(1)) if f_match else 0
            total = passed + failed
        else:
            if exit_code == 0:
                passed = 1
                total = 1
            else:
                failed = 1
                total = 1

        return TestSummary(
            passed=passed,
            failed=failed,
            total=total,
            output=output.strip(),
            exit_code=exit_code
        )
