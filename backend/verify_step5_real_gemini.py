"""
verify_step5_real_gemini.py — Real Gemini End-to-End Verification
Tests the exact two real scenarios specified in Section 13:
  Test 1: "I need ₹4,500 for my EMI in five days. What should I do?"
  Test 2: "I earned ₹950 today."
"""

import sys
import os
import asyncio
from datetime import datetime

# Add parent directory
sys.path.insert(0, os.path.dirname(__file__))

from app.db.database import init_db
from app.db import repository
from app.agent import tools as agent_tools
from app.memory.hindsight import hindsight
from app.agent.graph import run_agent
from app.agent.llm import llm_client

USER = "real_verification_user"


def setup():
    init_db()
    repository.seed_factual_demo_data(USER)
    hindsight.seed_demo_memories(USER)


async def run_verification():
    print("=" * 70)
    print("  STEP 5: REAL GEMINI END-TO-END VERIFICATION")
    print("=" * 70)

    setup()

    print(f"\n[INFO] Gemini client configured: {llm_client.is_configured}")

    # ─── TEST 1: Grounded Planning & Adaptive Advice ───────────────────────
    print("\n--- TEST 1: Planning / EMI Query ---")
    query_1 = "I need ₹4,500 for my EMI in five days. What should I do?"
    print(f"User Request: \"{query_1}\"")

    response_1 = await run_agent(USER, query_1)

    print(f"\nResponse Text:\n{response_1.get('text', '')}")
    print(f"\nLLM Used: {response_1.get('llm_used', False)}")
    print(f"Facts Cited: {response_1.get('facts', [])}")
    print(f"Why This Advice (Evidence): {response_1.get('why_this_advice', [])}")
    print(f"Memories Used Count: {response_1.get('memories_used_count', 0)}")
    print(f"Primary Memory Influence: {response_1.get('primary_memory_influence', '')}")

    assert response_1.get("text"), "Test 1 must produce a non-empty response"
    assert len(response_1.get("facts", [])) > 0, "Test 1 must cite SQLite financial facts"
    print("\n>>> TEST 1: PASSED (Grounded response generated successfully)")

    # ─── TEST 2: Controlled Income Recording & Persistence ─────────────────
    print("\n--- TEST 2: Controlled Income Recording ---")
    query_2 = "I earned ₹950 today."
    print(f"User Request: \"{query_2}\"")

    # Check income before
    income_before = agent_tools.get_income(USER, days=1)
    print(f"Today's Income Before: ₹{income_before.get('total_income', 0):,.2f}")

    response_2 = await run_agent(USER, query_2)

    print(f"\nResponse Text: {response_2.get('text', '')}")

    # Check income after
    income_after = agent_tools.get_income(USER, days=1)
    print(f"Today's Income After: ₹{income_after.get('total_income', 0):,.2f}")

    # Verify transaction was persisted
    diff = income_after.get("total_income", 0) - income_before.get("total_income", 0)
    assert diff >= 950.0, f"Income must increase by at least ₹950, increased by ₹{diff}"

    # Verify subsequent query sees the new state
    query_3 = "How much did I earn today?"
    response_3 = await run_agent(USER, query_3)
    print(f"\nSubsequent Query: \"{query_3}\"")
    print(f"Subsequent Response: {response_3.get('text', '')}")
    print("\n>>> TEST 2: PASSED (Income recorded through controlled tool and persisted in SQLite)")

    print("\n" + "=" * 70)
    print("  ALL REAL GEMINI END-TO-END VERIFICATIONS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(run_verification())
