"""
report_builder.py — Assemble a full Report from parsed diff + AST analysis.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone

from app.analysis.ast_analyzer import (
    find_callers_in_diff,
    identify_changed_symbols,
)
from app.analysis.diff_parser import FileDiff, parse_diff
from app.models import (
    AnalysisMode,
    CallerRelationship,
    ChangedFile,
    ChangeType,
    Confidence,
    ProjectContext,
    Report,
    ReportSummary,
    Risk,
    RiskLevel,
    SummaryRisks,
    Symbol,
    SymbolKind,
    TestRecommendation,
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _make_session_id(diff: str) -> str:
    """Deterministic 8-char session ID from diff content + timestamp."""
    ts = datetime.now(timezone.utc).isoformat()
    raw = f"{diff[:200]}{ts}"
    return hashlib.sha256(raw.encode()).hexdigest()[:8]


def _change_type(ct: str) -> ChangeType:
    mapping = {
        "added": ChangeType.added,
        "deleted": ChangeType.deleted,
        "renamed": ChangeType.renamed,
    }
    return mapping.get(ct, ChangeType.modified)


def _symbol_kind(kind: str) -> SymbolKind:
    mapping = {
        "function": SymbolKind.function,
        "method": SymbolKind.method,
        "class": SymbolKind.class_,
    }
    return mapping.get(kind, SymbolKind.function)


# ---------------------------------------------------------------------------
# Risk heuristics
# ---------------------------------------------------------------------------

_SIGNATURE_RE = re.compile(r"^\s*(?:async\s+)?def\s+\w+\s*\((.+)\)\s*(?:->.*)?:")


def _infer_risks(file_diffs: list[FileDiff], changed_symbol_names: list[str]) -> list[Risk]:
    risks: list[Risk] = []

    for fd in file_diffs:
        # Detect signature change: removed def differs from added def
        removed_sigs = [
            ln.text.strip()
            for ln in fd.removed_lines
            if _SIGNATURE_RE.match(ln.text)
        ]
        added_sigs = [
            ln.text.strip()
            for ln in fd.added_lines
            if _SIGNATURE_RE.match(ln.text)
        ]

        for removed, added in zip(removed_sigs, added_sigs):
            if removed != added:
                # Extract function name for the risk title
                m = re.search(r"def\s+(\w+)", added)
                fname = m.group(1) if m else "unknown"
                risks.append(
                    Risk(
                        level=RiskLevel.high,
                        title=f"Signature changed: {fname}",
                        description=(
                            f"The signature of `{fname}` in `{fd.path}` changed. "
                            "Callers may break if positional or keyword arguments differ."
                        ),
                        affected_symbols=[fname],
                        evidence=[f"- {removed}", f"+ {added}"],
                        confidence=Confidence.potential,
                    )
                )

        # Detect deleted public function / class
        for sym_name in changed_symbol_names:
            short = sym_name.split(".")[-1]
            if not short.startswith("_") and fd.change_type == "deleted":
                risks.append(
                    Risk(
                        level=RiskLevel.high,
                        title=f"Public symbol deleted: {sym_name}",
                        description=(
                            f"`{sym_name}` was deleted from `{fd.path}`. "
                            "Any code referencing this symbol will break at runtime."
                        ),
                        affected_symbols=[sym_name],
                        evidence=[f"File {fd.path} was deleted"],
                        confidence=Confidence.potential,
                    )
                )

        # Detect large churn (> 30 lines changed)
        total_churn = fd.lines_added + fd.lines_removed
        if total_churn > 30:
            risks.append(
                Risk(
                    level=RiskLevel.medium,
                    title=f"Large change in {fd.path}",
                    description=(
                        f"{total_churn} lines changed in `{fd.path}`. "
                        "Large diffs are harder to review and may hide subtle bugs."
                    ),
                    affected_symbols=[s for s in changed_symbol_names if fd.path in s or True],
                    evidence=[
                        f"+{fd.lines_added} lines added, -{fd.lines_removed} lines removed"
                    ],
                    confidence=Confidence.potential,
                )
            )

        # Detect removed exception handling
        removed_try = sum(
            1 for ln in fd.removed_lines
            if re.match(r"^\s*except\b", ln.text)
        )
        if removed_try > 0:
            risks.append(
                Risk(
                    level=RiskLevel.medium,
                    title=f"Exception handling removed in {fd.path}",
                    description=(
                        f"{removed_try} `except` clause(s) were removed from `{fd.path}`. "
                        "Error paths may now be unhandled."
                    ),
                    affected_symbols=[],
                    evidence=[
                        ln.text.strip()
                        for ln in fd.removed_lines
                        if re.match(r"^\s*except\b", ln.text)
                    ],
                    confidence=Confidence.potential,
                )
            )

    return risks


# ---------------------------------------------------------------------------
# Test recommendations
# ---------------------------------------------------------------------------


def _build_recommendations(
    changed_symbol_names: list[str],
    risks: list[Risk],
) -> list[TestRecommendation]:
    recs: list[TestRecommendation] = []

    for sym in changed_symbol_names:
        short = sym.split(".")[-1]
        priority = "high" if any(sym in r.affected_symbols for r in risks if r.level == RiskLevel.high) else "medium"
        recs.append(
            TestRecommendation(
                title=f"Test `{sym}` after change",
                rationale=(
                    f"`{sym}` was modified. Verify behaviour at boundary values "
                    "and any new/removed code paths."
                ),
                suggested_test_ids=[f"tests/test_{short.lower()}.py"],
                priority=priority,
            )
        )

    # Add a regression recommendation if callers exist
    if len(changed_symbol_names) > 1:
        recs.append(
            TestRecommendation(
                title="Run full regression suite",
                rationale="Multiple symbols changed; integration tests are recommended.",
                suggested_test_ids=["tests/"],
                priority="high",
            )
        )

    return recs


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def build_report(
    diff_text: str,
    mode: AnalysisMode,
    session_id: str | None = None,
    is_demo: bool = False,
    scenario_id: str | None = None,
) -> Report:
    if session_id is None:
        session_id = _make_session_id(diff_text)

    file_diffs: list[FileDiff] = parse_diff(diff_text)

    # ---- Changed files ----------------------------------------------------
    changed_files = [
        ChangedFile(
            path=fd.path,
            change_type=_change_type(fd.change_type),
            lines_added=fd.lines_added,
            lines_removed=fd.lines_removed,
        )
        for fd in file_diffs
    ]

    # ---- Changed symbols --------------------------------------------------
    all_symbol_infos = []
    for fd in file_diffs:
        syms = identify_changed_symbols(fd)
        for s in syms:
            s.file = fd.path  # ensure correct file path
        all_symbol_infos.extend(syms)

    changed_symbols: list[Symbol] = []
    seen_sym_names: set[str] = set()
    for s in all_symbol_infos:
        if s.name in seen_sym_names:
            continue
        seen_sym_names.add(s.name)
        changed_symbols.append(
            Symbol(
                name=s.name,
                kind=_symbol_kind(s.kind),
                file=s.file,
                line_start=s.line_start or None,
                line_end=s.line_end or None,
                change_type=ChangeType.modified,
            )
        )
        # Update changed_files with symbol names
        for cf in changed_files:
            if cf.path == s.file:
                cf.changed_symbols.append(s.name)

    changed_symbol_names = [s.name for s in changed_symbols]

    # ---- Caller graph (standard + deep) -----------------------------------
    caller_relationships: list[CallerRelationship] = []
    if mode in (AnalysisMode.standard, AnalysisMode.deep):
        raw_callers = find_callers_in_diff(changed_symbol_names, file_diffs)
        for caller, callee, caller_file, caller_line in raw_callers:
            caller_relationships.append(
                CallerRelationship(
                    caller=caller,
                    callee=callee,
                    caller_file=caller_file,
                    caller_line=caller_line,
                    confidence=Confidence.potential,
                )
            )

    # ---- Affected symbols (symbols that call a changed symbol) ------------
    affected_symbol_names = {cr.caller for cr in caller_relationships}
    affected_symbols: list[Symbol] = [
        Symbol(
            name=n,
            kind=SymbolKind.function,
            file=next(
                (cr.caller_file for cr in caller_relationships if cr.caller == n),
                "unknown",
            ),
            change_type=None,
        )
        for n in affected_symbol_names
        if n not in seen_sym_names
    ]

    # ---- Risks ------------------------------------------------------------
    risks = _infer_risks(file_diffs, changed_symbol_names)

    # ---- Test recommendations ---------------------------------------------
    test_recommendations = _build_recommendations(changed_symbol_names, risks)
    if mode == AnalysisMode.quick:
        test_recommendations = test_recommendations[:2]

    # ---- Summary ----------------------------------------------------------
    risk_counts = SummaryRisks(
        high=sum(1 for r in risks if r.level == RiskLevel.high),
        medium=sum(1 for r in risks if r.level == RiskLevel.medium),
        low=sum(1 for r in risks if r.level == RiskLevel.low),
        info=sum(1 for r in risks if r.level == RiskLevel.info),
    )
    summary = ReportSummary(
        changed_files=len(changed_files),
        changed_symbols=len(changed_symbols),
        affected_symbols=len(affected_symbols),
        caller_relationships=len(caller_relationships),
        risks=risk_counts,
        test_recommendations=len(test_recommendations),
    )

    # ---- Project context --------------------------------------------------
    diff_lines = diff_text.count("\n")
    project_context = ProjectContext(
        inferred_language="Python",
        total_files_changed=len(changed_files),
        total_symbols_changed=len(changed_symbols),
        diff_size_lines=diff_lines,
    )

    return Report(
        session_id=session_id,
        created_at=datetime.now(timezone.utc),
        analysis_mode=mode,
        project_context=project_context,
        summary=summary,
        changed_files=changed_files,
        changed_symbols=changed_symbols,
        affected_symbols=affected_symbols,
        caller_relationships=caller_relationships,
        risks=risks,
        test_recommendations=test_recommendations,
        limitations=[
            "Caller detection uses static AST analysis only; dynamic dispatch and monkey-patching are not captured.",
            "Cross-repository calls are not analysed.",
            "Only the diff is available; full project source is not read.",
            "All caller relationships and risk assessments are labelled 'potential' unless runtime verification confirms them.",
        ],
        explanations={
            "affected_symbols": "Symbols found in the diff that call a changed symbol.",
            "caller_relationships": "Statically inferred call edges within the provided diff.",
            "risks": "Heuristic rules applied to AST change patterns (signature changes, deletions, large churn, removed error handling).",
            "potential": "Results labelled 'potential' could not be proven statically and may not be accurate.",
        },
        is_demo=is_demo,
        scenario_id=scenario_id,
    )
