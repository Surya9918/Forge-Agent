"""
Agent Orchestrator: Central conductor executing the autonomous engineering loop end-to-end.
"""

import uuid
from pathlib import Path
from typing import Optional, Dict, Any, List

from forgeagent.config.models import ForgeConfig, AutonomyMode
from forgeagent.llm.base import LLMProvider
from forgeagent.llm.factory import get_llm_provider
from forgeagent.tools.registry import ToolRegistry
from forgeagent.sandbox.manager import SandboxManager
from forgeagent.git.engine import GitEngine
from forgeagent.github.client import GitHubClient
from forgeagent.state.state import TaskState, AgentPhase
from forgeagent.state.persistence import StateManager
from forgeagent.events.bus import bus
from forgeagent.events.events import ForgeEvent, EventType
from forgeagent.ci.generator import CIWorkflowGenerator
from forgeagent.ci.healer import CIHealer
from forgeagent.intelligence.detector import ProjectDetector
from forgeagent.antigravity.artifacts import AntigravityArtifactManager

from forgeagent.agents.planner import PlannerAgent, DevelopmentPlan
from forgeagent.agents.architect import ArchitectAgent
from forgeagent.agents.coder import CoderAgent
from forgeagent.agents.tester import TesterAgent
from forgeagent.agents.debugger import DebuggerAgent
from forgeagent.agents.reviewer import ReviewerAgent
from forgeagent.observability.logger import get_logger

logger = get_logger("forgeagent.orchestrator")


