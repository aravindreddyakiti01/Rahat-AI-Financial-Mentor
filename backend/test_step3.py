"""
test_step3.py — Step 3: LangGraph Agent Workflow Test Suite
Strictly verifies all 15 requirements specified in Section 16:
 1. Financial summary question retrieves SQLite facts.
 2. Income recording request writes to SQLite.
 3. Expense recording request writes to SQLite.
 4. Goal progress question retrieves the correct goal.
 5. Planning question retrieves relevant Hindsight memory.
 6. Retrieved memory is actually passed into the reasoning stage.
 7. Meaningful outcome is stored when appropriate.
 8. Raw transactions are NOT unnecessarily stored as Hindsight memories.
 9. Invalid tool arguments are rejected.
10. Unknown/unsupported intent is handled safely.
11. Database failure is handled.
12. Hindsight failure is handled without fabricating memory.
13. LLM failure/fallback behavior is handled.
14. Agent response is grounded in current financial facts.
15. Complete graph executes successfully for a representative planning request.
"""

import sys
import os
import tempfile
import traceback
import asyncio
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
from app.memory.hindsight import hindsight
from app.agent import tools as agent_tools
from app.agent.graph import (
    financial_mentor_graph,
    run_agent,
    parse_intent,
    load_current_financial_state,
    retrieve_relevant_hindsight,
    reason_with_llm,
    execute_action,
    generate_response,
)
from app.agent.state import FinancialMentorState
from app.agent.llm import llm_client

USER = "test_user_step3"

# Initialize DB and seed demo data for USER
init_db()
repository.seed_factual_demo_data(USER)
hindsight.seed_demo_memories(USER)

results = []

import inspect

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
print("  RAHAT - Step 3 LangGraph Agent Workflow Tests (15 Tests)")
print("=" * 65 + "\n")


# 1. Financial summary question retrieves SQLite facts
@test("01. Financial summary question retrieves SQLite facts")
async def t01():
    response = await run_agent(USER, "How much did I spend this week?")
    assert "facts" in response
    assert len(response["facts"]) > 0
    # Must mention actual expenses from SQLite
    fin_summary = repository.get_financial_summary(USER, "7d")
    expected_exp = fin_summary["total_expenses"]
    assert f"₹{expected_exp:,.0f}" in response["text"] or f"{expected_exp:.0f}" in response["text"]


# 2. Income recording request writes to SQLite
@test("02. Income recording request writes to SQLite")
async def t02():
    initial_income = repository.get_income_records(USER, 7)["total_income"]
    response = await run_agent(USER, "I earned ₹950 today from delivery shifts")
    assert "Logged income of **₹950**" in response["text"]

    # Verify SQLite actually received the new record
    updated_income = repository.get_income_records(USER, 7)["total_income"]
    assert updated_income == initial_income + 950.0


# 3. Expense recording request writes to SQLite
@test("03. Expense recording request writes to SQLite")
async def t03():
    initial_exp = repository.get_expense_records(USER, 7)["total_expenses"]
    response = await run_agent(USER, "I spent ₹280 on fuel at HP Petrol")
    assert "Logged expense of **₹280**" in response["text"]

    # Verify SQLite persisted the expense
    updated_exp = repository.get_expense_records(USER, 7)["total_expenses"]
    assert updated_exp == initial_exp + 280.0


# 4. Goal progress question retrieves the correct goal
@test("04. Goal progress question retrieves the correct goal")
async def t04():
    response = await run_agent(USER, "Am I on track for my EMI?")
    assert "facts" in response
    # Factual active goal in seed data is Bike EMI
    assert "Bike EMI" in response["text"] or any("Bike EMI" in f for f in response["facts"])
    assert "saved" in response["text"] or "progress" in response["text"]


# 5. Planning question retrieves relevant Hindsight memory
@test("05. Planning question retrieves relevant Hindsight memory")
def t05():
    state: FinancialMentorState = {
        "user_id": USER,
        "user_message": "I need ₹4,500 for my EMI in five days. What should I do?",
        "intent": "financial_planning",
    }
    result = retrieve_relevant_hindsight(state)
    assert result["memory_status"] == "available"
    assert len(result["hindsight_memories"]) > 0
    # Must retrieve previous outcome or plan regarding EMI
    mem_types = [m["type"] for m in result["hindsight_memories"]]
    assert "outcome" in mem_types or "plan" in mem_types or "pattern" in mem_types


# 6. Retrieved memory is actually passed into the reasoning stage
@test("06. Retrieved memory is actually passed into the reasoning stage")
def t06():
    memories = hindsight.search_memories(USER, query="EMI", category="emi", limit=4)
    state: FinancialMentorState = {
        "user_id": USER,
        "user_message": "I need ₹4,500 for my EMI in five days. What should I do?",
        "intent": "financial_planning",
        "current_financial_state": agent_tools.get_financial_summary(USER, "7d"),
        "hindsight_memories": memories,
        "memory_status": "available",
    }
    reasoning = reason_with_llm(state)
    assert "reasoning_plan" in reasoning
    # The reasoning plan must detect past failed plan
    assert reasoning["reasoning_plan"]["has_failed_previous_plan"] is True
    assert reasoning["action_decision"] == "create_plan"


# 7. Meaningful outcome is stored when appropriate
@test("07. Meaningful outcome is stored when appropriate")
async def t07():
    initial_memories = len(hindsight.get_timeline(USER))
    # Report a meaningful outcome
    await run_agent(USER, "I missed my target because Wednesday was raining")
    updated_memories = len(hindsight.get_timeline(USER))
    assert updated_memories == initial_memories + 1


