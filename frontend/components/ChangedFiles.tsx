import type { ChangedFile } from "@/lib/types";
import { ChangeChip } from "./Badges";

interface Props {
  files: ChangedFile[];
}

export default function ChangedFiles({ files }: Props) {
  if (!files.length) return null;

  return (
    <section aria-label="Changed files">
      <h3 className="text-base font-bold text-gray-900 mb-3">Changed Files</h3>
      <div className="overflow-x-auto rounded-lg border border-gray-200">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide">
            <tr>
              <th className="text-left px-4 py-2.5 font-semibold">Path</th>
              <th className="text-left px-4 py-2.5 font-semibold">Type</th>
              <th className="text-right px-4 py-2.5 font-semibold text-green-600">+Added</th>
              <th className="text-right px-4 py-2.5 font-semibold text-red-600">−Removed</th>
              <th className="text-left px-4 py-2.5 font-semibold">Changed symbols</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 bg-white">
            {files.map((f) => (
              <tr key={f.path} className="hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3 font-mono text-xs text-gray-800 max-w-xs truncate">
                  {f.path}
                </td>
                <td className="px-4 py-3">
                  <ChangeChip type={f.change_type} />
                </td>
                <td className="px-4 py-3 text-right font-mono text-green-600 text-xs">
                  +{f.lines_added}
                </td>
                <td className="px-4 py-3 text-right font-mono text-red-600 text-xs">
                  −{f.lines_removed}
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    {f.changed_symbols.length > 0 ? (
                      f.changed_symbols.map((sym) => (
                        <span
                          key={sym}
                          className="inline-block bg-gray-100 text-gray-700 font-mono text-xs px-1.5 py-0.5 rounded"
                        >
                          {sym}
                        </span>
                      ))
                    ) : (
                      <span className="text-gray-400 text-xs italic">—</span>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
