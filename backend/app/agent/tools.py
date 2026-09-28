from typing import List, Dict, Any, Optional
from datetime import datetime
from app.db import repository
from app.memory.hindsight import hindsight


# ─────────────────────────────────────────────────────────────────────────────
# FACTUAL RETRIEVAL TOOLS (delegates to SQLite repository)
# ─────────────────────────────────────────────────────────────────────────────

def get_income(user_id: str, days: int = 7) -> Dict[str, Any]:
    """Retrieve factual income records and breakdown from SQLite."""
    return repository.get_income_records(user_id, days=days)


def get_expenses(user_id: str, days: int = 7) -> Dict[str, Any]:
    """Retrieve factual expense records and category breakdown from SQLite."""
    return repository.get_expense_records(user_id, days=days)


def get_goals(user_id: str, status: Optional[str] = "active") -> List[Dict[str, Any]]:
    """Retrieve factual active or historical goals from SQLite."""
    return repository.get_active_goals(user_id, status=status)


def get_obligations(user_id: str) -> List[Dict[str, Any]]:
    """Retrieve scheduled financial obligations from SQLite."""
    return repository.get_obligations(user_id)


def get_financial_summary(user_id: str, range_type: str = "7d") -> Dict[str, Any]:
    """Retrieve unified income, expenses, net cash flow, and active goals from SQLite."""
    return repository.get_financial_summary(user_id, range_type=range_type)


