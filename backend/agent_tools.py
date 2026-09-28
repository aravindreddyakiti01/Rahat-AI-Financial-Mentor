import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from database import get_db_connection
from hindsight_memory import hindsight

def get_income(user_id: str, days: int = 7) -> Dict[str, Any]:
    """
    Retrieves factual income transactions and breakdown from SQLite.
    Never fabricates data.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    cursor.execute("""
    SELECT amount, category, description, date, source FROM transactions
    WHERE user_id = ? AND type = 'income' AND date >= ?
    ORDER BY date DESC
    """, (user_id, cutoff_date))
    
    rows = cursor.fetchall()
    conn.close()
    
    transactions = [dict(r) for r in rows]
    total_income = sum(t["amount"] for t in transactions)
    avg_daily_income = total_income / max(days, 1)
    
    # Categorize weekday vs weekend for pattern grounding
    weekday_income = 0
    weekend_income = 0
    for t in transactions:
        try:
            dt = datetime.strptime(t["date"], "%Y-%m-%d")
            if dt.weekday() in [5, 6]: # Sat, Sun
                weekend_income += t["amount"]
            else:
                weekday_income += t["amount"]
        except Exception:
            pass

    return {
        "user_id": user_id,
        "timeframe_days": days,
        "total_income": total_income,
        "average_daily_income": round(avg_daily_income, 2),
        "weekend_income": weekend_income,
        "weekday_income": weekday_income,
        "count": len(transactions),
        "recent_income_entries": transactions[:5]
    }

def get_expenses(user_id: str, days: int = 7) -> Dict[str, Any]:
    """
    Retrieves factual expense transactions and breakdown from SQLite.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    cursor.execute("""
    SELECT amount, category, description, date, source FROM transactions
    WHERE user_id = ? AND type = 'expense' AND date >= ?
    ORDER BY date DESC
    """, (user_id, cutoff_date))
    
    rows = cursor.fetchall()
    conn.close()
    
    transactions = [dict(r) for r in rows]
    total_expenses = sum(t["amount"] for t in transactions)
    
    # Category breakdown
    categories = {}
    for t in transactions:
        cat = t["category"]
        categories[cat] = categories.get(cat, 0.0) + t["amount"]

    return {
        "user_id": user_id,
        "timeframe_days": days,
        "total_expenses": total_expenses,
        "category_breakdown": categories,
        "count": len(transactions),
        "recent_expense_entries": transactions[:5]
    }

def get_goals(user_id: str, status: Optional[str] = "active") -> List[Dict[str, Any]]:
    """
    Retrieves factual goals from SQLite.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    if status:
        cursor.execute("SELECT * FROM goals WHERE user_id = ? AND status = ? ORDER BY due_date ASC", (user_id, status))
    else:
        cursor.execute("SELECT * FROM goals WHERE user_id = ? ORDER BY due_date ASC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    
    goals = []
    for r in rows:
        g = dict(r)
        remaining = max(0.0, g["target_amount"] - g["current_amount"])
        try:
            due_dt = datetime.strptime(g["due_date"], "%Y-%m-%d")
            days_left = max(0, (due_dt - datetime.now()).days)
        except Exception:
            days_left = 5
            
        g["remaining_amount"] = remaining
        g["days_remaining"] = days_left
        g["progress_percentage"] = round((g["current_amount"] / max(g["target_amount"], 1)) * 100, 1)
        goals.append(g)
    return goals

def calculate_progress(user_id: str, goal_id: str) -> Dict[str, Any]:
    """
    Computes precise factual math for a goal.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM goals WHERE user_id = ? AND id = ?", (user_id, goal_id))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return {"error": f"Goal with ID {goal_id} not found"}
        
    g = dict(row)
    remaining = max(0.0, g["target_amount"] - g["current_amount"])
    try:
        due_dt = datetime.strptime(g["due_date"], "%Y-%m-%d")
        days_left = max(1, (due_dt - datetime.now()).days)
    except Exception:
        days_left = 5
        
    daily_needed = round(remaining / days_left, 2)
    return {
        "goal_id": goal_id,
        "title": g["title"],
        "target_amount": g["target_amount"],
        "current_amount": g["current_amount"],
        "remaining_amount": remaining,
        "days_remaining": days_left,
        "required_daily_rate": daily_needed,
        "is_on_track": g["current_amount"] >= g["target_amount"] * 0.5
    }

