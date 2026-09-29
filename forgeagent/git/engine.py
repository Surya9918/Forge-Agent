"""
Git Engine for safe, auditable version control operations.
"""

import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
from forgeagent.config.models import GitConfig
from forgeagent.observability.logger import get_logger

logger = get_logger("forgeagent.git")


class GitEngine:
    def __init__(self, workspace_root: str, config: Optional[GitConfig] = None):
        self.workspace_root = Path(workspace_root).resolve()
        self.config = config or GitConfig()

    def _exec(self, args: List[str], check: bool = True) -> subprocess.CompletedProcess:
        cmd = ["git"] + args
        res = subprocess.run(
            cmd,
            cwd=str(self.workspace_root),
            capture_output=True,
            text=True
        )
        if check and res.returncode != 0:
            raise RuntimeError(f"Git command failed: {' '.join(cmd)}\nStderr: {res.stderr}")
        return res

    def is_repo(self) -> bool:
        return (self.workspace_root / ".git").is_dir()

    def initialize_repository(self, initial_branch: Optional[str] = None) -> str:
        branch = initial_branch or self.config.default_branch
        self._exec(["init", "-b", branch])
        # Set dummy identity if not configured
        self._exec(["config", "user.name", "ForgeAgent"], check=False)
        self._exec(["config", "user.email", "forgeagent@antigravity.local"], check=False)
        return f"Initialized Git repository with default branch '{branch}'"

    def get_status(self) -> Dict[str, Any]:
        if not self.is_repo():
            return {"is_repo": False, "staged": [], "unstaged": [], "untracked": []}

        res = self._exec(["status", "--porcelain"], check=False)
        staged = []
        unstaged = []
        untracked = []
        for line in res.stdout.splitlines():
            if not line:
                continue
            x = line[0]
            y = line[1]
            path = line[3:].strip()
            if x in ["M", "A", "D", "R", "C"]:
                staged.append(path)
            if y in ["M", "D"]:
                unstaged.append(path)
            if x == "?" and y == "?":
                untracked.append(path)

        current_branch = self.get_current_branch()
        return {
            "is_repo": True,
            "branch": current_branch,
            "staged": staged,
            "unstaged": unstaged,
            "untracked": untracked,
            "clean": len(staged) == 0 and len(unstaged) == 0 and len(untracked) == 0,
        }

    def get_current_branch(self) -> str:
        res = self._exec(["rev-parse", "--abbrev-ref", "HEAD"], check=False)
        if res.returncode == 0:
            return res.stdout.strip()
        return self.config.default_branch

    def get_diff(self, staged: bool = False) -> str:
        args = ["diff", "--staged"] if staged else ["diff"]
        res = self._exec(args, check=False)
        return res.stdout

    def create_branch(self, branch_name: str, checkout: bool = True) -> str:
        if checkout:
            self._exec(["checkout", "-b", branch_name])
            return f"Created and checked out branch '{branch_name}'"
        else:
            self._exec(["branch", branch_name])
            return f"Created branch '{branch_name}'"

    def checkout_branch(self, branch_name: str) -> str:
        self._exec(["checkout", branch_name])
        return f"Checked out branch '{branch_name}'"

    def stage_files(self, paths: Optional[List[str]] = None) -> str:
        if not paths:
            self._exec(["add", "-A"])
            return "Staged all modified, deleted, and untracked files"
        else:
            self._exec(["add"] + paths)
            return f"Staged {len(paths)} files"

    def commit(self, message: str) -> str:
        res = self._exec(["commit", "-m", message])
        # Retrieve commit SHA
        sha_res = self._exec(["rev-parse", "HEAD"], check=False)
        sha = sha_res.stdout.strip() if sha_res.returncode == 0 else ""
        return sha

    def push(self, remote: str = "origin", branch: Optional[str] = None, force: bool = False) -> str:
        target_branch = branch or self.get_current_branch()
        if target_branch in self.config.protected_branches and force:
            raise PermissionError(f"Safety Violation: Force-push is strictly prohibited on protected branch '{target_branch}'.")

        args = ["push", remote, target_branch]
        if force:
            args.append("--force")

        res = self._exec(args, check=False)
        if res.returncode != 0:
            return f"Push skipped/failed: {res.stderr.strip()}"
        return f"Pushed {target_branch} to {remote}"

    def pull(self, remote: str = "origin", branch: Optional[str] = None) -> str:
        target_branch = branch or self.get_current_branch()
        res = self._exec(["pull", remote, target_branch], check=False)
        return res.stdout

    def get_log(self, limit: int = 10) -> List[Dict[str, str]]:
        if not self.is_repo():
            return []
        fmt = "%H%x1f%an%x1f%ae%x1f%ad%x1f%s"
        res = self._exec(["log", f"-n{limit}", f"--format={fmt}"], check=False)
        commits = []
        for line in res.stdout.splitlines():
            if not line:
                continue
            parts = line.split("\x1f")
            if len(parts) >= 5:
                commits.append({
                    "sha": parts[0],
                    "author_name": parts[1],
                    "author_email": parts[2],
                    "date": parts[3],
                    "message": parts[4],
                })
        return commits

    def create_tag(self, tag_name: str, message: Optional[str] = None) -> str:
        args = ["tag", tag_name]
        if message:
            args.extend(["-m", message])
        self._exec(args)
        return f"Created tag '{tag_name}'"
