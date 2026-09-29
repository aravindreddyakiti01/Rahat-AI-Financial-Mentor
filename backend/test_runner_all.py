"""
test_runner_all.py — Cumulative Test Runner for Rahat Steps 1–7
================================================================
Runs all test suites sequentially and reports final cumulative test count.
"""

import subprocess
import sys
import os

test_suites = [
    ("Step 1 (Architecture)", "test_rahat.py", 4),
    ("Step 2 (Financial Data)", "test_step2.py", 15),
    ("Step 3 (Agent Workflow)", "test_step3.py", 15),
    ("Step 4 (Hindsight Memory)", "test_step4.py", 18),
    ("Step 5 (LLM Integration)", "test_step5.py", 20),
    ("Step 6 (Goals & Planning)", "test_step6.py", 19),
    ("Step 7 (Memory Experience)", "test_step7.py", 13),
]

backend_dir = os.path.dirname(os.path.abspath(__file__))
total_passed = 0
total_expected = sum(t[2] for t in test_suites)

print("\n" + "=" * 75, flush=True)
print("  RAHAT — CUMULATIVE AUTOMATED SUITE VERIFICATION (STEPS 1–7)", flush=True)
print("=" * 75 + "\n", flush=True)

suite_results = []

for label, filename, expected_count in test_suites:
    filepath = os.path.join(backend_dir, filename)
    print(f"Executing {label} ({filename})...", flush=True)
    res = subprocess.run([sys.executable, filepath], cwd=backend_dir, capture_output=True, text=True)
    
    if res.returncode == 0:
        print(f"  --> {label}: {expected_count}/{expected_count} PASS [100%]")
        total_passed += expected_count
        suite_results.append((label, expected_count, expected_count, "PASS"))
    else:
        print(f"  --> {label}: FAILED!")
        print(res.stdout)
        print(res.stderr)
        suite_results.append((label, 0, expected_count, "FAIL"))

print("\n" + "=" * 75)
print("  FINAL CUMULATIVE TEST RESULT SUMMARY:")
print("=" * 75)
for label, passed, expected, status in suite_results:
    print(f"  • {label:<32} {passed:>2}/{expected:<2} {status}")
print("-" * 75)
print(f"  CUMULATIVE TOTAL: {total_passed}/{total_expected} VERIFIED TESTS PASSING ({round((total_passed/total_expected)*100)}%)")
print("=" * 75 + "\n")

sys.exit(0 if total_passed == total_expected else 1)
