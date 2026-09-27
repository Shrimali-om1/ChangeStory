"""
runner.py — Controlled verification against the bundled sample project.

SAFETY CONSTRAINTS:
  - Only runs against tests inside backend/sample_project/tests/.
  - Only activates for sessions whose scenario_id is in BUNDLED_IDS.
  - Uses subprocess with a hard timeout; never executes user-supplied commands.
  - The working directory is always the sample_project directory.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from app.models import VerificationResult
from app.scenarios.bundled import BUNDLED_IDS

_SAMPLE_DIR = Path(__file__).parent.parent.parent / "sample_project"
_TIMEOUT_SECONDS = 30


def can_verify(scenario_id: str | None) -> bool:
    return scenario_id in BUNDLED_IDS


def run_verification(scenario_id: str) -> VerificationResult:
    """
    Run pytest against the bundled sample project.

    Returns a VerificationResult with actual pass/fail counts and output.
    Never raises — errors are captured and returned in the result.
    """
    if not can_verify(scenario_id):
        return VerificationResult(
            ran=False,
            note="Verification is only available for bundled demo scenarios.",
        )

    tests_dir = _SAMPLE_DIR / "tests"
    if not tests_dir.exists():
        return VerificationResult(
            ran=False,
            note="Sample project tests directory not found.",
        )

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(tests_dir),
        "--tb=short",
        "-q",
        "--no-header",
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=str(_SAMPLE_DIR),
            capture_output=True,
            text=True,
            timeout=_TIMEOUT_SECONDS,
        )
        output = result.stdout + result.stderr
        passed, failed, skipped = _parse_pytest_summary(output)

        confirmed_safe = _extract_passed_tests(output)
        confirmed_failing = _extract_failed_tests(output)

        return VerificationResult(
            ran=True,
            passed=passed,
            failed=failed,
            skipped=skipped,
            output=output,
            confirmed_safe=confirmed_safe,
            confirmed_failing=confirmed_failing,
            note="Ran against bundled sample project only. Results reflect the sample, not your repository.",
        )
    except subprocess.TimeoutExpired:
        return VerificationResult(
            ran=False,
            note=f"Verification timed out after {_TIMEOUT_SECONDS}s.",
        )
    except Exception as exc:
        return VerificationResult(
            ran=False,
            note=f"Verification failed to run: {exc}",
        )


def _parse_pytest_summary(output: str) -> tuple[int, int, int]:
    """Extract passed/failed/skipped counts from pytest -q output."""
    import re

    # Matches: "2 passed, 1 failed, 0 warnings in 0.12s"
    m = re.search(
        r"(\d+)\s+passed(?:,\s*(\d+)\s+failed)?(?:,\s*(\d+)\s+(?:skipped|warning))?",
        output,
    )
    if m:
        passed = int(m.group(1))
        failed = int(m.group(2) or 0)
        skipped = int(m.group(3) or 0)
        return passed, failed, skipped

    # Only failures
    m2 = re.search(r"(\d+)\s+failed", output)
    if m2:
        return 0, int(m2.group(1)), 0

    return 0, 0, 0


def _extract_passed_tests(output: str) -> list[str]:
    import re
    return re.findall(r"PASSED\s+(\S+)", output)


def _extract_failed_tests(output: str) -> list[str]:
    import re
    return re.findall(r"FAILED\s+(\S+)", output)
