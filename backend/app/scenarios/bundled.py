"""
bundled.py — Three deterministic demo scenarios.

Each scenario is a realistic Python diff that exercises ChangeStory's
analysis features.  These are the only diffs that are eligible for
POST /verify.
"""

from __future__ import annotations

from app.models import AnalysisMode, Scenario

# ---------------------------------------------------------------------------
# Scenario 1 — Public function renamed (breaks callers)
# ---------------------------------------------------------------------------

_RENAME_DIFF = """\
diff --git a/src/utils/string_helpers.py b/src/utils/string_helpers.py
index 1a2b3c4..5d6e7f8 100644
--- a/src/utils/string_helpers.py
+++ b/src/utils/string_helpers.py
@@ -1,18 +1,18 @@
 \"\"\"Utility helpers for string processing.\"\"\"
 
-def format_username(name: str) -> str:
-    \"\"\"Return the username in canonical form.\"\"\"
-    return name.strip().lower()
+def normalise_username(name: str) -> str:
+    \"\"\"Return the username in canonical form (renamed from format_username).\"\"\"
+    return name.strip().lower()
 
 
 def truncate(text: str, max_len: int = 80) -> str:
     return text[:max_len]
diff --git a/src/auth/login.py b/src/auth/login.py
index aabbcc0..ddeeff1 100644
--- a/src/auth/login.py
+++ b/src/auth/login.py
@@ -1,12 +1,12 @@
 from src.utils.string_helpers import format_username
 
 
 def authenticate(username: str, password: str) -> bool:
-    clean = format_username(username)
+    clean = normalise_username(username)
     return _check_credentials(clean, password)
 
 
 def _check_credentials(username: str, password: str) -> bool:
     return username == "admin" and password == "secret"
"""

# ---------------------------------------------------------------------------
# Scenario 2 — Signature change (new required parameter)
# ---------------------------------------------------------------------------

_ADD_PARAM_DIFF = """\
diff --git a/src/payments/processor.py b/src/payments/processor.py
index 1111111..2222222 100644
--- a/src/payments/processor.py
+++ b/src/payments/processor.py
@@ -1,30 +1,32 @@
 \"\"\"Payment processing module.\"\"\"
 
 
 class PaymentProcessor:
 
     def __init__(self, gateway: str) -> None:
         self.gateway = gateway
 
-    def charge(self, amount: float) -> dict:
+    def charge(self, amount: float, currency: str = "USD") -> dict:
         \"\"\"Charge the given amount.\"\"\"
         if amount <= 0:
             raise ValueError("Amount must be positive")
+        if not currency:
+            raise ValueError("Currency must not be empty")
         return {"status": "ok", "amount": amount, "gateway": self.gateway}
 
     def refund(self, transaction_id: str) -> dict:
         return {"status": "refunded", "id": transaction_id}
 
 
-def validate_amount(amount) -> bool:
-    return amount > 0
+def validate_amount(amount: float, max_amount: float = 10_000) -> bool:
+    \"\"\"Validate amount is positive and within limits.\"\"\"
+    return 0 < amount <= max_amount
"""

# ---------------------------------------------------------------------------
# Scenario 3 — Class refactor (method split, error handling removed)
# ---------------------------------------------------------------------------

_REFACTOR_DIFF = """\
diff --git a/src/data/importer.py b/src/data/importer.py
index aaaaaaa..bbbbbbb 100644
--- a/src/data/importer.py
+++ b/src/data/importer.py
@@ -1,45 +1,52 @@
 \"\"\"CSV data importer.\"\"\"
 import csv
 import io
 
 
 class DataImporter:
 
     def __init__(self, source: str) -> None:
         self.source = source
         self._records: list[dict] = []
 
-    def load(self, raw_csv: str) -> list[dict]:
-        \"\"\"Parse CSV and return list of records.\"\"\"
-        try:
-            reader = csv.DictReader(io.StringIO(raw_csv))
-            self._records = [row for row in reader]
-            return self._records
-        except Exception as exc:
-            raise RuntimeError(f"Import failed: {exc}") from exc
+    def load(self, raw_csv: str) -> list[dict]:
+        \"\"\"Parse CSV and return list of records (error handling removed).\"\"\"
+        reader = csv.DictReader(io.StringIO(raw_csv))
+        self._records = [row for row in reader]
+        return self._records
+
+    def validate(self, records: list[dict], required_fields: list[str]) -> bool:
+        \"\"\"Validate that all records contain required fields.\"\"\"
+        for record in records:
+            for field in required_fields:
+                if field not in record:
+                    return False
+        return True
 
     def transform(self, records: list[dict]) -> list[dict]:
-        \"\"\"Apply basic normalisation.\"\"\"
+        \"\"\"Apply basic normalisation (refactored).\"\"\"
         return [
-            {k: v.strip() for k, v in row.items()}
+            {k: (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
             for row in records
         ]
 
+    def _apply_defaults(self, record: dict, defaults: dict) -> dict:
+        return {**defaults, **record}
+
 
-def import_csv(path: str) -> list[dict]:
-    importer = DataImporter(path)
-    raw = open(path).read()
-    return importer.load(raw)
+def import_csv(path: str, required_fields: list[str] | None = None) -> list[dict]:
+    \"\"\"Convenience wrapper — now validates fields.\"\"\"
+    importer = DataImporter(path)
+    raw = open(path).read()
+    records = importer.load(raw)
+    if required_fields:
+        importer.validate(records, required_fields)
+    return records
"""

# ---------------------------------------------------------------------------
# Public export
# ---------------------------------------------------------------------------

BUNDLED_SCENARIOS: list[Scenario] = [
    Scenario(
        id="rename-function",
        title="Public function renamed",
        description=(
            "A public utility function `format_username` is renamed to "
            "`normalise_username`. Existing callers in `auth/login.py` are "
            "updated in the diff, but any caller outside the diff will break."
        ),
        mode=AnalysisMode.standard,
        diff=_RENAME_DIFF,
    ),
    Scenario(
        id="add-parameter",
        title="Signature change — new parameter added",
        description=(
            "`PaymentProcessor.charge` gains a new `currency` parameter "
            "(defaulted, so not immediately breaking). `validate_amount` "
            "also gains a `max_amount` cap. Callers relying on positional "
            "arguments may need review."
        ),
        mode=AnalysisMode.standard,
        diff=_ADD_PARAM_DIFF,
    ),
    Scenario(
        id="refactor-class",
        title="Class refactored — error handling removed",
        description=(
            "`DataImporter.load` has its try/except block removed, new "
            "methods `validate` and `_apply_defaults` are added, and "
            "`import_csv` gains an optional validation step. Removing "
            "error handling is a medium-to-high risk change."
        ),
        mode=AnalysisMode.deep,
        diff=_REFACTOR_DIFF,
    ),
]

BUNDLED_IDS: set[str] = {s.id for s in BUNDLED_SCENARIOS}


def get_scenario(scenario_id: str) -> Scenario | None:
    for s in BUNDLED_SCENARIOS:
        if s.id == scenario_id:
            return s
    return None
