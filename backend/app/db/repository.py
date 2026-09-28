import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from app.db.database import get_db_connection


# ─────────────────────────────────────────────────────────────────────────────
# INCOME
# ─────────────────────────────────────────────────────────────────────────────

def get_income_records(user_id: str, days: int = 7) -> Dict[str, Any]:
    """
    Factual income records from SQLite.
    Supports arbitrary day windows including 1 (today) and 30 (monthly).
    Never fabricates financial data.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cutoff_date = (datetime.now() - timedelta(days=days - 1)).strftime("%Y-%m-%d")

    cursor.execute("""
    SELECT id, amount, category, description, note, date, source FROM transactions
    WHERE user_id = ? AND type = 'income' AND date >= ?
    ORDER BY date DESC
    """, (user_id, cutoff_date))

    rows = cursor.fetchall()
    conn.close()

    transactions = [dict(r) for r in rows]
    total_income = sum(t["amount"] for t in transactions)
    avg_daily_income = total_income / max(days, 1)

    weekday_income = 0.0
    weekend_income = 0.0
    weekday_count = 0
    weekend_count = 0
    for t in transactions:
        try:
            dt = datetime.strptime(t["date"], "%Y-%m-%d")
            if dt.weekday() in [5, 6]:
                weekend_income += t["amount"]
                weekend_count += 1
            else:
                weekday_income += t["amount"]
                weekday_count += 1
        except Exception:
            pass

    return {
        "user_id": user_id,
        "timeframe_days": days,
        "total_income": round(total_income, 2),
        "average_daily_income": round(avg_daily_income, 2),
        "weekend_income": round(weekend_income, 2),
        "weekday_income": round(weekday_income, 2),
        "weekday_count": weekday_count,
        "weekend_count": weekend_count,
        "count": len(transactions),
        "recent_income_entries": transactions[:5],
    }


# ─────────────────────────────────────────────────────────────────────────────
# EXPENSES
# ─────────────────────────────────────────────────────────────────────────────

def get_expense_records(user_id: str, days: int = 7) -> Dict[str, Any]:
    """
    Factual expense records and category breakdown from SQLite.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cutoff_date = (datetime.now() - timedelta(days=days - 1)).strftime("%Y-%m-%d")

    cursor.execute("""
    SELECT id, amount, category, description, note, merchant, date, source FROM transactions
    WHERE user_id = ? AND type = 'expense' AND date >= ?
    ORDER BY date DESC
    """, (user_id, cutoff_date))

    rows = cursor.fetchall()
    conn.close()

    transactions = [dict(r) for r in rows]
    total_expenses = sum(t["amount"] for t in transactions)

    categories: Dict[str, float] = {}
    for t in transactions:
        cat = t["category"]
        categories[cat] = round(categories.get(cat, 0.0) + t["amount"], 2)

    return {
        "user_id": user_id,
        "timeframe_days": days,
        "total_expenses": round(total_expenses, 2),
        "category_breakdown": categories,
        "count": len(transactions),
        "recent_expense_entries": transactions[:5],
    }


# ─────────────────────────────────────────────────────────────────────────────
# FINANCIAL SUMMARY (today / monthly / arbitrary window)
# ─────────────────────────────────────────────────────────────────────────────

