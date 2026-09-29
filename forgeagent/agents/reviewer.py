"""
Code Reviewer Agent: conducts holistic quality, security, and architecture reviews.
Produces docs/agent/code-review.md.
"""

from pathlib import Path
from forgeagent.agents.base import BaseAgent
from forgeagent.llm.base import ChatMessage
from forgeagent.state.state import TaskState, AgentPhase
from forgeagent.intelligence.analyzer import RepoAnalyzer
from forgeagent.compat import model_to_dict


class ReviewerAgent(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(name="Reviewer", **kwargs)

    def run(self, state: TaskState) -> str:
        state.phase = AgentPhase.REVIEW
        state.status_message = "Performing comprehensive automated code and security review"

        analyzer = RepoAnalyzer(self.tools.workspace_root)
        summary = analyzer.analyze()
        diff_res = self.tools.execute_tool("git_diff")
        git_diff = diff_res.data if diff_res.success else ""

        prompt = f"""You are the Staff Security Engineer & Quality Reviewer for ForgeAgent.
Review the implemented codebase and produce a formal Code Review Document in Markdown.

Repository Statistics:
- Total Files: {summary.total_files}
- Languages: {summary.languages}
- Stack: {model_to_dict(summary.stack)}
- Key Files Changed: {state.changed_files}

Git Changes:
{git_diff[-3000:] if git_diff else "No diff (all committed)."}

Evaluate and write detailed sections covering:
1. Overall Quality & Architecture Conformance
2. Correctness & Edge-Case Handling
3. Security Evaluation (Secrets, Input Sanitization, Sandbox boundary)
4. Performance & Scalability
5. Test Coverage & Verification Integrity
6. Maintainability & Code Style
7. Recommendation & Production Sign-off Verdict (Approved / Changes Required)
"""
        messages = [ChatMessage(role="user", content=prompt)]
        resp = self.llm.generate(messages)
        review_doc = resp.content

        self.tools.execute_tool("write_file", file_path="docs/agent/code-review.md", content=review_doc)
        state.artifacts["code_review"] = "docs/agent/code-review.md"

        return review_doc
