# ChangeStory — API Contract

**Version:** 1.0  
**Base URL (local dev):** `http://localhost:8000/api/v1`  
**Content-Type:** `application/json` (all requests and responses)

> This document is the single source of truth for the frontend ↔ backend contract.  
> Update it whenever a model or endpoint changes.

---

## Table of contents

1. [Common types](#1-common-types)
2. [POST /analyze](#2-post-apiv1analyze)
3. [GET /reports/{session_id}](#3-get-apiv1reportssession_id)
4. [GET /reports/{session_id}/export.json](#4-get-apiv1reportssession_idexportjson)
5. [GET /reports/{session_id}/export.md](#5-get-apiv1reportssession_idexportmd)
6. [GET /scenarios](#6-get-apiv1scenarios)
7. [POST /verify/{session_id}](#7-post-apiv1verifysession_id)
8. [Error responses](#8-error-responses)

---

## 1. Common types

### `AnalysisMode`

```
"quick"    – symbol identification + risk summary only
"standard" – adds caller graph and test recommendations  (default)
"deep"     – adds best-effort transitive impact (may be slow)
```

### `Confidence`

```
"confirmed"  – verified at runtime
"potential"  – statically inferred; could not be proven
"unknown"    – insufficient information
```

### `RiskLevel`

```
"high" | "medium" | "low" | "info"
```

---

### `ChangedFile`

```jsonc
{
  "path": "src/payments/processor.py",   // str  — repo-relative path
  "change_type": "modified",             // "added" | "modified" | "deleted" | "renamed"
  "lines_added": 14,                     // int
  "lines_removed": 3,                    // int
  "changed_symbols": ["PaymentProcessor.charge", "validate_amount"]  // list[str]
}
```

### `Symbol`

```jsonc
{
  "name": "PaymentProcessor.charge",     // str  — qualified name
  "kind": "method",                      // "function" | "method" | "class" | "module"
  "file": "src/payments/processor.py",   // str
  "line_start": 42,                      // int | null
  "line_end": 61,                        // int | null
  "change_type": "modified"              // same enum as ChangedFile.change_type | null
}
```

### `CallerRelationship`

```jsonc
{
  "caller": "billing.invoice.generate",  // str — qualified caller name
  "callee": "PaymentProcessor.charge",   // str — qualified callee name
  "caller_file": "src/billing/invoice.py",
  "caller_line": 88,                     // int | null
  "confidence": "potential"              // Confidence
}
```

### `Risk`

```jsonc
{
  "level": "high",                       // RiskLevel
  "title": "Public API signature changed",
  "description": "PaymentProcessor.charge had a parameter removed …",
  "affected_symbols": ["PaymentProcessor.charge"],
  "evidence": ["Line 44: def charge(self, amount) — was (self, amount, currency)"],
  "confidence": "potential"
}
```

### `TestRecommendation`

```jsonc
{
  "title": "Test PaymentProcessor.charge with boundary amounts",
  "rationale": "Method body changed; existing tests may not cover new branch.",
  "suggested_test_ids": ["tests/test_processor.py::test_charge_zero"],  // list[str]
  "priority": "high"   // "high" | "medium" | "low"
}
```

### `VerificationResult`

```jsonc
{
  "ran": true,            // bool — false if verification was skipped
  "passed": 2,            // int
  "failed": 0,            // int
  "skipped": 0,           // int
  "output": "...",        // str — raw pytest output
  "confirmed_safe": ["tests/test_processor.py::test_charge_zero"],  // list[str]
  "confirmed_failing": [],
  "note": "Ran against bundled sample project only."
}
```

### `Report`

```jsonc
{
  "session_id": "a1b2c3d4",             // str — 8-char hex
  "created_at": "2024-01-15T10:30:00Z", // ISO-8601 UTC
  "analysis_mode": "standard",          // AnalysisMode

  // Project context
  "project_context": {
    "inferred_language": "Python",
    "total_files_changed": 2,
    "total_symbols_changed": 5,
    "diff_size_lines": 42
  },

  // Summary counts
  "summary": {
    "changed_files": 2,
    "changed_symbols": 5,
    "affected_symbols": 3,
    "caller_relationships": 4,
    "risks": { "high": 1, "medium": 2, "low": 0, "info": 1 },
    "test_recommendations": 3
  },

  // Detail arrays
  "changed_files": [ /* ChangedFile */ ],
  "changed_symbols": [ /* Symbol */ ],
  "affected_symbols": [ /* Symbol — confidence = "potential" */ ],
  "caller_relationships": [ /* CallerRelationship */ ],
  "risks": [ /* Risk */ ],
  "test_recommendations": [ /* TestRecommendation */ ],

  // Verification (null until POST /verify is called)
  "verification": null,  // VerificationResult | null

  // Transparency
  "limitations": [
    "Caller detection is static AST-only; dynamic dispatch is not captured.",
    "Cross-repository calls are not analysed."
  ],
  "explanations": {
    "affected_symbols": "Symbols in the same file that reference a changed symbol.",
    "risks": "Heuristic rules applied to AST change patterns."
  }
}
```

---

## 2. POST /api/v1/analyze

Submit a unified diff for analysis.

### Request body

```jsonc
{
  "diff": "diff --git a/src/…\n…",  // str — unified diff text (required)
  "mode": "standard",               // AnalysisMode (optional, default "standard")
  "project_root_hint": "src/"       // str (optional) — hint for import resolution
}
```

### Response `200 OK`

Full `Report` object (see §1 `Report`).

### Response `422 Unprocessable Entity`

```jsonc
{ "detail": [{ "loc": ["body", "diff"], "msg": "field required", "type": "value_error.missing" }] }
```

---

## 3. GET /api/v1/reports/{session_id}

Retrieve a previously analysed report by its session ID.

### Path parameters

| Param | Type | Description |
|-------|------|-------------|
| `session_id` | `string` | 8-char hex returned by `/analyze` |

### Response `200 OK`

Full `Report` object.

### Response `404 Not Found`

```jsonc
{ "detail": "Report not found" }
```

---

## 4. GET /api/v1/reports/{session_id}/export.json

Download the full report as a JSON file.

**Response `200 OK`**  
`Content-Type: application/json`  
`Content-Disposition: attachment; filename="changestory-<session_id>.json"`  
Body: full `Report` object.

---

## 5. GET /api/v1/reports/{session_id}/export.md

Download the report as a Markdown document.

**Response `200 OK`**  
`Content-Type: text/markdown`  
`Content-Disposition: attachment; filename="changestory-<session_id>.md"`  
Body: human-readable Markdown.

---

## 6. GET /api/v1/scenarios

Returns three bundled demo scenarios so the frontend can let users explore without
providing their own diff.

### Response `200 OK`

```jsonc
{
  "scenarios": [
    {
      "id": "rename-function",
      "title": "Public function renamed",
      "description": "A widely-used utility function is renamed, breaking callers.",
      "mode": "standard",
      "diff": "diff --git …"   // str — ready to POST to /analyze
    },
    { "id": "add-parameter", … },
    { "id": "refactor-class", … }
  ]
}
```

---

## 7. POST /api/v1/verify/{session_id}

Run pytest against the bundled sample project.  
**Only works for sessions created from a bundled scenario.**  
Never executes arbitrary user code or commands.

### Response `200 OK`

```jsonc
{
  "session_id": "a1b2c3d4",
  "verification": { /* VerificationResult */ }
}
```

### Response `403 Forbidden`

```jsonc
{ "detail": "Verification is only available for bundled demo scenarios." }
```

### Response `404 Not Found`

```jsonc
{ "detail": "Report not found" }
```

---

## 8. Error responses

All errors follow FastAPI's default format:

```jsonc
{
  "detail": "Human-readable message"   // str  OR  list of validation errors
}
```

| HTTP Status | Meaning |
|-------------|---------|
| `400` | Bad request (e.g. unparseable diff) |
| `403` | Action not permitted (e.g. verify on non-demo session) |
| `404` | Resource not found |
| `422` | Validation error (Pydantic) |
| `500` | Internal server error |
