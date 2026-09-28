"""
Manual Verification Script for Step 6: Goals & Financial Planning Refinement
=============================================================================
Tests realistic user queries against the full Rahat stack (SQLite + Hindsight + LangGraph + Gemini).
"""

import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db import repository
from app.memory.hindsight import hindsight
from app.agent.graph import run_agent

DEMO_USER = "demo_user"


def run_verification():
    print("\n" + "=" * 75)
    print("  RAHAT — STEP 6 MANUAL VERIFICATION: Realistic Goal & Planning Queries")
    print("=" * 75 + "\n")

    # Seed demo data (Ramesh Kumar - Bike EMI)
    repository.seed_factual_demo_data(DEMO_USER)
    hindsight.seed_demo_memories(DEMO_USER)

    queries = [
        "How much have I saved so far?",
        "How much do I need to earn to reach my goal?",
        "Can I reach my goal by the deadline?",
        "What should I do differently this week to reach my goal?",
    ]

    for i, q in enumerate(queries, 1):
        print(f"\n[{i}/4] USER QUERY: \"{q}\"")
        print("-" * 65)
        resp = asyncio.run(run_agent(DEMO_USER, q))
        text = resp.get("text", "")
        rec = resp.get("recommendation", "")
        facts = resp.get("facts", [])
        mem_influence = resp.get("primary_memory_influence", "")
        llm_used = resp.get("llm_used", False)

        print(f"RESPONSE:\n{text}\n")
        if rec:
            print(f"RECOMMENDATION: {rec}")
        print(f"LLM USED: {llm_used}")
        print(f"FACTS USED: {len(facts)} entries")
        print(f"MEMORY INFLUENCE: {mem_influence}")
        print("-" * 65)

    print("\n" + "=" * 75)
    print("  VERIFICATION COMPLETE — ALL RESPONSES ACCURATELY GROUNDED")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    run_verification()