def get_recent_transactions(user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
    """Retrieve recent factual transactions from SQLite."""
    return repository.get_recent_transactions(user_id, limit=limit)


def calculate_progress(user_id: str, goal_id: Optional[str] = None) -> Dict[str, Any]:
    """Calculate progress for an active goal or a specific goal."""
    goals = repository.get_active_goals(user_id, status=None)
    if goal_id:
        goal = next((g for g in goals if g["id"] == goal_id), None)
    else:
        goal = next((g for g in goals if g["status"] == "active"), None)

    if not goal:
        return {"found": False, "message": "No active goal found"}

    return {
        "found": True,
        "goal_id": goal["id"],
        "title": goal["title"],
        "target_amount": goal["target_amount"],
        "current_amount": goal["current_amount"],
        "remaining_amount": goal["remaining_amount"],
        "days_remaining": goal["days_remaining"],
        "progress_percentage": goal["progress_percentage"],
        "due_date": goal["due_date"],
        "status": goal["status"],
    }


# ─────────────────────────────────────────────────────────────────────────────
# CONTROLLED WRITE ACTIONS (Strict validation; no raw SQL execution)
# ─────────────────────────────────────────────────────────────────────────────

def record_transaction(
    user_id: str,
    amount: float,
    type_: str,
    category: str,
    description: str = "",
    source: str = "agent",
    date: Optional[str] = None,
    note: str = "",
    merchant: str = "",
) -> Dict[str, Any]:
    """
    Safely record an income or expense transaction in SQLite.
    Validates arguments:
    - amount must be positive (> 0)
    - type_ must be 'income' or 'expense'
    - category must not be empty
    - date must be valid YYYY-MM-DD if provided
    """
    if not isinstance(amount, (int, float)) or amount <= 0:
        raise ValueError(f"Invalid transaction amount: {amount}. Amount must be greater than zero.")

    if type_ not in ("income", "expense"):
        raise ValueError(f"Invalid transaction type: '{type_}'. Must be 'income' or 'expense'.")

    if not category or not category.strip():
        category = "Delivery Earnings" if type_ == "income" else "Expense"

    if date:
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date format: '{date}'. Expected YYYY-MM-DD.")

    return repository.record_transaction_db(
        user_id=user_id,
        amount=amount,
        type_=type_,
        category=category.strip(),
        description=description.strip(),
        source=source,
        date=date,
        note=note.strip(),
        merchant=merchant.strip(),
    )


def create_goal(
    user_id: str,
    title: str,
    target_amount: float,
    due_date: str,
    category: str = "emi",
    initial_amount: float = 0.0,
) -> Dict[str, Any]:
    """
    Safely creates a new savings goal in SQLite through the controlled tool path.
    Also stores a profile_fact in Hindsight.
    """
    goal = repository.create_goal_db(
        user_id=user_id,
        title=title,
        target_amount=target_amount,
        due_date=due_date,
        category=category,
        initial_amount=initial_amount,
    )
    hindsight.store_memory(
        user_id=user_id,
        memory_type="profile_fact",
        title=f"Goal Created: {goal['title']}",
        content=f"Set target of ₹{target_amount:,.0f} due on {due_date}.",
        category=category,
        outcome_status="active",
        related_goal_id=goal["id"],
        relevance_tags=["goal", category, "target"],
    )
    return goal


def update_goal(
    user_id: str,
    goal_id: str,
    amount_to_add: Optional[float] = None,
    new_current_amount: Optional[float] = None,
    status: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Controlled tool to update goal progress or status.
    Records milestone outcome to Hindsight when achieved or missed.
    """
    updated = repository.update_goal_db(
        user_id=user_id,
        goal_id=goal_id,
        amount_to_add=amount_to_add,
        new_current_amount=new_current_amount,
        status=status,
    )
    if not updated:
        return None

    if updated.get("status") == "achieved":
        hindsight.store_memory(
            user_id=user_id,
            memory_type="outcome",
            title=f"Goal Achieved: {updated['title']}",
            content=f"Successfully reached target of ₹{updated['target_amount']:,.0f}.",
            category=updated.get("category", "emi"),
            outcome_status="succeeded",
            related_goal_id=goal_id,
            relevance_tags=["goal", "achieved", "success"],
        )
    return updated


def create_financial_plan(
    user_id: str,
    goal_id: str,
    target_amount: float,
    daily_target: float,
    strategy: str,
    timeframe_days: int,
    assumptions: str = "",
) -> Dict[str, Any]:
    """
    Create a financial plan:
    1. Records plan in SQLite (factual plan record)
    2. Records plan in Hindsight (long-term experiential memory)
    """
    if target_amount <= 0 or daily_target <= 0 or timeframe_days <= 0:
        raise ValueError("target_amount, daily_target, and timeframe_days must be positive.")

    # 1. Record plan in SQLite
    plan = repository.create_plan_db(
        user_id=user_id,
        goal_id=goal_id,
        target_amount=target_amount,
        daily_target=daily_target,
        strategy=strategy,
        timeframe_days=timeframe_days,
        assumptions=assumptions,
    )

    # 2. Record plan in Hindsight experiential memory
    hindsight.store_memory(
        user_id=user_id,
        memory_type="plan",
        title=f"New Financial Plan: {strategy[:40]}",
        content=(
            f"Plan to reach ₹{target_amount:,.0f} across {timeframe_days} days. "
            f"Daily pacing: ₹{daily_target:,.0f}/day with strategy: {strategy}. "
            f"{assumptions[:100]}"
        ).strip(),
        category="emi",
        outcome_status="active",
        related_goal_id=goal_id,
        related_plan_id=plan["plan_id"],
        importance=3.5,
        source="agent_plan",
        relevance_tags=["active_plan", "emi", "strategy"],
    )
    return plan


def get_irregular_income_plan(
    user_id: str,
    goal: Optional[Dict[str, Any]] = None,
    memories: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Calculates deterministic irregular-income financial plan based on actual SQLite history and Hindsight."""
    return repository.calculate_irregular_income_plan(user_id=user_id, goal=goal, memories=memories)


# ─────────────────────────────────────────────────────────────────────────────
# HINDSIGHT EXPERIENTIAL MEMORY TOOLS
# ─────────────────────────────────────────────────────────────────────────────

def search_memory(
    user_id: str,
    query: str = "",
    category: Optional[str] = None,
    limit: int = 4,
) -> List[Dict[str, Any]]:
    """Retrieve relevant past experiences, plans, and outcomes from Hindsight."""
    return hindsight.search_memories(user_id=user_id, query=query, category=category, limit=limit)


def store_meaningful_outcome(
    user_id: str,
    memory_type: str,
    title: str,
    content: str,
    category: str = "emi",
    outcome_status: str = "observed",
    related_goal_id: Optional[str] = None,
    related_plan_id: Optional[str] = None,
    importance: float = 3.5,
    source: str = "user_reported",
    relevance_tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Store an experiential outcome or behavioral learning in Hindsight.
    NEVER store raw financial transactions here.
    """
    valid_types = ("profile_fact", "plan", "outcome", "pattern", "preference")
    norm_type = memory_type.strip().lower()
    if norm_type not in valid_types:
        raise ValueError(f"Invalid memory_type: '{memory_type}'. Must be one of {valid_types}.")

    return hindsight.store_memory(
        user_id=user_id,
        memory_type=norm_type,
        title=title,
        content=content,
        category=category,
        outcome_status=outcome_status,
        related_goal_id=related_goal_id,
        related_plan_id=related_plan_id,
        importance=importance,
        source=source,
        relevance_tags=relevance_tags or ["outcome"],
    )
