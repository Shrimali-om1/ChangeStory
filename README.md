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

---

## 🖥️ IBM Bob Usage Proof

> All screenshots captured during live development and testing with IBM Bob 2.0.

### Project Creation & Backend Setup
![Backend Summary](docs/screenshots/backen_done.png)
![Create Files & Writing](docs/screenshots/create_file_and_writting.png)
![Repo Layout](docs/screenshots/repo_layout.png)

### API Development
![API Made](docs/screenshots/maded_api.png)
![API Response](docs/screenshots/reponse_api.png)
![Server Test](docs/screenshots/server_test.png)

### CLI Development
![Packages](docs/screenshots/packages.png)
![API Client](docs/screenshots/api_client.png)
![Git Utils](docs/screenshots/git_utils.png)
![Config](docs/screenshots/config.png)
![Init Command](docs/screenshots/init.png)
![Main.py](docs/screenshots/main.py.png)
![Commands to Verify](docs/screenshots/commands_to_verify.png)
![Run CLI Test](docs/screenshots/run_CLI_test.png)

### Flow & Architecture
![ChangeStory Flow](docs/screenshots/chake_flow.png)
![ChangeStory Flow App](docs/screenshots/chake_flowapp.png)
![Decision Boundaries](docs/screenshots/decision_boundaries.png)

### Bug Fixes & Testing
![Bug Fix 1](docs/screenshots/bugfix1.png)
![Bug Fix 2](docs/screenshots/bugfix2.png)
![Bug Fix 2.1](docs/screenshots/bugfix2_1.png)
![Bug Fix 3](docs/screenshots/bugfix3.png)
![Bug Fix 4](docs/screenshots/bugfindandfix4.png)
![Bug Fix 5](docs/screenshots/bugfix5.png)
![Guide of Testing](docs/screenshots/guideof%20testing.png)
![Project Run Guide](docs/screenshots/projectrunguide.png)

---

## 🚀 Complete Step-by-Step Usage Guide

### Prerequisites

Make sure these are installed:
- Python 3.11+
- Node.js 18+
- Git 2.x

---

### Step 1 — Clone the Repository

```bash
git clone https://github.com/Shrimali-om1/ChangeStory.git
cd ChangeStory
```

---

### Step 2 — Start the Backend Server

> Open **Terminal 1** — keep this running always.

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (macOS / Linux)
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Start server
uvicorn app.main:app --reload --port 8000
```

✅ Backend is live at: **http://localhost:8000**
✅ Interactive API docs: **http://localhost:8000/docs**

---

### Step 3 — Start the Frontend Dashboard

> Open **Terminal 2** — keep this running always.

```bash
cd frontend

# Install dependencies
npm install

# Start dashboard
npm run dev
```

✅ Dashboard is live at: **http://localhost:3000**

---

### Step 4 — Install the CLI

> Open **Terminal 3** — use this for your projects.

```bash
cd cli
pip install -e ".[dev]"
```

Verify installation:
```bash
py -m changestory --version
# changestory, version 0.1.0
```

---

### Step 5 — Initialize Your Project

Go to **your own project folder** and run:

```bash
cd C:\path\to\your-project

py -m changestory init --repo .
```

This creates `.changestory.json` in your project — run this only once.

---

### Step 6 — Analyze Your Changes

After making any code changes in your project:

```bash
py -m changestory analyze
```

ChangeStory will:
1. Collect your git diff automatically
2. Send it to the backend for analysis
3. Print a report in the terminal
4. **Automatically open the dashboard in your browser** 🌐

---

### Step 7 — View Report in Browser

Browser opens automatically at:
```
http://localhost:3000/?session=<session-id>
```

You will see:
- 📁 Changed files
- 🔣 Changed symbols (functions, classes, methods)
- ⚠️ Risk assessment (HIGH / MEDIUM / LOW)
- 🧪 Test recommendations
- 📤 Export as JSON or Markdown

---

### Step 8 — Try a Demo (No Real Project Needed)

```bash
# List all demo scenarios
py -m changestory demo --list

# Run a specific demo
py -m changestory demo rename-function
py -m changestory demo add-parameter
py -m changestory demo refactor-class

# Run all three demos
py -m changestory demo --all
```

---

### Quick Reference — All Commands

| Command | What it does |
|---------|-------------|
| `py -m changestory init --repo .` | Initialize your project (once) |
| `py -m changestory analyze` | Analyze current git changes |
| `py -m changestory analyze --mode deep` | Deep analysis (transitive impact) |
| `py -m changestory analyze --mode quick` | Quick risk summary only |
| `py -m changestory analyze --no-open` | Analyze without opening browser |
| `py -m changestory demo --list` | Show all demo scenarios |
| `py -m changestory demo rename-function` | Run rename demo |
| `py -m changestory demo --all` | Run all 3 demos |

---

### Export Your Report

```bash
# After analyzing, use the session ID from terminal output

# Download as JSON
curl http://localhost:8000/api/v1/reports/<session-id>/export.json

# Download as Markdown
curl http://localhost:8000/api/v1/reports/<session-id>/export.md
```

Or click the **Export** buttons directly in the dashboard.

---

<div align="center">

Built for **IBM Bob 2.0 Hackathon** · Local-first · No cloud required · Zero telemetry

</div>
