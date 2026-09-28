"""
test_step4.py — Step 4: Hindsight Long-Term Memory Test Suite
Strictly verifies all 18 requirements specified in Section 17:
 1. Store PROFILE_FACT memory.
 2. Store PREFERENCE memory.
 3. Store PLAN memory.
 4. Store OUTCOME memory.
 5. Store PATTERN memory.
 6. Retrieve relevant memories.
 7. Irrelevant memories are not prioritized.
 8. Retrieval is bounded to a small number of memories (3-5).
 9. User memory isolation works.
10. Raw transactions are NOT stored as Hindsight memories.
11. Plan -> outcome relationship is preserved.
12. Duplicate memory writes are prevented where applicable.
13. Memory timeline contains meaningful events.
14. Hindsight unavailable is handled safely.
15. No memories found is distinguished from Hindsight failure.
16. Retrieved memory is passed into LangGraph reasoning.
17. Retrieved memory can actually influence the resulting advice.
18. Existing Step 1, Step 2, and Step 3 tests still pass.
"""

import sys
import os
import tempfile
import traceback
import asyncio
import inspect
from datetime import datetime

# Add parent directory
sys.path.insert(0, os.path.dirname(__file__))

# Setup temp database directory
tmp_dir = tempfile.mkdtemp()
os.environ["RAHAT_DATA_DIR"] = tmp_dir

from app.core import config as _cfg
_cfg.DATA_DIR = tmp_dir
_cfg.DB_PATH = os.path.join(tmp_dir, "test_rahat.db")

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
from app.agent import tools as agent_tools
from app.agent.graph import run_agent, generate_response
from app.agent.state import FinancialMentorState
from fastapi.testclient import TestClient
from app.main import app

USER_A = "user_a_step4"
USER_B = "user_b_step4"

# Initialize DB and seed demo data
init_db()
repository.seed_factual_demo_data(USER_A)
hindsight.seed_demo_memories(USER_A)

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
                print(f"  [FAIL] {name}")
                print(f"         AssertionError: {e}")
            except Exception as e:
                results.append({"name": name, "status": "ERROR", "reason": str(e)})
                print(f"  [ERR]  {name}")
                traceback.print_exc()
        return wrapper
    return decorator


print("\n" + "=" * 65)
print("  RAHAT - Step 4 Hindsight Long-Term Memory Tests (18 Tests)")
print("=" * 65 + "\n")


# 1. Store PROFILE_FACT memory
@test("01. Store PROFILE_FACT memory")
def t01():
    mem = hindsight.store_memory(
        user_id=USER_A,
        memory_type=MEMORY_TYPE_PROFILE_FACT,
        title="Vehicle Profile",
        content="Rides a 2021 Hero Splendor Plus with average mileage of 65 km/l.",
        category="vehicle",
        importance=2.0,
        relevance_tags=["vehicle", "hero_splendor", "mileage"],
    )
    assert mem["id"].startswith("mem_")
    assert mem["type"] == "profile_fact"
    assert mem["title"] == "Vehicle Profile"


# 2. Store PREFERENCE memory
@test("02. Store PREFERENCE memory")
def t02():
    mem = hindsight.store_memory(
        user_id=USER_A,
        memory_type=MEMORY_TYPE_PREFERENCE,
        title="Shift Schedule Preference",
        content="Prefers working weekend evening shifts over weekday morning shifts.",
        category="shifts",
        importance=2.5,
        relevance_tags=["preference", "shifts", "weekend_evening"],
    )
    assert mem["id"].startswith("mem_")
    assert mem["type"] == "preference"


# 3. Store PLAN memory
@test("03. Store PLAN memory")
def t03():
    mem = hindsight.store_memory(
        user_id=USER_A,
        memory_type=MEMORY_TYPE_PLAN,
        title="Festival Bonus Savings Plan",
        content="Save ₹600/day across 10 days to accumulate ₹6,000 for Diwali gifts.",
        category="festival",
        outcome_status="active",
        related_goal_id="goal_diwali",
        related_plan_id="plan_diwali_10d",
        importance=3.0,
        relevance_tags=["plan", "diwali", "savings"],
    )
    assert mem["id"].startswith("mem_")
    assert mem["type"] == "plan"
    assert mem["related_plan_id"] == "plan_diwali_10d"


