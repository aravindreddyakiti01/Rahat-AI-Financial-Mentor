"""
test_step2.py — Step 2: Financial Data & Persistence Test Suite
Strictly verifies the 15 requirements specified in Section 11:
 1. Create income
 2. Retrieve income
 3. Create expense
 4. Retrieve expense
 5. Update a supported record
 6. Delete a supported record
 7. Invalid amount
 8. Invalid/nonexistent record ID
 9. Goal creation
10. Goal progress calculation
11. Obligation retrieval
12. Financial summary calculation
13. Data persistence after reopening/reinitializing the database
14. API error handling
15. Agent financial tools retrieving the same facts from SQLite
"""

import sys
import os
import tempfile
import traceback
from datetime import datetime

# Add parent so 'app' package resolves
sys.path.insert(0, os.path.dirname(__file__))

# Setup temp database directory
tmp_dir = tempfile.mkdtemp()
os.environ["RAHAT_DATA_DIR"] = tmp_dir

from app.core import config as _cfg
_cfg.DATA_DIR = tmp_dir
_cfg.DB_PATH = os.path.join(tmp_dir, "test_rahat.db")

from app.db.database import init_db, get_db_connection
from app.db import repository
from app.agent import tools as agent_tools
from app.schemas.schemas import (
    TransactionCreateRequest,
    GoalCreateRequest,
    GoalUpdateRequest,
)
from pydantic import ValidationError
from fastapi.testclient import TestClient
from app.main import app

USER = "test_user_step2"

# Initialise schema + seed demo data for USER
init_db()
repository.seed_factual_demo_data(USER)

client = TestClient(app)

results = []

def test(name: str):
    def decorator(fn):
        def wrapper():
            try:
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
print("  RAHAT - Step 2 Financial Data & Persistence Tests (15 Tests)")
print("=" * 65 + "\n")


# 1. Create income
@test("01. Create income record in SQLite")
def t01():
    res = repository.record_transaction_db(
        user_id=USER,
        amount=1250.0,
        type_="income",
        category="Delivery Earnings",
        description="Evening dinner shift",
        note="Rain surge incentive included",
        date=datetime.now().strftime("%Y-%m-%d"),
    )
    assert res["id"].startswith("tx_")
    assert res["amount"] == 1250.0
    assert res["type"] == "income"
    assert res["note"] == "Rain surge incentive included"


# 2. Retrieve income
@test("02. Retrieve income records from SQLite")
def t02():
    income_data = repository.get_income_records(USER, days=7)
    assert income_data["total_income"] >= 1250.0
    assert income_data["count"] > 0
    assert any(t["description"] == "Evening dinner shift" for t in income_data["recent_income_entries"])


# 3. Create expense
@test("03. Create expense record with merchant in SQLite")
def t03():
    res = repository.record_transaction_db(
        user_id=USER,
        amount=310.0,
        type_="expense",
        category="Fuel",
        description="Full tank refill",
        merchant="Shell Petrol Bunk",
        note="Pre-weekend shift",
        date=datetime.now().strftime("%Y-%m-%d"),
    )
    assert res["id"].startswith("tx_")
    assert res["amount"] == 310.0
    assert res["type"] == "expense"
    assert res["merchant"] == "Shell Petrol Bunk"


# 4. Retrieve expense
@test("04. Retrieve expense records and category breakdown")
def t04():
    expense_data = repository.get_expense_records(USER, days=7)
    assert expense_data["total_expenses"] >= 310.0
    assert "Fuel" in expense_data["category_breakdown"]
    assert expense_data["category_breakdown"]["Fuel"] >= 310.0


# 5. Update a supported record
@test("05. Update supported record (Goal progress and status)")
def t05():
    # Update current active goal
    goals = repository.get_active_goals(USER, status="active")
    assert len(goals) > 0, "Expected at least one active goal"
    goal_id = goals[0]["id"]
    prev_saved = goals[0]["current_amount"]

    updated = repository.update_goal_db(
        user_id=USER,
        goal_id=goal_id,
        amount_to_add=200.0,
    )
    assert updated is not None
    assert updated["current_amount"] == prev_saved + 200.0
    assert updated["remaining_amount"] == max(0.0, updated["target_amount"] - updated["current_amount"])


# 6. Delete a supported record
@test("06. Delete supported record (Transaction deletion returns True / False)")
def t06():
    tx = repository.record_transaction_db(
        user_id=USER,
        amount=50.0,
        type_="expense",
        category="Tea",
        description="Chai break",
    )
    # First delete succeeds
    assert repository.delete_transaction_db(USER, tx["id"]) is True
    # Second delete returns False (record no longer exists)
    assert repository.delete_transaction_db(USER, tx["id"]) is False
    # Verify transaction is gone
    assert repository.get_transaction_by_id(USER, tx["id"]) is None


# 7. Invalid amount
@test("07. Business rule validation: Invalid amounts rejected (<= 0)")
def t07():
    # Negative amount
    try:
        TransactionCreateRequest(amount=-100.0, category="Fuel")
        assert False, "Should have rejected negative amount"
    except ValidationError:
        pass

    # Zero amount
    try:
        TransactionCreateRequest(amount=0.0, category="Fuel")
        assert False, "Should have rejected zero amount"
    except ValidationError:
        pass

    # Target amount in Goal <= 0
    try:
        GoalCreateRequest(title="Emergency Fund", target_amount=0.0, due_date="2026-12-31")
        assert False, "Should have rejected zero target amount"
    except ValidationError:
        pass


