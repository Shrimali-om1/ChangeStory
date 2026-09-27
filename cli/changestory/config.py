"""
config.py — Read/write the minimal per-project configuration file.

The config file is stored at <repo>/.changestory.json and contains:
  {
    "repo": "/absolute/path/to/repo",
    "api_url": "http://localhost:8000/api/v1"   // optional override
  }
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

CONFIG_FILENAME = ".changestory.json"
DEFAULT_API_URL = "http://localhost:8000/api/v1"


def config_path(repo: Path) -> Path:
    return repo / CONFIG_FILENAME


def write_config(repo: Path, api_url: str = DEFAULT_API_URL) -> Path:
    """Write a minimal config file into the repository root."""
    cfg: dict[str, Any] = {
        "repo": str(repo.resolve()),
        "api_url": api_url,
    }
    path = config_path(repo)
    path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    return path


def read_config(repo: Path) -> dict[str, Any]:
    """
    Load the config for the given repo directory.
    Returns an empty dict (with defaults) if the file is missing.
    """
    path = config_path(repo)
    if not path.exists():
        return {"repo": str(repo.resolve()), "api_url": DEFAULT_API_URL}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Malformed config file {path}: {exc}") from exc


def find_config_upward(start: Path | None = None) -> dict[str, Any] | None:
    """
    Walk upward from *start* (default: cwd) looking for a .changestory.json.
    Returns the parsed config dict, or None if not found.
    """
    current = (start or Path.cwd()).resolve()
    for directory in [current, *current.parents]:
        candidate = directory / CONFIG_FILENAME
        if candidate.exists():
            try:
                return json.loads(candidate.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                return None
    return None


def get_api_url(override: str | None = None, repo: Path | None = None) -> str:
    """
    Resolve the API base URL by priority:
      1. --api-url CLI flag override
      2. CHANGESTORY_API_URL environment variable
      3. .changestory.json in repo (or cwd)
      4. Default http://localhost:8000/api/v1
    """
    if override:
        return override.rstrip("/")
    env = os.environ.get("CHANGESTORY_API_URL")
    if env:
        return env.rstrip("/")
    if repo:
        cfg = read_config(repo)
        return cfg.get("api_url", DEFAULT_API_URL).rstrip("/")
    cfg = find_config_upward()
    if cfg:
        return cfg.get("api_url", DEFAULT_API_URL).rstrip("/")
    return DEFAULT_API_URL