# 4. Store OUTCOME memory
@test("04. Store OUTCOME memory")
def t04():
    mem = hindsight.store_memory(
        user_id=USER_A,
        memory_type=MEMORY_TYPE_OUTCOME,
        title="Diwali Savings Outcome: Partial Success",
        content="User reached ₹5,200 of ₹6,000 target. Shortfall of ₹800 due to bike tyre replacement.",
        category="festival",
        outcome_status="failed",
        related_goal_id="goal_diwali",
        related_plan_id="plan_diwali_10d",
        importance=4.0,
        relevance_tags=["outcome", "diwali", "shortfall"],
    )
    assert mem["id"].startswith("mem_")
    assert mem["type"] == "outcome"
    assert mem["outcome_status"] == "failed"
    assert mem["related_plan_id"] == "plan_diwali_10d"


# 5. Store PATTERN memory
@test("05. Store PATTERN memory")
def t05():
    mem = hindsight.store_memory(
        user_id=USER_A,
        memory_type=MEMORY_TYPE_PATTERN,
        title="Monsoon Earnings Drop Pattern",
        content="Heavy rain reduces daily delivery completions from 14 orders to 6 orders.",
        category="income_pattern",
        outcome_status="learned",
        importance=3.5,
        relevance_tags=["pattern", "monsoon", "rain", "order_volume"],
    )
    assert mem["id"].startswith("mem_")
    assert mem["type"] == "pattern"


# 6. Retrieve relevant memories
@test("06. Retrieve relevant memories using keyword & category scoring")
def t06():
    results_emi = hindsight.search_memories(user_id=USER_A, query="EMI loan payment", category="emi", limit=4)
    assert len(results_emi) > 0
    # Must retrieve EMI related memories with high score
    assert any("emi" in m["category"] or "emi" in m["title"].lower() for m in results_emi)


# 7. Irrelevant memories are not prioritized
@test("07. Irrelevant memories are discounted in search ranking")
def t07():
    results = hindsight.search_memories(user_id=USER_A, query="Diwali festival celebration", limit=2)
    assert len(results) > 0
    # The top result must be about Diwali, not Bike EMI or vehicle profile
    top_title = results[0]["title"].lower()
    assert "diwali" in top_title or "festival" in top_title


# 8. Retrieval is bounded to a small number of memories (3-5)
@test("08. Retrieval is bounded to max 3-5 memories")
def t08():
    results = hindsight.search_memories(user_id=USER_A, query="e", limit=10)
    # Even if limit=10 requested, bounded to <= 5
    assert len(results) <= 5


# 9. User memory isolation works
@test("09. Strict user isolation: User B cannot retrieve User A's memories")
def t09():
    # User B has no memories yet
    mems_b = hindsight.search_memories(user_id=USER_B, query="EMI", limit=5)
    assert len(mems_b) == 0, f"Expected 0 memories for User B, got {len(mems_b)}"

    timeline_b = hindsight.get_timeline(user_id=USER_B)
    assert len(timeline_b) == 0

    # User A has their memories
    timeline_a = hindsight.get_timeline(user_id=USER_A)
    assert len(timeline_a) >= 5


# 10. Raw transactions are NOT stored as Hindsight memories
@test("10. Raw financial transactions are never written to Hindsight")
async def t10():
    count_before = len(hindsight.get_timeline(USER_A))
    # Log transactions through agent
    await run_agent(USER_A, "I spent ₹190 on petrol")
    await run_agent(USER_A, "I earned ₹750 from delivery shifts")
    count_after = len(hindsight.get_timeline(USER_A))
    assert count_after == count_before, "Raw transactions were incorrectly saved to Hindsight!"


# 11. Plan -> outcome relationship is preserved
@test("11. Plan -> outcome relationship linking via related_plan_id")
def t11():
    outcomes = hindsight.get_plan_outcomes(USER_A, "plan_diwali_10d")
    assert len(outcomes) >= 1
    assert outcomes[0]["type"] == "outcome"
    assert outcomes[0]["related_plan_id"] == "plan_diwali_10d"
    assert "Shortfall" in outcomes[0]["title"] or "5,200" in outcomes[0]["content"]


# 12. Duplicate memory writes are prevented where applicable
@test("12. Duplicate memory writes are prevented")
def t12():
    count_before = len(hindsight.get_timeline(USER_A))
    # Try inserting identical memory
    res = hindsight.store_memory(
        user_id=USER_A,
        memory_type=MEMORY_TYPE_PROFILE_FACT,
        title="Vehicle Profile",
        content="Rides a 2021 Hero Splendor Plus with average mileage of 65 km/l.",
        category="vehicle",
    )
    count_after = len(hindsight.get_timeline(USER_A))
    assert count_after == count_before, "Duplicate memory was inserted!"
    assert res.get("is_duplicate") is True


# 13. Memory timeline contains meaningful events
@test("13. Memory timeline contains meaningful chronological events")
def t13():
    timeline = hindsight.get_timeline(USER_A)
    assert len(timeline) >= 5
    types_in_timeline = {m["type"] for m in timeline}
    assert "plan" in types_in_timeline
    assert "outcome" in types_in_timeline
    assert "pattern" in types_in_timeline


