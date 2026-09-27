"""
session_store.py — Lightweight flat-file session persistence.

Reports are stored as JSON files in backend/data/sessions/.
This is intentionally simple — no database required for a hackathon demo.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.models import Report

_SESSIONS_DIR = Path(__file__).parent.parent / "data" / "sessions"


def _path(session_id: str) -> Path:
    _SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    return _SESSIONS_DIR / f"{session_id}.json"


def save_report(report: Report) -> None:
    _path(report.session_id).write_text(
        report.model_dump_json(indent=2), encoding="utf-8"
    )


def load_report(session_id: str) -> Report | None:
    p = _path(session_id)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return Report.model_validate(data)
    except Exception:
        return None


def update_report(report: Report) -> None:
    save_report(report)
