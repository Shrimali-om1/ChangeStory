"""
demo.py — `changestory demo` command.

Runs one (or all) of the three bundled demo scenarios against the
live backend and prints a summary.  Works with the existing
GET /scenarios → POST /scenarios/{id}/analyze flow.
"""

from __future__ import annotations

import webbrowser

import click

from changestory.api_client import APIError, get_scenarios, post_analyze_scenario
from changestory.commands.analyze import _print_report_summary
from changestory.config import get_api_url

# ---------------------------------------------------------------------------
# Scenario metadata (mirrors backend/app/scenarios/bundled.py)
# ---------------------------------------------------------------------------

SCENARIO_IDS = ["rename-function", "add-parameter", "refactor-class"]

SCENARIO_DESCRIPTIONS = {
    "rename-function": (
        "Public function renamed -- `format_username` -> `normalise_username`. "
        "Existing callers outside the diff will break."
    ),
    "add-parameter": (
        "Signature change -- `PaymentProcessor.charge` gains a new `currency` "
        "parameter; `validate_amount` adds a `max_amount` cap."
    ),
    "refactor-class": (
        "Class refactored -- `DataImporter.load` loses its try/except block; "
        "new methods `validate` and `_apply_defaults` are added."
    ),
}


# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------


@click.command("demo")
@click.argument(
    "scenario",
    required=False,
    metavar="[SCENARIO]",
)
@click.option(
    "--open/--no-open",
    "open_browser",
    default=True,
    show_default=True,
    help="Automatically open the dashboard in the browser after analysis.",
)
@click.option(
    "--list",
    "list_only",
    is_flag=True,
    default=False,
    help="List available scenarios and exit.",
)
@click.option(
    "--all",
    "run_all",
    is_flag=True,
    default=False,
    help="Run all three demo scenarios.",
)
@click.option(
    "--api-url",
    "api_url_override",
    default=None,
    metavar="URL",
    envvar="CHANGESTORY_API_URL",
    help="Override backend URL.",
)
@click.option(
    "--frontend-url",
    default="http://localhost:3000",
    show_default=True,
    help="Frontend base URL (used when printing the dashboard link).",
)
def demo_cmd(
    scenario: str | None,
    open_browser: bool,
    list_only: bool,
    run_all: bool,
    api_url_override: str | None,
    frontend_url: str,
) -> None:
    """
    Run a bundled demo scenario through the ChangeStory backend.

    \b
    Available scenarios:
      rename-function   Public function renamed (breaks callers)
      add-parameter     Signature change -- new parameter added
      refactor-class    Class refactored -- error handling removed

    \b
    Examples:
      changestory demo --list
      changestory demo rename-function
      changestory demo add-parameter --mode standard
      changestory demo --all
    """
    api_url = get_api_url(override=api_url_override)

    # ── List mode ──────────────────────────────────────────────────────────
    if list_only:
        click.echo("Available demo scenarios:")
        click.echo()
        for sid in SCENARIO_IDS:
            click.echo(f"  {sid}")
            click.echo(f"    {SCENARIO_DESCRIPTIONS[sid]}")
            click.echo()
        return

    # ── Resolve which scenarios to run ────────────────────────────────────
    if run_all:
        to_run = SCENARIO_IDS
    elif scenario:
        if scenario not in SCENARIO_IDS:
            raise click.ClickException(
                f"Unknown scenario '{scenario}'.\n"
                f"Valid options: {', '.join(SCENARIO_IDS)}\n"
                "Run `changestory demo --list` to see descriptions."
            )
        to_run = [scenario]
    else:
        # Interactive selection
        click.echo("Available demo scenarios:")
        for i, sid in enumerate(SCENARIO_IDS, 1):
            click.echo(f"  {i}. {sid}")
            click.echo(f"     {SCENARIO_DESCRIPTIONS[sid]}")
        click.echo()
        choice = click.prompt(
            "Choose a scenario (1-3, or name)",
            default="1",
        )
        if choice.isdigit():
            idx = int(choice) - 1
            if idx < 0 or idx >= len(SCENARIO_IDS):
                raise click.ClickException("Invalid choice. Enter 1, 2, or 3.")
            to_run = [SCENARIO_IDS[idx]]
        elif choice in SCENARIO_IDS:
            to_run = [choice]
        else:
            raise click.ClickException(
                f"Invalid choice '{choice}'. Enter 1-3 or a scenario name."
            )

    # ── Verify scenarios are available on the backend ─────────────────────
    click.echo(f"Fetching scenario list from {api_url} ...")
    try:
        remote_scenarios = get_scenarios(api_url)
    except ConnectionError as exc:
        raise click.ClickException(str(exc)) from exc
    except APIError as exc:
        raise click.ClickException(
            f"Backend error ({exc.status}): {exc.detail}"
        ) from exc

    remote_ids = {s["id"] for s in remote_scenarios}
    for sid in to_run:
        if sid not in remote_ids:
            raise click.ClickException(
                f"Scenario '{sid}' is not available on the backend. "
                "Make sure you are running ChangeStory >= 0.1.0."
            )

    # ── Run scenarios ──────────────────────────────────────────────────────
    for sid in to_run:
        click.echo()
        click.echo("=" * 60)
        click.echo(f"  Demo scenario: {sid}")
        click.echo(f"  {SCENARIO_DESCRIPTIONS[sid]}")
        click.echo("=" * 60)

        click.echo(f"\nRunning analysis ...")
        try:
            report = post_analyze_scenario(api_url, sid)
        except ConnectionError as exc:
            raise click.ClickException(str(exc)) from exc
        except APIError as exc:
            raise click.ClickException(
                f"Backend error ({exc.status}): {exc.detail}"
            ) from exc

        dashboard_url = _print_report_summary(report, api_url=api_url, frontend_url=frontend_url)

        if open_browser and dashboard_url:
            click.echo(f"  Opening dashboard: {dashboard_url}")
            webbrowser.open(dashboard_url)

    if len(to_run) > 1:
        click.echo(f"[ok] Completed {len(to_run)} demo scenarios.")
