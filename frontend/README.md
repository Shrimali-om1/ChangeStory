# ChangeStory — Frontend Dashboard

**Stack:** Next.js 16 · React 19 · TypeScript · Tailwind CSS v4

---

## Quick start

```bash
# 1. Start the backend first (port 8000)
cd ../backend
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000

# 2. Start the frontend (new terminal)
cd ../frontend
npm install
npm run dev
```

Open **http://localhost:3000** in your browser.

The Next.js dev server proxies all `/api/*` requests to `http://localhost:8000/api/*`,
so no CORS configuration is needed.

---

## Available npm scripts

| Command | Purpose |
|---------|---------|
| `npm run dev` | Start dev server with hot reload |
| `npm run build` | Production build |
| `npm run start` | Serve the production build |
| `npm run lint` | ESLint check |

---

## Dashboard features

| Feature | Details |
|---------|---------|
| **Diff input** | Paste any unified diff; choose Quick / Standard / Deep mode |
| **Demo scenarios** | Three bundled scenarios loaded from `GET /api/v1/scenarios` |
| **Analyze** | Submits to `POST /api/v1/analyze` or `POST /api/v1/scenarios/{id}/analyze` |
| **Reset** | Clears state back to the input form |
| **Summary cards** | Changed files, symbols, affected symbols, caller links, risks, test recs |
| **Changed files table** | Path, change type, +/− line counts, changed symbols |
| **Changed symbols** | Qualified name, kind, file/line |
| **Affected symbols** | Potential impact symbols, amber-highlighted |
| **Caller relationships** | Caller → callee table with confidence labels |
| **Risks** | Sorted by severity; collapsible evidence |
| **Test recommendations** | Sorted by priority; suggested test IDs |
| **Verification** | Shown only when `report.is_demo === true`; calls `POST /api/v1/verify/{session_id}` |
| **Export** | JSON (`/export.json`) and Markdown (`/export.md`) — browser-initiated downloads |
| **Limitations** | Displayed from `report.limitations[]` |
| **Error states** | Friendly error panel with retry link |
| **Loading states** | Spinner overlay during analysis; inline spinner for scenarios/verify |

---

## API assumptions

All assumptions are derived from `docs/API_CONTRACT.md` — no routes or fields were invented.

| Assumption | Source |
|-----------|--------|
| Backend runs at `http://localhost:8000` | `README.md` |
| `POST /api/v1/scenarios/{id}/analyze` triggers analysis for a demo scenario | `backend/app/routes/scenarios.py` |
| `report.is_demo` is `true` only for bundled-scenario reports | `backend/app/models.py` |
| `POST /api/v1/verify/{session_id}` returns `{ session_id, verification }` | `docs/API_CONTRACT.md §7` |
| Export routes return file downloads with `Content-Disposition: attachment` | `docs/API_CONTRACT.md §4–5` |
| Diff validation: must contain `diff `, `---`, `+++`, or `@@` | `backend/app/routes/analyze.py` |
| All errors follow `{ "detail": "..." }` shape | `docs/API_CONTRACT.md §8` |

---

## Project layout

```
frontend/
├── app/
│   ├── globals.css          # Tailwind base styles
│   ├── layout.tsx           # Root layout + metadata
│   └── page.tsx             # Main dashboard (client component)
├── components/
│   ├── Badges.tsx           # RiskBadge, ConfidenceBadge, PriorityBadge, ChangeChip
│   ├── ChangedFiles.tsx     # Changed-files table
│   ├── ChangedSymbols.tsx   # Changed/affected symbols + caller relationships
│   ├── DiffInput.tsx        # Diff textarea + mode selector + actions
│   ├── ExportPanel.tsx      # JSON / Markdown download links
│   ├── ReportSummary.tsx    # Summary stat cards + risk breakdown
│   ├── ReportView.tsx       # Full report assembly + in-page nav
│   ├── RiskList.tsx         # Risk cards with evidence
│   ├── ScenarioPicker.tsx   # Three-scenario selector grid
│   ├── TestRecommendations.tsx
│   └── VerificationPanel.tsx  # Verify button + result (demo only)
└── lib/
    ├── api.ts               # Typed fetch wrappers for all backend routes
    └── types.ts             # TypeScript mirrors of backend Pydantic models
```
