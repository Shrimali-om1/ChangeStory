"""
analyze.py — `changestory analyze` command.

Collects staged/unstaged Git changes (plus eligible untracked Python
files), sends them to the ChangeStory backend, and prints a summary
with the report URL.

Diff-only mode (--diff-file / stdin) is also supported when the full
repository context is unavailable; limitations are clearly disclosed.
"""

from __future__ import annotations

import sys
from pathlib import Path

import click

from changestory.api_client import APIError, post_analyze
from changestory.config import DEFAULT_API_URL, get_api_url
from changestory.git_utils import (
    collect_diff,
    get_project_root_hint,
    get_repo_root,
    is_git_repo,
)

# ---------------------------------------------------------------------------
# Diff-only limitations disclosure
# ---------------------------------------------------------------------------

_DIFF_ONLY_LIMITATIONS = """\
+------------------------------------------------------------------+
|  DIFF-ONLY MODE -- limitations apply                             |
+------------------------------------------------------------------+
|  Analysis is performed on the provided diff text only.           |
|  Without a full repository:                                      |
|    * Caller graphs cover only symbols present in the diff.       |
|    * Cross-file impact outside the diff is NOT analysed.         |
|    * Import resolution and package context are unavailable.      |
|    * Risk heuristics may miss issues visible only in full source. |
|                                                                  |
|  For richer analysis run: changestory analyze --repo PATH        |
+------------------------------------------------------------------+
"""

# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------


def _print_report_summary(report: dict, api_url: str, frontend_url: str) -> None:
    """Print a human-readable report summary to stdout."""
    session_id = report.get("session_id", "?")
    summary = report.get("summary", {})
    risks = summary.get("risks", {})
    ctx = report.get("project_context", {})

    click.echo()
    click.echo("-" * 60)
    click.echo(f"  ChangeStory Report  --  session {session_id}")
    click.echo("-" * 60)
    click.echo(f"  Mode              : {report.get('analysis_mode', '?')}")
    click.echo(f"  Files changed     : {ctx.get('total_files_changed', 0)}")
    click.echo(f"  Symbols changed   : {ctx.get('total_symbols_changed', 0)}")
    click.echo(f"  Diff size (lines) : {ctx.get('diff_size_lines', 0)}")
    click.echo()
    click.echo("  Risks:")
    click.echo(f"    HIGH   : {risks.get('high', 0)}")
    click.echo(f"    MEDIUM : {risks.get('medium', 0)}")
    click.echo(f"    LOW    : {risks.get('low', 0)}")
    click.echo(f"    INFO   : {risks.get('info', 0)}")
    click.echo()
    click.echo(f"  Test recommendations : {summary.get('test_recommendations', 0)}")
    click.echo()

    # Top risks
    top_risks = report.get("risks", [])[:3]
    if top_risks:
        click.echo("  Top risks:")
        for risk in top_risks:
            level = risk.get("level", "?").upper()
            title = risk.get("title", "")
            click.echo(f"    [{level}] {title}")
        click.echo()

    # Report URLs
    base = api_url.rstrip("/")
    click.echo("-" * 60)
    click.echo(f"  Report URL (API)     : {base}/reports/{session_id}")
    click.echo(f"  Dashboard URL        : {frontend_url}/?session={session_id}")
    click.echo(f"  Export JSON          : {base}/reports/{session_id}/export.json")
    click.echo(f"  Export Markdown      : {base}/reports/{session_id}/export.md")
    click.echo("-" * 60)
    click.echo()

    # Limitations
    limitations = report.get("limitations", [])
    if limitations:
        click.echo("  [!] Analysis limitations:")
        for lim in limitations:
            click.echo(f"       - {lim}")
        click.echo()


# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------


