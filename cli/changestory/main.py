"""
main.py — ChangeStory CLI entry point.

Registered as the `changestory` console script in pyproject.toml.
"""

from __future__ import annotations

import click

from changestory.commands.analyze import analyze_cmd
from changestory.commands.demo import demo_cmd
from changestory.commands.init import init_cmd


@click.group()
@click.version_option(version="0.1.0", prog_name="changestory")
def cli() -> None:
    """
    ChangeStory — understand changes in a Python Git repository.

    \b
    Quick start:
      changestory init --repo .
      changestory analyze
      changestory demo rename-function

    Run any command with --help for full options.
    """


cli.add_command(init_cmd, name="init")
cli.add_command(analyze_cmd, name="analyze")
cli.add_command(demo_cmd, name="demo")


def main() -> None:
    """Package entry point called by the `changestory` console script."""
    cli()


if __name__ == "__main__":
    main()
