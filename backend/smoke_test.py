"""
smoke_test.py — End-to-end integration tests against the running server.
Run: python smoke_test.py
"""
import sys
import httpx
import json

BASE = "http://localhost:8000/api/v1"

# Inline the minimal diff so we don't need to import app during smoke
RENAME_DIFF = """\
diff --git a/src/utils/string_helpers.py b/src/utils/string_helpers.py
index 1a2b3c4..5d6e7f8 100644
--- a/src/utils/string_helpers.py
+++ b/src/utils/string_helpers.py
@@ -1,10 +1,10 @@
 \"\"\"Utility helpers.\"\"\"
 
-def format_username(name: str) -> str:
-    return name.strip().lower()
+def normalise_username(name: str) -> str:
+    return name.strip().lower()
 
 def truncate(text: str, max_len: int = 80) -> str:
     return text[:max_len]
"""

errors = []

def check(label, condition, detail=""):
    if condition:
        print(f"  PASS  {label}")
    else:
        print(f"  FAIL  {label}  {detail}")
        errors.append(label)

print("\n=== ChangeStory Smoke Tests ===\n")

try:
    client = httpx.Client(timeout=15)
except Exception as e:
    print(f"Cannot create HTTP client: {e}")
    sys.exit(1)

# --- Health ---
r = client.get("http://localhost:8000/health")
check("GET /health -> 200", r.status_code == 200)

# --- Root ---
r = client.get("http://localhost:8000/")
check("GET / -> 200", r.status_code == 200)
check("GET / has service key", "service" in r.json())

# --- Scenarios ---
r = client.get(f"{BASE}/scenarios")
check("GET /scenarios -> 200", r.status_code == 200)
data = r.json()
check("GET /scenarios has 3 items", len(data.get("scenarios", [])) == 3)
ids = {s["id"] for s in data["scenarios"]}
check("GET /scenarios includes rename-function", "rename-function" in ids)
check("GET /scenarios includes add-parameter", "add-parameter" in ids)
check("GET /scenarios includes refactor-class", "refactor-class" in ids)

# --- Analyze ---
r = client.post(f"{BASE}/analyze", json={"diff": RENAME_DIFF, "mode": "standard"})
check("POST /analyze -> 200", r.status_code == 200, r.text[:200])
report = r.json()
sid = report.get("session_id", "")
check("POST /analyze has session_id", bool(sid))
check("POST /analyze has project_context", "project_context" in report)
check("POST /analyze has summary", "summary" in report)
check("POST /analyze has changed_files", isinstance(report.get("changed_files"), list))
check("POST /analyze has changed_symbols", isinstance(report.get("changed_symbols"), list))
check("POST /analyze has affected_symbols", isinstance(report.get("affected_symbols"), list))
check("POST /analyze has caller_relationships", isinstance(report.get("caller_relationships"), list))
check("POST /analyze has risks", isinstance(report.get("risks"), list))
check("POST /analyze has test_recommendations", isinstance(report.get("test_recommendations"), list))
check("POST /analyze has limitations", len(report.get("limitations", [])) > 0)
check("POST /analyze has explanations", isinstance(report.get("explanations"), dict))
check("POST /analyze verification is null", report.get("verification") is None)
check("POST /analyze is_demo=False", report.get("is_demo") is False)
print(f"       summary={json.dumps(report['summary'])}")

# --- Retrieve ---
r = client.get(f"{BASE}/reports/{sid}")
check("GET /reports/{id} -> 200", r.status_code == 200)

# --- 404 ---
r = client.get(f"{BASE}/reports/00000000")
check("GET /reports/badid -> 404", r.status_code == 404)

# --- Export JSON ---
r = client.get(f"{BASE}/reports/{sid}/export.json")
check("GET export.json -> 200", r.status_code == 200)
check("GET export.json content-disposition", "changestory" in r.headers.get("content-disposition", ""))

# --- Export MD ---
r = client.get(f"{BASE}/reports/{sid}/export.md")
check("GET export.md -> 200", r.status_code == 200)
check("GET export.md starts with ChangeStory", "ChangeStory" in r.text[:50])
check("GET export.md has ## Risks", "## Risks" in r.text)

# --- Scenario analyze shortcut ---
r = client.post(f"{BASE}/scenarios/add-parameter/analyze")
check("POST /scenarios/add-parameter/analyze -> 200", r.status_code == 200, r.text[:200])
demo = r.json()
demo_sid = demo.get("session_id", "")
check("Scenario analyze is_demo=True", demo.get("is_demo") is True)
check("Scenario analyze scenario_id set", demo.get("scenario_id") == "add-parameter")

# --- Verify: 403 for non-demo ---
r = client.post(f"{BASE}/verify/{sid}")
check("POST /verify non-demo -> 403", r.status_code == 403)

# --- Verify: 404 for unknown ---
r = client.post(f"{BASE}/verify/00000000")
check("POST /verify unknown -> 404", r.status_code == 404)

# --- Verify: demo session ---
r = client.post(f"{BASE}/verify/{demo_sid}")
check("POST /verify demo -> 200", r.status_code == 200, r.text[:200])
if r.status_code == 200:
    v = r.json()
    vr = v.get("verification", {})
    check("Verify ran=True", vr.get("ran") is True)
    check("Verify passed >= 0", isinstance(vr.get("passed"), int) and vr["passed"] >= 0)
    check("Verify has note", bool(vr.get("note")))
    print(f"       verification: ran={vr['ran']} passed={vr['passed']} failed={vr['failed']}")

# --- Bad diff -> 400 ---
r = client.post(f"{BASE}/analyze", json={"diff": "not a diff at all"})
check("POST /analyze bad diff -> 400", r.status_code == 400)

# --- Empty diff -> 422 ---
r = client.post(f"{BASE}/analyze", json={})
check("POST /analyze missing diff -> 422", r.status_code == 422)

# --- Summary ---
print()
if errors:
    print(f"FAILED — {len(errors)} test(s) failed:")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print("ALL SMOKE TESTS PASSED")
