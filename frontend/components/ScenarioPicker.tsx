"use client";

import { useState } from "react";
import type { Scenario } from "@/lib/types";

interface Props {
  scenarios: Scenario[];
  onSelect: (scenario: Scenario) => void;
  loading: boolean;
}

export default function ScenarioPicker({ scenarios = [], onSelect, loading }: Props) {
  const [selected, setSelected] = useState<string | null>(null);

  return (
    <div>
      <p className="text-sm text-gray-500 mb-3">
        Choose a bundled demo to explore without providing your own diff:
      </p>
      <div className="grid gap-3 sm:grid-cols-3">
        {(scenarios ?? []).map((s) => (
          <button
            key={s.id}
            disabled={loading}
            onClick={() => {
              setSelected(s.id);
              onSelect(s);
            }}
            className={`text-left rounded-lg border p-4 transition-all focus:outline-none focus:ring-2 focus:ring-blue-400 disabled:opacity-50 ${
              selected === s.id
                ? "border-blue-500 bg-blue-50 ring-1 ring-blue-400"
                : "border-gray-200 bg-white hover:border-blue-300 hover:bg-blue-50/40"
            }`}
          >
            <div className="font-semibold text-sm text-gray-900 mb-1">{s.title}</div>
            <div className="text-xs text-gray-500 leading-snug">{s.description}</div>
            <div className="mt-2 text-xs text-blue-600 font-medium">Mode: {s.mode}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
