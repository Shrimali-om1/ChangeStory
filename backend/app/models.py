"""
ChangeStory — Pydantic models (shared with frontend via docs/API_CONTRACT.md).
Keep this file in sync with docs/API_CONTRACT.md.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class AnalysisMode(str, Enum):
    quick = "quick"
    standard = "standard"
    deep = "deep"


class Confidence(str, Enum):
    confirmed = "confirmed"
    potential = "potential"
    unknown = "unknown"


class RiskLevel(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"
    info = "info"


class ChangeType(str, Enum):
    added = "added"
    modified = "modified"
    deleted = "deleted"
    renamed = "renamed"


class SymbolKind(str, Enum):
    function = "function"
    method = "method"
    class_ = "class"
    module = "module"


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------


class ChangedFile(BaseModel):
    path: str
    change_type: ChangeType
    lines_added: int = 0
    lines_removed: int = 0
    changed_symbols: list[str] = Field(default_factory=list)


class Symbol(BaseModel):
    name: str
    kind: SymbolKind
    file: str
    line_start: int | None = None
    line_end: int | None = None
    change_type: ChangeType | None = None


class CallerRelationship(BaseModel):
    caller: str
    callee: str
    caller_file: str
    caller_line: int | None = None
    confidence: Confidence = Confidence.potential


class Risk(BaseModel):
    level: RiskLevel
    title: str
    description: str
    affected_symbols: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    confidence: Confidence = Confidence.potential


class TestRecommendation(BaseModel):
    title: str
    rationale: str
    suggested_test_ids: list[str] = Field(default_factory=list)
    priority: str = "medium"  # "high" | "medium" | "low"


class VerificationResult(BaseModel):
    ran: bool
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    output: str = ""
    confirmed_safe: list[str] = Field(default_factory=list)
    confirmed_failing: list[str] = Field(default_factory=list)
    note: str = ""


class ProjectContext(BaseModel):
    inferred_language: str = "Python"
    total_files_changed: int = 0
    total_symbols_changed: int = 0
    diff_size_lines: int = 0


class SummaryRisks(BaseModel):
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0


class ReportSummary(BaseModel):
    changed_files: int = 0
    changed_symbols: int = 0
    affected_symbols: int = 0
    caller_relationships: int = 0
    risks: SummaryRisks = Field(default_factory=SummaryRisks)
    test_recommendations: int = 0


# ---------------------------------------------------------------------------
# Top-level report
# ---------------------------------------------------------------------------


class Report(BaseModel):
    session_id: str
    created_at: datetime
    analysis_mode: AnalysisMode

    project_context: ProjectContext
    summary: ReportSummary

    changed_files: list[ChangedFile] = Field(default_factory=list)
    changed_symbols: list[Symbol] = Field(default_factory=list)
    affected_symbols: list[Symbol] = Field(default_factory=list)
    caller_relationships: list[CallerRelationship] = Field(default_factory=list)
    risks: list[Risk] = Field(default_factory=list)
    test_recommendations: list[TestRecommendation] = Field(default_factory=list)

    verification: VerificationResult | None = None

    limitations: list[str] = Field(default_factory=list)
    explanations: dict[str, str] = Field(default_factory=dict)

    # Flag — true only for reports created from a bundled scenario
    is_demo: bool = False
    scenario_id: str | None = None


# ---------------------------------------------------------------------------
# Request / Response wrappers
# ---------------------------------------------------------------------------


class AnalyzeRequest(BaseModel):
    diff: str = Field(..., min_length=1, description="Unified diff text")
    mode: AnalysisMode = AnalysisMode.standard
    project_root_hint: str | None = None


class VerifyResponse(BaseModel):
    session_id: str
    verification: VerificationResult


class Scenario(BaseModel):
    id: str
    title: str
    description: str
    mode: AnalysisMode
    diff: str


class ScenariosResponse(BaseModel):
    scenarios: list[Scenario]
