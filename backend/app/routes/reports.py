"""
reports.py — GET /api/v1/reports/{session_id} and export routes.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.models import Report
from app.session_store import load_report

router = APIRouter()


def _get_or_404(session_id: str) -> Report:
    report = load_report(session_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found.")
    return report


@router.get("/reports/{session_id}", response_model=Report)
async def get_report(session_id: str) -> Report:
    """Retrieve a previously analysed report."""
    return _get_or_404(session_id)


@router.get("/reports/{session_id}/export.json")
async def export_json(session_id: str) -> Response:
    """Download the full report as a JSON file."""
    report = _get_or_404(session_id)
    json_bytes = report.model_dump_json(indent=2).encode("utf-8")
    return Response(
        content=json_bytes,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="changestory-{session_id}.json"'
        },
    )


@router.get("/reports/{session_id}/export.md")
async def export_md(session_id: str) -> Response:
    """Download the report as a Markdown document."""
    report = _get_or_404(session_id)
    md = _render_markdown(report)
    return Response(
        content=md.encode("utf-8"),
        media_type="text/markdown",
        headers={
            "Content-Disposition": f'attachment; filename="changestory-{session_id}.md"'
        },
    )


# ---------------------------------------------------------------------------
# Markdown renderer
# ---------------------------------------------------------------------------


def _render_markdown(r: Report) -> str:
    lines: list[str] = []
    a = lines.append

    a(f"# ChangeStory Report — `{r.session_id}`")
    a(f"\n**Generated:** {r.created_at.strftime('%Y-%m-%d %H:%M UTC')}  ")
    a(f"**Mode:** {r.analysis_mode.value}  ")
    a(f"**Language:** {r.project_context.inferred_language}  ")
    if r.scenario_id:
        a(f"**Demo scenario:** `{r.scenario_id}`  ")

    a("\n---\n")
    a("## Summary\n")
    a(f"| Metric | Count |")
    a(f"|--------|-------|")
    a(f"| Changed files | {r.summary.changed_files} |")
    a(f"| Changed symbols | {r.summary.changed_symbols} |")
    a(f"| Affected symbols | {r.summary.affected_symbols} |")
    a(f"| Caller relationships | {r.summary.caller_relationships} |")
    a(f"| Risks (high/med/low/info) | {r.summary.risks.high}/{r.summary.risks.medium}/{r.summary.risks.low}/{r.summary.risks.info} |")
    a(f"| Test recommendations | {r.summary.test_recommendations} |")

    if r.changed_files:
        a("\n---\n")
        a("## Changed Files\n")
        for cf in r.changed_files:
            syms = ", ".join(f"`{s}`" for s in cf.changed_symbols) or "—"
            a(f"- **{cf.path}** ({cf.change_type.value}) +{cf.lines_added}/−{cf.lines_removed}  ")
            a(f"  Symbols: {syms}")

    if r.changed_symbols:
        a("\n---\n")
        a("## Changed Symbols\n")
        for s in r.changed_symbols:
            loc = f":{s.line_start}" if s.line_start else ""
            a(f"- `{s.name}` ({s.kind.value}) — `{s.file}{loc}`")

    if r.affected_symbols:
        a("\n---\n")
        a("## Potentially Affected Symbols\n")
        a("> These symbols call a changed symbol. Labelled **potential**.\n")
        for s in r.affected_symbols:
            a(f"- `{s.name}` — `{s.file}`")

    if r.caller_relationships:
        a("\n---\n")
        a("## Caller Relationships\n")
        a("| Caller | Callee | File | Line | Confidence |")
        a("|--------|--------|------|------|------------|")
        for cr in r.caller_relationships:
            line = str(cr.caller_line) if cr.caller_line else "—"
            a(f"| `{cr.caller}` | `{cr.callee}` | `{cr.caller_file}` | {line} | {cr.confidence.value} |")

    if r.risks:
        a("\n---\n")
        a("## Risks\n")
        for risk in r.risks:
            icon = {"high": "🔴", "medium": "🟡", "low": "🟢", "info": "ℹ️"}.get(risk.level.value, "•")
            a(f"\n### {icon} [{risk.level.value.upper()}] {risk.title}\n")
            a(f"{risk.description}\n")
            if risk.evidence:
                a("**Evidence:**")
                for ev in risk.evidence:
                    a(f"```\n{ev}\n```")
            a(f"*Confidence: {risk.confidence.value}*")

    if r.test_recommendations:
        a("\n---\n")
        a("## Test Recommendations\n")
        for rec in r.test_recommendations:
            a(f"\n### [{rec.priority.upper()}] {rec.title}\n")
            a(f"{rec.rationale}\n")
            if rec.suggested_test_ids:
                a("Suggested test locations: " + ", ".join(f"`{t}`" for t in rec.suggested_test_ids))

    if r.verification:
        v = r.verification
        a("\n---\n")
        a("## Verification\n")
        if v.ran:
            a(f"- **Passed:** {v.passed}")
            a(f"- **Failed:** {v.failed}")
            a(f"- **Skipped:** {v.skipped}")
            if v.confirmed_safe:
                a("\n**Confirmed safe:**")
                for t in v.confirmed_safe:
                    a(f"  - `{t}`")
            if v.confirmed_failing:
                a("\n**Confirmed failing:**")
                for t in v.confirmed_failing:
                    a(f"  - `{t}`")
        else:
            a(f"Verification did not run. Reason: {v.note}")

    if r.limitations:
        a("\n---\n")
        a("## Limitations\n")
        for lim in r.limitations:
            a(f"- {lim}")

    a("\n---\n*Generated by ChangeStory*")
    return "\n".join(lines)
