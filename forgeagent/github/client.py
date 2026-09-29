"""
GitHub Integration Client supporting both real REST API and simulated in-memory store for hermetic testing.
"""

import os
import requests
from typing import Dict, Any, Optional, List
from forgeagent.config.models import GitHubConfig
from forgeagent.observability.redactor import redact_secrets
from forgeagent.observability.logger import get_logger

logger = get_logger("forgeagent.github")


class GitHubClient:
    def __init__(self, config: Optional[GitHubConfig] = None, token: Optional[str] = None):
        self.config = config or GitHubConfig()
        self.token = token or os.environ.get(self.config.token_env, "")
        self.base_url = "https://api.github.com"
        self._simulated_repos: Dict[str, Dict[str, Any]] = {}
        self._simulated_prs: Dict[str, List[Dict[str, Any]]] = {}
        self._simulated_ci: Dict[str, Dict[str, Any]] = {}

    @property
    def is_configured(self) -> bool:
        return bool(self.token and not self.token.startswith("mock"))

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    def create_repository(
        self,
        name: str,
        description: str = "",
        private: bool = True,
        auto_init: bool = False
    ) -> Dict[str, Any]:
        """Create a GitHub repository idempotently."""
        if not self.is_configured:
            # Simulated in-memory repo for testing / offline
            logger.info(f"[Simulation] Creating GitHub repository: {name}")
            repo_data = {
                "id": 12345678,
                "name": name,
                "full_name": f"antigravity-dev/{name}",
                "html_url": f"https://github.com/antigravity-dev/{name}",
                "clone_url": f"https://github.com/antigravity-dev/{name}.git",
                "default_branch": "main",
                "private": private,
                "description": description,
            }
            self._simulated_repos[name] = repo_data
            return repo_data

        url = f"{self.base_url}/user/repos"
        payload = {
            "name": name,
            "description": description,
            "private": private,
            "auto_init": auto_init
        }
        resp = requests.post(url, headers=self._headers(), json=payload, timeout=30)
        if resp.status_code == 422:
            # Repository may already exist, fetch it idempotently
            logger.info(f"Repository {name} already exists. Fetching existing repository.")
            return self.get_repository(name)
        resp.raise_for_status()
        return resp.json()

    def get_repository(self, name: str, owner: Optional[str] = None) -> Dict[str, Any]:
        if not self.is_configured:
            if name in self._simulated_repos:
                return self._simulated_repos[name]
            return {
                "id": 12345678,
                "name": name,
                "full_name": f"{owner or 'antigravity-dev'}/{name}",
                "html_url": f"https://github.com/{owner or 'antigravity-dev'}/{name}",
                "clone_url": f"https://github.com/{owner or 'antigravity-dev'}/{name}.git",
                "default_branch": "main",
                "private": True,
            }

        target = f"{owner}/{name}" if owner else f"{self.config.owner or 'user'}/{name}"
        url = f"{self.base_url}/repos/{target}"
        resp = requests.get(url, headers=self._headers(), timeout=30)
        resp.raise_for_status()
        return resp.json()

    def create_pull_request(
        self,
        repo: str,
        title: str,
        head: str,
        base: str = "main",
        body: str = "",
        owner: Optional[str] = None
    ) -> Dict[str, Any]:
        if not self.is_configured:
            logger.info(f"[Simulation] Creating PR in {repo}: '{title}' ({head} -> {base})")
            pr_data = {
                "id": 9901,
                "number": len(self._simulated_prs.get(repo, [])) + 1,
                "title": title,
                "html_url": f"https://github.com/{owner or 'antigravity-dev'}/{repo}/pull/1",
                "state": "open",
                "head": {"ref": head},
                "base": {"ref": base},
                "body": body,
            }
            self._simulated_prs.setdefault(repo, []).append(pr_data)
            return pr_data

        target = f"{owner}/{repo}" if owner else f"{self.config.owner}/{repo}"
        url = f"{self.base_url}/repos/{target}/pulls"
        payload = {"title": title, "head": head, "base": base, "body": body}
        resp = requests.post(url, headers=self._headers(), json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def get_pull_request(self, repo: str, pull_number: int, owner: Optional[str] = None) -> Dict[str, Any]:
        if not self.is_configured:
            prs = self._simulated_prs.get(repo, [])
            for pr in prs:
                if pr["number"] == pull_number:
                    return pr
            return {"number": pull_number, "state": "open", "title": "Autonomous PR", "html_url": f"https://github.com/org/{repo}/pull/{pull_number}"}

        target = f"{owner}/{repo}" if owner else f"{self.config.owner}/{repo}"
        url = f"{self.base_url}/repos/{target}/pulls/{pull_number}"
        resp = requests.get(url, headers=self._headers(), timeout=30)
        resp.raise_for_status()
        return resp.json()

    def get_ci_status(self, repo: str, branch_or_sha: str, owner: Optional[str] = None) -> Dict[str, Any]:
        if not self.is_configured:
            # Simulated CI result
            return self._simulated_ci.get(f"{repo}:{branch_or_sha}", {
                "status": "completed",
                "conclusion": "success",
                "total_count": 1,
                "workflow_runs": [
                    {
                        "name": "CI",
                        "status": "completed",
                        "conclusion": "success",
                        "html_url": f"https://github.com/{owner or 'antigravity-dev'}/{repo}/actions/runs/101"
                    }
                ]
            })

        target = f"{owner}/{repo}" if owner else f"{self.config.owner}/{repo}"
        url = f"{self.base_url}/repos/{target}/actions/runs?branch={branch_or_sha}"
        resp = requests.get(url, headers=self._headers(), timeout=30)
        resp.raise_for_status()
        return resp.json()

    def set_simulated_ci_status(self, repo: str, branch_or_sha: str, conclusion: str, logs: str = "") -> None:
        """Helper for benchmark and unit test simulation."""
        self._simulated_ci[f"{repo}:{branch_or_sha}"] = {
            "status": "completed",
            "conclusion": conclusion,
            "total_count": 1,
            "workflow_runs": [
                {
                    "name": "CI",
                    "status": "completed",
                    "conclusion": conclusion,
                    "logs_preview": logs,
                }
            ]
        }

    def get_workflow_logs(self, repo: str, run_id: int, owner: Optional[str] = None) -> str:
        if not self.is_configured:
            return "CI Step 1: Install dependencies [OK]\nCI Step 2: Run tests [FAILED]\nAssertionError: expected True but got False"
        target = f"{owner}/{repo}" if owner else f"{self.config.owner}/{repo}"
        url = f"{self.base_url}/repos/{target}/actions/runs/{run_id}/logs"
        resp = requests.get(url, headers=self._headers(), timeout=30)
        resp.raise_for_status()
        return redact_secrets(resp.text)