def get_financial_summary(user_id: str, range_type: str = "7d") -> Dict[str, Any]:
    """
    Returns combined income + expense summary for a named range.
    range_type: 'today' | '7d' | 'month'
    """
    today = datetime.now().strftime("%Y-%m-%d")
    if range_type == "today":
        days = 1
        start_date = today
    elif range_type == "month":
        # Current calendar month from the 1st
        first_of_month = datetime.now().replace(day=1).strftime("%Y-%m-%d")
        days_elapsed = datetime.now().day
        days = days_elapsed
        start_date = first_of_month
    else:  # default '7d'
        days = 7
        start_date = (datetime.now() - timedelta(days=6)).strftime("%Y-%m-%d")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT type, SUM(amount) as total FROM transactions
    WHERE user_id = ? AND date >= ?
    GROUP BY type
    """, (user_id, start_date))
    rows = {r["type"]: r["total"] for r in cursor.fetchall()}
    conn.close()

    total_income = round(rows.get("income", 0.0), 2)
    total_expenses = round(rows.get("expense", 0.0), 2)
    net_cash_flow = round(total_income - total_expenses, 2)

    goals = get_active_goals(user_id, status="active")
    obligations = get_obligations(user_id)
    active_goal = goals[0] if goals else None

    return {
        "range": range_type,
        "start_date": start_date,
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_cash_flow": net_cash_flow,
        "net_available": max(0.0, net_cash_flow),
        "active_goal": active_goal,
        "goal_progress_percent": active_goal["progress_percentage"] if active_goal else 0.0,
        "daily_avg_income": round(total_income / max(days, 1), 2),
        "obligations": obligations,
    }


# ─────────────────────────────────────────────────────────────────────────────
# GOALS
# ─────────────────────────────────────────────────────────────────────────────

def get_active_goals(user_id: str, status: Optional[str] = "active") -> List[Dict[str, Any]]:
    """Factual goal records with computed derived fields."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if status:
        cursor.execute(
            "SELECT * FROM goals WHERE user_id = ? AND status = ? ORDER BY due_date ASC",
            (user_id, status),
        )
    else:
        cursor.execute(
            "SELECT * FROM goals WHERE user_id = ? ORDER BY due_date ASC",
            (user_id,),
        )
    rows = cursor.fetchall()
    conn.close()

    goals = []
    today_date = datetime.now().date()
    for r in rows:
        g = dict(r)
        current = max(0.0, float(g.get("current_amount") or 0.0))
        target = float(g.get("target_amount") or 0.0)
        remaining = max(0.0, target - current)
        try:
            due_dt = datetime.strptime(g["due_date"], "%Y-%m-%d").date()
            days_left = max(0, (due_dt - today_date).days)
        except Exception:
            days_left = 0

        g["current_amount"] = round(current, 2)
        g["target_amount"] = round(target, 2)
        g["remaining_amount"] = round(remaining, 2)
        g["days_remaining"] = days_left
        g["progress_percentage"] = round(
            min(100.0, (current / max(target, 0.01)) * 100), 1
        )
        g["updated_at"] = g.get("updated_at") or g.get("created_at")
        goals.append(g)
    return goals


