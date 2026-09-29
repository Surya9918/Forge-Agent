"""
Filesystem tools with strict workspace boundary checks.
"""

import os
from pathlib import Path
from typing import List, Optional
from forgeagent.tools.base import BaseTool, ToolResult
from forgeagent.config.models import ForgeConfig


class FileToolBase(BaseTool):
    def __init__(self, workspace_root: str, config: Optional[ForgeConfig] = None):
        super().__init__(config=config)
        self.workspace_root = Path(workspace_root).resolve()
        self.workspace_root.mkdir(parents=True, exist_ok=True)

    def _resolve_safe(self, rel_path: str) -> Path:
        resolved = (self.workspace_root / rel_path).resolve()
        try:
            resolved.relative_to(self.workspace_root)
        except ValueError:
            raise PermissionError(f"Access violation: path '{rel_path}' resolves outside workspace root.")
        return resolved


class ReadFileTool(FileToolBase):
    name = "read_file"
    description = "Read file contents within the workspace."

    def _run(self, file_path: str) -> ToolResult:
        try:
            target = self._resolve_safe(file_path)
            if not target.is_file():
                return ToolResult(success=False, error=f"File not found: {file_path}")
            content = target.read_text(encoding="utf-8")
            return ToolResult(success=True, data=content, metadata={"path": str(file_path)})
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class WriteFileTool(FileToolBase):
    name = "write_file"
    description = "Write complete content to a file inside the workspace, creating parent directories."

    def _run(self, file_path: str, content: str) -> ToolResult:
        try:
            target = self._resolve_safe(file_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            return ToolResult(success=True, data=f"Wrote {len(content)} characters to {file_path}", metadata={"path": file_path})
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class EditFileTool(FileToolBase):
    name = "edit_file"
    description = "Replace specific string pattern or append content in a file within the workspace."

    def _run(self, file_path: str, old_content: str, new_content: str) -> ToolResult:
        try:
            target = self._resolve_safe(file_path)
            if not target.is_file():
                return ToolResult(success=False, error=f"File not found: {file_path}")
            text = target.read_text(encoding="utf-8")
            if old_content not in text:
                return ToolResult(success=False, error=f"Pattern not found in {file_path}")
            updated = text.replace(old_content, new_content, 1)
            target.write_text(updated, encoding="utf-8")
            return ToolResult(success=True, data=f"Successfully updated {file_path}", metadata={"path": file_path})
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class DeleteFileTool(FileToolBase):
    name = "delete_file"
    description = "Delete a file within the workspace."

    def _run(self, file_path: str) -> ToolResult:
        try:
            target = self._resolve_safe(file_path)
            if not target.exists():
                return ToolResult(success=False, error=f"Path not found: {file_path}")
            if target.is_file():
                target.unlink()
            elif target.is_dir():
                import shutil
                shutil.rmtree(target)
            return ToolResult(success=True, data=f"Deleted {file_path}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class ListDirectoryTool(FileToolBase):
    name = "list_directory"
    description = "List files and subdirectories at a given workspace path."

    def _run(self, directory: str = ".") -> ToolResult:
        try:
            target = self._resolve_safe(directory)
            if not target.is_dir():
                return ToolResult(success=False, error=f"Not a directory: {directory}")
            entries = []
            for item in sorted(target.iterdir()):
                rel = item.relative_to(self.workspace_root)
                entries.append({
                    "path": str(rel),
                    "name": item.name,
                    "is_dir": item.is_dir(),
                    "size": item.stat().st_size if item.is_file() else None,
                })
            return ToolResult(success=True, data=entries)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class SearchCodeTool(FileToolBase):
    name = "search_code"
    description = "Search for a keyword or regex pattern across workspace text files."

    def _run(self, pattern: str, max_results: int = 50) -> ToolResult:
        import re
        try:
            regex = re.compile(pattern)
            matches = []
            for root, dirs, files in os.walk(str(self.workspace_root)):
                # Skip hidden/cache directories
                dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ["node_modules", "__pycache__", "venv"]]
                for file_name in files:
                    file_path = Path(root) / file_name
                    try:
                        rel = file_path.relative_to(self.workspace_root)
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            for idx, line in enumerate(f, 1):
                                if regex.search(line):
                                    matches.append({
                                        "file": str(rel),
                                        "line": idx,
                                        "content": line.strip()
                                    })
                                    if len(matches) >= max_results:
                                        return ToolResult(success=True, data=matches)
                    except Exception:
                        continue
            return ToolResult(success=True, data=matches)
        except Exception as e:
            return ToolResult(success=False, error=str(e))
