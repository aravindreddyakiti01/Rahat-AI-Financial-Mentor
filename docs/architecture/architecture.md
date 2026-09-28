# Rahat System Architecture & Data Model

## System Overview

Rahat is an outcome-aware financial mentor built specifically for gig workers with irregular daily income and fixed recurring obligations.

```
                    USER
                      │
                      ▼
             FLUTTER MOBILE APP
                      │
                      ▼
               FASTAPI GATEWAY
                      │
                      ▼
           FINANCIAL MENTOR AGENT
                  LANGGRAPH
                      │
          ┌───────────┼───────────┐
          │           │           │
          ▼           ▼           ▼
       SQLITE       REDIS      HINDSIGHT
       Current      Temporary   Long-term
       Facts        State       Experience
          │           │           │
          └───────────┼───────────┘
                      │
                      ▼
                 GEMINI LLM
                      │
                      ▼
              CONTROLLED TOOL
                      │
                      ▼
               REAL OUTCOME
                      │
                      ▼
                 HINDSIGHT
                      │
                      ▼
             BETTER NEXT DECISION
```

## Storage Responsibilities

1. **SQLite Database (`backend/app/db/`):** Stores structured factual application data. Answers *"What is currently true?"*
   - Transactions (income, expenses, category, merchant, date, source)
   - Goals (title, target amount, current amount, due date, status)
   - Fixed Obligations (title, amount, frequency, due day, status)
   - Financial Plans (goal_id, target_amount, daily_target, strategy, assumptions, status)

2. **Redis Cache (`backend/app/core/cache.py`):** Temporary session state and rate limiting with FakeRedis fallback. Answers *"What does the system temporarily need right now?"*

3. **Hindsight Long-Term Memory (`backend/app/memory/hindsight.py`):** Stores outcome-aware experiential memories. Answers *"What did Rahat learn from previous experience?"*
   - `PROFILE_FACT`: Stable user context (e.g. Hero Splendor EMI obligation)
   - `PLAN`: Formulated financial plans
   - `OUTCOME`: Real-world results and friction after a plan or action (linked to plans via `related_plan_id`)
   - `PATTERN`: Derived behavioral or earning rhythms (e.g. weekend surge vs weekday average)
   - `PREFERENCE`: Explicit user planning preferences

## Controlled Tool Execution

The LLM **never** directly mutates the database. All database writes pass through validated backend tools:
- `record_transaction`: Validates positive amounts, categorizes, and records in SQLite.
- `create_goal`: Validates positive target amounts, sets status to `'active'`, and saves in SQLite.
- `update_goal`: Incrementally updates saved progress or status with bounds checking.
- `create_financial_plan`: Saves plan in SQLite and records `PLAN` memory in Hindsight.