def create_financial_plan(
    user_id: str,
    goal_id: str,
    target_amount: float,
    daily_target: float,
    strategy: str,
    timeframe_days: int
) -> Dict[str, Any]:
    """
    Saves a newly agreed financial plan in SQLite and records plan memory in Hindsight.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    plan_id = f"plan_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    cursor.execute("""
    INSERT INTO financial_plans (id, user_id, goal_id, target_amount, daily_target, strategy, timeframe_days, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, 'active')
    """, (plan_id, user_id, goal_id, target_amount, daily_target, strategy, timeframe_days))
    
    conn.commit()
    conn.close()
    
    # Store in Hindsight memory
    hindsight.store_memory(
        user_id=user_id,
        memory_type="plan",
        title=f"New Financial Plan: {strategy[:40]}",
        content=f"Plan to reach ₹{target_amount:,.0f} across {timeframe_days} days. Daily pacing: ₹{daily_target:,.0f}/day with strategy: {strategy}",
        category="emi",
        outcome_status="active",
        related_goal_id=goal_id,
        relevance_tags=["active_plan", "emi", "strategy"]
    )
    
    return {
        "plan_id": plan_id,
        "user_id": user_id,
        "goal_id": goal_id,
        "target_amount": target_amount,
        "daily_target": daily_target,
        "strategy": strategy,
        "timeframe_days": timeframe_days,
        "status": "active"
    }

def update_goal(user_id: str, goal_id: str, added_amount: float) -> Dict[str, Any]:
    """
    Updates factual goal progress.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT current_amount, target_amount FROM goals WHERE user_id = ? AND id = ?", (user_id, goal_id))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return {"error": "Goal not found"}
        
    new_amount = row["current_amount"] + added_amount
    status = "completed" if new_amount >= row["target_amount"] else "active"
    
    cursor.execute("UPDATE goals SET current_amount = ?, status = ? WHERE user_id = ? AND id = ?", (new_amount, status, user_id, goal_id))
    conn.commit()
    conn.close()
    
    return {
        "goal_id": goal_id,
        "new_amount": new_amount,
        "target_amount": row["target_amount"],
        "status": status
    }

def record_transaction(
    user_id: str,
    amount: float,
    type_: str,
    category: str,
    description: str,
    source: str = "manual",
    date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Records a factual transaction into SQLite.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    tx_id = f"tx_{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.urandom(2).hex()}"
    tx_date = date or datetime.now().strftime("%Y-%m-%d")
    
    cursor.execute("""
    INSERT INTO transactions (id, user_id, amount, type, category, description, date, source)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (tx_id, user_id, amount, type_, category, description, tx_date, source))
    
    conn.commit()
    conn.close()
    
    return {
        "id": tx_id,
        "amount": amount,
        "type": type_,
        "category": category,
        "description": description,
        "date": tx_date,
        "source": source
    }

def search_memory(user_id: str, query: str = "", category: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Searches Hindsight memory for relevant past plans, outcomes, and patterns.
    """
    return hindsight.search_memories(user_id=user_id, query=query, category=category, limit=4)

def store_outcome(
    user_id: str,
    plan_id: str,
    outcome_description: str,
    outcome_status: str,
    learned_pattern: Optional[str] = None
) -> Dict[str, Any]:
    """
    Stores an outcome into Hindsight, optionally recording a newly learned pattern.
    """
    # 1. Update plan status in SQLite if applicable
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE financial_plans SET status = ? WHERE id = ? AND user_id = ?", (outcome_status, plan_id, user_id))
    conn.commit()
    conn.close()
    
    # 2. Store outcome memory
    outcome_mem = hindsight.store_memory(
        user_id=user_id,
        memory_type="outcome",
        title=f"Plan Outcome: {outcome_status.capitalize()}",
        content=outcome_description,
        category="emi",
        outcome_status=outcome_status,
        relevance_tags=["outcome", outcome_status, "learning"]
    )
    
    # 3. Store learned pattern if provided
    pattern_mem = None
    if learned_pattern:
        pattern_mem = hindsight.store_memory(
            user_id=user_id,
            memory_type="pattern",
            title="Learned Behavioral Pattern",
            content=learned_pattern,
            category="income_pattern",
            outcome_status="learned",
            relevance_tags=["pattern", "adaptive_learning"]
        )
        
    return {
        "outcome_memory": outcome_mem,
        "pattern_memory": pattern_mem
    }

def get_recent_transactions(user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions WHERE user_id = ? ORDER BY date DESC, created_at DESC LIMIT ?", (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_obligations(user_id: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM obligations WHERE user_id = ? ORDER BY due_day ASC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]
