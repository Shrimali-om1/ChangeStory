"use client";

import { useState } from "react";
import type { Report, VerificationResult } from "@/lib/types";
import ReportSummary from "./ReportSummary";
import ChangedFiles from "./ChangedFiles";
import ChangedSymbols from "./ChangedSymbols";
import RiskList from "./RiskList";
import TestRecommendations from "./TestRecommendations";
import VerificationPanel from "./VerificationPanel";
import ExportPanel from "./ExportPanel";

interface Props {
  report: Report;
}

export default function ReportView({ report: initialReport }: Props) {
  const [report, setReport] = useState<Report>(initialReport);

  const handleVerified = (result: VerificationResult) => {
    setReport((prev) => ({ ...prev, verification: result }));
  };

  const sections = [
    { id: "summary", label: "Summary" },
    { id: "files", label: "Files" },
    { id: "symbols", label: "Symbols" },
    { id: "risks", label: "Risks" },
    { id: "tests", label: "Tests" },
    ...(report.limitations.length > 0 ? [{ id: "limitations", label: "Limitations" }] : []),
  ];

  const scrollTo = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <div className="space-y-8">
      {/* In-page nav */}
      <nav className="flex flex-wrap gap-2 pb-2 border-b border-gray-200 sticky top-0 bg-white z-10 pt-2 -mx-4 px-4 sm:-mx-6 sm:px-6">
        {sections.map((s) => (
          <button
            key={s.id}
            onClick={() => scrollTo(s.id)}
            className="text-xs font-medium text-gray-500 hover:text-blue-600 px-2 py-1 rounded hover:bg-blue-50 transition-colors"
          >
            {s.label}
          </button>
        ))}
        <div className="ml-auto">
          <ExportPanel report={report} />
        </div>
      </nav>

      {/* Summary */}
      <div id="summary">
        <ReportSummary report={report} />
      </div>

      {/* Verification — shown only for demo sessions */}
      {report.is_demo && (
        <VerificationPanel
          sessionId={report.session_id}
          isDemo={report.is_demo}
          existingResult={report.verification}
          onVerified={handleVerified}
        />
      )}

      {/* Changed files */}
      {report.changed_files.length > 0 && (
        <div id="files">
          <ChangedFiles files={report.changed_files} />
        </div>
      )}

      {/* Changed & affected symbols + caller relationships */}
      {(report.changed_symbols.length > 0 ||
        report.affected_symbols.length > 0 ||
        report.caller_relationships.length > 0) && (
        <div id="symbols">
          <ChangedSymbols
            changedSymbols={report.changed_symbols}
            affectedSymbols={report.affected_symbols}
            callerRelationships={report.caller_relationships}
            explanations={report.explanations}
          />
        </div>
      )}

      {/* Risks */}
      {report.risks.length > 0 && (
        <div id="risks">
          <RiskList risks={report.risks} />
        </div>
      )}

      {/* Test recommendations */}
      {report.test_recommendations.length > 0 && (
        <div id="tests">
          <TestRecommendations recommendations={report.test_recommendations} />
        </div>
      )}

      {/* Limitations */}
      {report.limitations.length > 0 && (
        <div id="limitations">
          <section aria-label="Limitations">
            <h3 className="text-base font-bold text-gray-900 mb-2">Limitations</h3>
            <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
              <ul className="space-y-1">
                {report.limitations.map((lim, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                    <span className="text-gray-400 mt-0.5">•</span>
                    {lim}
                  </li>
                ))}
              </ul>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
