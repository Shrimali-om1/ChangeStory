/**
 * Typed fetch wrappers for the ChangeStory backend API.
 * Base URL: http://localhost:8000/api/v1  (proxied via Next.js rewrites in dev)
 */

import type {
  AnalyzeRequest,
  Report,
  ScenariosResponse,
  VerifyResponse,
} from "./types";

// In development the Next.js rewrite in next.config.ts proxies /api/* → http://localhost:8000/api/*
// so we avoid CORS entirely. In production set NEXT_PUBLIC_API_BASE to the backend origin.
const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ??
  (typeof window !== "undefined" ? "/api/v1" : "http://localhost:8000/api/v1");

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });

  if (!res.ok) {
    let message = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      if (typeof body.detail === "string") {
        message = body.detail;
      } else if (Array.isArray(body.detail)) {
        message = body.detail.map((e: { msg: string }) => e.msg).join("; ");
      }
    } catch {
      // ignore parse errors
    }
    throw new Error(message);
  }

  return res.json() as Promise<T>;
}

export async function postAnalyze(req: AnalyzeRequest): Promise<Report> {
  return apiFetch<Report>("/analyze", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

export async function getReport(sessionId: string): Promise<Report> {
  return apiFetch<Report>(`/reports/${sessionId}`);
}

export async function getScenarios(): Promise<ScenariosResponse> {
  return apiFetch<ScenariosResponse>("/scenarios");
}

export async function postAnalyzeScenario(scenarioId: string): Promise<Report> {
  return apiFetch<Report>(`/scenarios/${scenarioId}/analyze`, { method: "POST" });
}

export async function postVerify(sessionId: string): Promise<VerifyResponse> {
  return apiFetch<VerifyResponse>(`/verify/${sessionId}`, { method: "POST" });
}

/** Returns a direct URL for browser-initiated download (no auth needed). */
export function exportJsonUrl(sessionId: string): string {
  return `${API_BASE}/reports/${sessionId}/export.json`;
}

export function exportMdUrl(sessionId: string): string {
  return `${API_BASE}/reports/${sessionId}/export.md`;
}
