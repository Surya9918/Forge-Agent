"""
Model Context Protocol (MCP) Server for Google Antigravity.
Connects Antigravity IDE, CLI, and Antigravity 2.0 to ForgeAgent tools and artifacts.
"""

import sys
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from forgeagent.config.loader import load_config
from forgeagent.agents.orchestrator import AgentOrchestrator
from forgeagent.state.persistence import StateManager
from forgeagent.compat import model_to_dict

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("forgeagent.mcp")


class ForgeMCPServer:
    def __init__(self, workspace_root: Optional[str] = None):
        self.config = load_config()
        if workspace_root:
            self.config.project.workspace = workspace_root
        self.workspace_root = self.config.project.workspace
        self.orchestrator = AgentOrchestrator(self.config, workspace_root=self.workspace_root)
        self.state_manager = StateManager(f"{self.workspace_root}/.forge/state")

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        method = request.get("method")
        msg_id = request.get("id")
        params = request.get("params", {})

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {
                        "name": "ForgeAgent",
                        "version": "0.1.0",
                        "tagline": "Autonomous Software Engineering inside Antigravity."
                    },
                    "capabilities": {
                        "tools": {"listChanged": True},
                        "resources": {"subscribe": True, "listChanged": True},
                        "prompts": {"listChanged": True}
                    }
                }
            }

        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": [
                        {
                            "name": "forge_plan",
                            "description": "Analyze requirements and create an autonomous software engineering plan.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "requirement": {"type": "string", "description": "High-level software specification"},
                                    "project_name": {"type": "string", "description": "Optional project identifier"}
                                },
                                "required": ["requirement"]
                            }
                        },
                        {
                            "name": "forge_develop",
                            "description": "End-to-end autonomous implementation, testing, self-healing, and git commit.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "requirement": {"type": "string", "description": "High-level software specification"},
                                    "project_name": {"type": "string", "description": "Target project name"}
                                },
                                "required": ["requirement"]
                            }
                        },
                        {
                            "name": "forge_test_and_heal",
                            "description": "Run tests and execute self-healing cycle until all tests pass.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "test_command": {"type": "string", "description": "Test command or auto-detect"}
                                }
                            }
                        },
                        {
                            "name": "forge_status",
                            "description": "Retrieve current task state, iteration count, and test summary.",
                            "inputSchema": {"type": "object", "properties": {}}
                        },
                        {
                            "name": "forge_git_commit",
                            "description": "Commit staged changes with conventional commit format.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "message": {"type": "string", "description": "Commit message"}
                                },
                                "required": ["message"]
                            }
                        },
                        {
                            "name": "forge_github_pr",
                            "description": "Push branch to remote and create a GitHub Pull Request.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "repo": {"type": "string", "description": "Repository name"},
                                    "title": {"type": "string", "description": "PR Title"},
                                    "body": {"type": "string", "description": "PR Description"}
                                },
                                "required": ["repo", "title"]
                            }
                        }
                    ]
                }
            }

        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            return self._call_tool(msg_id, tool_name, arguments)

        elif method == "resources/list":
            artifacts_dir = Path(self.workspace_root) / ".agents" / "artifacts"
            resources = []
            if artifacts_dir.exists():
                for f in artifacts_dir.glob("*.md"):
                    resources.append({
                        "uri": f"antigravity://artifacts/{f.name}",
                        "name": f"Artifact: {f.name}",
                        "mimeType": "text/markdown"
                    })
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"resources": resources}
            }

        elif method == "resources/read":
            uri = params.get("uri", "")
            filename = uri.replace("antigravity://artifacts/", "")
            target = Path(self.workspace_root) / ".agents" / "artifacts" / filename
            if target.is_file():
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "contents": [
                            {"uri": uri, "mimeType": "text/markdown", "text": target.read_text(encoding="utf-8")}
                        ]
                    }
                }
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32602, "message": f"Resource not found: {uri}"}
            }

        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"}
        }

    def _call_tool(self, msg_id: Any, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if tool_name == "forge_develop":
                req = args.get("requirement", "")
                name = args.get("project_name", "app")
                state = self.orchestrator.run(requirement=req, project_name=name)
                res_text = (
                    f"ForgeAgent autonomous run completed.\n"
                    f"Phase: {state.phase.value}\n"
                    f"Status: {state.status_message}\n"
                    f"Tests: {state.tests.passed} passed, {state.tests.failed} failed\n"
                    f"Commit: {state.commit_sha or 'None'}\n"
                    f"PR: {state.pr_url or 'None'}"
                )
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {"content": [{"type": "text", "text": res_text}]}
                }

            elif tool_name == "forge_plan":
                req = args.get("requirement", "")
                name = args.get("project_name", "app")
                state = self.orchestrator.state_manager.load_latest()
                plan = self.orchestrator.planner.run(state, requirement=req)
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {"content": [{"type": "text", "text": json.dumps(model_to_dict(plan), indent=2)}]}
                }

            elif tool_name == "forge_status":
                state = self.state_manager.load_latest()
                data = model_to_dict(state) if state else {"status": "No active tasks"}
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {"content": [{"type": "text", "text": json.dumps(data, indent=2)}]}
                }

            elif tool_name == "forge_test_and_heal":
                latest = self.state_manager.load_latest()
                if not latest:
                    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32000, "message": "No active project state found"}}
                summary = self.orchestrator.tester.run(latest)
                while summary.failed > 0 and latest.iteration < self.config.agent.max_iterations:
                    self.orchestrator.debugger.run(latest, test_output=summary.output)
                    summary = self.orchestrator.tester.run(latest)
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {"content": [{"type": "text", "text": f"Tests: {summary.passed} passed, {summary.failed} failed. Iterations: {latest.iteration}"}]}
                }

            elif tool_name == "forge_git_commit":
                msg = args.get("message", "feat: autonomous update")
                self.orchestrator.git_engine.stage_files()
                sha = self.orchestrator.git_engine.commit(msg)
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {"content": [{"type": "text", "text": f"Committed with SHA: {sha}"}]}
                }

            elif tool_name == "forge_github_pr":
                repo = args.get("repo", "app")
                title = args.get("title", "feat: autonomous update")
                body = args.get("body", "")
                pr = self.orchestrator.github_client.create_pull_request(
                    repo=repo,
                    title=title,
                    head=self.orchestrator.git_engine.get_current_branch(),
                    body=body
                )
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {"content": [{"type": "text", "text": f"PR created: {pr.get('html_url')}"}]}
                }

            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}
            }

        except Exception as e:
            logger.error(f"Error handling tool call {tool_name}: {e}", exc_info=True)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32000, "message": str(e)}
            }

    def run_stdio(self) -> None:
        logger.info("ForgeAgent MCP Server listening on stdio...")
        for line in sys.stdin:
            if not line.strip():
                continue
            try:
                req = json.loads(line)
                resp = self.handle_request(req)
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()
            except Exception as e:
                err_resp = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": f"Parse error: {e}"}}
                sys.stdout.write(json.dumps(err_resp) + "\n")
                sys.stdout.flush()


def main():
    server = ForgeMCPServer()
    server.run_stdio()


if __name__ == "__main__":
    main()
