# ChangeStory — Frontend

**Stack:** Next.js 14+ · React · TypeScript

## Setup

```bash
npm create next-app@latest . --typescript --tailwind --eslint --app
npm install
npm run dev
```

## API integration

The backend runs at `http://localhost:8000`.  See `../docs/API_CONTRACT.md` for all
endpoints, request shapes, and response types.

## Key pages to build

| Route | Purpose |
|-------|---------|
| `/` | Landing / upload diff or choose a scenario |
| `/report/[session_id]` | Full report view |
| `/report/[session_id]/export` | Export controls (JSON / MD) |
| `/scenarios` | Browse bundled demo scenarios |

## Suggested component structure

```
frontend/
├── app/
│   ├── page.tsx               # Landing
│   ├── report/[session_id]/
│   │   └── page.tsx           # Report view
│   └── scenarios/
│       └── page.tsx           # Demo browser
├── components/
│   ├── DiffUploader.tsx
│   ├── ReportSummary.tsx
│   ├── ChangedSymbols.tsx
│   ├── CallerGraph.tsx
│   ├── RiskList.tsx
│   └── TestRecommendations.tsx
└── lib/
    ├── api.ts                 # Typed fetch wrappers
    └── types.ts               # Mirror of backend/app/models.py
```

## Types

Mirror the Pydantic models from `docs/API_CONTRACT.md` into `lib/types.ts`.
Example:

```typescript
export type AnalysisMode = "quick" | "standard" | "deep";
export type Confidence = "confirmed" | "potential" | "unknown";
export type RiskLevel = "high" | "medium" | "low" | "info";

export interface Report {
  session_id: string;
  created_at: string;
  analysis_mode: AnalysisMode;
  project_context: ProjectContext;
  summary: ReportSummary;
  changed_files: ChangedFile[];
  changed_symbols: Symbol[];
  affected_symbols: Symbol[];
  caller_relationships: CallerRelationship[];
  risks: Risk[];
  test_recommendations: TestRecommendation[];
  verification: VerificationResult | null;
  limitations: string[];
  explanations: Record<string, string>;
  is_demo: boolean;
  scenario_id: string | null;
}
```