# 8. Raw transactions are NOT unnecessarily stored as Hindsight memories
@test("08. Raw transactions are NOT stored in Hindsight memory")
async def t08():
    initial_mem_count = len(hindsight.get_timeline(USER))
    # Record normal expense
    await run_agent(USER, "I spent ₹140 on fuel")
    after_exp_count = len(hindsight.get_timeline(USER))
    assert after_exp_count == initial_mem_count, "Expense transaction was incorrectly saved to Hindsight!"

    # Record normal income
    await run_agent(USER, "I earned ₹600 from deliveries")
    after_inc_count = len(hindsight.get_timeline(USER))
    assert after_inc_count == initial_mem_count, "Income transaction was incorrectly saved to Hindsight!"


# 9. Invalid tool arguments are rejected
@test("09. Invalid tool arguments are rejected safely")
def t09():
    # Negative amount
    try:
        agent_tools.record_transaction(USER, -100.0, "income", "Delivery")
        assert False, "Should reject negative amount"
    except ValueError:
        pass

    # Invalid transaction type
    try:
        agent_tools.record_transaction(USER, 100.0, "invalid_type", "Delivery")
        assert False, "Should reject invalid type"
    except ValueError:
        pass

    # Invalid plan values
    try:
        agent_tools.create_financial_plan(USER, "g1", -100.0, 50.0, "strat", 5)
        assert False, "Should reject negative plan target"
    except ValueError:
        pass


# 10. Unknown/unsupported intent is handled safely
@test("10. Unknown/unsupported intent is handled safely")
async def t10():
    resp = await run_agent(USER, "xyzzy123 arbitrary gibberish input")
    assert "text" in resp
    assert "didn't quite understand" in resp["text"].lower() or "rahat" in resp["text"].lower()
    # Does not crash, returns valid structured response
    assert isinstance(resp["facts"], list)
    assert isinstance(resp["why_this_advice"], list)


# 11. Database failure is handled gracefully
@test("11. Database failure is handled gracefully without fabricating data")
def t11():
    # Simulate DB error in load_current_financial_state by passing invalid user or simulating exception
    state: FinancialMentorState = {
        "user_id": USER,
        "user_message": "How much did I earn?",
        "intent": "income_query",
        "financial_state_error": "Simulated database connection failure",
        "current_financial_state": {},
        "hindsight_memories": [],
    }
    response = generate_response(state)
    assert "temporarily unable" in response["final_response"].lower() or "system issue" in response["final_response"].lower()
    # Must NOT fabricate numbers
    assert len(response["structured_response"]["facts"]) == 0


# 12. Hindsight failure is handled without fabricating memory
@test("12. Hindsight failure is handled without fabricating memory")
def t12():
    state: FinancialMentorState = {
        "user_id": USER,
        "user_message": "I need ₹4,500 for my EMI in 5 days",
        "intent": "financial_planning",
        "current_financial_state": repository.get_financial_summary(USER, "7d"),
        "hindsight_memories": [],
        "memory_status": "unavailable",
        "memory_error": "Hindsight vector storage timed out",
    }
    response = generate_response(state)
    assert response["structured_response"]["memories_used_count"] == 0
    # Why this advice should note memory is offline rather than inventing past memories
    assert any("offline" in e.lower() or "temporarily" in e.lower() for e in response["structured_response"]["why_this_advice"])


# 13. LLM failure/fallback behavior is handled
@test("13. LLM failure/fallback behavior uses deterministic reasoning")
def t13():
    # Verify llm_client without keys returns None and graph falls back seamlessly
    assert llm_client.is_configured is False or llm_client.gemini_key is None
    state: FinancialMentorState = {
        "user_id": USER,
        "user_message": "I need ₹4,500 for my EMI in five days. What should I do?",
        "intent": "financial_planning",
        "current_financial_state": repository.get_financial_summary(USER, "7d"),
        "hindsight_memories": hindsight.search_memories(USER, "EMI"),
    }
    res = reason_with_llm(state)
    assert res["reasoning_plan"] is not None
    assert res["action_decision"] == "create_plan"
    assert res["llm_used"] is False


# 14. Agent response is grounded in current financial facts
@test("14. Agent response is strictly grounded in current SQLite facts")
async def t14():
    resp = await run_agent(USER, "What are my total expenses?")
    actual_exp = repository.get_expense_records(USER, 7)["total_expenses"]
    # Check that the response mentions the exact factual expense amount
    facts_str = " ".join(resp["facts"])
    assert f"₹{actual_exp:,.0f}" in facts_str or f"₹{actual_exp:,.0f}" in resp["text"]


# 15. Complete graph executes successfully for representative planning request
@test("15. Complete graph executes successfully for representative planning request")
async def t15():
    resp = await run_agent(USER, "I need ₹4,500 for my EMI in 5 days. What should I do?")
    assert "text" in resp
    assert "recommendation" in resp
    assert "why_this_advice" in resp

    # Core Ramesh Kumar case: adaptive plan incorporates weekend surge vs flat target
    assert "adaptive" in resp["text"].lower() or "surge" in resp["text"].lower() or "weekend" in resp["text"].lower()
    # Must reference the past ₹900/day plan outcome from Hindsight
    why_str = " ".join(resp["why_this_advice"])
    assert "900" in why_str or "outcome" in why_str.lower() or "sept" in why_str.lower()
    assert resp["memories_used_count"] > 0


# ─── Run all tests ────────────────────────────────────────────────────────────

for fn in [t01, t02, t03, t04, t05, t06, t07, t08, t09, t10, t11, t12, t13, t14, t15]:
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
    print("  - ALL 15 TESTS PASS")
print("=" * 65 + "\n")

sys.exit(0 if failed == 0 else 1)
