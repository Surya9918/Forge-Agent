"""
Secret redactor for ForgeAgent to prevent credential leaks to LLMs or logs.
"""

import re
from typing import Any, Union, Dict, List

SECRET_PATTERNS = [
    (re.compile(r"ghp_[A-Za-z0-9_]{36,255}"), "ghp_********"),
    (re.compile(r"github_pat_[A-Za-z0-9_]{36,255}"), "github_pat_********"),
    (re.compile(r"sk-[A-Za-z0-9_-]{20,255}"), "sk-********"),
    (re.compile(r"AIza[0-9A-Za-z-_]{35}"), "AIza********"),
    (re.compile(r"(?i)aws_secret_access_key\s*=\s*['\"]?[A-Za-z0-9/+=]{40}['\"]?"), "AWS_SECRET_ACCESS_KEY=********"),
    (re.compile(r"(?i)bearer\s+[A-Za-z0-9\-._~+/]+=*"), "Bearer ********"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"), "-----BEGIN PRIVATE KEY-----\n[REDACTED PRIVATE KEY]\n-----END PRIVATE KEY-----"),
    (re.compile(r"(?i)(password|secret|token|api[_-]?key)\s*[:=]\s*['\"][^'\"]{4,}['\"]"), r"\1='********'"),
]


def redact_secrets(text: Union[str, Any]) -> str:
    """Mask credentials and sensitive strings from text."""
    if not isinstance(text, str):
        text = str(text)

    for pattern, replacement in SECRET_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def redact_data(obj: Any) -> Any:
    """Recursively redact secrets in dicts, lists, or strings."""
    if isinstance(obj, str):
        return redact_secrets(obj)
    if isinstance(obj, dict):
        return {k: redact_data(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact_data(v) for v in obj]
    return obj
