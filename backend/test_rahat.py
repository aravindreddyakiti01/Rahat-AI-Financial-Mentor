import asyncio
import sys

# Ensure UTF-8 output encoding on Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from app.db.database import init_db
from app.db.repository import seed_factual_demo_data, get_income_records, get_expense_records, get_active_goals
from app.memory.hindsight import hindsight
from app.agent.graph import run_agent

async def run_tests():
    print("========================================")
    print("RAHAT FOUNDATIONAL ARCHITECTURE TESTS")
    print("========================================")

    # 1. Initialize SQLite Database and Hindsight Memory
    print("\n[TEST 1] Initializing Modular SQLite & Hindsight Layers...")
    init_db()
    seed_factual_demo_data("demo_user")
    hindsight.seed_demo_memories("demo_user")
    print("[OK] SQLite factual repository initialized and seeded.")
    print("[OK] Hindsight experiential memory layer seeded with past plans & outcomes.")

    # 2. Test Factual DB Service Boundary (SQLite)
    print("\n[TEST 2] Verifying Factual Data Separation (SQLite)...")
    income = get_income_records("demo_user", days=7)
    expenses = get_expense_records("demo_user", days=7)
    goals = get_active_goals("demo_user", status="active")
    
    print(f"[OK] 7-Day Income: Rs. {income['total_income']:,.0f} across {income['count']} shifts")
    print(f"[OK] Weekend Income: Rs. {income['weekend_income']:,.0f}, Weekday Income: Rs. {income['weekday_income']:,.0f}")
    print(f"[OK] 7-Day Expenses: Rs. {expenses['total_expenses']:,.0f}")
    print(f"[OK] Active Goals: {len(goals)} (Remaining: Rs. {goals[0]['remaining_amount']:,.0f})")
    assert income['total_income'] > 0, "Income must be positive"
    assert len(goals) > 0, "Must have active goal"

    # 3. Test Experiential Memory Service Boundary (Hindsight)
    print("\n[TEST 3] Verifying Long-Term Memory Separation (Hindsight)...")
    timeline = hindsight.get_timeline("demo_user")
    print(f"[OK] Total Timeline Memories in Hindsight: {len(timeline)}")
    for m in timeline:
        print(f"  - [{m['date']}] ({m['type'].upper()}): {m['title']}")
    
    searched = hindsight.search_memories("demo_user", query="emi plan target", category="emi", limit=3)
    print(f"[OK] Retrieved Experiential Memories for 'EMI': {len(searched)}")
    assert any(m['type'] == 'outcome' for m in searched), "Must retrieve previous plan outcome"

    # 4. Test LangGraph Agent Orchestration & Outcome Loop
    print("\n[TEST 4] Testing LangGraph Agent Workflow Execution...")
    print(">> Query: 'I need Rs. 4,500 for my EMI in 5 days. What should I do?'")
    
    response = await run_agent(user_id="demo_user", user_message="I need Rs. 4,500 for my EMI in 5 days. What should I do?")
    
    print("\n--- AGENT RESPONSE ---")
    print(response["text"])
    print("\n--- GROUNDED FACTS (SQLite) ---")
    for f in response["facts"]:
        print(f"  * {f}")
    print("\n--- ADAPTIVE RECOMMENDATION ---")
    print(response["recommendation"])
    print("\n--- WHY THIS ADVICE EVIDENCE (Hindsight) ---")
    for ev in response["why_this_advice"]:
        print(f"  [Evidence] {ev}")
    
    assert response["memories_used_count"] > 0, "Must use Hindsight memories"
    assert "weekend" in response["recommendation"].lower() or "surge" in response["recommendation"].lower(), "Must use learned weekend surge pattern"
    print("\n[OK] SUCCESS: Agent used SQLite facts + Hindsight memories to produce grounded adaptive guidance.")

    print("\n========================================")
    print("ALL FOUNDATIONAL ARCHITECTURE CHECKS PASSED!")
    print("========================================")

if __name__ == "__main__":
    asyncio.run(run_tests())
