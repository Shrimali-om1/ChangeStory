import type { TestRecommendation } from "@/lib/types";
import { PriorityBadge } from "./Badges";

interface Props {
  recommendations: TestRecommendation[];
}

const priorityOrder = { high: 0, medium: 1, low: 2 };

export default function TestRecommendations({ recommendations }: Props) {
  if (!recommendations.length) return null;

  const sorted = [...recommendations].sort(
    (a, b) =>
      (priorityOrder[a.priority as keyof typeof priorityOrder] ?? 99) -
      (priorityOrder[b.priority as keyof typeof priorityOrder] ?? 99)
  );

  return (
    <section aria-label="Test recommendations">
      <h3 className="text-base font-bold text-gray-900 mb-3">
        Test Recommendations
        <span className="ml-2 text-xs font-normal text-gray-400">({recommendations.length})</span>
      </h3>
      <div className="space-y-3">
        {sorted.map((rec, i) => (
          <div key={i} className="rounded-lg border border-gray-200 bg-white p-4">
            <div className="flex flex-wrap items-center gap-2 mb-1.5">
              <PriorityBadge priority={rec.priority} />
              <span className="font-semibold text-sm text-gray-900">{rec.title}</span>
            </div>
            <p className="text-sm text-gray-600 mb-2">{rec.rationale}</p>
            {rec.suggested_test_ids.length > 0 && (
              <div>
                <span className="text-xs text-gray-500 block mb-1">Suggested tests:</span>
                <div className="flex flex-wrap gap-1.5">
                  {rec.suggested_test_ids.map((tid) => (
                    <span
                      key={tid}
                      className="font-mono text-xs bg-gray-100 text-gray-700 rounded px-2 py-0.5"
                    >
                      {tid}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
