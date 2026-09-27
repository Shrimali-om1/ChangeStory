import type { Report } from "@/lib/types";
import { RiskBadge } from "./Badges";

interface Props {
  report: Report;
}

interface StatCardProps {
  label: string;
  value: number | string;
  sub?: string;
  highlight?: boolean;
}

function StatCard({ label, value, sub, highlight }: StatCardProps) {
  return (
    <div
      className={`rounded-xl border px-5 py-4 flex flex-col gap-1 ${
        highlight ? "border-blue-200 bg-blue-50" : "border-gray-200 bg-white"
      }`}
    >
      <div className={`text-2xl font-bold ${highlight ? "text-blue-700" : "text-gray-900"}`}>
        {value}
      </div>
      <div className="text-sm font-medium text-gray-700">{label}</div>
      {sub && <div className="text-xs text-gray-400">{sub}</div>}
    </div>
  );
}

export default function ReportSummary({ report }: Props) {
  const { summary, project_context, analysis_mode, created_at, scenario_id } = report;
  const { risks } = summary;

  const riskStr = [
    risks.high > 0 ? `${risks.high} high` : null,
    risks.medium > 0 ? `${risks.medium} med` : null,
    risks.low > 0 ? `${risks.low} low` : null,
    risks.info > 0 ? `${risks.info} info` : null,
  ]
    .filter(Boolean)
    .join(" · ") || "none";

  return (
    <section aria-label="Report summary">
      {/* Header row */}
      <div className="flex flex-wrap items-center gap-3 mb-4">
        <h2 className="text-lg font-bold text-gray-900">Summary</h2>
        <span className="text-xs bg-gray-100 text-gray-600 rounded px-2 py-0.5 font-mono">
          {report.session_id}
        </span>
        <span className="text-xs text-gray-400">
          {new Date(created_at).toLocaleString()} · mode: {analysis_mode}
        </span>
        {scenario_id && (
          <span className="text-xs bg-purple-100 text-purple-700 rounded px-2 py-0.5">
            demo: {scenario_id}
          </span>
        )}
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-4">
        <StatCard label="Changed files" value={summary.changed_files} />
        <StatCard label="Changed symbols" value={summary.changed_symbols} />
        <StatCard label="Affected symbols" value={summary.affected_symbols} sub="potential" />
        <StatCard label="Caller links" value={summary.caller_relationships} />
        <StatCard
          label="Risks"
          value={risks.high + risks.medium + risks.low + risks.info}
          sub={riskStr}
          highlight={risks.high > 0}
        />
        <StatCard label="Test recs" value={summary.test_recommendations} />
      </div>

      {/* Risk breakdown row */}
      {(risks.high > 0 || risks.medium > 0) && (
        <div className="flex flex-wrap gap-2">
          {risks.high > 0 && (
            <div className="flex items-center gap-1.5">
              <RiskBadge level="high" />
              <span className="text-sm text-gray-700">{risks.high}</span>
            </div>
          )}
          {risks.medium > 0 && (
            <div className="flex items-center gap-1.5">
              <RiskBadge level="medium" />
              <span className="text-sm text-gray-700">{risks.medium}</span>
            </div>
          )}
          {risks.low > 0 && (
            <div className="flex items-center gap-1.5">
              <RiskBadge level="low" />
              <span className="text-sm text-gray-700">{risks.low}</span>
            </div>
          )}
          {risks.info > 0 && (
            <div className="flex items-center gap-1.5">
              <RiskBadge level="info" />
              <span className="text-sm text-gray-700">{risks.info}</span>
            </div>
          )}
        </div>
      )}

      {/* Project context */}
      <div className="mt-4 text-xs text-gray-400 space-x-3">
        <span>Language: {project_context.inferred_language}</span>
        <span>·</span>
        <span>Diff size: {project_context.diff_size_lines} lines</span>
      </div>
    </section>
  );
}