@click.command("analyze")
@click.option(
    "--repo",
    "repo_path",
    default=None,
    metavar="PATH",
    help=(
        "Path to the Git repository to analyse. "
        "If omitted the current directory is used."
    ),
)
@click.option(
    "--mode",
    type=click.Choice(["quick", "standard", "deep"], case_sensitive=False),
    default="standard",
    show_default=True,
    help="Analysis depth.",
)
@click.option(
    "--diff-file",
    "diff_file",
    default=None,
    metavar="FILE",
    help=(
        "Read diff from FILE instead of the repository. "
        "Use '-' to read from stdin. "
        "Diff-only limitations apply (see output)."
    ),
)
@click.option(
    "--api-url",
    "api_url_override",
    default=None,
    metavar="URL",
    envvar="CHANGESTORY_API_URL",
    help="Override backend URL (default: http://localhost:8000/api/v1).",
)
@click.option(
    "--frontend-url",
    default="http://localhost:3000",
    show_default=True,
    help="Frontend base URL (used only when printing the dashboard link).",
)
def analyze_cmd(
    repo_path: str | None,
    mode: str,
    diff_file: str | None,
    api_url_override: str | None,
    frontend_url: str,
) -> None:
    """
    Collect Git changes and submit them to the ChangeStory backend.

    By default, staged changes, unstaged changes, and eligible
    untracked Python files are included in the diff.

    \b
    Examples:
      changestory analyze
      changestory analyze --repo /path/to/myproject --mode deep
      changestory analyze --diff-file changes.patch
      git diff HEAD~1 | changestory analyze --diff-file -
    """
    diff_only_mode = diff_file is not None

    # ── Resolve repository ─────────────────────────────────────────────────
    if repo_path:
        repo = Path(repo_path).resolve()
    else:
        repo = Path.cwd().resolve()

    # ── Resolve API URL ────────────────────────────────────────────────────
    if not diff_only_mode and is_git_repo(repo):
        try:
            root = get_repo_root(repo)
        except RuntimeError:
            root = repo
        api_url = get_api_url(override=api_url_override, repo=root)
    else:
        api_url = get_api_url(override=api_url_override)

    # ── Collect diff ───────────────────────────────────────────────────────
    diff_text: str = ""
    warnings: list[str] = []
    project_root_hint: str | None = None

    if diff_only_mode:
        # ── Diff-only path ─────────────────────────────────────────────────
        click.echo(_DIFF_ONLY_LIMITATIONS)
        if diff_file == "-":
            diff_text = sys.stdin.read()
        else:
            path = Path(diff_file)  # type: ignore[arg-type]
            if not path.exists():
                raise click.ClickException(f"Diff file not found: {path}")
            diff_text = path.read_text(encoding="utf-8", errors="replace")

        if not diff_text.strip():
            raise click.ClickException("Diff input is empty.")

    else:
        # ── Repository path ────────────────────────────────────────────────
        if not repo.exists():
            raise click.ClickException(f"Path does not exist: {repo}")

        if not is_git_repo(repo):
            raise click.ClickException(
                f"{repo} is not a Git repository.\n"
                "Tip: run `changestory init --repo PATH` first, or use "
                "--diff-file to analyse a patch file without a repository."
            )

        click.echo(f"Collecting changes from: {repo}")

        try:
            diff_text, warnings = collect_diff(repo)
        except RuntimeError as exc:
            raise click.ClickException(str(exc)) from exc

        for w in warnings:
            click.echo(f"  [!] {w}")

        if not diff_text.strip():
            click.echo("No changes detected in the repository.")
            click.echo(
                "  Tip: stage or modify files, or use --diff-file to "
                "analyse a specific patch."
            )
            sys.exit(0)

        project_root_hint = get_project_root_hint(repo)

    # ── Submit to backend ──────────────────────────────────────────────────
    click.echo(f"Submitting to ChangeStory backend ({api_url}) ...")
    try:
        report = post_analyze(
            api_url=api_url,
            diff=diff_text,
            mode=mode,
            project_root_hint=project_root_hint,
        )
    except ConnectionError as exc:
        raise click.ClickException(str(exc)) from exc
    except APIError as exc:
        raise click.ClickException(
            f"Backend returned an error ({exc.status}): {exc.detail}"
        ) from exc

    # ── Print results ──────────────────────────────────────────────────────
    _print_report_summary(report, api_url=api_url, frontend_url=frontend_url)
