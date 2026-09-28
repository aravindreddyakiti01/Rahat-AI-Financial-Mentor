from fastapi import APIRouter, HTTPException, Query
from app.db import repository
from app.memory.hindsight import hindsight
from app.schemas.schemas import (
    GoalCreateRequest,
    GoalUpdateRequest,
    ObligationCreateRequest,
    ObligationUpdateRequest,
)

router = APIRouter(prefix="/goals", tags=["Goals & Obligations"])


# ─── Goals ────────────────────────────────────────────────────────────────────

@router.get("")
def get_goals(user_id: str = Query("demo_user"), status: str = Query(None)):
    """List goals. Optionally filter by status: 'active' | 'achieved' | 'missed'."""
    return repository.get_active_goals(user_id, status=status)


@router.get("/{goal_id}")
def get_goal(goal_id: str, user_id: str = Query("demo_user")):
    goal = repository.get_goal_by_id(user_id, goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail=f"Goal '{goal_id}' not found")
    return goal


@router.post("", status_code=201)
def create_goal(req: GoalCreateRequest, user_id: str = Query("demo_user")):
    """Create a new savings goal."""
    goal = repository.create_goal_db(
        user_id=user_id,
        title=req.title,
        target_amount=req.target_amount,
        due_date=req.due_date,
        category=req.category or "emi",
        initial_amount=req.initial_amount or 0.0,
    )

    # Store goal creation as a Hindsight profile fact (not the raw numbers — the intention)
    hindsight.store_memory(
        user_id=user_id,
        memory_type="profile_fact",
        title=f"Goal Created: {req.title}",
        content=f"Set target of ₹{req.target_amount:,.0f} due on {req.due_date}.",
        category=req.category or "emi",
        outcome_status="active",
        related_goal_id=goal["id"],
        relevance_tags=["goal", req.category or "emi", "target"],
    )

    return goal


@router.patch("/{goal_id}")
def update_goal(goal_id: str, req: GoalUpdateRequest, user_id: str = Query("demo_user")):
    """
    Update goal progress or status.
    - amount_to_add: incremental deposit (e.g. ₹200 saved today)
    - new_current_amount: set absolute saved amount
    - status: 'active' | 'achieved' | 'missed'
    """
    updated = repository.update_goal_db(
        user_id=user_id,
        goal_id=goal_id,
        amount_to_add=req.amount_to_add,
        new_current_amount=req.new_current_amount,
        status=req.status,
    )
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Goal '{goal_id}' not found")

    # Record meaningful milestones to Hindsight (not raw numbers)
    if req.status == "achieved":
        hindsight.store_memory(
            user_id=user_id,
            memory_type="outcome",
            title=f"Goal Achieved: {updated['title']}",
            content=f"Successfully saved ₹{updated['current_amount']:,.0f} to reach target of ₹{updated['target_amount']:,.0f}.",
            category=updated.get("category", "emi"),
            outcome_status="succeeded",
            related_goal_id=goal_id,
            relevance_tags=["goal", "achieved", "success"],
        )
    elif req.status == "missed":
        hindsight.store_memory(
            user_id=user_id,
            memory_type="outcome",
            title=f"Goal Missed: {updated['title']}",
            content=f"Saved ₹{updated['current_amount']:,.0f} of ₹{updated['target_amount']:,.0f} target. Shortfall: ₹{updated['remaining_amount']:,.0f}.",
            category=updated.get("category", "emi"),
            outcome_status="missed",
            related_goal_id=goal_id,
            relevance_tags=["goal", "missed", "learning"],
        )

    return updated


# ─── Obligations ──────────────────────────────────────────────────────────────

@router.get("/obligations/list")
def get_obligations(user_id: str = Query("demo_user"), status: str = Query(None)):
    """List all financial obligations, optionally filtered by status."""
    return repository.get_obligations(user_id, status=status)


@router.get("/obligations/{obligation_id}")
def get_obligation(obligation_id: str, user_id: str = Query("demo_user")):
    obl = repository.get_obligation_by_id(user_id, obligation_id)
    if not obl:
        raise HTTPException(status_code=404, detail=f"Obligation '{obligation_id}' not found")
    return obl


@router.post("/obligations", status_code=201)
def create_obligation(req: ObligationCreateRequest, user_id: str = Query("demo_user")):
    """Add a new recurring financial obligation (e.g. EMI, rent)."""
    return repository.create_obligation_db(
        user_id=user_id,
        title=req.title,
        amount=req.amount,
        frequency=req.frequency or "monthly",
        due_day=req.due_day or 10,
        next_due_date=req.next_due_date,
    )


@router.patch("/obligations/{obligation_id}")
def update_obligation(
    obligation_id: str,
    req: ObligationUpdateRequest,
    user_id: str = Query("demo_user"),
):
    """Update obligation status: 'active' | 'paid' | 'overdue'."""
    updated = repository.update_obligation_status(user_id, obligation_id, req.status)
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Obligation '{obligation_id}' not found")
    return updated
