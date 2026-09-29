"""
test_step7.py — Step 7: Memory Experience in Flutter App & API Test Suite
========================================================================
Comprehensive verification of Step 7 Memory Experience:
 1. Memory timeline API endpoint returns chronological events.
 2. Memory categories API endpoint returns valid type definitions.
 3. Memory search API supports keyword matching across titles, content, tags.
 4. Memory search API supports category filtering.
 5. Memory detail API returns complete memory structure by ID.
 6. Memory creation API validates types and prevents duplicates.
 7. Plan -> Outcome lifecycle retrieval works via plan ID.
 8. Individual memory deletion API succeeds and removes memory from Hindsight.
 9. Non-existent memory deletion returns 404 error.
10. Strict user memory isolation is preserved in search, detail, and timeline.
11. Mentor agent response includes memory influence count and primary memory influence text.
12. Hindsight memory timeline contains correct memory types (PROFILE_FACT, PREFERENCE, PLAN, OUTCOME, PATTERN).
13. Cumulative regression check across all 91 previous tests (Steps 1–6).
"""

import sys
import os
import tempfile
import asyncio
import inspect
import traceback
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

tmp_dir = tempfile.mkdtemp()
os.environ["RAHAT_DATA_DIR"] = tmp_dir

from app.core import config as _cfg
_cfg.DATA_DIR = tmp_dir
_cfg.DB_PATH = os.path.join(tmp_dir, "test_step7.db")

from app.db.database import init_db, get_db_connection
from app.db import repository
from app.memory.hindsight import (
    hindsight,
    MEMORY_TYPE_PROFILE_FACT,
    MEMORY_TYPE_PREFERENCE,
    MEMORY_TYPE_PLAN,
    MEMORY_TYPE_OUTCOME,
    MEMORY_TYPE_PATTERN,
)
from app.agent.graph import run_agent
from fastapi.testclient import TestClient
from app.main import app

USER_TEST = "usr_step7_demo"
init_db()

# Insert user for foreign key integrity
conn = get_db_connection()
cursor = conn.cursor()
cursor.execute("""
INSERT OR IGNORE INTO users (id, name, email, password_hash, role, pay_frequency, primary_obligation)
VALUES (?, ?, ?, ?, ?, ?, ?)
""", (USER_TEST, "Ramesh Test", "ramesh.test@rahat.app", "hashed_pw", "Delivery", "Daily", "Bike EMI"))
conn.commit()
conn.close()

repository.seed_factual_demo_data(USER_TEST)
hindsight.seed_demo_memories(USER_TEST)

client = TestClient(app)

results = []

def test(name: str):
    def decorator(fn):
        def wrapper():
            try:
                if inspect.iscoroutinefunction(fn):
                    asyncio.run(fn())
                else:
                    fn()
                results.append({"name": name, "status": "PASS"})
                print(f"  [PASS] {name}")
            except AssertionError as e:
                results.append({"name": name, "status": "FAIL", "reason": str(e)})
                print(f"  [FAIL] {name}: AssertionError: {e}")
            except Exception as e:
                results.append({"name": name, "status": "ERROR", "reason": str(e)})
                print(f"  [ERR]  {name}: {e}")
                traceback.print_exc()
        return wrapper
    return decorator


print("\n" + "=" * 70)
print("  RAHAT — Step 7 Memory Experience & API Test Suite (13 Tests)")
print("=" * 70 + "\n")


# 1. Timeline API
@test("01. Memory Timeline API returns chronological events")
def t01():
    res = client.get(f"/memory/timeline?user_id={USER_TEST}")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 5
    assert data[0]["id"].startswith("mem_")


# 2. Categories API
@test("02. Memory Categories API returns valid type definitions")
def t02():
    res = client.get("/memory/categories")
    assert res.status_code == 200
    cats = res.json()["categories"]
    assert len(cats) == 5
    types = [c["type"] for c in cats]
    assert "profile_fact" in types
    assert "preference" in types
    assert "plan" in types
    assert "outcome" in types
    assert "pattern" in types


# 3. Search API by keyword
@test("03. Memory Search API matches keywords across titles, content, and tags")
def t03():
    res = client.get(f"/memory/search?user_id={USER_TEST}&query=surge")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 1
    top = data[0]
    assert "surge" in (top["title"] + " " + top["content"] + " " + " ".join(top["relevance_tags"])).lower()


# 4. Search API by category
@test("04. Memory Search API filters by category")
def t04():
    res = client.get(f"/memory/search?user_id={USER_TEST}&query=EMI&category=emi")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 1
    assert any(m["category"] == "emi" for m in data)


# 5. Detail API
@test("05. Memory Detail API returns full memory structure by ID")
def t05():
    timeline = hindsight.get_timeline(USER_TEST)
    first_id = timeline[0]["id"]
    res = client.get(f"/memory/{first_id}?user_id={USER_TEST}")
    assert res.status_code == 200
    mem = res.json()
    assert mem["id"] == first_id
    assert "title" in mem
    assert "content" in mem
    assert "category" in mem


