"""
git_utils.py — Helpers for collecting diff content from a Git repository.

Design rules:
  - Never execute arbitrary commands from the target repository.
  - Only runs well-known, read-only git subcommands (diff, ls-files, rev-parse).
  - No shell=True — arguments are always passed as a list.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _git(args: list[str], cwd: Path) -> str:
    """Run a read-only git subcommand and return stdout as a string."""
    result = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed (exit {result.returncode}):\n{result.stderr.strip()}"
        )
    return result.stdout


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def is_git_repo(path: Path) -> bool:
    """Return True if *path* is inside a Git repository."""
    result = subprocess.run(
        ["git", "rev-parse", "--git-dir"],
        cwd=str(path),
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def get_repo_root(path: Path) -> Path:
    """Return the top-level directory of the Git repository containing *path*."""
    root = _git(["rev-parse", "--show-toplevel"], cwd=path).strip()
    return Path(root)


def collect_diff(repo: Path) -> tuple[str, list[str]]:
    """
    Collect a unified diff from the repository.

    Strategy:
      1. Staged changes (git diff --cached HEAD)      — files added to index
      2. Unstaged changes (git diff HEAD)              — tracked but modified
      3. Eligible untracked Python files               — new .py files not yet tracked

    Returns:
      (diff_text, warnings)
      diff_text : unified diff string (may be empty if no changes)
      warnings  : list of human-readable advisory messages
    """
    warnings: list[str] = []
    parts: list[str] = []

    # 1. Staged diff
    staged = _git(["diff", "--cached", "HEAD"], cwd=repo)
    if staged.strip():
        parts.append(staged)

    # 2. Unstaged diff (tracked files)
    unstaged = _git(["diff", "HEAD"], cwd=repo)
    if unstaged.strip():
        parts.append(unstaged)

    # 3. Untracked Python files (eligible = *.py, not in .git/)
    untracked_raw = _git(
        ["ls-files", "--others", "--exclude-standard", "--", "*.py"],
        cwd=repo,
    )
    untracked_py = [p.strip() for p in untracked_raw.splitlines() if p.strip()]

    if untracked_py:
        warnings.append(
            f"Including {len(untracked_py)} untracked Python file(s) as synthetic diffs."
        )
        for rel_path in untracked_py:
            full = repo / rel_path
            try:
                content = full.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            lines = content.splitlines()
            added = "\n".join(f"+{line}" for line in lines)
            hunk = (
                f"diff --git a/{rel_path} b/{rel_path}\n"
                f"new file mode 100644\n"
                f"--- /dev/null\n"
                f"+++ b/{rel_path}\n"
                f"@@ -0,0 +1,{len(lines)} @@\n"
                f"{added}\n"
            )
            parts.append(hunk)

    if not parts:
        # Fallback: try diff against the previous commit (useful for freshly committed changes)
        try:
            head_diff = _git(["diff", "HEAD~1", "HEAD"], cwd=repo)
            if head_diff.strip():
                parts.append(head_diff)
                warnings.append(
                    "No staged/unstaged changes found. Using diff between HEAD~1 and HEAD."
                )
        except RuntimeError:
            pass  # single-commit repo or bare repo — handled by caller

    combined = "\n".join(parts)
    return combined, warnings


def get_project_root_hint(repo: Path) -> str | None:
    """
    Return a simple project-root hint for the backend (e.g. 'src/').
    Looks for a 'src' or 'lib' subdirectory; otherwise returns None.
    """
    for candidate in ("src", "lib"):
        if (repo / candidate).is_dir():
            return f"{candidate}/"
    return None
