"""
Configuration loading utilities for ForgeAgent.
"""

import os
from pathlib import Path
from typing import Optional, Union, Dict, Any
import yaml

from forgeagent.config.models import ForgeConfig
from forgeagent.compat import model_to_dict


def load_config(config_path: Optional[Union[str, Path]] = None, overrides: Optional[Dict[str, Any]] = None) -> ForgeConfig:
    data: Dict[str, Any] = {}
    candidate_paths = []
    if config_path:
        candidate_paths.append(Path(config_path))
    else:
        candidate_paths.extend([
            Path("forge.yaml"),
            Path("forge.yml"),
            Path(".forge.yaml"),
            Path(".agents/forge.yaml"),
            Path("~/.gemini/config/forge.yaml").expanduser(),
        ])

    for p in candidate_paths:
        if p.is_file():
            with open(p, "r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f)
                if isinstance(loaded, dict):
                    data = loaded
            break

    if overrides:
        _deep_update(data, overrides)

    if "FORGE_MODE" in os.environ:
        data.setdefault("agent", {})["mode"] = os.environ["FORGE_MODE"]
    if "FORGE_LLM_PROVIDER" in os.environ:
        data.setdefault("llm", {})["provider"] = os.environ["FORGE_LLM_PROVIDER"]
    if "FORGE_LLM_MODEL" in os.environ:
        data.setdefault("llm", {})["model"] = os.environ["FORGE_LLM_MODEL"]

    return ForgeConfig(**data)


def save_config(config: ForgeConfig, target_path: Union[str, Path]) -> None:
    path = Path(target_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(model_to_dict(config), f, default_flow_style=False, sort_keys=False)


def _deep_update(base: dict, update: dict) -> dict:
    for k, v in update.items():
        if isinstance(v, dict) and k in base and isinstance(base[k], dict):
            _deep_update(base[k], v)
        else:
            base[k] = v
    return base
