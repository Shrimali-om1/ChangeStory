"use client";

import { useState } from "react";
import type { VerificationResult } from "@/lib/types";
import { postVerify } from "@/lib/api";

interface Props {
  sessionId: string;
  isDemo: boolean;
  existingResult: VerificationResult | null;
  onVerified: (result: VerificationResult) => void;
}

export default function VerificationPanel({
  sessionId,
  isDemo,
  existingResult,
  onVerified,
}: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<VerificationResult | null>(existingResult);

  if (!isDemo) return null;

  const handleVerify = async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await postVerify(sessionId);
      setResult(resp.verification);
      onVerified(resp.verification);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Verification failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section
      aria-label="Verification"
      className="rounded-lg border border-emerald-200 bg-emerald-50 p-4"
    >
      <div className="flex flex-wrap items-center justify-between gap-3 mb-2">
        <div>
          <h3 className="text-base font-bold text-gray-900">Verification</h3>
          <p className="text-xs text-gray-500 mt-0.5">
            Runs pytest against the bundled sample project only — no arbitrary code execution.
          </p>
        </div>
        {!result && (
          <button
            onClick={handleVerify}
            disabled={loading}
            className="flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:ring-offset-2 disabled:opacity-50 transition-colors"
          >
            {loading ? (
              <>
                <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Running…
              </>
            ) : (
              "Run Verification"
            )}
          </button>
        )}
      </div>

      {error && (
        <p className="text-sm text-red-600 mb-2">{error}</p>
      )}

      {result && (
        <div className="mt-3 space-y-3">
          {result.ran ? (
            <>
              {/* Summary row */}
              <div className="flex gap-4 text-sm">
                <span className="text-emerald-700 font-semibold">✓ {result.passed} passed</span>
                {result.failed > 0 && (
                  <span className="text-red-700 font-semibold">✗ {result.failed} failed</span>
                )}
                {result.skipped > 0 && (
                  <span className="text-gray-500">{result.skipped} skipped</span>
                )}
              </div>

              {/* Confirmed safe */}
              {result.confirmed_safe.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-gray-500 mb-1">Confirmed safe:</p>
                  <div className="flex flex-wrap gap-1">
                    {result.confirmed_safe.map((t) => (
                      <span key={t} className="font-mono text-xs bg-emerald-100 text-emerald-800 rounded px-2 py-0.5">
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Confirmed failing */}
              {result.confirmed_failing.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-gray-500 mb-1">Confirmed failing:</p>
                  <div className="flex flex-wrap gap-1">
                    {result.confirmed_failing.map((t) => (
                      <span key={t} className="font-mono text-xs bg-red-100 text-red-800 rounded px-2 py-0.5">
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Raw output */}
              {result.output && (
                <details>
                  <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700 select-none">
                    Raw pytest output
                  </summary>
                  <pre className="mt-2 text-xs font-mono bg-gray-900 text-gray-100 rounded p-3 overflow-x-auto whitespace-pre-wrap max-h-64">
                    {result.output}
                  </pre>
                </details>
              )}

              {result.note && (
                <p className="text-xs text-gray-500 italic">{result.note}</p>
              )}
            </>
          ) : (
            <p className="text-sm text-gray-600">
              Verification did not run.{result.note ? ` ${result.note}` : ""}
            </p>
          )}
        </div>
      )}
    </section>
  );
}
