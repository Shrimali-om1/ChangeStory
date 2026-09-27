<div align="center">

# ChangeStory

**Understand every change before it ships.**

ChangeStory is a local-first developer tool that turns a raw Git diff into a structured impact report — changed symbols, caller graphs, risk assessments, test recommendations, and export-ready evidence. Zero cloud. Zero tracking. Runs entirely on your machine.

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js 16](https://img.shields.io/badge/Next.js-16-black?logo=next.js)](https://nextjs.org/)
[![License MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)

</div>

---

## What it does

```
git diff  ──►  ChangeStory CLI  ──►  Backend Analysis  ──►  Report Dashboard
                                           │
                        ┌──────────────────┼──────────────────┐
                        ▼                  ▼                  ▼
                  Changed Symbols     Caller Graph        Risk Heuristics
                  (AST-extracted)     (static, diff-only) (signature / churn /
                                                           error-handling)
                        │                  │                  │
                        └──────────────────┼──────────────────┘
                                           ▼
                              Test Recommendations + Export
                              (JSON · Markdown · Dashboard)
```

| Capability | Detail |
|---|---|
| **Symbol detection** | Identifies every changed function, method, and class via Python AST |
| **Caller graph** | Finds callers of changed symbols within the diff |
| **Risk heuristics** | Signature changes · public symbol deletions · large churn · removed error handling |
| **Test recommendations** | Prioritised suggestions tied directly to changed symbols and risks |
| **Export** | JSON and Markdown reports with one command |
| **Verification** | Controlled pytest run against bundled sample project (demo only) |
| **CLI** | `changestory init` · `changestory analyze` · `changestory demo` |

---

## Repository layout

```
ChangeStory/
├── backend/                  # Python 3.11 + FastAPI — analysis engine & REST API
│   ├── app/
│   │   ├── analysis/         # AST analyzer, diff parser, report builder
│   │   ├── routes/           # analyze · reports · scenarios · verify
│   │   ├── scenarios/        # Three bundled demo diffs
│   │   ├── models.py         # Pydantic models (source of truth)
│   │   └── main.py           # FastAPI app entry point
│   ├── sample_project/       # Bundled Python project for verification
│   └── pyproject.toml
│
├── cli/                      # Python CLI — changestory command
│   ├── changestory/
│   │   ├── commands/         # init · analyze · demo
│   │   ├── api_client.py     # stdlib-only HTTP client
│   │   ├── config.py         # .changestory.json read/write
│   │   └── git_utils.py      # read-only git helpers
│   ├── demo_patches/         # Three .patch files for offline demo
│   ├── tests/                # 17 unit tests (no backend required)
│   └── pyproject.toml
│
├── frontend/                 # Next.js 16 + React 19 + TypeScript — dashboard
│   ├── app/                  # Next.js App Router pages
│   ├── components/           # ReportView · RiskList · TestRecommendations · …
│   └── lib/
│       ├── api.ts            # Typed fetch wrappers
│       └── types.ts          # TypeScript mirror of Pydantic models
│
└── docs/
    └── API_CONTRACT.md       # Single source of truth — read before touching the API
```

---

## Quick start

> **Prerequisites:** Python 3.11+, Node.js 18+, Git 2.x

### 1 — Backend

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

API is live at **http://localhost:8000** · Interactive docs at **http://localhost:8000/docs**

### 2 — Frontend dashboard

```bash
cd frontend
npm install
npm run dev
```

Dashboard is live at **http://localhost:3000**

### 3 — CLI

```bash
cd cli
pip install -e ".[dev]"    # registers the `changestory` console script
```

---

## CLI usage

### `changestory init`

Validates a Git repository and writes `.changestory.json` config.

```bash
changestory init                                   # current directory
changestory init --repo /path/to/myproject
changestory init --repo . --api-url http://localhost:8000/api/v1
```

### `changestory analyze`

Collects staged changes, unstaged changes, and eligible untracked Python files, then submits to the backend and prints the report.

```bash
changestory analyze                                # auto-collects from cwd
changestory analyze --repo /path/to/project
changestory analyze --repo . --mode deep           # quick | standard | deep
changestory analyze --diff-file changes.patch      # diff-only mode
git diff HEAD~1 | changestory analyze --diff-file -
```

**Analysis modes**

| Mode | What is included |
|------|-----------------|
| `quick` | Symbol identification + risk summary |
| `standard` | + caller graph + test recommendations *(default)* |
| `deep` | + best-effort transitive impact |

### `changestory demo`

Runs a bundled scenario through the live backend. No real diff needed.

```bash
changestory demo --list                            # show all three scenarios
changestory demo rename-function
changestory demo add-parameter
changestory demo refactor-class
changestory demo --all                             # run all three
```

**Offline patch-file demos (no backend required)**

```bash
changestory analyze --diff-file cli/demo_patches/rename-function.patch
changestory analyze --diff-file cli/demo_patches/add-parameter.patch
changestory analyze --diff-file cli/demo_patches/refactor-class.patch
```

---

## Demo scenarios

Three deterministic scenarios ship with ChangeStory, wired into both the backend (`GET /api/v1/scenarios`) and the CLI:

| ID | Title | What it exercises |
|----|-------|-------------------|
| `rename-function` | Public function renamed | Callers outside diff break · name-change risk |
| `add-parameter` | Signature change — new parameter | Positional-caller review · boundary tests |
| `refactor-class` | Class refactored — error handling removed | Removed `except` detection · method-split analysis |

---

## API reference

**Base URL:** `http://localhost:8000/api/v1`

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/analyze` | Submit a diff — returns a full `Report` |
| `GET` | `/reports/{session_id}` | Retrieve a saved report |
| `GET` | `/reports/{session_id}/export.json` | Download report as JSON |
| `GET` | `/reports/{session_id}/export.md` | Download report as Markdown |
| `GET` | `/scenarios` | List the three bundled demo scenarios |
| `POST` | `/scenarios/{id}/analyze` | Analyse a bundled scenario by ID |
| `POST` | `/verify/{session_id}` | Run controlled pytest (demo sessions only) |

Full schema, request/response shapes, and error codes: [`docs/API_CONTRACT.md`](docs/API_CONTRACT.md)

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      CLI (Python)                        │
│  changestory init / analyze / demo                       │
│  git_utils  ──►  api_client  ──►  backend               │
└───────────────────────────┬─────────────────────────────┘
                            │ HTTP POST /analyze
                            ▼
┌─────────────────────────────────────────────────────────┐
│                   Backend (FastAPI)                      │
│                                                          │
│  diff_parser  ──►  ast_analyzer  ──►  report_builder    │
│                         │                               │
│                  session_store  (flat JSON, local)       │
└───────────────────────────┬─────────────────────────────┘
                            │ REST JSON
                            ▼
┌─────────────────────────────────────────────────────────┐
│                  Frontend (Next.js)                      │
│                                                          │
│  ReportView · RiskList · ChangedSymbols                  │
│  TestRecommendations · ExportPanel · VerificationPanel   │
└─────────────────────────────────────────────────────────┘
```

**Key design decisions**

- **Local-first** — no external services, no telemetry, no network calls outside your machine.
- **Clearly labelled uncertainty** — all statically inferred results are marked `"potential"`; only runtime-verified results are `"confirmed"`.
- **No arbitrary execution** — the CLI only runs read-only git subcommands. The verify endpoint only runs pytest against the bundled sample project; it never executes user-supplied code.
- **Minimal dependencies** — backend: FastAPI + uvicorn + pydantic. CLI: click. Frontend: Next.js + React + TypeScript.
- **Single API contract** — `docs/API_CONTRACT.md` is the ground truth shared by all three components.

---

## Known limitations

| # | Limitation |
|---|------------|
| 1 | Caller detection is static AST-only. Dynamic dispatch, monkey-patching, and runtime-generated calls are not captured. All caller relationships are labelled `"potential"`. |
| 2 | Only the diff is analysed — full project source is not read. Symbols referenced from files outside the diff do not appear in the caller graph. |
| 3 | Cross-repository calls are not analysed. |
| 4 | Diff-only mode (`--diff-file`) is further limited: import resolution and cross-file impact are unavailable. The CLI discloses this before printing results. |
| 5 | Risk heuristics cover: signature changes, public symbol deletions, large churn (> 30 lines), and removed exception handling. Other patterns are not yet detected. |
| 6 | The verify endpoint runs only against the bundled sample project. It cannot run tests from a user's own repository. |

---

## Running the tests

```bash
# Backend
cd backend
pytest

# CLI (no backend or real git repo needed)
cd cli
pytest
```

---

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CHANGESTORY_API_URL` | `http://localhost:8000/api/v1` | Override backend URL for the CLI |
| `NEXT_PUBLIC_API_BASE` | *(proxied via Next.js rewrite)* | Override backend URL for the frontend |

---

## Team conventions

- All API models live in `backend/app/models.py` **and** `docs/API_CONTRACT.md`. Keep them in sync.
- Session data is stored in `backend/data/sessions/` (flat JSON files, gitignored).
- Labels: `"potential"` = statically inferred, unproven · `"confirmed"` = verified at runtime.
- Never add new endpoints or report fields without updating `docs/API_CONTRACT.md`.
- CLI must never execute arbitrary commands from a target repository.

---

<div align="center">

Built for the hackathon · Local-first · No cloud required

</div>
