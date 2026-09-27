import type { RiskLevel, Confidence } from "@/lib/types";

// ---- Risk badge ----
const riskColors: Record<RiskLevel, string> = {
  high: "bg-red-100 text-red-800 border-red-200",
  medium: "bg-yellow-100 text-yellow-800 border-yellow-200",
  low: "bg-green-100 text-green-800 border-green-200",
  info: "bg-blue-100 text-blue-800 border-blue-200",
};

const riskDot: Record<RiskLevel, string> = {
  high: "bg-red-500",
  medium: "bg-yellow-500",
  low: "bg-green-500",
  info: "bg-blue-500",
};

export function RiskBadge({ level }: { level: RiskLevel }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-semibold border ${riskColors[level]}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${riskDot[level]}`} />
      {level.toUpperCase()}
    </span>
  );
}

// ---- Confidence badge ----
const confColors: Record<Confidence, string> = {
  confirmed: "bg-emerald-100 text-emerald-800 border-emerald-200",
  potential: "bg-amber-100 text-amber-800 border-amber-200",
  unknown: "bg-gray-100 text-gray-600 border-gray-200",
};

export function ConfidenceBadge({ confidence }: { confidence: Confidence }) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${confColors[confidence]}`}
    >
      {confidence}
    </span>
  );
}

// ---- Priority badge ----
const priorityColors: Record<string, string> = {
  high: "bg-red-100 text-red-700 border-red-200",
  medium: "bg-yellow-100 text-yellow-700 border-yellow-200",
  low: "bg-green-100 text-green-700 border-green-200",
};

export function PriorityBadge({ priority }: { priority: string }) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${priorityColors[priority] ?? "bg-gray-100 text-gray-600"}`}
    >
      {priority}
    </span>
  );
}

// ---- Change-type chip ----
const changeColors: Record<string, string> = {
  added: "bg-green-100 text-green-700",
  modified: "bg-blue-100 text-blue-700",
  deleted: "bg-red-100 text-red-700",
  renamed: "bg-purple-100 text-purple-700",
};

export function ChangeChip({ type }: { type: string }) {
  return (
    <span
      className={`inline-block px-1.5 py-0.5 rounded text-xs font-mono font-medium ${changeColors[type] ?? "bg-gray-100 text-gray-700"}`}
    >
      {type}
    </span>
  );
}
