import type { Symbol, CallerRelationship } from "@/lib/types";
import { ChangeChip, ConfidenceBadge } from "./Badges";

interface Props {
  changedSymbols: Symbol[];
  affectedSymbols: Symbol[];
  callerRelationships: CallerRelationship[];
  explanations: Record<string, string>;
}

function SymbolRow({ sym }: { sym: Symbol }) {
  return (
    <div className="flex flex-wrap items-start gap-2 py-2.5 border-b border-gray-100 last:border-0">
      <span className="font-mono text-xs text-gray-900 font-semibold break-all">{sym.name}</span>
      <span className="text-xs text-gray-400 bg-gray-100 rounded px-1.5 py-0.5">{sym.kind}</span>
      {sym.change_type && <ChangeChip type={sym.change_type} />}
      <span className="text-xs text-gray-500 font-mono truncate max-w-xs">
        {sym.file}
        {sym.line_start != null ? `:${sym.line_start}` : ""}
      </span>
    </div>
  );
}

export default function ChangedSymbols({
  changedSymbols,
  affectedSymbols,
  callerRelationships,
  explanations,
}: Props) {
  return (
    <section aria-label="Symbols">
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Changed symbols */}
        {changedSymbols.length > 0 && (
          <div>
            <h3 className="text-base font-bold text-gray-900 mb-2">
              Changed Symbols
              <span className="ml-2 text-xs font-normal text-gray-400">({changedSymbols.length})</span>
            </h3>
            <div className="rounded-lg border border-gray-200 bg-white px-4">
              {changedSymbols.map((s) => (
                <SymbolRow key={`${s.file}:${s.name}`} sym={s} />
              ))}
            </div>
          </div>
        )}

        {/* Affected symbols */}
        {affectedSymbols.length > 0 && (
          <div>
            <h3 className="text-base font-bold text-gray-900 mb-1">
              Potentially Affected Symbols
              <span className="ml-2 text-xs font-normal text-gray-400">({affectedSymbols.length})</span>
            </h3>
            {explanations["affected_symbols"] && (
              <p className="text-xs text-gray-500 mb-2 italic">{explanations["affected_symbols"]}</p>
            )}
            <div className="rounded-lg border border-amber-200 bg-amber-50 px-4">
              {affectedSymbols.map((s) => (
                <SymbolRow key={`${s.file}:${s.name}`} sym={s} />
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Caller relationships */}
      {callerRelationships.length > 0 && (
        <div className="mt-6">
          <h3 className="text-base font-bold text-gray-900 mb-3">
            Caller Relationships
            <span className="ml-2 text-xs font-normal text-gray-400">({callerRelationships.length})</span>
          </h3>
          <div className="overflow-x-auto rounded-lg border border-gray-200">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide">
                <tr>
                  <th className="text-left px-4 py-2.5 font-semibold">Caller</th>
                  <th className="text-left px-4 py-2.5 font-semibold">→ Callee</th>
                  <th className="text-left px-4 py-2.5 font-semibold">File</th>
                  <th className="text-left px-4 py-2.5 font-semibold">Line</th>
                  <th className="text-left px-4 py-2.5 font-semibold">Confidence</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 bg-white">
                {callerRelationships.map((cr, i) => (
                  <tr key={i} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3 font-mono text-xs text-gray-800 max-w-[200px] truncate">
                      {cr.caller}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-blue-700 max-w-[200px] truncate">
                      {cr.callee}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-gray-500 max-w-[200px] truncate">
                      {cr.caller_file}
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-500">
                      {cr.caller_line ?? "—"}
                    </td>
                    <td className="px-4 py-3">
                      <ConfidenceBadge confidence={cr.confidence} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </section>
  );
}