class AgentOrchestrator:
    def __init__(
        self,
        config: Optional[ForgeConfig] = None,
        workspace_root: Optional[str] = None,
        llm_provider: Optional[LLMProvider] = None,
    ):
        self.config = config or ForgeConfig()
        self.workspace_root = workspace_root or self.config.project.workspace
        self.llm = llm_provider or get_llm_provider(self.config.llm)

        # Core subsystems
        self.sandbox_manager = SandboxManager(self.workspace_root, self.config.sandbox)
        self.git_engine = GitEngine(self.workspace_root, self.config.git)
        self.github_client = GitHubClient(self.config.github)
        self.tool_registry = ToolRegistry(
            self.workspace_root,
            self.config,
            self.sandbox_manager,
            self.git_engine,
            self.github_client
        )
        self.state_manager = StateManager(f"{self.workspace_root}/.forge/state")
        self.artifact_manager = AntigravityArtifactManager(self.workspace_root)
        self.ci_healer = CIHealer(self.github_client, self.llm, self.tool_registry, self.config.ci.max_healing_attempts)

        # Specialized agents
        self.planner = PlannerAgent(llm_provider=self.llm, tool_registry=self.tool_registry, config=self.config)
        self.architect = ArchitectAgent(llm_provider=self.llm, tool_registry=self.tool_registry, config=self.config)
        self.coder = CoderAgent(llm_provider=self.llm, tool_registry=self.tool_registry, config=self.config)
        self.tester = TesterAgent(llm_provider=self.llm, tool_registry=self.tool_registry, config=self.config)
        self.debugger = DebuggerAgent(llm_provider=self.llm, tool_registry=self.tool_registry, config=self.config)
        self.reviewer = ReviewerAgent(llm_provider=self.llm, tool_registry=self.tool_registry, config=self.config)

    def run(self, requirement: str, project_name: Optional[str] = None) -> TaskState:
        """Run the full autonomous software engineering loop."""
        proj_name = project_name or self.config.project.name or "project"
        task_id = str(uuid.uuid4())[:8]

        state = TaskState(
            task_id=task_id,
            project_id=proj_name,
            requirement=requirement,
            max_iterations=self.config.agent.max_iterations,
        )
        self.state_manager.save(state)

        bus.emit(ForgeEvent(
            event_type=EventType.PROJECT_CREATED,
            task_id=task_id,
            project_id=proj_name,
            message=f"Starting autonomous software engineering project '{proj_name}'"
        ))

        try:
            # Step 1: Planning
            plan = self.planner.run(state, requirement)
            self.artifact_manager.write_implementation_plan(plan)
            self.state_manager.save(state)

            # Step 2: Architecture
            self.architect.run(state, plan)
            self.state_manager.save(state)

            # Step 3: Git setup
            branch_name = f"{self.config.git.branch_prefix}{proj_name}"
            state.branch = branch_name
            if not self.git_engine.is_repo():
                self.git_engine.initialize_repository()
                self.git_engine.create_branch(branch_name, checkout=True)
            else:
                try:
                    self.git_engine.create_branch(branch_name, checkout=True)
                except Exception:
                    self.git_engine.checkout_branch(branch_name)

            # Step 4: Code Implementation
            for task in plan.tasks:
                self.coder.run(state, task, plan)
                self.state_manager.save(state)

            # Step 5: Test and Build Verification
            test_summary = self.tester.run(state)
            self.state_manager.save(state)

            # Step 6: Self-Healing Loop
            previous_fixes = []
            while test_summary.failed > 0 and state.iteration < self.config.agent.max_iterations:
                logger.info(f"Self-healing: fixing {test_summary.failed} test failures (iteration {state.iteration + 1})")
                healed = self.debugger.run(state, test_output=test_summary.output, previous_attempts=previous_fixes)
                if not healed:
                    logger.warning("Debugger could not apply fix or stopped.")
                    break
                previous_fixes.append(f"Iteration {state.iteration}: applied fix")
                # Retest
                test_summary = self.tester.run(state)
                self.state_manager.save(state)

            # Step 7: Code & Security Review
            self.reviewer.run(state)

            # Step 8: CI Workflow Generation
            stack = ProjectDetector.detect(Path(self.workspace_root))
            workflow_yaml = CIWorkflowGenerator.generate_workflow(stack, proj_name)
            self.tool_registry.execute_tool("write_file", file_path=self.config.ci.workflow_path, content=workflow_yaml)

            # Step 9: Git Commit
            if self.config.git.auto_commit:
                state.phase = AgentPhase.GIT_OPERATIONS
                self.git_engine.stage_files()
                commit_msg = f"feat({proj_name}): complete autonomous implementation\n\nRequirement: {requirement}"
                sha = self.git_engine.commit(commit_msg)
                state.commit_sha = sha
                bus.emit(ForgeEvent(
                    event_type=EventType.COMMIT_CREATED,
                    task_id=task_id,
                    project_id=proj_name,
                    message=f"Created commit {sha[:7] if sha else 'N/A'}"
                ))

            # Step 10: GitHub Repo, Push & Pull Request
            if self.config.github.enabled:
                state.phase = AgentPhase.GITHUB_PR
                if self.config.github.create_repository:
                    repo_res = self.github_client.create_repository(
                        name=proj_name,
                        description=requirement,
                        private=(self.config.github.visibility == "private")
                    )
                if self.config.git.auto_push:
                    self.git_engine.push(branch=branch_name)
                    bus.emit(ForgeEvent(
                        event_type=EventType.PUSH_COMPLETED,
                        task_id=task_id,
                        project_id=proj_name,
                        message=f"Pushed branch {branch_name} to remote"
                    ))

                if self.config.github.create_pull_request:
                    pr = self.github_client.create_pull_request(
                        repo=proj_name,
                        title=f"feat: {proj_name} autonomous implementation",
                        head=branch_name,
                        base=self.config.git.default_branch,
                        body=f"Autonomous Pull Request generated by ForgeAgent.\n\n### Requirement\n{requirement}\n\n### Tests\n- Passed: {test_summary.passed}\n- Failed: {test_summary.failed}"
                    )
                    state.pr_number = pr.get("number")
                    state.pr_url = pr.get("html_url")
                    bus.emit(ForgeEvent(
                        event_type=EventType.PR_CREATED,
                        task_id=task_id,
                        project_id=proj_name,
                        message=f"Created Pull Request #{state.pr_number}: {state.pr_url}"
                    ))

            # Step 11: CI Monitoring & Healing
            if self.config.ci.enabled and self.config.ci.self_healing:
                state.phase = AgentPhase.CI_MONITORING
                self.ci_healer.monitor_and_heal(state, proj_name, branch_name)

            # Step 12: Artifacts & Final Report
            self.artifact_manager.write_walkthrough(state)
            self.artifact_manager.write_verification_report(state)

            state.phase = AgentPhase.COMPLETED
            state.status_message = "All tasks autonomously completed and verified."
            self.state_manager.save(state)

            bus.emit(ForgeEvent(
                event_type=EventType.PROJECT_COMPLETED,
                task_id=task_id,
                project_id=proj_name,
                message="Autonomous engineering pipeline finished successfully."
            ))

        except Exception as e:
            logger.error(f"Orchestrator error: {e}", exc_info=True)
            state.phase = AgentPhase.BLOCKED
            state.status_message = f"Error during execution: {e}"
            self.state_manager.save(state)
            bus.emit(ForgeEvent(
                event_type=EventType.AGENT_BLOCKED,
                task_id=task_id,
                project_id=proj_name,
                message=str(e)
            ))

        return state
