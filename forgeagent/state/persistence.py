"""
State persistence layer supporting JSON files and recoverable sessions.
"""

import json
from pathlib import Path
from typing import Optional, List
from forgeagent.state.state import TaskState
from forgeagent.compat import model_to_dict


class StateManager:
    def __init__(self, state_dir: str = ".forge/state"):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def save(self, state: TaskState) -> Path:
        state.update_timestamp()
        file_path = self.state_dir / f"{state.task_id}.json"
        latest_path = self.state_dir / "latest.json"

        content = json.dumps(model_to_dict(state), indent=2)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        with open(latest_path, "w", encoding="utf-8") as f:
            f.write(content)

        return file_path

    def load(self, task_id: str) -> Optional[TaskState]:
        file_path = self.state_dir / f"{task_id}.json"
        if not file_path.is_file():
            return None
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return TaskState(**data)

    def load_latest(self) -> Optional[TaskState]:
        latest_path = self.state_dir / "latest.json"
        if not latest_path.is_file():
            return None
        with open(latest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return TaskState(**data)

    def list_tasks(self) -> List[str]:
        return [p.stem for p in self.state_dir.glob("*.json") if p.stem != "latest"]