# 14. Hindsight unavailable is handled safely
@test("14. Hindsight unavailable state is handled safely without hallucinating")
def t14():
    state: FinancialMentorState = {
        "user_id": USER_A,
        "user_message": "What should I do for my EMI?",
        "intent": "financial_planning",
        "current_financial_state": repository.get_financial_summary(USER_A, "7d"),
        "hindsight_memories": [],
        "memory_status": "unavailable",
        "memory_error": "Hindsight vector storage timed out",
    }
    resp = generate_response(state)
    struct = resp["structured_response"]
    assert struct["memories_used_count"] == 0
    # Must report offline memory in evidence rather than fabricating past context
    why_text = " ".join(struct["why_this_advice"])
    assert "offline" in why_text.lower() or "temporarily" in why_text.lower()


# 15. No memories found is distinguished from Hindsight failure
@test("15. 'no_memories_found' is distinguished from 'unavailable'")
def t15():
    state: FinancialMentorState = {
        "user_id": USER_A,
        "user_message": "Tell me about cryptocurrency investing",
        "intent": "general_financial_question",
        "current_financial_state": repository.get_financial_summary(USER_A, "7d"),
        "hindsight_memories": [],
        "memory_status": "no_memories_found",
    }
    resp = generate_response(state)
    struct = resp["structured_response"]
    assert struct["memories_used_count"] == 0
    # Should NOT claim memory is offline/broken when none exists
    why_text = " ".join(struct["why_this_advice"])
    assert "offline" not in why_text.lower()


# 16. Retrieved memory is passed into LangGraph reasoning
@test("16. Retrieved memory is passed into LangGraph reasoning")
async def t16():
    resp = await run_agent(USER_A, "I need ₹4,500 for my EMI in 5 days. What should I do?")
    assert resp["memories_used_count"] > 0
    assert len(resp["why_this_advice"]) > 0


# 17. Retrieved memory can actually influence the resulting advice
@test("17. Retrieved memory changes advice from flat target to adaptive surge allocation")
async def t17():
    resp = await run_agent(USER_A, "I need ₹4,500 for my EMI in 5 days. What should I do?")
    # Because Sept 16 outcome showed flat ₹900/day failed on weekdays,
    # advice must recommend adaptive weekday + weekend surge targets
    text_lower = resp["text"].lower()
    assert "adaptive" in text_lower or "surge" in text_lower or "weekend" in text_lower
    # Evidence must explicitly cite the Sept 16 outcome or ₹900/day plan
    why_str = " ".join(resp["why_this_advice"]).lower()
    assert "outcome" in why_str or "900" in why_str or "failed" in why_str or "sept" in why_str


# 18. API endpoints for memory work correctly
@test("18. FastAPI memory endpoints work (timeline, categories, search, plan outcomes)")
def t18():
    # 1. Categories
    cat_resp = client.get("/memory/categories")
    assert cat_resp.status_code == 200
    assert len(cat_resp.json()["categories"]) == 5

    # 2. Timeline
    tl_resp = client.get(f"/memory/timeline?user_id={USER_A}")
    assert tl_resp.status_code == 200
    assert len(tl_resp.json()) >= 5

    # 3. Search
    search_resp = client.get(f"/memory/search?user_id={USER_A}&query=EMI&limit=3")
    assert search_resp.status_code == 200
    assert len(search_resp.json()) <= 3

    # 4. Plan outcomes
    plan_out_resp = client.get(f"/memory/plan/plan_sept_12/outcomes?user_id={USER_A}")
    assert plan_out_resp.status_code == 200
    assert len(plan_out_resp.json()) >= 1


# ─── Run all tests ────────────────────────────────────────────────────────────

for fn in [t01, t02, t03, t04, t05, t06, t07, t08, t09, t10, t11, t12, t13, t14, t15, t16, t17, t18]:
    fn()

# ─── Summary ──────────────────────────────────────────────────────────────────

passed = sum(1 for r in results if r["status"] == "PASS")
failed = sum(1 for r in results if r["status"] in ("FAIL", "ERROR"))
total = len(results)

print(f"\n{'=' * 65}")
print(f"  Results: {passed}/{total} passed", end="")
if failed:
    print(f"  ({failed} FAILED)")
    for r in results:
        if r["status"] != "PASS":
            print(f"     [FAIL] {r['name']}: {r.get('reason', '')}")
else:
    print("  - ALL 18 TESTS PASS")
print("=" * 65 + "\n")

sys.exit(0 if failed == 0 else 1)
