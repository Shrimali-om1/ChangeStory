/**
 * TypeScript types mirroring backend/app/models.py and docs/API_CONTRACT.md.
 * Keep in sync with the Pydantic models.
 */

export type AnalysisMode = "quick" | "standard" | "deep";
export type Confidence = "confirmed" | "potential" | "unknown";
export type RiskLevel = "high" | "medium" | "low" | "info";
export type ChangeType = "added" | "modified" | "deleted" | "renamed";
export type SymbolKind = "function" | "method" | "class" | "module";

export interface ChangedFile {
  path: string;
  change_type: ChangeType;
  lines_added: number;
  lines_removed: number;
  changed_symbols: string[];
}

export interface Symbol {
  name: string;
  kind: SymbolKind;
  file: string;
  line_start: number | null;
  line_end: number | null;
  change_type: ChangeType | null;
}

export interface CallerRelationship {
  caller: string;
  callee: string;
  caller_file: string;
  caller_line: number | null;
  confidence: Confidence;
}

export interface Risk {
  level: RiskLevel;
  title: string;
  description: string;
  affected_symbols: string[];
  evidence: string[];
  confidence: Confidence;
}

export interface TestRecommendation {
  title: string;
  rationale: string;
  suggested_test_ids: string[];
  priority: "high" | "medium" | "low";
}

export interface VerificationResult {
  ran: boolean;
  passed: number;
  failed: number;
  skipped: number;
  output: string;
  confirmed_safe: string[];
  confirmed_failing: string[];
  note: string;
}

export interface ProjectContext {
  inferred_language: string;
  total_files_changed: number;
  total_symbols_changed: number;
  diff_size_lines: number;
}

export interface SummaryRisks {
  high: number;
  medium: number;
  low: number;
  info: number;
}

export interface ReportSummary {
  changed_files: number;
  changed_symbols: number;
  affected_symbols: number;
  caller_relationships: number;
  risks: SummaryRisks;
  test_recommendations: number;
}

export interface Report {
  session_id: string;
  created_at: string;
  analysis_mode: AnalysisMode;
  project_context: ProjectContext;
  summary: ReportSummary;
  changed_files: ChangedFile[];
  changed_symbols: Symbol[];
  affected_symbols: Symbol[];
  caller_relationships: CallerRelationship[];
  risks: Risk[];
  test_recommendations: TestRecommendation[];
  verification: VerificationResult | null;
  limitations: string[];
  explanations: Record<string, string>;
  is_demo: boolean;
  scenario_id: string | null;
}

export interface Scenario {
  id: string;
  title: string;
  description: string;
  mode: AnalysisMode;
  diff: string;
}

export interface ScenariosResponse {
  scenarios: Scenario[];
}

export interface VerifyResponse {
  session_id: string;
  verification: VerificationResult;
}

export interface AnalyzeRequest {
  diff: string;
  mode?: AnalysisMode;
  project_root_hint?: string;
}

export interface ApiError {
  detail: string | Array<{ loc: string[]; msg: string; type: string }>;
}
