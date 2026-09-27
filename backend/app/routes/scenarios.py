"""
scenarios.py — GET /api/v1/scenarios and POST /api/v1/verify/{session_id}
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.analysis.report_builder import build_report
from app.models import Report, ScenariosResponse, VerifyResponse
from app.scenarios.bundled import BUNDLED_SCENARIOS, get_scenario
from app.session_store import load_report, save_report, update_report
from app.verify.runner import can_verify, run_verification

router = APIRouter()


@router.get("/scenarios", response_model=ScenariosResponse)
async def list_scenarios() -> ScenariosResponse:
    """Return the three bundled demo scenarios."""
    return ScenariosResponse(scenarios=BUNDLED_SCENARIOS)


@router.post("/scenarios/{scenario_id}/analyze", response_model=Report)
async def analyze_scenario(scenario_id: str) -> Report:
    """
    Run analysis on a bundled scenario by ID.
    Shortcut so the frontend can trigger analysis without constructing a diff.
    """
    scenario = get_scenario(scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found.")

    report = build_report(
        diff_text=scenario.diff,
        mode=scenario.mode,
        is_demo=True,
        scenario_id=scenario.id,
    )
    save_report(report)
    return report


@router.post("/verify/{session_id}", response_model=VerifyResponse)
async def verify(session_id: str) -> VerifyResponse:
    """
    Run controlled pytest verification against the bundled sample project.
    Only available for reports created from a bundled demo scenario.
    """
    report = load_report(session_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found.")

    if not report.is_demo or not can_verify(report.scenario_id):
        raise HTTPException(
            status_code=403,
            detail="Verification is only available for bundled demo scenarios.",
        )

    verification = run_verification(report.scenario_id)  # type: ignore[arg-type]

    report.verification = verification
    update_report(report)

    return VerifyResponse(session_id=session_id, verification=verification)
