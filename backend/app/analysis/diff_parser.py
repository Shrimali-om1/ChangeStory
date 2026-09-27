"""
diff_parser.py — Parse a unified diff into structured file/hunk information.

Supports the standard `git diff` / `diff -u` format.  No external libraries.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class HunkLine:
    kind: str  # "context" | "added" | "removed"
    text: str
    old_lineno: int | None
    new_lineno: int | None


@dataclass
class Hunk:
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: list[HunkLine] = field(default_factory=list)


@dataclass
class FileDiff:
    old_path: str
    new_path: str
    change_type: str  # "added" | "modified" | "deleted" | "renamed"
    hunks: list[Hunk] = field(default_factory=list)

    @property
    def path(self) -> str:
        """Canonical path (new path for renames, otherwise shared)."""
        if self.change_type == "deleted":
            return self.old_path
        return self.new_path

    @property
    def lines_added(self) -> int:
        return sum(1 for h in self.hunks for ln in h.lines if ln.kind == "added")

    @property
    def lines_removed(self) -> int:
        return sum(1 for h in self.hunks for ln in h.lines if ln.kind == "removed")

    @property
    def added_lines(self) -> list[HunkLine]:
        return [ln for h in self.hunks for ln in h.lines if ln.kind == "added"]

    @property
    def removed_lines(self) -> list[HunkLine]:
        return [ln for h in self.hunks for ln in h.lines if ln.kind == "removed"]

    @property
    def changed_line_numbers(self) -> set[int]:
        """New-file line numbers that are added (or removed adjacent lines)."""
        nums: set[int] = set()
        for h in self.hunks:
            for ln in h.lines:
                if ln.kind in ("added", "removed") and ln.new_lineno is not None:
                    nums.add(ln.new_lineno)
        return nums


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

_DIFF_HEADER = re.compile(r"^diff --git a/(.+?) b/(.+)$")
_OLD_FILE = re.compile(r"^--- (?:a/)?(.+)$")
_NEW_FILE = re.compile(r"^\+\+\+ (?:b/)?(.+)$")
_HUNK_HEADER = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
_NEW_FILE_MODE = re.compile(r"^new file mode")
_DELETED_FILE_MODE = re.compile(r"^deleted file mode")
_RENAME_FROM = re.compile(r"^rename from (.+)$")
_RENAME_TO = re.compile(r"^rename to (.+)$")
_SIMILARITY = re.compile(r"^similarity index")


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def parse_diff(diff_text: str) -> list[FileDiff]:
    """Parse a unified diff string into a list of FileDiff objects."""
    files: list[FileDiff] = []
    current: FileDiff | None = None
    current_hunk: Hunk | None = None

    old_lineno = 0
    new_lineno = 0

    lines = diff_text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]

        # ---- new file block -----------------------------------------------
        m = _DIFF_HEADER.match(line)
        if m:
            old_path = m.group(1)
            new_path = m.group(2)
            current_hunk = None
            change_type = "modified"  # default; refined below
            current = FileDiff(
                old_path=old_path,
                new_path=new_path,
                change_type=change_type,
            )
            files.append(current)
            i += 1
            continue

        if current is None:
            i += 1
            continue

        # ---- change-type refinement ---------------------------------------
        if _NEW_FILE_MODE.match(line):
            current.change_type = "added"
            i += 1
            continue

        if _DELETED_FILE_MODE.match(line):
            current.change_type = "deleted"
            i += 1
            continue

        if _SIMILARITY.match(line):
            current.change_type = "renamed"
            i += 1
            continue

        m = _RENAME_FROM.match(line)
        if m:
            current.old_path = m.group(1)
            i += 1
            continue

        m = _RENAME_TO.match(line)
        if m:
            current.new_path = m.group(1)
            i += 1
            continue

        # ---- hunk header --------------------------------------------------
        m = _HUNK_HEADER.match(line)
        if m:
            old_start = int(m.group(1))
            new_start = int(m.group(3))
            old_count = int(m.group(2)) if m.group(2) is not None else 1
            new_count = int(m.group(4)) if m.group(4) is not None else 1
            current_hunk = Hunk(
                old_start=old_start,
                old_count=old_count,
                new_start=new_start,
                new_count=new_count,
            )
            current.hunks.append(current_hunk)
            old_lineno = old_start
            new_lineno = new_start
            i += 1
            continue

        # ---- hunk content -------------------------------------------------
        if current_hunk is not None:
            if line.startswith("+") and not line.startswith("+++"):
                current_hunk.lines.append(
                    HunkLine("added", line[1:], None, new_lineno)
                )
                new_lineno += 1
            elif line.startswith("-") and not line.startswith("---"):
                current_hunk.lines.append(
                    HunkLine("removed", line[1:], old_lineno, None)
                )
                old_lineno += 1
            elif line.startswith(" ") or line == "":
                current_hunk.lines.append(
                    HunkLine("context", line[1:] if line else "", old_lineno, new_lineno)
                )
                old_lineno += 1
                new_lineno += 1

        i += 1

    return files
