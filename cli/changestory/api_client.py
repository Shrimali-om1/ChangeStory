"""
api_client.py — Minimal HTTP client for the ChangeStory backend.

Uses only the Python standard library (urllib) so no extra runtime
dependency is needed.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _request(
    method: str,
    url: str,
    body: dict[str, Any] | None = None,
    timeout: int = 60,
) -> Any:
    """Perform an HTTP request and return the parsed JSON response."""
    data: bytes | None = None
    headers: dict[str, str] = {}

    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw)
            detail = payload.get("detail", raw)
            if isinstance(detail, list):
                detail = "; ".join(e.get("msg", str(e)) for e in detail)
        except json.JSONDecodeError:
            detail = raw or str(exc)
        raise APIError(exc.code, detail) from exc
    except urllib.error.URLError as exc:
        raise ConnectionError(
            f"Cannot reach ChangeStory backend at {url}.\n"
            f"Is the server running? (uvicorn app.main:app --port 8000)\n"
            f"Reason: {exc.reason}"
        ) from exc


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class APIError(Exception):
    """Raised when the backend returns a non-2xx status."""

    def __init__(self, status: int, detail: str) -> None:
        self.status = status
        self.detail = detail
        super().__init__(f"HTTP {status}: {detail}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def post_analyze(
    api_url: str,
    diff: str,
    mode: str = "standard",
    project_root_hint: str | None = None,
) -> dict[str, Any]:
    """POST /api/v1/analyze and return the report dict."""
    body: dict[str, Any] = {"diff": diff, "mode": mode}
    if project_root_hint:
        body["project_root_hint"] = project_root_hint
    url = f"{api_url}/analyze"
    return _request("POST", url, body=body)


def get_report(api_url: str, session_id: str) -> dict[str, Any]:
    """GET /api/v1/reports/{session_id} and return the report dict."""
    url = f"{api_url}/reports/{session_id}"
    return _request("GET", url)


def get_scenarios(api_url: str) -> list[dict[str, Any]]:
    """GET /api/v1/scenarios and return the list of scenario dicts."""
    url = f"{api_url}/scenarios"
    data = _request("GET", url)
    return data.get("scenarios", [])


def post_analyze_scenario(api_url: str, scenario_id: str) -> dict[str, Any]:
    """POST /api/v1/scenarios/{scenario_id}/analyze and return the report dict."""
    url = f"{api_url}/scenarios/{scenario_id}/analyze"
    return _request("POST", url)


def post_verify(api_url: str, session_id: str) -> dict[str, Any]:
    """POST /api/v1/verify/{session_id} and return the verify-response dict."""
    url = f"{api_url}/verify/{session_id}"
    return _request("POST", url)


def health_check(api_url: str) -> bool:
    """Return True if the backend responds to GET /health."""
    # health lives at root, not under /api/v1
    base = api_url.rstrip("/").rsplit("/api/v1", 1)[0]
    try:
        _request("GET", f"{base}/health", timeout=5)
        return True
    except (ConnectionError, APIError):
        return False
