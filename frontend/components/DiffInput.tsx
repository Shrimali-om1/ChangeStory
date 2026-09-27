"use client";

import { useState, useRef } from "react";
import type { AnalysisMode } from "@/lib/types";

interface Props {
  initialDiff?: string;
  initialMode?: AnalysisMode;
  onSubmit: (diff: string, mode: AnalysisMode) => void;
  onReset: () => void;
  loading: boolean;
}

const MODES: { value: AnalysisMode; label: string; description: string }[] = [
  { value: "quick", label: "Quick", description: "Symbol ID + risk summary" },
  { value: "standard", label: "Standard", description: "Adds caller graph & test recs" },
  { value: "deep", label: "Deep", description: "Best-effort transitive impact" },
];

export default function DiffInput({ initialDiff = "", initialMode = "standard", onSubmit, onReset, loading }: Props) {
  const [diff, setDiff] = useState(initialDiff);
  const [mode, setMode] = useState<AnalysisMode>(initialMode);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Sync when parent updates initial values (scenario selection)
  const [prevInitialDiff, setPrevInitialDiff] = useState(initialDiff);
  if (initialDiff !== prevInitialDiff) {
    setPrevInitialDiff(initialDiff);
    setDiff(initialDiff);
    setMode(initialMode);
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (diff.trim()) onSubmit(diff.trim(), mode);
  };

  const handleReset = () => {
    setDiff("");
    setMode("standard");
    onReset();
    textareaRef.current?.focus();
  };

  const lineCount = diff ? diff.split("\n").length : 0;

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Textarea */}
      <div>
        <div className="flex items-center justify-between mb-1.5">
          <label htmlFor="diff-input" className="text-sm font-medium text-gray-700">
            Unified diff
          </label>
          {diff && (
            <span className="text-xs text-gray-400">{lineCount} lines</span>
          )}
        </div>
        <textarea
          ref={textareaRef}
          id="diff-input"
          value={diff}
          onChange={(e) => setDiff(e.target.value)}
          placeholder={"Paste a unified diff here — e.g. git diff HEAD~1\n\ndiff --git a/src/..."}
          rows={14}
          spellCheck={false}
          className="w-full rounded-lg border border-gray-300 bg-gray-50 px-3 py-2.5 font-mono text-xs text-gray-800 placeholder:text-gray-400 focus:border-blue-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-100 resize-y"
        />
      </div>

      {/* Mode selector */}
      <div>
        <span className="text-sm font-medium text-gray-700 block mb-2">Analysis mode</span>
        <div className="flex gap-2 flex-wrap">
          {MODES.map((m) => (
            <label
              key={m.value}
              className={`flex-1 min-w-[110px] cursor-pointer rounded-lg border px-3 py-2 transition-all ${
                mode === m.value
                  ? "border-blue-500 bg-blue-50 ring-1 ring-blue-400"
                  : "border-gray-200 bg-white hover:border-blue-300"
              }`}
            >
              <input
                type="radio"
                name="mode"
                value={m.value}
                checked={mode === m.value}
                onChange={() => setMode(m.value)}
                className="sr-only"
              />
              <div className="font-semibold text-sm text-gray-900">{m.label}</div>
              <div className="text-xs text-gray-500 mt-0.5">{m.description}</div>
            </label>
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <button
          type="submit"
          disabled={loading || !diff.trim()}
          className="flex items-center gap-2 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? (
            <>
              <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Analyzing…
            </>
          ) : (
            "Analyze"
          )}
        </button>
        <button
          type="button"
          onClick={handleReset}
          disabled={loading}
          className="rounded-lg border border-gray-300 px-5 py-2.5 text-sm font-semibold text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-2 disabled:opacity-50 transition-colors"
        >
          Reset
        </button>
      </div>
    </form>
  );
}