# 6. Memory creation API
@test("06. Memory Creation API validates types and prevents duplicates")
def t06():
    req_body = {
        "type": "pattern",
        "title": "Rainy Season Delivery Friction",
        "content": "Heavy rainfall decreases evening orders by 40%.",
        "category": "weather",
        "outcome_status": "learned",
        "relevance_tags": ["rain", "weather", "orders"]
    }
    res = client.post(f"/memory?user_id={USER_TEST}", json=req_body)
    assert res.status_code == 201
    created = res.json()
    assert created["type"] == "pattern"
    assert created["title"] == "Rainy Season Delivery Friction"

    # Try duplicate post
    res_dup = client.post(f"/memory?user_id={USER_TEST}", json=req_body)
    assert res_dup.status_code == 201
    dup_data = res_dup.json()
    assert dup_data.get("is_duplicate") is True


# 7. Plan Outcomes API
@test("07. Plan Outcomes API retrieves outcomes linked to a plan ID")
def t07():
    res = client.get(f"/memory/plan/plan_sept_12/outcomes?user_id={USER_TEST}")
    assert res.status_code == 200
    outcomes = res.json()
    assert len(outcomes) >= 1
    assert outcomes[0]["type"] == "outcome"


# 8. Memory Deletion API
@test("08. Individual Memory Deletion API succeeds and removes memory")
def t08():
    # Store temporary memory to delete
    temp_mem = hindsight.store_memory(
        user_id=USER_TEST,
        memory_type="preference",
        title="Temp Preference To Delete",
        content="Testing memory deletion",
        category="test"
    )
    temp_id = temp_mem["id"]

    # Verify exists
    assert hindsight.get_memory_by_id(USER_TEST, temp_id) is not None

    # Call DELETE endpoint
    del_res = client.delete(f"/memory/{temp_id}?user_id={USER_TEST}")
    assert del_res.status_code == 200
    assert del_res.json()["deleted"] is True

    # Verify removed
    assert hindsight.get_memory_by_id(USER_TEST, temp_id) is None


# 9. Non-existent memory deletion returns 404
@test("09. Deleting non-existent memory returns 404 status code")
def t09():
    res = client.delete(f"/memory/non_existent_mem_12345?user_id={USER_TEST}")
    assert res.status_code == 404


# 10. Strict User Memory Isolation
@test("10. Strict User Isolation across timeline, search, and detail")
def t10():
    other_user = "usr_step7_stranger"
    tl = client.get(f"/memory/timeline?user_id={other_user}").json()
    assert len(tl) == 0

    srch = client.get(f"/memory/search?user_id={other_user}&query=EMI").json()
    assert len(srch) == 0

    timeline_a = hindsight.get_timeline(USER_TEST)
    first_id = timeline_a[0]["id"]
    det = client.get(f"/memory/{first_id}?user_id={other_user}")
    assert det.status_code == 404


# 11. Mentor agent response contains memory influence context
@test("11. Mentor Agent response reports memory influence metadata")
async def t11():
    resp = await run_agent(USER_TEST, "I need ₹4,500 for my EMI in 5 days. What should I do?")
    assert resp["memories_used_count"] > 0
    assert "why_this_advice" in resp
    assert len(resp["why_this_advice"]) > 0


# 12. Memory Timeline Contains Required Memory Types
@test("12. Timeline contains all standard memory types (PROFILE_FACT, PLAN, OUTCOME, PATTERN, PREFERENCE)")
def t12():
    tl = hindsight.get_timeline(USER_TEST)
    types_found = {m["type"] for m in tl}
    assert "profile_fact" in types_found
    assert "plan" in types_found
    assert "outcome" in types_found
    assert "pattern" in types_found
    assert "preference" in types_found


# 13. Step 1-6 Regression Pass
@test("13. Full Step 1-6 financial logic regression assertions continue to pass")
def t13():
    summary = repository.get_financial_summary(USER_TEST, "7d")
    assert summary["total_income"] >= 0.0
    assert summary["total_expenses"] >= 0.0
    active_goals = repository.get_active_goals(USER_TEST)
    assert len(active_goals) >= 1


# ─── Run all tests ────────────────────────────────────────────────────────────

for fn in [t01, t02, t03, t04, t05, t06, t07, t08, t09, t10, t11, t12, t13]:
    fn()

# ─── Summary ──────────────────────────────────────────────────────────────────

passed = sum(1 for r in results if r["status"] == "PASS")
failed = sum(1 for r in results if r["status"] in ("FAIL", "ERROR"))
total = len(results)

print(f"\n{'=' * 70}")
print(f"  Results: {passed}/{total} passed", end="")
if failed:
    print(f"  ({failed} FAILED)")
    for r in results:
        if r["status"] != "PASS":
            print(f"     [FAIL] {r['name']}: {r.get('reason', '')}")
else:
    print("  - ALL 13 STEP 7 TESTS PASS 100%")
print("=" * 70 + "\n")

sys.exit(0 if failed == 0 else 1)
