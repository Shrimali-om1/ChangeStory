import type { Risk } from "@/lib/types";
import { RiskBadge, ConfidenceBadge } from "./Badges";

interface Props {
  risks: Risk[];
}

const riskOrder = { high: 0, medium: 1, low: 2, info: 3 };

export default function RiskList({ risks }: Props) {
  if (!risks.length) return null;

  const sorted = [...risks].sort((a, b) => riskOrder[a.level] - riskOrder[b.level]);

  return (
    <section aria-label="Risks">
      <h3 className="text-base font-bold text-gray-900 mb-3">
        Risks
        <span className="ml-2 text-xs font-normal text-gray-400">({risks.length})</span>
      </h3>
      <div className="space-y-3">
        {sorted.map((risk, i) => (
          <div
            key={i}
            className={`rounded-lg border p-4 ${
              risk.level === "high"
                ? "border-red-200 bg-red-50"
                : risk.level === "medium"
                ? "border-yellow-200 bg-yellow-50"
                : risk.level === "low"
                ? "border-green-200 bg-green-50"
                : "border-blue-200 bg-blue-50"
            }`}
          >
            {/* Header */}
            <div className="flex flex-wrap items-center gap-2 mb-1.5">
              <RiskBadge level={risk.level} />
              <span className="font-semibold text-sm text-gray-900">{risk.title}</span>
              <ConfidenceBadge confidence={risk.confidence} />
            </div>

            {/* Description */}
            <p className="text-sm text-gray-700 mb-2">{risk.description}</p>

            {/* Affected symbols */}
            {risk.affected_symbols.length > 0 && (
              <div className="flex flex-wrap gap-1 mb-2">
                <span className="text-xs text-gray-500 mr-1">Affects:</span>
                {risk.affected_symbols.map((sym) => (
                  <span key={sym} className="font-mono text-xs bg-white border border-gray-200 rounded px-1.5 py-0.5 text-gray-700">
                    {sym}
                  </span>
                ))}
              </div>
            )}

            {/* Evidence */}
            {risk.evidence.length > 0 && (
              <details className="mt-2">
                <summary className="text-xs font-medium text-gray-500 cursor-pointer hover:text-gray-700 select-none">
                  Evidence ({risk.evidence.length})
                </summary>
                <ul className="mt-1.5 space-y-1">
                  {risk.evidence.map((ev, j) => (
                    <li key={j} className="font-mono text-xs bg-white border border-gray-200 rounded px-2 py-1 text-gray-700 whitespace-pre-wrap break-all">
                      {ev}
                    </li>
                  ))}
                </ul>
              </details>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
