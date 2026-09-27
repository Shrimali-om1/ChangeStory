# ChangeStory

**ChangeStory** is a local-first tool for understanding changes to Python Git repositories.  
It accepts a Git diff, identifies changed symbols, finds callers and potentially-affected code,
reports potential risks and recommended tests with evidence, and produces a report that can be
viewed and exported.

---

## Repository layout

```
ChangeStory/
├── backend/          # Python 3.11 + FastAPI — analysis engine & API
├── frontend/         # Next.js + React + TypeScript — dashboard (teammate scope)
├── docs/
│   └── API_CONTRACT.md   # Shared schema — read this before touching the API
└── README.md
```

---

## Quick start — backend

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

Interactive docs: <http://localhost:8000/docs>

---

## Quick start — frontend (teammate)

```bash
cd frontend
npm install
npm run dev
```

See `docs/API_CONTRACT.md` for all endpoints and response shapes.

---

## Key endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/v1/analyze` | Submit a diff → receive a full report |
| `GET`  | `/api/v1/reports/{session_id}` | Retrieve a saved report |
| `GET`  | `/api/v1/reports/{session_id}/export.json` | Export report as JSON |
| `GET`  | `/api/v1/reports/{session_id}/export.md` | Export report as Markdown |
| `GET`  | `/api/v1/scenarios` | Three bundled demo scenarios |
| `POST` | `/api/v1/verify/{session_id}` | Run controlled verification (sample project only) |

---

## Design notes

- **Local-first** — no external services; all analysis is deterministic Python AST + diff parsing.
- **Clearly labelled uncertainty** — caller relationships and risk assessments are labelled
  `"potential"` when they cannot be proven statically.
- **No arbitrary execution** — the verify endpoint only runs against a small bundled sample
  project; it never executes user-supplied commands.
- **Minimal dependencies** — FastAPI, uvicorn, pydantic.  No heavyweight ML libraries.

---

## Team conventions

- All API types live in `backend/app/models.py` **and** in `docs/API_CONTRACT.md`.
  Keep them in sync.
- Session data is stored in `backend/data/sessions/` (flat JSON files, gitignored).
- Labels: `"potential"` = could not be statically proven; `"confirmed"` = verified at runtime.