# 8. Invalid/nonexistent record ID
@test("08. Error handling: Nonexistent record IDs return 404 / None")
def t08():
    # Repository level
    assert repository.get_transaction_by_id(USER, "nonexistent_tx_123") is None
    assert repository.get_goal_by_id(USER, "nonexistent_goal_456") is None
    assert repository.update_goal_db(USER, "nonexistent_goal_456", amount_to_add=100.0) is None

    # API level HTTP 404
    resp = client.get(f"/finance/transactions/nonexistent_tx_123?user_id={USER}")
    assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"

    resp_del = client.delete(f"/finance/transactions/nonexistent_tx_123?user_id={USER}")
    assert resp_del.status_code == 404, f"Expected 404 on delete, got {resp_del.status_code}"

    resp_patch = client.patch(f"/goals/nonexistent_goal_456?user_id={USER}", json={"amount_to_add": 100.0})
    assert resp_patch.status_code == 404, f"Expected 404 on patch, got {resp_patch.status_code}"


# 9. Goal creation
@test("09. Goal creation with initial amount and target date")
def t09():
    goal = repository.create_goal_db(
        user_id=USER,
        title="Insurance Premium",
        target_amount=3000.0,
        due_date="2026-11-15",
        category="insurance",
        initial_amount=500.0,
    )
    assert goal["id"].startswith("goal_")
    assert goal["title"] == "Insurance Premium"
    assert goal["target_amount"] == 3000.0
    assert goal["current_amount"] == 500.0
    assert goal["status"] == "active"


# 10. Goal progress calculation
@test("10. Goal progress calculation (remaining_amount & percentage)")
def t10():
    goals = repository.get_active_goals(USER, status=None)
    ins_goal = next((g for g in goals if g["title"] == "Insurance Premium"), None)
    assert ins_goal is not None
    # 500 saved of 3000 target = 2500 remaining, 16.7% progress
    assert ins_goal["remaining_amount"] == 2500.0
    assert ins_goal["progress_percentage"] == round((500.0 / 3000.0) * 100, 1)


# 11. Obligation retrieval
@test("11. Obligation retrieval from SQLite (active obligations)")
def t11():
    obligations = repository.get_obligations(USER)
    assert len(obligations) >= 1
    bike_emi = next((o for o in obligations if "Bike EMI" in o["title"]), None)
    assert bike_emi is not None
    assert bike_emi["amount"] == 4500.0
    assert bike_emi["status"] == "active"


# 12. Financial summary calculation
@test("12. Financial summary calculation (income, expenses, net cash flow)")
def t12():
    summary_7d = repository.get_financial_summary(USER, range_type="7d")
    assert summary_7d["total_income"] > 0
    assert summary_7d["total_expenses"] > 0
    expected_net = round(summary_7d["total_income"] - summary_7d["total_expenses"], 2)
    assert summary_7d["net_cash_flow"] == expected_net
    assert summary_7d["range"] == "7d"

    # Today summary
    summary_today = repository.get_financial_summary(USER, range_type="today")
    assert summary_today["range"] == "today"
    assert summary_today["start_date"] == datetime.now().strftime("%Y-%m-%d")


# 13. Data persistence after reopening/reinitializing the database
@test("13. Persistence: Data survives SQLite connection close and reopen")
def t13():
    # Insert new record directly through repo
    tx = repository.record_transaction_db(
        user_id=USER,
        amount=777.0,
        type_="income",
        category="Incentive",
        description="Persistence check bonus",
    )
    tx_id = tx["id"]

    # Open fresh isolated SQLite connection directly to DB file
    fresh_conn = get_db_connection()
    cur = fresh_conn.cursor()
    cur.execute("SELECT amount, description FROM transactions WHERE id = ?", (tx_id,))
    row = cur.fetchone()
    fresh_conn.close()

    assert row is not None, "Transaction did not persist to SQLite file"
    assert row["amount"] == 777.0
    assert row["description"] == "Persistence check bonus"


# 14. API error handling
@test("14. FastAPI error handling (422 Unprocessable Entity for invalid payloads)")
def t14():
    # Invalid amount via API
    resp = client.post(f"/finance/income?user_id={USER}", json={"amount": -50.0, "category": "Earnings"})
    assert resp.status_code == 422, f"Expected 422 for negative amount, got {resp.status_code}"

    # Invalid range parameter
    resp_range = client.get(f"/finance/summary?user_id={USER}&range=invalid_range")
    assert resp_range.status_code == 422, f"Expected 422 for invalid range, got {resp_range.status_code}"


# 15. Agent financial tools retrieving the same facts from SQLite
@test("15. Agent boundary: LangGraph tools query factual SQLite repository")
def t15():
    # Test agent tool get_income
    tool_inc = agent_tools.get_income(USER, days=7)
    repo_inc = repository.get_income_records(USER, days=7)
    assert tool_inc["total_income"] == repo_inc["total_income"]
    assert tool_inc["count"] == repo_inc["count"]

    # Test agent tool get_goals
    tool_goals = agent_tools.get_goals(USER, status="active")
    repo_goals = repository.get_active_goals(USER, status="active")
    assert len(tool_goals) == len(repo_goals)
    assert tool_goals[0]["id"] == repo_goals[0]["id"]

    # Test agent tool get_obligations
    tool_obls = agent_tools.get_obligations(USER)
    repo_obls = repository.get_obligations(USER)
    assert len(tool_obls) == len(repo_obls)


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
