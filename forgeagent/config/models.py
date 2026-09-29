"""
Configuration models for ForgeAgent.
"""

from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class AutonomyMode(str, Enum):
    ASSISTED = "assisted"
    AUTONOMOUS = "autonomous"
    SAFE_PRODUCTION = "safe_production"


class LLMConfig(BaseModel):
    provider: str = Field(default="mock", description="LLM provider: google, openai, anthropic, ollama, mock")
    model: str = Field(default="gemini-2.0-flash", description="Model name")
    api_key_env: str = Field(default="GEMINI_API_KEY", description="Environment variable holding API key")
    api_key: Optional[str] = Field(default=None, description="Direct API key (prefer environment variable)")
    temperature: float = Field(default=0.2, description="Sampling temperature")
    max_tokens: int = Field(default=8192, description="Maximum tokens per response")
    timeout_seconds: int = Field(default=60, description="Request timeout")
    max_retries: int = Field(default=3, description="Retry attempts on transient failure")
    fallback_models: List[str] = Field(default_factory=list, description="Fallback models on failure")


class ProjectConfig(BaseModel):
    name: str = Field(default="unnamed-project", description="Project name")
    workspace: str = Field(default="./workspace", description="Local workspace directory")
    description: Optional[str] = Field(default="", description="Project description")
    stack: Dict[str, str] = Field(default_factory=dict, description="Tech stack mapping")


class AgentConfig(BaseModel):
    mode: AutonomyMode = Field(default=AutonomyMode.AUTONOMOUS, description="Autonomy mode")
    max_iterations: int = Field(default=10, description="Max repair / self-healing iterations")
    max_runtime_minutes: int = Field(default=120, description="Max execution time in minutes")
    max_files_changed: int = Field(default=50, description="Maximum files modified per run")
    token_budget: int = Field(default=500_000, description="Max token spend limit")


class GitConfig(BaseModel):
    auto_commit: bool = Field(default=True, description="Automatically commit on verified changes")
    auto_push: bool = Field(default=True, description="Automatically push to remote branch")
    protected_branches: List[str] = Field(
        default_factory=lambda: ["main", "master", "production", "release"],
        description="Branches protected from direct commits / force push"
    )
    default_branch: str = Field(default="main", description="Default branch name")
    branch_prefix: str = Field(default="forgeagent/", description="Prefix for feature branches")


class GitHubConfig(BaseModel):
    enabled: bool = Field(default=True, description="Enable GitHub integration")
    token_env: str = Field(default="GITHUB_TOKEN", description="Env variable for GitHub PAT or App token")
    create_repository: bool = Field(default=True, description="Auto-create repository if not found")
    create_pull_request: bool = Field(default=True, description="Auto-create pull request on completion")
    visibility: str = Field(default="private", description="Repo visibility: private or public")
    owner: Optional[str] = Field(default=None, description="GitHub user or org owner")


class SandboxConfig(BaseModel):
    enabled: bool = Field(default=True, description="Enforce execution sandboxing")
    runtime: str = Field(default="local_process", description="Sandbox runtime: docker or local_process")
    timeout_seconds: int = Field(default=120, description="Process execution timeout")
    memory_limit_mb: int = Field(default=2048, description="Max memory in MB (Docker only)")
    cpu_limit: float = Field(default=2.0, description="Max CPU cores (Docker only)")


class CIConfig(BaseModel):
    enabled: bool = Field(default=True, description="Enable CI workflow generation and monitoring")
    self_healing: bool = Field(default=True, description="Auto-heal CI build and test failures")
    max_healing_attempts: int = Field(default=5, description="Max attempts to fix remote CI failures")
    workflow_path: str = Field(default=".github/workflows/ci.yml", description="Generated CI workflow location")


class SecurityConfig(BaseModel):
    require_approval_for: List[str] = Field(
        default_factory=lambda: [
            "repository_delete",
            "force_push",
            "production_deploy",
            "secret_access",
            "system_file_write"
        ],
        description="Actions requiring explicit human approval"
    )
    allowed_commands: List[str] = Field(
        default_factory=lambda: [
            "npm", "npx", "node", "yarn", "pnpm",
            "python", "python3", "pytest", "pip", "poetry",
            "mvn", "gradle", "go", "cargo",
            "git", "echo", "cat", "ls", "pwd", "mkdir"
        ],
        description="Allowed binary command prefixes"
    )
    denied_commands: List[str] = Field(
        default_factory=lambda: [
            "rm -rf /", "mkfs", "dd", "shutdown", "reboot",
            ":(){ :|:& };:", "chmod -R 777 /", "sudo"
        ],
        description="Strictly forbidden commands"
    )
    redact_secrets: bool = Field(default=True, description="Redact secrets from logs and LLM prompts")


class ForgeConfig(BaseModel):
    project: ProjectConfig = Field(default_factory=ProjectConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    git: GitConfig = Field(default_factory=GitConfig)
    github: GitHubConfig = Field(default_factory=GitHubConfig)
    sandbox: SandboxConfig = Field(default_factory=SandboxConfig)
    ci: CIConfig = Field(default_factory=CIConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)

    def is_action_permitted(self, action: str) -> bool:
        """Check if an action requires approval based on autonomy mode."""
        if self.agent.mode == AutonomyMode.ASSISTED:
            return False  # Requires approval for everything significant
        if self.agent.mode == AutonomyMode.SAFE_PRODUCTION:
            return action not in self.security.require_approval_for
        # Autonomous mode allows everything except hard-denied destructive acts
        return action not in ["repository_delete", "force_push", "rm_rf_root"]
