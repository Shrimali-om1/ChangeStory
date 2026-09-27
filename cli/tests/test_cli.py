"""
Tests for changestory CLI.

These tests do NOT require a running backend or a real git repository.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner

from changestory.commands.analyze import analyze_cmd
from changestory.commands.demo import demo_cmd
from changestory.commands.init import init_cmd
from changestory.config import (
    DEFAULT_API_URL,
    config_path,
    read_config,
    write_config,
)
from changestory.main import cli


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def git_repo(tmp_path: Path) -> Path:
    """Create a minimal git repository in a temp directory."""
    subprocess.run(["git", "init", str(tmp_path)], capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )
    # Initial commit so HEAD exists
    (tmp_path / "README.md").write_text("# test\n")
    subprocess.run(["git", "add", "."], cwd=str(tmp_path), capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )
    return tmp_path


# ---------------------------------------------------------------------------
# config tests
# ---------------------------------------------------------------------------


class TestConfig:
    def test_write_and_read(self, tmp_path: Path) -> None:
        write_config(tmp_path)
        cfg = read_config(tmp_path)
        assert cfg["repo"] == str(tmp_path.resolve())
        assert cfg["api_url"] == DEFAULT_API_URL

    def test_write_custom_api_url(self, tmp_path: Path) -> None:
        write_config(tmp_path, api_url="http://example.com/api/v1")
        cfg = read_config(tmp_path)
        assert cfg["api_url"] == "http://example.com/api/v1"

    def test_read_missing_returns_defaults(self, tmp_path: Path) -> None:
        cfg = read_config(tmp_path)
        assert cfg["api_url"] == DEFAULT_API_URL

    def test_malformed_config_raises(self, tmp_path: Path) -> None:
        config_path(tmp_path).write_text("not json", encoding="utf-8")
        with pytest.raises(ValueError, match="Malformed config"):
            read_config(tmp_path)


# ---------------------------------------------------------------------------
# init command tests
# ---------------------------------------------------------------------------


class TestInitCommand:
    def test_init_valid_repo(self, git_repo: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(init_cmd, ["--repo", str(git_repo)])
        assert result.exit_code == 0, result.output
        assert "[ok] Repository validated" in result.output
        assert "[ok] Config written to" in result.output
        cfg_file = config_path(git_repo)
        assert cfg_file.exists()

    def test_init_non_existent_path(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(init_cmd, ["--repo", str(tmp_path / "nodir")])
        assert result.exit_code != 0
        assert "does not exist" in result.output

    def test_init_non_git_dir(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(init_cmd, ["--repo", str(tmp_path)])
        assert result.exit_code != 0
        assert "not a Git repository" in result.output

    def test_init_writes_correct_api_url(self, git_repo: Path) -> None:
        runner = CliRunner()
        custom_url = "http://prod.example.com/api/v1"
        result = runner.invoke(init_cmd, ["--repo", str(git_repo), "--api-url", custom_url])
        assert result.exit_code == 0, result.output
        cfg = read_config(git_repo)
        assert cfg["api_url"] == custom_url

    def test_init_overwrites_existing_config(self, git_repo: Path) -> None:
        runner = CliRunner()
        runner.invoke(init_cmd, ["--repo", str(git_repo)])
        result = runner.invoke(init_cmd, ["--repo", str(git_repo)])
        assert result.exit_code == 0
        assert "overwriting" in result.output.lower()


# ---------------------------------------------------------------------------
# analyze command — diff-only mode (no backend needed)
# ---------------------------------------------------------------------------


class TestAnalyzeDiffOnly:
    def test_diff_file_not_found(self) -> None:
        runner = CliRunner()
        result = runner.invoke(analyze_cmd, ["--diff-file", "/nonexistent/file.patch"])
        assert result.exit_code != 0
        assert "not found" in result.output.lower()

    def test_empty_diff_from_stdin(self) -> None:
        runner = CliRunner()
        result = runner.invoke(analyze_cmd, ["--diff-file", "-"], input="   ")
        assert result.exit_code != 0
        assert "empty" in result.output.lower()

    def test_diff_only_shows_limitations(self, tmp_path: Path) -> None:
        """Reading a patch file should display the DIFF-ONLY MODE banner."""
        patch = tmp_path / "test.patch"
        patch.write_text(
            "diff --git a/x.py b/x.py\n"
            "--- a/x.py\n"
            "+++ b/x.py\n"
            "@@ -1,1 +1,1 @@\n"
            "-old()\n"
            "+new()\n",
            encoding="utf-8",
        )
        runner = CliRunner()
        # Will fail at the HTTP call — that's expected without a running backend
        result = runner.invoke(analyze_cmd, ["--diff-file", str(patch)])
        assert "DIFF-ONLY MODE" in result.output


# ---------------------------------------------------------------------------
# demo command — list mode (no backend needed)
# ---------------------------------------------------------------------------


class TestDemoCommand:
    def test_list_shows_three_scenarios(self) -> None:
        runner = CliRunner()
        result = runner.invoke(demo_cmd, ["--list"])
        assert result.exit_code == 0, result.output
        assert "rename-function" in result.output
        assert "add-parameter" in result.output
        assert "refactor-class" in result.output

    def test_invalid_scenario_name(self) -> None:
        runner = CliRunner()
        result = runner.invoke(demo_cmd, ["nonexistent-scenario"])
        assert result.exit_code != 0
        assert "Unknown scenario" in result.output

    def test_help_text(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["demo", "--help"])
        assert result.exit_code == 0
        assert "rename-function" in result.output


# ---------------------------------------------------------------------------
# Top-level CLI tests
# ---------------------------------------------------------------------------


class TestCLIGroup:
    def test_version(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "init" in result.output
        assert "analyze" in result.output
        assert "demo" in result.output
