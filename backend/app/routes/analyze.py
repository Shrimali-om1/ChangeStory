"""
analyze.py — POST /api/v1/analyze
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.analysis.report_builder import build_report
from app.models import AnalyzeRequest, Report
from app.session_store import save_report

router = APIRouter()


@router.post("/analyze", response_model=Report)
async def analyze(request: AnalyzeRequest) -> Report:
    """
    Accept a unified diff and return a full analysis report.
    The report is persisted and retrievable via GET /reports/{session_id}.
    """
    diff = request.diff.strip()
    if not diff:
        raise HTTPException(status_code=400, detail="Diff text must not be empty.")

    # Very basic guard: reject if it does not look like a diff at all
    if not any(line.startswith(("diff ", "---", "+++", "@@")) for line in diff.splitlines()):
        raise HTTPException(
            status_code=400,
            detail="The provided text does not appear to be a valid unified diff.",
        )

    report = build_report(diff, request.mode)
    save_report(report)
    return report
