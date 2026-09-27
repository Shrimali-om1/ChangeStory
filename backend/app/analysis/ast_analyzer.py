"""
ast_analyzer.py — Python AST analysis utilities.

Given the *text* of added/removed lines from a diff, we reconstruct enough
context to identify:
  - which symbols (functions, methods, classes) were changed
  - which symbols in the same source call a changed symbol (caller graph)

Because we only have the diff — not the full repo — all caller relationships
are labelled "potential".
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field

from app.analysis.diff_parser import FileDiff


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class SymbolInfo:
    name: str          # qualified: "ClassName.method_name" or "function_name"
    kind: str          # "function" | "method" | "class"
    file: str
    line_start: int
    line_end: int
    calls: list[str] = field(default_factory=list)  # names called inside body


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _qualify(class_name: str | None, func_name: str) -> str:
    if class_name:
        return f"{class_name}.{func_name}"
    return func_name


def _collect_calls(node: ast.AST) -> list[str]:
    """Return a deduplicated list of function/method names called within node."""
    names: list[str] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            func = child.func
            if isinstance(func, ast.Name):
                names.append(func.id)
            elif isinstance(func, ast.Attribute):
                names.append(func.attr)
    seen: set[str] = set()
    result: list[str] = []
    for n in names:
        if n not in seen:
            seen.add(n)
            result.append(n)
    return result


# ---------------------------------------------------------------------------
# Parse source text → SymbolInfo list
# ---------------------------------------------------------------------------


def extract_symbols(source: str, file_path: str) -> list[SymbolInfo]:
    """
    Parse Python source and return all top-level and class-level functions.
    Returns an empty list if parsing fails (e.g. partial / broken source).
    """
    try:
        tree = ast.parse(source, filename=file_path)
    except SyntaxError:
        return []

    symbols: list[SymbolInfo] = []

    # Build a set of function nodes that are direct children of a class body
    # so we can skip them when we encounter them as standalone ast.walk nodes.
    method_nodes: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method_nodes.add(id(item))

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            class_name = node.name
            symbols.append(
                SymbolInfo(
                    name=class_name,
                    kind="class",
                    file=file_path,
                    line_start=node.lineno,
                    line_end=node.end_lineno or node.lineno,
                    calls=_collect_calls(node),
                )
            )
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    symbols.append(
                        SymbolInfo(
                            name=_qualify(class_name, item.name),
                            kind="method",
                            file=file_path,
                            line_start=item.lineno,
                            line_end=item.end_lineno or item.lineno,
                            calls=_collect_calls(item),
                        )
                    )
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Only emit top-level functions (skip methods already emitted above)
            if id(node) not in method_nodes:
                symbols.append(
                    SymbolInfo(
                        name=node.name,
                        kind="function",
                        file=file_path,
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno,
                        calls=_collect_calls(node),
                    )
                )

    return symbols


# ---------------------------------------------------------------------------
# Identify changed symbols from a FileDiff
# ---------------------------------------------------------------------------


def identify_changed_symbols(file_diff: FileDiff) -> list[SymbolInfo]:
    """
    Reconstruct symbol names touched by this diff.

    Strategy:
    1. Try to parse the added lines as a Python source fragment.
       If they form valid Python, extract symbols directly.
    2. Otherwise fall back to regex over the raw diff lines.
    """
    changed_line_numbers = file_diff.changed_line_numbers

    # ---- Strategy 1: parse added block ------------------------------------
    added_text = "\n".join(ln.text for ln in file_diff.added_lines)
    symbols_from_added = extract_symbols(added_text, file_diff.path)

    if symbols_from_added:
        return symbols_from_added

    # ---- Strategy 2: regex heuristic over all changed lines ---------------
    symbols: list[SymbolInfo] = []
    seen: set[str] = set()

    all_changed = file_diff.added_lines + file_diff.removed_lines
    func_re = re.compile(r"^\s*(?:async\s+)?def\s+(\w+)\s*\(")
    class_re = re.compile(r"^\s*class\s+(\w+)\s*[:(]")

    for ln in all_changed:
        m = class_re.match(ln.text)
        if m:
            name = m.group(1)
            if name not in seen:
                seen.add(name)
                lineno = ln.new_lineno or ln.old_lineno or 0
                symbols.append(
                    SymbolInfo(
                        name=name, kind="class",
                        file=file_diff.path,
                        line_start=lineno, line_end=lineno,
                    )
                )
            continue

        m = func_re.match(ln.text)
        if m:
            name = m.group(1)
            if name not in seen:
                seen.add(name)
                lineno = ln.new_lineno or ln.old_lineno or 0
                symbols.append(
                    SymbolInfo(
                        name=name, kind="function",
                        file=file_diff.path,
                        line_start=lineno, line_end=lineno,
                    )
                )

    return symbols


# ---------------------------------------------------------------------------
# Find callers within the diff itself
# ---------------------------------------------------------------------------


def find_callers_in_diff(
    changed_symbol_names: list[str],
    all_file_diffs: list[FileDiff],
) -> list[tuple[str, str, str, int | None]]:
    """
    Return (caller_name, callee_name, caller_file, caller_line) tuples.

    We look for the changed symbol names being referenced inside the *added*
    lines of every file in the diff.  All results are "potential".
    """
    results: list[tuple[str, str, str, int | None]] = []
    target_set = set(changed_symbol_names)

    for fd in all_file_diffs:
        # Build symbol map for this file's added text
        added_text = "\n".join(ln.text for ln in fd.added_lines)
        file_symbols = extract_symbols(added_text, fd.path)

        for sym in file_symbols:
            for call in sym.calls:
                # Simple name match or "Class.method" → "method"
                short_call = call.split(".")[-1]
                for target in target_set:
                    short_target = target.split(".")[-1]
                    if short_call == short_target and sym.name != target:
                        results.append((sym.name, target, fd.path, sym.line_start))

    return results