def get_goal_by_id(user_id: str, goal_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM goals WHERE id = ? AND user_id = ?", (goal_id, user_id))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    g = dict(row)
    current = max(0.0, float(g.get("current_amount") or 0.0))
    target = float(g.get("target_amount") or 0.0)
    remaining = max(0.0, target - current)
    today_date = datetime.now().date()
    try:
        due_dt = datetime.strptime(g["due_date"], "%Y-%m-%d").date()
        days_left = max(0, (due_dt - today_date).days)
    except Exception:
        days_left = 0

    g["current_amount"] = round(current, 2)
    g["target_amount"] = round(target, 2)
    g["remaining_amount"] = round(remaining, 2)
    g["days_remaining"] = days_left
    g["progress_percentage"] = round(
        min(100.0, (current / max(target, 0.01)) * 100), 1
    )
    g["updated_at"] = g.get("updated_at") or g.get("created_at")
    return g


def create_goal_db(
    user_id: str,
    title: str,
    target_amount: float,
    due_date: Optional[str] = None,
    target_date: Optional[str] = None,
    category: str = "emi",
    initial_amount: float = 0.0,
) -> Dict[str, Any]:
    due_date = due_date or target_date
    if not due_date:
        raise ValueError("Due date or target date must be provided in YYYY-MM-DD format.")
    if not isinstance(target_amount, (int, float)) or target_amount <= 0:
        raise ValueError(f"Invalid target amount: {target_amount}. Target must be greater than zero.")
    if initial_amount < 0:
        raise ValueError(f"Invalid initial amount: {initial_amount}. Initial amount must be >= 0.")
    if not title or not title.strip():
        raise ValueError("Goal title must not be empty.")

    try:
        datetime.strptime(due_date, "%Y-%m-%d")
    except (ValueError, TypeError):
        raise ValueError(f"Invalid due date: '{due_date}'. Expected format YYYY-MM-DD.")

    conn = get_db_connection()
    cursor = conn.cursor()
    goal_id = f"goal_{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.urandom(2).hex()}"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    INSERT INTO goals (id, user_id, title, target_amount, current_amount, due_date, category, status, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?)
    """, (goal_id, user_id, title.strip(), round(target_amount, 2), round(initial_amount, 2), due_date, category, now_str, now_str))
    conn.commit()
    conn.close()
    return get_goal_by_id(user_id, goal_id)


def update_goal_db(
    user_id: str,
    goal_id: str,
    amount_to_add: Optional[float] = None,
    added_amount: Optional[float] = None,
    new_current_amount: Optional[float] = None,
    status: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Updates goal current_amount or status with strict validation and user isolation.
    - amount_to_add / added_amount: incremental deposit (must be > 0)
    - new_current_amount: absolute override (must be >= 0)
    - status: 'active' | 'achieved' | 'missed'
    Returns None if goal does not exist or does not belong to user_id.
    """
    if amount_to_add is None and added_amount is not None:
        amount_to_add = added_amount
    goal = get_goal_by_id(user_id, goal_id)
    if not goal:
        return None

    if amount_to_add is not None and amount_to_add <= 0:
        raise ValueError(f"Invalid amount to add: {amount_to_add}. Must be greater than zero.")
    if new_current_amount is not None and new_current_amount < 0:
        raise ValueError(f"Invalid current amount: {new_current_amount}. Must be non-negative.")

    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    new_amount = goal["current_amount"]
    if amount_to_add is not None:
        new_amount = min(goal["current_amount"] + amount_to_add, goal["target_amount"])
        cursor.execute(
            "UPDATE goals SET current_amount = ?, updated_at = ? WHERE id = ? AND user_id = ?",
            (round(new_amount, 2), now_str, goal_id, user_id),
        )

    if new_current_amount is not None:
        new_amount = min(new_current_amount, goal["target_amount"])
        cursor.execute(
            "UPDATE goals SET current_amount = ?, updated_at = ? WHERE id = ? AND user_id = ?",
            (round(new_amount, 2), now_str, goal_id, user_id),
        )

    # Auto-achieved if savings reach target and status is not explicitly set
    if status is None and new_amount >= goal["target_amount"] and goal["status"] == "active":
        status = "achieved"

    if status is not None:
        cursor.execute(
            "UPDATE goals SET status = ?, updated_at = ? WHERE id = ? AND user_id = ?",
            (status, now_str, goal_id, user_id),
        )

    conn.commit()
    conn.close()
    return get_goal_by_id(user_id, goal_id)


# ─────────────────────────────────────────────────────────────────────────────
# OBLIGATIONS
# ─────────────────────────────────────────────────────────────────────────────

def get_obligations(user_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    if status:
        cursor.execute(
            "SELECT * FROM obligations WHERE user_id = ? AND status = ? ORDER BY due_day ASC",
            (user_id, status),
        )
    else:
        cursor.execute(
            "SELECT * FROM obligations WHERE user_id = ? ORDER BY due_day ASC",
            (user_id,),
        )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_obligation_by_id(user_id: str, obligation_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM obligations WHERE id = ? AND user_id = ?",
        (obligation_id, user_id),
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def create_obligation_db(
    user_id: str,
    title: str,
    amount: float,
    frequency: str = "monthly",
    due_day: int = 10,
    next_due_date: Optional[str] = None,
) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    obl_id = f"obl_{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.urandom(2).hex()}"
    cursor.execute("""
    INSERT INTO obligations (id, user_id, title, amount, frequency, due_day, next_due_date, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, 'active')
    """, (obl_id, user_id, title, amount, frequency, due_day, next_due_date))
    conn.commit()
    conn.close()
    return get_obligation_by_id(user_id, obl_id)


def update_obligation_status(user_id: str, obligation_id: str, status: str) -> Optional[Dict[str, Any]]:
    """Update obligation status ('active' | 'paid' | 'overdue'). Returns None if not found."""
    obl = get_obligation_by_id(user_id, obligation_id)
    if not obl:
        return None
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE obligations SET status = ? WHERE id = ? AND user_id = ?",
        (status, obligation_id, user_id),
    )
    conn.commit()
    conn.close()
    return get_obligation_by_id(user_id, obligation_id)


# ─────────────────────────────────────────────────────────────────────────────
# TRANSACTIONS
# ─────────────────────────────────────────────────────────────────────────────

def get_recent_transactions(user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM transactions WHERE user_id = ? ORDER BY date DESC, created_at DESC LIMIT ?",
        (user_id, limit),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_transaction_by_id(user_id: str, tx_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions WHERE id = ? AND user_id = ?", (tx_id, user_id))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def record_transaction_db(
    user_id: str,
    amount: float,
    type_: str,
    category: str,
    description: str = "",
    source: str = "manual",
    date: Optional[str] = None,
    note: str = "",
    merchant: str = "",
) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    tx_id = f"tx_{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.urandom(2).hex()}"
    tx_date = date or datetime.now().strftime("%Y-%m-%d")

    cursor.execute("""
    INSERT INTO transactions (id, user_id, amount, type, category, description, note, merchant, date, source)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (tx_id, user_id, round(amount, 2), type_, category, description, note, merchant, tx_date, source))

    conn.commit()
    conn.close()

    return {
        "id": tx_id,
        "user_id": user_id,
        "amount": round(amount, 2),
        "type": type_,
        "category": category,
        "description": description,
        "note": note,
        "merchant": merchant,
        "date": tx_date,
        "source": source,
    }


def delete_transaction_db(user_id: str, tx_id: str) -> bool:
    """Returns True if a row was deleted, False if transaction not found."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE id = ? AND user_id = ?", (tx_id, user_id))
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success


# ─────────────────────────────────────────────────────────────────────────────
# FINANCIAL PLANS
# ─────────────────────────────────────────────────────────────────────────────

def create_plan_db(
    user_id: str,
    goal_id: str,
    target_amount: float,
    daily_target: float,
    strategy: str,
    timeframe_days: int,
    assumptions: str = "",
) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    plan_id = f"plan_{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.urandom(2).hex()}"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    INSERT INTO financial_plans (id, user_id, goal_id, target_amount, daily_target, strategy, timeframe_days, status, assumptions, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?)
    """, (plan_id, user_id, goal_id, round(target_amount, 2), round(daily_target, 2), strategy, timeframe_days, assumptions, now_str, now_str))

    conn.commit()
    conn.close()
    return {
        "id": plan_id,
        "plan_id": plan_id,
        "user_id": user_id,
        "goal_id": goal_id,
        "target_amount": target_amount,
        "daily_target": daily_target,
        "strategy": strategy,
        "timeframe_days": timeframe_days,
        "status": "active",
        "assumptions": assumptions,
        "created_at": now_str,
        "updated_at": now_str,
    }


def get_active_plan(user_id: str, goal_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieve the most recent active financial plan for the user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if goal_id:
        cursor.execute(
            "SELECT * FROM financial_plans WHERE user_id = ? AND goal_id = ? AND status = 'active' ORDER BY created_at DESC LIMIT 1",
            (user_id, goal_id),
        )
    else:
        cursor.execute(
            "SELECT * FROM financial_plans WHERE user_id = ? AND status = 'active' ORDER BY created_at DESC LIMIT 1",
            (user_id,),
        )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_plan_status(user_id: str, plan_id: str, status: str) -> Optional[Dict[str, Any]]:
    """Updates plan status ('active' | 'succeeded' | 'failed' | 'revised') with user isolation."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "UPDATE financial_plans SET status = ?, updated_at = ? WHERE id = ? AND user_id = ?",
        (status, now_str, plan_id, user_id),
    )
    conn.commit()
    cursor.execute("SELECT * FROM financial_plans WHERE id = ? AND user_id = ?", (plan_id, user_id))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_plan_by_id(user_id: str, plan_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a specific plan by ID with user isolation."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM financial_plans WHERE id = ? AND user_id = ?",
        (plan_id, user_id),
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def calculate_irregular_income_plan(
    user_id: str,
    goal: Optional[Dict[str, Any]] = None,
    memories: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Computes deterministic irregular-income financial plan based on actual SQLite shift history
    and Hindsight experiential memories.
    - Inspects recent shift history (last 7 days).
    - Checks history sufficiency (>= 3 shifts logged).
    - If sufficient: computes Adaptive Surge Allocation (lighter weekday saving + higher weekend surge).
    - If insufficient: honestly states data is building and provides transparent baseline pacing.
    - Honors past memories: if a past outcome failed flat pacing, firmly applies adaptive strategy.
    """
    if goal is None:
        goals = get_active_goals(user_id, status="active")
        goal = goals[0] if goals else None

    if not goal:
        return {
            "has_goal": False,
            "message": "No active savings goal found.",
            "is_sufficient_history": False,
            "target_amount": 0.0,
            "current_amount": 0.0,
            "remaining_amount": 0.0,
            "days_left": 0,
            "progress_percentage": 0.0,
            "strategy": "No Active Goal",
            "daily_target": 0.0,
            "weekday_target": 0.0,
            "weekend_target": 0.0,
            "assumptions": "No active goal set",
            "is_adaptive": False,
        }

    target_amount = float(goal.get("target_amount") or 0.0)
    current_amount = float(goal.get("current_amount") or 0.0)
    remaining_amount = max(0.0, float(goal.get("remaining_amount", target_amount - current_amount)))
    days_left = max(1, int(goal.get("days_remaining", 1)))
    deadline = goal.get("due_date", "")

    # Pull factual financial metrics from SQLite
    income_data = get_income_records(user_id, days=7)
    expense_data = get_expense_records(user_id, days=7)

    shift_count = income_data.get("count", 0)
    total_income_7d = income_data.get("total_income", 0.0)
    weekday_income = income_data.get("weekday_income", 0.0)
    weekend_income = income_data.get("weekend_income", 0.0)
    weekday_shifts = income_data.get("weekday_count", 0)
    weekend_shifts = income_data.get("weekend_count", 0)
    total_expenses_7d = expense_data.get("total_expenses", 0.0)
    fuel_expenses = expense_data.get("category_breakdown", {}).get("Fuel", 0.0)

    avg_weekday_shift = round(weekday_income / max(weekday_shifts, 1), 2) if weekday_shifts > 0 else 0.0
    avg_weekend_shift = round(weekend_income / max(weekend_shifts, 1), 2) if weekend_shifts > 0 else 0.0

    # Calculate remaining weekdays vs weekend days until deadline
    today = datetime.now().date()
    weekdays_remaining = 0
    weekends_remaining = 0
    for d in range(days_left):
        day_date = today + timedelta(days=d)
        if day_date.weekday() < 5:  # Mon-Fri
            weekdays_remaining += 1
        else:  # Sat-Sun
            weekends_remaining += 1

    # Check Hindsight memory for past failed strategies or pattern preferences
    mem_list = memories or []
    has_failed_flat_plan = any(
        m.get("type") == "outcome" and m.get("outcome_status") == "failed"
        for m in mem_list
    )
    has_weekend_surge_pattern = any(
        "weekend" in m.get("content", "").lower() or m.get("type") == "pattern"
        for m in mem_list
    )

    # Check data sufficiency: gig workers need at least 3 logged shifts for pattern discovery
    is_sufficient_history = shift_count >= 3 and total_income_7d > 0

    if not is_sufficient_history:
        # Honest Insufficient-History Case
        baseline_daily = round(remaining_amount / max(days_left, 1), 2)
        strategy = "Baseline Pacing (Insufficient History)"
        assumptions = (
            f"Only {shift_count} delivery shift(s) logged so far. "
            f"Transparent pace of ₹{baseline_daily:,.0f}/day calculated across {days_left} days. "
            f"Log at least 3–5 shifts so Rahat can adapt to your weekday vs. weekend surge rhythms."
        )
        return {
            "has_goal": True,
            "goal_id": goal["id"],
            "goal_title": goal["title"],
            "target_amount": target_amount,
            "current_amount": current_amount,
            "remaining_amount": remaining_amount,
            "days_left": days_left,
            "deadline": deadline,
            "is_sufficient_history": False,
            "is_adaptive": False,
            "strategy": strategy,
            "daily_target": baseline_daily,
            "weekday_target": baseline_daily,
            "weekend_target": baseline_daily,
            "weekdays_remaining": weekdays_remaining,
            "weekends_remaining": weekends_remaining,
            "shift_count": shift_count,
            "assumptions": assumptions,
            "memory_influence": "No historical patterns used (history is currently building).",
            "supporting_facts": [
                f"Active Goal: {goal['title']} (₹{remaining_amount:,.0f} remaining, {days_left} days left)",
                f"Logged shifts: {shift_count} (insufficient for pattern modeling; min 3 required)",
            ],
        }

    # Sufficient History: Irregular-Income Adaptive Planning
    flat_pace = round(remaining_amount / max(days_left, 1), 2)

    # If weekend surge exists and weekend days remain:
    if weekends_remaining > 0 and (weekend_income > 0 or has_weekend_surge_pattern or has_failed_flat_plan):
        strategy = "Adaptive Surge Allocation"
        if weekdays_remaining > 0:
            # Reserve lighter allocation for weekdays (~35-45% of total goal), heavy allocation on weekends
            weekday_share = remaining_amount * 0.40
            weekend_share = remaining_amount * 0.60
            weekday_target = max(100.0, round(weekday_share / weekdays_remaining, -1))
            weekend_target = max(150.0, round(weekend_share / max(weekends_remaining, 1), -1))
        else:
            weekday_target = 0.0
            weekend_target = round(remaining_amount / max(weekends_remaining, 1), -1)

        is_adaptive = True
        memory_influence = (
            "Previous Sept 16 failed flat target and weekend surge pattern in Hindsight informed this adaptive split."
            if (has_failed_flat_plan or has_weekend_surge_pattern)
            else "Shift-to-shift weekday vs. weekend earning rhythm from SQLite records informed this adaptive split."
        )
        assumptions = (
            f"Grounded in {shift_count} logged shifts (avg weekday: ₹{avg_weekday_shift:,.0f}, "
            f"avg weekend surge: ₹{avg_weekend_shift:,.0f}). Weekdays reserve lighter ₹{weekday_target:,.0f}/day "
            f"to prevent cashflow stress; weekend peak shifts allocate ₹{weekend_target:,.0f}/day."
        )
    else:
        strategy = "Balanced Daily Allocation"
        weekday_target = flat_pace
        weekend_target = flat_pace
        is_adaptive = False
        memory_influence = "Grounded in standard consistent daily pacing."
        assumptions = f"Balanced pacing of ₹{flat_pace:,.0f}/day across {days_left} remaining days."

    return {
        "has_goal": True,
        "goal_id": goal["id"],
        "goal_title": goal["title"],
        "target_amount": target_amount,
        "current_amount": current_amount,
        "remaining_amount": remaining_amount,
        "days_left": days_left,
        "deadline": deadline,
        "is_sufficient_history": True,
        "is_adaptive": is_adaptive,
        "strategy": strategy,
        "daily_target": flat_pace,
        "weekday_target": weekday_target,
        "weekend_target": weekend_target,
        "weekdays_remaining": weekdays_remaining,
        "weekends_remaining": weekends_remaining,
        "shift_count": shift_count,
        "assumptions": assumptions,
        "memory_influence": memory_influence,
        "supporting_facts": [
            f"Active Goal: {goal['title']} — ₹{remaining_amount:,.0f} remaining ({days_left} days left)",
            f"7-Day Income: ₹{total_income_7d:,.0f} across {shift_count} shifts (weekday avg: ₹{avg_weekday_shift:,.0f}, weekend avg: ₹{avg_weekend_shift:,.0f})",
            f"7-Day Operating Expenses: ₹{total_expenses_7d:,.0f} (Fuel: ₹{fuel_expenses:,.0f})",
        ],
    }


# ─────────────────────────────────────────────────────────────────────────────
# DEMO SEED
# ─────────────────────────────────────────────────────────────────────────────

def seed_factual_demo_data(user_id: str = "demo_user"):
    """
    Seeds factual SQLite database with deterministic case-study data.
    User: Ramesh Kumar — Delivery Partner (Zomato/Swiggy)
    Obligation: Hero Splendor Bike EMI ₹4,500/month, due 10th
    Active Goal: Upcoming Bike EMI Target (₹4,500 target, ₹1,800 saved)
    Past Goal: September Bike EMI (missed — ₹3,900/₹4,500)
    7 days of realistic variable shift earnings & fuel expenses
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM transactions WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM financial_plans WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM goals WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM obligations WHERE user_id = ?", (user_id,))

    # Upsert user to preserve foreign key constraints from dependent tables (e.g. hindsight_memories)
    cursor.execute("""
    INSERT INTO users (id, name, email, password_hash, role, pay_frequency, primary_obligation)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(id) DO UPDATE SET
        name = excluded.name,
        email = excluded.email,
        password_hash = excluded.password_hash,
        role = excluded.role,
        pay_frequency = excluded.pay_frequency,
        primary_obligation = excluded.primary_obligation
    """, (
        user_id,
        "Ramesh Kumar",
        f"ramesh.{user_id}@rahat.app",
        "demo_secure_hash",
        "Delivery Partner (Zomato/Swiggy)",
        "Daily",
        "Bike EMI (₹4,500)",
    ))

    # Fixed Obligation
    cursor.execute("""
    INSERT OR REPLACE INTO obligations (id, user_id, title, amount, frequency, due_day, next_due_date, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (f"obl_1_{user_id}", user_id, "Hero Splendor Bike EMI", 4500.0, "monthly", 10, "2026-10-10", "active"))

    # Active Goal: Upcoming Bike EMI
    cursor.execute("""
    INSERT OR REPLACE INTO goals (id, user_id, title, target_amount, current_amount, due_date, category, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (f"goal_current_emi_{user_id}", user_id, "Upcoming Bike EMI Target", 4500.0, 1800.0, "2026-10-05", "emi", "active"))

    # Past Goal: September EMI (missed)
    cursor.execute("""
    INSERT OR REPLACE INTO goals (id, user_id, title, target_amount, current_amount, due_date, category, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (f"goal_sept_emi_{user_id}", user_id, "September Bike EMI", 4500.0, 3900.0, "2026-09-16", "emi", "missed"))

    # Past Plan (Sept 12)
    cursor.execute("""
    INSERT OR REPLACE INTO financial_plans (id, user_id, goal_id, target_amount, daily_target, strategy, timeframe_days, status, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        f"plan_sept_12_{user_id}",
        user_id,
        f"goal_sept_emi_{user_id}",
        4500.0,
        900.0,
        "Flat ₹900/day saving across 5 weekdays",
        5,
        "failed",
        "2026-09-12 09:00:00",
    ))

    # Seed Transactions (7 days of realistic gig worker data)
    today = datetime.now()
    transactions = [
        # (id, amount, type, category, description, note, merchant, date_offset_days)
        ("tx_s1", 1300.0, "income", "Delivery Earnings",  "Sunday peak hours delivery (14 orders)",     "", "",                  1),
        ("tx_s2",  240.0, "expense", "Fuel",              "Fuel refill before Sunday peak shift",       "", "HP Petrol Pump",    1),
        ("tx_s3", 1050.0, "income", "Delivery Earnings",  "Saturday weekend surge deliveries",          "", "",                  2),
        ("tx_s4",  180.0, "expense", "Fuel",              "Fuel top-up after Saturday shift",           "", "IndianOil Petrol",  2),
        ("tx_s5",  650.0, "income", "Delivery Earnings",  "Friday dinner shifts",                       "", "",                  3),
        ("tx_s6",  430.0, "income", "Delivery Earnings",  "Thursday rain slow shift (6 orders)",        "", "",                  4),
        ("tx_s7",  120.0, "expense", "Food",              "Tiffin during afternoon rest",               "", "Udupi Hotel",       4),
        ("tx_s8",  900.0, "income", "Delivery Earnings",  "Wednesday lunch & dinner shifts",            "", "",                  5),
        ("tx_s9",  350.0, "expense", "Maintenance",       "Clutch cable & brake shoe service",          "", "Sharma Bike Works", 5),
        ("tx_s10", 720.0, "income", "Delivery Earnings",  "Tuesday weekday shift",                      "", "",                  6),
        ("tx_s11", 680.0, "income", "Delivery Earnings",  "Monday regular shift",                       "", "",                  7),
        ("tx_s12", 220.0, "expense", "Fuel",              "Bharat Petroleum refueling",                 "", "BP Fuel Station",   7),
    ]

    for tx in transactions:
        tx_date = (today - timedelta(days=tx[7])).strftime("%Y-%m-%d")
        tx_id = f"{tx[0]}_{user_id}"
        cursor.execute("""
        INSERT OR REPLACE INTO transactions (id, user_id, amount, type, category, description, note, merchant, date, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (tx_id, user_id, tx[1], tx[2], tx[3], tx[4], tx[5], tx[6], tx_date, "seed"))

    conn.commit()
    conn.close()


# Convenience aliases
create_transaction = record_transaction_db
get_finance_summary = get_financial_summary
