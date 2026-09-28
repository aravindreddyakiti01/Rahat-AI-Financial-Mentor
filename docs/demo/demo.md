# Rahat Hackathon Demo Script & Case Study

## Case Study: Ramesh Kumar (Food Delivery Partner)

- **Persona:** Ramesh Kumar, Swiggy & Zomato delivery driver.
- **Income Rhythm:** Irregular daily earnings (₹430 on slow weekdays up to ₹1,300 on peak weekend shifts).
- **Obligation:** Hero Splendor bike loan EMI of ₹4,500 due on the 10th of every month.
- **Active Goal:** ₹4,500 target, ₹1,800 saved so far (₹2,700 remaining).

## Step-by-Step 60-Second Demo Walkthrough

1. **Step 1: Ask for EMI Planning**
   - **Query:** *"I need ₹4,500 for my EMI in 5 days. What should I do?"*
   - **Agent Action:** Retrieves SQLite facts (₹1,800 saved, ₹2,700 remaining, 5 days left) + Hindsight memory (Sept 16 outcome showing flat ₹900/day target failed on slow weekdays).
   - **Agent Output:** Recommends **Adaptive Surge Allocation**: Mon–Fri ₹270/day, Sat–Sun ₹810 peak surge allocation.

2. **Step 2: Log Shift Earnings**
   - **Query:** *"I earned ₹950 today from delivery shifts."*
   - **Agent Action:** Executes `record_transaction` controlled tool, updating SQLite income ledger to ₹950.

3. **Step 3: Update Goal Progress**
   - **Query:** *"Add ₹500 to my bike EMI goal."*
   - **Agent Action:** Executes `update_goal` tool, updating current saved amount from ₹1,800 to ₹2,300 (51.1% complete).

4. **Step 4: Report Shift Outcome**
   - **Query:** *"I fell short on savings today, could not save the planned amount."*
   - **Agent Action:** Stores meaningful `OUTCOME` memory in Hindsight linked to the active plan (`related_plan_id`), updating plan status to `'missed'` without polluting raw transactions.
