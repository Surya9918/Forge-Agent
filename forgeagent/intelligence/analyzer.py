"""
Repository Intelligence Analyzer: extracts structure, symbols, imports, and incremental context.
"""

import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from forgeagent.intelligence.detector import ProjectDetector, ProjectStackInfo


class RepoSummary(BaseModel):
    total_files: int = 0
    languages: Dict[str, int] = Field(default_factory=dict)
    stack: ProjectStackInfo = Field(default_factory=ProjectStackInfo)
    directory_tree: List[str] = Field(default_factory=list)
    todos: List[Dict[str, Any]] = Field(default_factory=list)
    key_files: List[str] = Field(default_factory=list)


class RepoAnalyzer:
    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root).resolve()

    def analyze(self) -> RepoSummary:
        if not self.workspace_root.exists():
            return RepoSummary()

        summary = RepoSummary()
        summary.stack = ProjectDetector.detect(self.workspace_root)

        todo_pattern = re.compile(r"(?i)\b(TODO|FIXME|BUG|HACK)\b:?\s*(.*)")
        ext_lang_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".tsx": "react/typescript",
            ".jsx": "react/javascript",
            ".rs": "rust",
            ".go": "go",
            ".java": "java",
            ".json": "json",
            ".md": "markdown",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".html": "html",
            ".css": "css",
        }

        tree_lines = []
        for root, dirs, files in os.walk(str(self.workspace_root)):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["node_modules", "dist", "build", "venv", "__pycache__"]]
            rel_dir = Path(root).relative_to(self.workspace_root)
            depth = len(rel_dir.parts)
            indent = "  " * depth
            if str(rel_dir) != ".":
                tree_lines.append(f"{indent}📁 {rel_dir.name}/")

            for file in sorted(files):
                if file.startswith("."):
                    continue
                summary.total_files += 1
                file_path = Path(root) / file
                rel_path = file_path.relative_to(self.workspace_root)
                tree_lines.append(f"{indent}  📄 {file}")

                ext = file_path.suffix.lower()
                lang = ext_lang_map.get(ext, "other")
                summary.languages[lang] = summary.languages.get(lang, 0) + 1

                # Track key root or config files
                if depth == 0 or file in ["main.py", "app.py", "index.ts", "server.js", "README.md"]:
                    summary.key_files.append(str(rel_path))

                # Scan for TODOs
                if ext in ext_lang_map and ext not in [".json", ".md"]:
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            for idx, line in enumerate(f, 1):
                                match = todo_pattern.search(line)
                                if match:
                                    summary.todos.append({
                                        "file": str(rel_path),
                                        "line": idx,
                                        "tag": match.group(1).upper(),
                                        "comment": match.group(2).strip()
                                    })
                    except Exception:
                        continue

        summary.directory_tree = tree_lines[:100]  # Cap for prompt efficiency
        return summary

    def get_context_for_task(self, relevant_keywords: List[str]) -> str:
        """Incremental retrieval of matching snippets without loading whole repo."""
        snippets = []
        for root, dirs, files in os.walk(str(self.workspace_root)):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["node_modules", "dist", "build", "venv", "__pycache__"]]
            for file in files:
                ext = Path(file).suffix.lower()
                if ext in [".py", ".ts", ".js", ".go", ".rs", ".java", ".md", ".json"]:
                    full_p = Path(root) / file
                    rel_p = full_p.relative_to(self.workspace_root)
                    try:
                        text = full_p.read_text(encoding="utf-8", errors="ignore")
                        if any(kw.lower() in text.lower() for kw in relevant_keywords):
                            snippets.append(f"--- File: {rel_p} ---\n{text[:1500]}\n")
                    except Exception:
                        continue
        return "\n".join(snippets[:5])
