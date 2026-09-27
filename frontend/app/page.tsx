"use client";

import { useState, useEffect, useCallback } from "react";
import type { Report, Scenario, AnalysisMode } from "@/lib/types";
import { postAnalyze, getScenarios, postAnalyzeScenario, getReport } from "@/lib/api";
import DiffInput from "@/components/DiffInput";
import ScenarioPicker from "@/components/ScenarioPicker";
import ReportView from "@/components/ReportView";

type Phase = "input" | "loading" | "report" | "error";

export default function HomePage() {
  const [phase, setPhase] = useState<Phase>("input");
  const [report, setReport] = useState<Report | null>(null);
  const [errorMsg, setErrorMsg] = useState<string>("");
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [scenariosError, setScenariosError] = useState<string>("");
  const [selectedScenario, setSelectedScenario] = useState<Scenario | null>(null);

  // If URL has ?session=<id>, load that report automatically (used by CLI redirect)
  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    const sessionId = params.get("session");
    if (!sessionId) return;
    setPhase("loading");
    getReport(sessionId)
      .then((r) => {
        setReport(r);
        setPhase("report");
        // Clean up URL so refresh doesn't reload the same session
        window.history.replaceState({}, "", window.location.pathname);
      })
      .catch(() => {
        setErrorMsg(`Could not load report for session: ${sessionId}`);
        setPhase("error");
      });
  }, []);

  // Load scenarios on mount
  useEffect(() => {
    getScenarios()
      .then((res) => setScenarios(res.scenarios))
      .catch(() => setScenariosError("Could not load demo scenarios — is the backend running?"));
  }, []);

  const handleAnalyze = useCallback(async (diff: string, mode: AnalysisMode) => {
    setPhase("loading");
    setErrorMsg("");
    try {
      const result = await postAnalyze({ diff, mode });
      setReport(result);
      setPhase("report");
    } catch (e) {
      setErrorMsg(e instanceof Error ? e.message : "Analysis failed");
      setPhase("error");
    }
  }, []);

  const handleScenarioSelect = useCallback(async (scenario: Scenario) => {
    setSelectedScenario(scenario);
    setPhase("loading");
    setErrorMsg("");
    try {
      const result = await postAnalyzeScenario(scenario.id);
      setReport(result);
      setPhase("report");
    } catch (e) {
      setErrorMsg(e instanceof Error ? e.message : "Analysis failed");
      setPhase("error");
    }
  }, []);

  const handleReset = useCallback(() => {
    setReport(null);
    setSelectedScenario(null);
    setPhase("input");
    setErrorMsg("");
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white font-bold text-sm">
              CS
            </div>
            <div>
              <h1 className="text-lg font-bold text-gray-900 leading-tight">ChangeStory</h1>
              <p className="text-xs text-gray-500 leading-tight">Python Git diff analyzer</p>
            </div>
          </div>
          {phase === "report" && report && (
            <button
              onClick={handleReset}
              className="text-sm text-gray-500 hover:text-gray-900 border border-gray-300 rounded-lg px-3 py-1.5 hover:bg-gray-50 transition-colors"
            >
              ← New analysis
            </button>
          )}
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
        {/* INPUT PHASE */}
        {(phase === "input" || phase === "loading") && (
          <div className="space-y-8">
            {/* Scenarios */}
            <section className="bg-white rounded-xl border border-gray-200 p-6">
              <h2 className="text-base font-bold text-gray-900 mb-4">Demo Scenarios</h2>
              {scenariosError ? (
                <p className="text-sm text-red-600">{scenariosError}</p>
              ) : scenarios.length === 0 ? (
                <div className="flex items-center gap-2 text-sm text-gray-400">
                  <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Loading scenarios…
                </div>
              ) : (
                <ScenarioPicker
                  scenarios={scenarios}
                  onSelect={handleScenarioSelect}
                  loading={phase === "loading"}
                />
              )}
            </section>

            {/* Divider */}
            <div className="flex items-center gap-3">
              <div className="flex-1 border-t border-gray-200" />
              <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">or paste your own diff</span>
              <div className="flex-1 border-t border-gray-200" />
            </div>

            {/* Diff input */}
            <section className="bg-white rounded-xl border border-gray-200 p-6">
              <h2 className="text-base font-bold text-gray-900 mb-4">Analyze a Diff</h2>
              <DiffInput
                initialDiff={selectedScenario?.diff ?? ""}
                initialMode={selectedScenario?.mode ?? "standard"}
                onSubmit={handleAnalyze}
                onReset={handleReset}
                loading={phase === "loading"}
              />
            </section>

            {/* Loading overlay */}
            {phase === "loading" && (
              <div className="fixed inset-0 bg-white/60 backdrop-blur-sm flex items-center justify-center z-50">
                <div className="bg-white rounded-xl border border-gray-200 shadow-lg px-8 py-6 flex flex-col items-center gap-3">
                  <svg className="animate-spin w-8 h-8 text-blue-600" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  <p className="text-sm font-medium text-gray-700">Analyzing diff…</p>
                  <p className="text-xs text-gray-400">Running AST analysis & building report</p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ERROR PHASE */}
        {phase === "error" && (
          <div className="max-w-2xl mx-auto">
            <div className="rounded-xl border border-red-200 bg-red-50 p-6">
              <div className="flex items-start gap-3">
                <svg className="w-5 h-5 text-red-500 mt-0.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div className="flex-1">
                  <h3 className="font-semibold text-red-800 mb-1">Analysis failed</h3>
                  <p className="text-sm text-red-700">{errorMsg}</p>
                  <p className="text-xs text-red-500 mt-1">
                    Make sure the backend is running at{" "}
                    <code className="font-mono">http://localhost:8000</code>.
                  </p>
                </div>
              </div>
              <button
                onClick={handleReset}
                className="mt-4 text-sm font-medium text-red-700 hover:text-red-900 underline"
              >
                ← Try again
              </button>
            </div>
          </div>
        )}

        {/* REPORT PHASE */}
        {phase === "report" && report && (
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <ReportView report={report} />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-200 mt-16 py-6">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 text-center text-xs text-gray-400">
          ChangeStory — local-first Python diff analyzer · no external services
        </div>
      </footer>
    </div>
  );
}
