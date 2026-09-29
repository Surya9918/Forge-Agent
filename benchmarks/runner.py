"""
ForgeAgent Benchmark Evaluation Suite (Levels 1 to 7).
Tracks: success rate, iterations, time, tests passed, files changed, commits, tokens, failure categories.
"""

import time
import json
import tempfile
from pathlib import Path
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from forgeagent.config.models import ForgeConfig
from forgeagent.agents.orchestrator import AgentOrchestrator
from forgeagent.llm.mock_provider import MockProvider
from forgeagent.state.state import AgentPhase


class BenchmarkResult(BaseModel):
    level: int
    name: str
    requirement: str
    success: bool
    iterations: int
    duration_seconds: float
    tests_passed: int
    tests_failed: int
    files_changed: int
    commit_sha: str = ""
    pr_url: str = ""
    error: str = ""


BENCHMARKS = [
    {
        "level": 1,
        "name": "Simple Python CLI",
        "requirement": "Build a command-line utility in Python to parse CSV files and calculate column summary statistics (mean, median, min, max)."
    },
    {
        "level": 2,
        "name": "REST API",
        "requirement": "Build a REST API in Node.js/Express for an inventory management service with CRUD endpoints and input validation."
    },
    {
        "level": 3,
        "name": "React + API",
        "requirement": "Build a React component dashboard connected to a backend tasks endpoint with filtering and optimistic state updates."
    },
    {
        "level": 4,
        "name": "Full-Stack Application",
        "requirement": "Build a full-stack task management application with React frontend, Node.js backend, PostgreSQL schema migrations, and JWT auth."
    },
    {
        "level": 5,
        "name": "Existing Broken Repository",
        "requirement": "Analyze an existing repository with failing edge-case assertions in the string tokenizer, localize the bug, and repair it."
    },
    {
        "level": 6,
        "name": "CI Failure Recovery",
        "requirement": "Detect a simulated GitHub Actions CI failure caused by an unpinned dependency mismatch, diagnose the CI logs, and commit a fix."
    },
    {
        "level": 7,
        "name": "Multi-Service Application",
        "requirement": "Design and scaffold a multi-service event-driven architecture with an order producer service, payment consumer worker, and docker-compose orchestration."
    }
]


class BenchmarkRunner:
    def __init__(self):
        self.results: List[BenchmarkResult] = []

    def run_all(self) -> List[BenchmarkResult]:
        print("================================================================================")
        print("                 FORGEAGENT BENCHMARK EVALUATION SUITE                          ")
        print("================================================================================")

        for bench in BENCHMARKS:
            print(f"\n[Level {bench['level']}] {bench['name']}...")
            start_time = time.time()
            with tempfile.TemporaryDirectory() as tmp_workspace:
                config = ForgeConfig()
                config.project.name = f"benchmark-lvl{bench['level']}"
                config.project.workspace = tmp_workspace
                llm = MockProvider()

                orchestrator = AgentOrchestrator(
                    config=config,
                    workspace_root=tmp_workspace,
                    llm_provider=llm
                )

                try:
                    state = orchestrator.run(
                        requirement=bench["requirement"],
                        project_name=f"bench-lvl{bench['level']}"
                    )
                    duration = round(time.time() - start_time, 2)
                    success = (state.phase == AgentPhase.COMPLETED and state.tests.failed == 0)

                    res = BenchmarkResult(
                        level=bench["level"],
                        name=bench["name"],
                        requirement=bench["requirement"],
                        success=success,
                        iterations=state.iteration,
                        duration_seconds=duration,
                        tests_passed=state.tests.passed,
                        tests_failed=state.tests.failed,
                        files_changed=len(state.changed_files),
                        commit_sha=state.commit_sha or "N/A",
                        pr_url=state.pr_url or "N/A",
                        error=state.status_message if not success else ""
                    )
                    self.results.append(res)
                    status_icon = "✓ PASS" if success else "✗ FAIL"
                    print(f"  Result: {status_icon} | Duration: {duration}s | Tests: {state.tests.passed} passed | Iterations: {state.iteration}")
                except Exception as e:
                    duration = round(time.time() - start_time, 2)
                    self.results.append(BenchmarkResult(
                        level=bench["level"],
                        name=bench["name"],
                        requirement=bench["requirement"],
                        success=False,
                        iterations=0,
                        duration_seconds=duration,
                        tests_passed=0,
                        tests_failed=1,
                        files_changed=0,
                        error=str(e)
                    ))
                    print(f"  Result: ✗ ERROR: {e}")

        self._print_summary()
        return self.results

    def _print_summary(self):
        print("\n" + "="*80)
        print("                         BENCHMARK RESULTS SUMMARY                              ")
        print("="*80)
        passed_count = sum(1 for r in self.results if r.success)
        total_count = len(self.results)
        print(f"Total Evaluated: {total_count} | Succeeded: {passed_count} | Success Rate: {(passed_count/total_count)*100:.1f}%\n")

        print(f"{'Level':<7} | {'Name':<28} | {'Status':<7} | {'Time(s)':<8} | {'Tests':<8} | {'PR Created':<12}")
        print("-" * 80)
        for r in self.results:
            status = "PASS" if r.success else "FAIL"
            has_pr = "Yes" if r.pr_url and r.pr_url != "N/A" else "No"
            print(f"Lvl {r.level:<3} | {r.name:<28} | {status:<7} | {r.duration_seconds:<8} | {r.tests_passed:<8} | {has_pr:<12}")
        print("="*80)


if __name__ == "__main__":
    runner = BenchmarkRunner()
    runner.run_all()
