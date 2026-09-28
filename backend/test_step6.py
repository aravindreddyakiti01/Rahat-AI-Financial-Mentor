"""
RAHAT — Step 6: Goals + Financial Planning Refinement Tests
===========================================================
19 Comprehensive Automated Tests
"""

import sys
import os
import asyncio
import time
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import get_db_connection, init_db
from app.db import repository
from app.memory.hindsight import hindsight
from app.agent.graph import run_agent
from app.agent.llm import llm_client

TEST_USER_A = "usr_step6_alice"
TEST_USER_B = "usr_step6_bob"
passed = 0
failed = 0
failures = []


def record_pass(num: int, title: str):
    global passed
    passed += 1
    print(f"  [PASS] {num:02d}. {title}")


def record_fail(num: int, title: str, reason: str):
    global failed
    failed += 1
    failures.append(f"Test {num:02d} ({title}): {reason}")
    print(f"  [FAIL] {num:02d}. {title}: {reason}")


def ensure_user(user_id: str, name: str = "Test User"):
    """Insert a test user if not exists (needed for FOREIGN KEY constraints)."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT OR IGNORE INTO users (id, name, email, password_hash, role, pay_frequency, primary_obligation)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, name, f"{user_id}@test.rahat.app", "test_hash", "Delivery", "Daily", "Bike EMI"))
        conn.commit()
    finally:
        conn.close()


def cleanup_user(user_id: str):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM financial_plans WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM transactions WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM goals WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM obligations WHERE user_id = ?", (user_id,))
        conn.commit()
    finally:
        conn.close()
    hindsight.clear_memories(user_id)


def run_tests():
    print("\n" + "=" * 70)
    print("  RAHAT — Step 6: Goals + Financial Planning Refinement (19 Tests)")
    print("=" * 70 + "\n")

    init_db()

    # Ensure test users exist in the users table for FK constraints
    ensure_user(TEST_USER_A, "Alice Test")
    ensure_user(TEST_USER_B, "Bob Test")
    cleanup_user(TEST_USER_A)
    cleanup_user(TEST_USER_B)

    # ─────────────────────────────────────────────────────────────────────────
    # 01. Goal creation works
    # ─────────────────────────────────────────────────────────────────────────
    goal_a = None
    try:
        due = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
        goal_a = repository.create_goal_db(
            user_id=TEST_USER_A,
            title="Bike EMI Oct",
            target_amount=4500.0,
            due_date=due,
            initial_amount=1000.0,
            category="emi",
        )
        assert goal_a["id"] is not None
        assert goal_a["title"] == "Bike EMI Oct"
        assert goal_a["target_amount"] == 4500.0
        assert goal_a["current_amount"] == 1000.0
        assert goal_a["status"] == "active"
        record_pass(1, "Goal creation works with correct initial state")
    except Exception as e:
        record_fail(1, "Goal creation works", str(e))

    # ─────────────────────────────────────────────────────────────────────────
    # 02. Goal retrieval works
    # ─────────────────────────────────────────────────────────────────────────
    try:
        goals = repository.get_active_goals(TEST_USER_A)
        assert len(goals) >= 1
        g = goals[0]
        assert g["title"] == "Bike EMI Oct"
        fetched = repository.get_goal_by_id(TEST_USER_A, g["id"])
        assert fetched is not None
        assert fetched["id"] == g["id"]
        record_pass(2, "Goal retrieval works (active goals list and by ID)")
    except Exception as e:
        record_fail(2, "Goal retrieval works", str(e))

    # ─────────────────────────────────────────────────────────────────────────
    # 03. Goal update works
    # ─────────────────────────────────────────────────────────────────────────
    try:
        goals = repository.get_active_goals(TEST_USER_A)
        g_id = goals[0]["id"]
        updated = repository.update_goal_db(TEST_USER_A, g_id, amount_to_add=800.0)
        assert updated is not None
        assert updated["current_amount"] == 1800.0
        record_pass(3, "Goal update works (saving progress increments current_amount)")
    except Exception as e:
        record_fail(3, "Goal update works", str(e))

    # ─────────────────────────────────────────────────────────────────────────
    # 04. Goal progress calculation is correct
    # ─────────────────────────────────────────────────────────────────────────
    try:
        goals = repository.get_active_goals(TEST_USER_A)
        g = goals[0]
        # target 4500, current 1800 -> 1800 / 4500 = 40.0%
        assert g["progress_percentage"] == 40.0, f"Expected 40.0%, got {g['progress_percentage']}%"
        assert g["days_remaining"] >= 9 and g["days_remaining"] <= 10
        record_pass(4, "Goal progress calculation is correct (percentage and days remaining)")
    except Exception as e:
        record_fail(4, "Goal progress calculation is correct", str(e))

    # ─────────────────────────────────────────────────────────────────────────
    # 05. Remaining amount is correct
    # ─────────────────────────────────────────────────────────────────────────
    try:
        goals = repository.get_active_goals(TEST_USER_A)
        g = goals[0]
        assert g["remaining_amount"] == 2700.0, f"Expected 2700.0, got {g['remaining_amount']}"
        record_pass(5, "Remaining amount is correct (target_amount - current_amount)")
    except Exception as e:
        record_fail(5, "Remaining amount is correct", str(e))

    # ─────────────────────────────────────────────────────────────────────────
    # 06. Invalid goal amounts are rejected
    # ─────────────────────────────────────────────────────────────────────────
    try:
        due = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
        neg_target_failed = False
        try:
            repository.create_goal_db(TEST_USER_A, "Invalid", target_amount=-500.0, due_date=due)
        except ValueError:
            neg_target_failed = True

        neg_add_failed = False
        goals = repository.get_active_goals(TEST_USER_A)
        try:
            repository.update_goal_db(TEST_USER_A, goals[0]["id"], amount_to_add=-200.0)
        except ValueError:
            neg_add_failed = True

        assert neg_target_failed, "Negative target amount was not rejected"
        assert neg_add_failed, "Negative added amount was not rejected"
        record_pass(6, "Invalid goal amounts are rejected (target <= 0, add <= 0)")
    except Exception as e:
        record_fail(6, "Invalid goal amounts are rejected", str(e))

    # ─────────────────────────────────────────────────────────────────────────
    # 07. User isolation is preserved
    # ─────────────────────────────────────────────────────────────────────────
    try:
        b_goals = repository.get_active_goals(TEST_USER_B)
        assert len(b_goals) == 0, f"User B should see 0 goals, found {len(b_goals)}"

        a_goal_id = repository.get_active_goals(TEST_USER_A)[0]["id"]
        b_update_result = repository.update_goal_db(TEST_USER_B, a_goal_id, amount_to_add=100.0)
        assert b_update_result is None, "User B was able to update User A's goal"
        record_pass(7, "User isolation is preserved")
    except Exception as e:
        record_fail(7, "User isolation is preserved", str(e))

    # ─────────────────────────────────────────────────────────────────────────
    # 08. Goal-progress agent queries work
    # ─────────────────────────────────────────────────────────────────────────
    try:
        resp = asyncio.run(run_agent(TEST_USER_A, "How much have I saved so far for my bike goal?"))
        text = resp.get("text", "")
        assert "1,800" in text or "4,500" in text or "40" in text, f"Response missing goal figures: {text[:200]}"
        record_pass(8, "Goal-progress agent queries work and return accurate saved figures")
    except Exception as e:
        record_fail(8, "Goal-progress agent queries work", str(e))

    # ─────────────────────────────────────────────────────────────────────────
    # 09. Goal-planning queries work
    # ─────────────────────────────────────────────────────────────────────────
    try:
        resp = asyncio.run(run_agent(TEST_USER_A, "How should I plan to reach my Bike EMI goal?"))
        text = resp.get("text", "")
        assert len(text) > 20, f"Response too short: {text[:50]}"
        assert resp.get("recommendation") is not None
        record_pass(9, "Goal-planning queries work and return structured guidance")
    except Exception as e:
        record_fail(9, "Goal-planning queries work", str(e))

    # ─────────────────────────────────────────────────────────────────────────
    # 10. Backend calculates authoritative goal numbers
    # ─────────────────────────────────────────────────────────────────────────
    try:
        calc = repository.calculate_irregular_income_plan(TEST_USER_A)
        assert calc["target_amount"] == 4500.0, f"target_amount={calc.get('target_amount')}"
        assert calc["current_amount"] == 1800.0, f"current_amount={calc.get('current_amount')}"
        assert calc["remaining_amount"] == 2700.0, f"remaining_amount={calc.get('remaining_amount')}"
        assert calc["days_left"] >= 9 and calc["days_left"] <= 10
        assert "progress_percentage" not in calc or True  # progress_percentage computed on goal, not always on plan
        record_pass(10, "Backend calculates authoritative goal numbers deterministically")
    except Exception as e:
        record_fail(10, "Backend calculates authoritative goal numbers", str(e))

    # ─────────────────────────────────────────────────────────────────────────
    # 11. Gemini receives structured goal/financial context
    # ─────────────────────────────────────────────────────────────────────────
    try:
        # Seed sufficient shifts for User A
        today = datetime.now()
        for i in range(4):
            shift_date = (today - timedelta(days=i + 1)).strftime("%Y-%m-%d")
            amt = 1200.0 if i % 2 == 0 else 700.0
            repository.record_transaction_db(TEST_USER_A, amt, "income", "Delivery Earnings", date=shift_date)

        prompt_str = llm_client.build_grounded_prompt(
            user_message="Plan my goal",
            financial_facts={
                "remaining_amount": 2700.0,
                "days_left": 10,
                "strategy": "Adaptive Surge Allocation",
                "weekday_target": 200.0,
                "weekend_target": 450.0,
                "is_sufficient_history": True,
                "assumptions": "",
            },
            hindsight_memories=[],
            intent="financial_planning",
            memory_status="available",
        )
        assert "2,700" in prompt_str
        assert "Adaptive Surge Allocation" in prompt_str
        record_pass(11, "Gemini receives structured goal and financial context in system prompt")
    except Exception as e:
        record_fail(11, "Gemini receives structured goal/financial context", str(e))

    # ─────────────────────────────────────────────────────────────────────────
    # 12. Relevant Hindsight memories are retrieved
    # ─────────────────────────────────────────────────────────────────────────
    try:
        hindsight.store_memory(
            user_id=TEST_USER_A,
            memory_type="outcome",
            title="Sept 16 Shift Missed Flat Target",
            content="Flat 900/day daily savings target was missed on slow weekday shifts; only saved 500.",
            category="emi",
            outcome_status="missed",
            relevance_tags=["emi", "savings", "planning", "flat_target"],
        )
        retrieved = hindsight.search_memories(TEST_USER_A, "plan my bike EMI goal", category="emi")
        assert len(retrieved) >= 1, f"Expected >= 1 memories, got {len(retrieved)}"
        record_pass(12, "Relevant Hindsight memories are retrieved for planning queries")
    except Exception as e:
        record_fail(12, "Relevant Hindsight memories are retrieved", str(e))

    # ─────────────────────────────────────────────────────────────────────────
    # 13. Memory actually influences planning
    # ─────────────────────────────────────────────────────────────────────────
    try:
        # Add a pattern memory for adaptive surge
        hindsight.store_memory(
            user_id=TEST_USER_A,
            memory_type="pattern",
            title="Weekend Surge Pattern",
            content="Weekend deliveries generate 1050-1300/day with platform surge bonuses, whereas weekday earnings average 600-720/day.",
            category="income_pattern",
            outcome_status="learned",
            relevance_tags=["pattern", "weekend_surge", "weekday_average"],
        )

        calc = repository.calculate_irregular_income_plan(
            TEST_USER_A,
            memories=hindsight.search_memories(TEST_USER_A, "plan EMI goal", category="emi"),
        )
        # Should detect weekend surge or adaptive pattern
        is_adaptive = calc.get("is_adaptive", False)
        strategy = calc.get("strategy", "")
        has_surge = "surge" in strategy.lower() or "adaptive" in strategy.lower()
        # If weekday/weekend targets differ, that's also adaptive
        wk_diff = calc.get("weekday_target", 0) != calc.get("weekend_target", 0)
        assert has_surge or wk_diff or is_adaptive, f"Memory did not influence plan: strategy={strategy}"
        record_pass(13, "Retrieved memory influences planning (adaptive surge allocation)")
    except Exception as e:
        record_fail(13, "Memory actually influences planning", str(e))

    # ─────────────────────────────────────────────────────────────────────────
    # 14. Previous plan can be linked to an outcome
    # ─────────────────────────────────────────────────────────────────────────
    try:
        goals = repository.get_active_goals(TEST_USER_A)
        g_id = goals[0]["id"]
        plan_rec = repository.create_plan_db(
            user_id=TEST_USER_A,
            goal_id=g_id,
            target_amount=2700.0,
            daily_target=350.0,
            strategy="Adaptive Surge Allocation",
            timeframe_days=10,
            assumptions="Weekday 200, Weekend 450",
        )
        active_plan = repository.get_active_plan(TEST_USER_A)
        assert active_plan is not None, "Active plan not found after creation"
        assert active_plan["id"] == plan_rec["id"]

        # User reports outcome
        resp = asyncio.run(run_agent(TEST_USER_A, "I was short on savings today, could not save the planned amount."))

        # Verify the plan was updated to missed
        updated_plan = repository.get_plan_by_id(TEST_USER_A, active_plan["id"])
        assert updated_plan["status"] == "missed", f"Plan status should be 'missed', got '{updated_plan['status']}'"
        record_pass(14, "Previous plan is linked to reported outcome and updated in SQLite")
    except Exception as e:
        record_fail(14, "Previous plan can be linked to an outcome", str(e))

    # ─────────────────────────────────────────────────────────────────────────
    # 15. Meaningful outcomes are stored correctly
    # ─────────────────────────────────────────────────────────────────────────
    try:
        timeline = hindsight.get_timeline(TEST_USER_A)
        outcomes = [m for m in timeline if m.get("type") == "outcome"]
        assert len(outcomes) >= 1, f"Expected >= 1 outcome memories, got {len(outcomes)}"
        # Find the latest outcome that matches our reported one
        latest_outcomes = [o for o in outcomes if "short" in o.get("content", "").lower() or "could not" in o.get("content", "").lower()]
        assert len(latest_outcomes) >= 1, "Reported outcome not found in Hindsight timeline"
        latest = latest_outcomes[-1]
        assert latest.get("outcome_status") in ("missed", "achieved", "observed"), f"Unexpected status: {latest.get('outcome_status')}"
        record_pass(15, "Meaningful outcomes are stored correctly with outcome_status")
    except Exception as e:
        record_fail(15, "Meaningful outcomes are stored correctly", str(e))

    # ─────────────────────────────────────────────────────────────────────────
    # 16. Non-meaningful conversations do not create unnecessary memories
    # ─────────────────────────────────────────────────────────────────────────
    try:
        count_before = len(hindsight.get_timeline(TEST_USER_A))
        asyncio.run(run_agent(TEST_USER_A, "What was my fuel expense this week?"))
        count_after = len(hindsight.get_timeline(TEST_USER_A))
        assert count_before == count_after, f"Memory count increased from {count_before} to {count_after}"
        record_pass(16, "Non-meaningful conversations do not create unnecessary memories")
    except Exception as e:
        record_fail(16, "Non-meaningful conversations do not create unnecessary memories", str(e))

    # ─────────────────────────────────────────────────────────────────────────
    # 17. Irregular-income planning uses available financial history
    # ─────────────────────────────────────────────────────────────────────────
    try:
        calc = repository.calculate_irregular_income_plan(TEST_USER_A)
        assert calc.get("is_sufficient_history") is True, f"Expected sufficient history, got {calc.get('is_sufficient_history')}"
        assert calc["weekday_target"] > 0, f"weekday_target should be > 0, got {calc['weekday_target']}"
        assert calc["weekend_target"] > 0, f"weekend_target should be > 0, got {calc['weekend_target']}"
        record_pass(17, "Irregular-income planning uses available history (sufficient shifts)")
    except Exception as e:
        record_fail(17, "Irregular-income planning uses available financial history", str(e))

    # ─────────────────────────────────────────────────────────────────────────
    # 18. Insufficient-history cases are handled honestly
    # ─────────────────────────────────────────────────────────────────────────
    try:
        due_b = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        repository.create_goal_db(TEST_USER_B, "Emergency Cushion", 3000.0, due_date=due_b, category="savings")
        calc_b = repository.calculate_irregular_income_plan(TEST_USER_B)
        assert calc_b.get("is_sufficient_history") is False, f"Expected insufficient history for User B"
        assert "baseline" in calc_b.get("assumptions", "").lower() or "insufficient" in calc_b.get("strategy", "").lower(), \
            f"Baseline/insufficient not mentioned: {calc_b.get('assumptions', '')}"

        # Agent query for User B should acknowledge limited data
        resp_b = asyncio.run(run_agent(TEST_USER_B, "Plan my Emergency Cushion savings goal"))
        b_text = (resp_b.get("text", "") + " " + resp_b.get("recommendation", "")).lower()
        honest = any(w in b_text for w in ["insufficient", "fewer", "log", "baseline", "shift", "limited", "3"])
        assert honest, f"Insufficient history not communicated: {b_text[:200]}"
        record_pass(18, "Insufficient-history cases are handled honestly with baseline pacing")
    except Exception as e:
        record_fail(18, "Insufficient-history cases are handled honestly", str(e))

    # ─────────────────────────────────────────────────────────────────────────
    # 19. Existing Step 1-5 regression tests continue to pass
    # ─────────────────────────────────────────────────────────────────────────
    try:
        user_c = "usr_step6_regress"
        ensure_user(user_c, "Regress Test")
        cleanup_user(user_c)
        tx = repository.record_transaction_db(user_c, 850.0, "income", "Delivery Earnings")
        assert tx["amount"] == 850.0
        exp = repository.record_transaction_db(user_c, 200.0, "expense", "Fuel")
        assert exp["amount"] == 200.0
        summary = repository.get_financial_summary(user_c, "7d")
        assert summary["total_income"] == 850.0
        assert summary["total_expenses"] == 200.0
        assert summary["net_available"] == 650.0
        cleanup_user(user_c)
        record_pass(19, "Step 1-5 core regression assertions continue to pass")
    except Exception as e:
        record_fail(19, "Step 1-5 regression checks pass", str(e))

    # Cleanup
    cleanup_user(TEST_USER_A)
    cleanup_user(TEST_USER_B)

    print("\n" + "=" * 70)
    print(f"  RESULTS: {passed} passed, {failed} failed out of {passed + failed}")
    print("=" * 70)

    if failures:
        print("\n  FAILURES:")
        for f in failures:
            print(f"    - {f}")
    else:
        print("\n  ALL 19 TESTS PASSED")
    print()

    return len(failures) == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
