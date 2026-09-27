"""
init.py — `changestory init` command.

Validates that PATH is a Git repository and writes a minimal
.changestory.json project configuration file.
"""

from __future__ import annotations

from pathlib import Path

import click

from changestory.config import DEFAULT_API_URL, config_path, write_config
from changestory.git_utils import get_repo_root, is_git_repo


@click.command("init")
@click.option(
    "--repo",
    "repo_path",
    default=".",
    show_default=True,
    metavar="PATH",
    help="Path to the Git repository to configure.",
)
@click.option(
    "--api-url",
    default=DEFAULT_API_URL,
    show_default=True,
    help="Base URL of the ChangeStory backend.",
)
def init_cmd(repo_path: str, api_url: str) -> None:
    """
    Validate a Git repository and save project configuration.

    Writes .changestory.json to the repository root.  Run this once
    before using `changestory analyze`.

    \b
    Examples:
      changestory init
      changestory init --repo /path/to/myproject
      changestory init --repo . --api-url http://localhost:8000/api/v1
    """
    repo = Path(repo_path).resolve()

    # ── Validate directory exists ──────────────────────────────────────────
    if not repo.exists():
        raise click.ClickException(f"Path does not exist: {repo}")
    if not repo.is_dir():
        raise click.ClickException(f"Path is not a directory: {repo}")

    # ── Validate it is a Git repo ──────────────────────────────────────────
    if not is_git_repo(repo):
        raise click.ClickException(
            f"{repo} is not a Git repository (or any parent directory).\n"
            "Initialise Git first:  git init"
        )

    # ── Resolve actual repo root (might differ from given path) ───────────
    try:
        root = get_repo_root(repo)
    except RuntimeError as exc:
        raise click.ClickException(str(exc)) from exc

    # Warn if config already exists
    existing = config_path(root)
    if existing.exists():
        click.echo(f"[!] Config already exists at {existing} -- overwriting.")

    # Write config
    out = write_config(root, api_url=api_url)

    click.echo(f"[ok] Repository validated: {root}")
    click.echo(f"[ok] Config written to:    {out}")
    click.echo()
    click.echo("Next steps:")
    click.echo("  1. Start the backend:  cd backend && uvicorn app.main:app --reload --port 8000")
    click.echo("  2. Analyse changes:    changestory analyze")
