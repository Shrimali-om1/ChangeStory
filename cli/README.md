# ChangeStory CLI

**`changestory`** is the command-line interface for ChangeStory.  
It collects Git changes from a local Python repository, submits them to the
ChangeStory backend for analysis, and prints an actionable report summary.

---

## Requirements

| Component | Minimum version | Notes |
|-----------|----------------|-------|
| Python    | 3.11            | Required by all ChangeStory components |
| Git       | 2.x             | Must be on `PATH` |
| Node.js   | 18+             | Required for the frontend dashboard only |
| npm       | 9+              | Required for the frontend dashboard only |

---

## Install

### 1 — Install the backend (required)

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -e ".[dev]"
```

### 2 — Install the CLI

```bash
cd cli
pip install -e ".[dev]"
```

This registers the `changestory` console script in the active virtual environment.

### 3 — Install the frontend (optional — for the visual dashboard)

```bash
cd frontend
npm install
```

---

## Start the services

### Backend (required)

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Interactive API docs: <http://localhost:8000/docs>

### Frontend dashboard (optional)

```bash
cd frontend
npm run dev
```

Dashboard: <http://localhost:3000>

---

## CLI usage

### `changestory init`

Validates a Git repository and writes a minimal `.changestory.json` config file.  
Run this once before using `changestory analyze`.

```bash
# Current directory
changestory init

# Specific path
changestory init --repo /path/to/myproject

# With custom backend URL
changestory init --repo . --api-url http://localhost:8000/api/v1
```

The generated `.changestory.json` looks like:

```json
{
  "repo": "/absolute/path/to/myproject",
  "api_url": "http://localhost:8000/api/v1"
}
```

---

### `changestory analyze`

Collects staged changes, unstaged changes, and eligible untracked Python
files from the repository, then submits the diff to the backend.

```bash
# Analyse the current directory
changestory analyze

# Analyse a specific repository
changestory analyze --repo /path/to/myproject

# Use deep analysis mode
changestory analyze --repo . --mode deep

# Analyse a saved patch file
changestory analyze --diff-file changes.patch

# Pipe a diff from stdin
git diff HEAD~1 | changestory analyze --diff-file -
```

**Diff collection strategy (from highest to lowest priority):**

1. Staged changes (`git diff --cached HEAD`)
2. Unstaged changes on tracked files (`git diff HEAD`)
3. Eligible untracked Python files (`git ls-files --others --exclude-standard -- *.py`)
4. If none found: diff between `HEAD~1` and `HEAD` (last commit)

**Analysis modes:**

| Mode       | What is included |
|------------|-----------------|
| `quick`    | Symbol identification + risk summary only |
| `standard` | Adds caller graph and test recommendations (default) |
| `deep`     | Adds best-effort transitive impact |

**Output includes:**

- Changed files and symbols count
- Risk breakdown (HIGH / MEDIUM / LOW / INFO)
- Test recommendations count
- Top risks (up to 3)
- Report URL (API), dashboard URL, export links (JSON and Markdown)
- Analysis limitations

---

### `changestory demo`

Runs one or all of the three bundled demo scenarios through the live backend.
No local Git repository is required.

```bash
# List available scenarios
changestory demo --list

# Run a specific scenario (interactive picker if omitted)
changestory demo rename-function
changestory demo add-parameter
changestory demo refactor-class

# Run all three scenarios
changestory demo --all

# Use a patch file directly (no backend required)
changestory analyze --diff-file cli/demo_patches/rename-function.patch
changestory analyze --diff-file cli/demo_patches/add-parameter.patch
changestory analyze --diff-file cli/demo_patches/refactor-class.patch
```

**Available demo scenarios:**

| ID | Title | Risk highlight |
|----|-------|---------------|
| `rename-function`  | Public function renamed | Callers outside diff will break |
| `add-parameter`    | Signature change — new parameter | Positional callers need review |
| `refactor-class`   | Class refactored — error handling removed | Unhandled exceptions in callers |

---

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CHANGESTORY_API_URL` | `http://localhost:8000/api/v1` | Backend base URL override |

---

## Known analysis limitations

These limitations are reported by the backend and printed at the end of every
`changestory analyze` run.  They apply to all modes.

1. **Caller detection is static AST-only.**  
   Dynamic dispatch, monkey-patching, and runtime-generated calls are not
   captured.  All caller relationships are labelled `"potential"`.

2. **Cross-repository calls are not analysed.**  
   Only symbols present in the submitted diff are considered.

3. **Full project source is not read.**  
   The backend analyses only the diff text.  Symbols referenced from files
   not present in the diff will not appear in the caller graph.

4. **Diff-only mode is even more limited.**  
   When `--diff-file` is used without a repository, cross-file impact
   outside the diff is entirely unavailable.  Import resolution and package
   context are not available.

5. **Risk heuristics are not exhaustive.**  
   Detected patterns: signature changes, public symbol deletions, large churn
   (> 30 lines), removed exception handling.  Other risk patterns are not yet
   covered.

---

## Running the tests

```bash
cd cli
pytest
```

Tests do not require a running backend or a real Git repository.

---

## Repository layout (CLI scope)

```
cli/
├── changestory/
│   ├── __init__.py
│   ├── main.py            # Click group — entry point
│   ├── config.py          # .changestory.json read/write
│   ├── git_utils.py       # Read-only git helpers (no arbitrary execution)
│   ├── api_client.py      # Minimal urllib HTTP client
│   └── commands/
│       ├── __init__.py
│       ├── init.py        # changestory init
│       ├── analyze.py     # changestory analyze
│       └── demo.py        # changestory demo
├── demo_patches/
│   ├── rename-function.patch
│   ├── add-parameter.patch
│   └── refactor-class.patch
├── tests/
│   └── test_cli.py
└── pyproject.toml
```
