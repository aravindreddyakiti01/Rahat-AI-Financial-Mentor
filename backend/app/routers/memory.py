from fastapi import APIRouter, HTTPException, Query
from app.memory.hindsight import hindsight, VALID_MEMORY_TYPES
from app.schemas.schemas import MemoryCreateRequest

router = APIRouter(prefix="/memory", tags=["Hindsight Experiential Memory"])


@router.get("/timeline")
def get_memory_timeline(user_id: str = Query("demo_user")):
    """
    Returns the chronological timeline of meaningful events for the user.
    Strictly isolated per user. Raw transactions are not included.
    """
    return hindsight.get_timeline(user_id)


@router.get("/search")
def search_memories(
    user_id: str = Query("demo_user"),
    query: str = Query("", description="Keywords to match in title, content, or tags"),
    category: str = Query(None, description="Optional category filter e.g. emi, income_pattern"),
    limit: int = Query(4, ge=1, le=10, description="Max memories to return (bounded to 3-5)"),
):
    """
    Retrieves ranked relevant memories for the user using weighted importance scoring.
    """
    return hindsight.search_memories(
        user_id=user_id,
        query=query,
        category=category,
        limit=limit,
    )


@router.get("/categories")
def get_memory_categories():
    """
    Returns supported Hindsight memory categories and their product definitions.
    """
    return {
        "categories": [
            {
                "type": "profile_fact",
                "description": "Stable characteristics about the gig worker (work pattern, fixed obligations).",
            },
            {
                "type": "preference",
                "description": "Meaningful user preferences relevant to financial pacing and budgeting.",
            },
            {
                "type": "plan",
                "description": "Formulated savings pacing strategy for an upcoming goal or bill.",
            },
            {
                "type": "outcome",
                "description": "Real-world result or friction observed after executing a plan or decision.",
            },
            {
                "type": "pattern",
                "description": "Derived behavioral pattern (e.g. weekend surge vs weekday earnings).",
            },
        ]
    }


@router.get("/plan/{plan_id}/outcomes")
def get_plan_outcomes(plan_id: str, user_id: str = Query("demo_user")):
    """
    Retrieves outcomes associated with a specific financial plan (Plan -> Outcome lifecycle).
    """
    return hindsight.get_plan_outcomes(user_id=user_id, plan_id=plan_id)


@router.get("/{memory_id}")
def get_memory(memory_id: str, user_id: str = Query("demo_user")):
    mem = hindsight.get_memory_by_id(user_id, memory_id)
    if not mem:
        raise HTTPException(status_code=404, detail=f"Memory '{memory_id}' not found")
    return mem


@router.post("", status_code=201)
def add_memory(req: MemoryCreateRequest, user_id: str = Query("demo_user")):
    """
    Stores an experiential memory. Validates type and prevents duplicate writes.
    """
    return hindsight.store_memory(
        user_id=user_id,
        memory_type=req.type,
        title=req.title,
        content=req.content,
        category=req.category or "emi",
        outcome_status=req.outcome_status or "observed",
        related_goal_id=req.related_goal_id,
        related_plan_id=req.related_plan_id,
        importance=req.importance or 1.0,
        source=req.source or "user_reported",
        relevance_tags=req.relevance_tags,
        date=req.date,
    )


@router.delete("/{memory_id}")
def delete_memory(memory_id: str, user_id: str = Query("demo_user")):
    deleted = hindsight.delete_memory(user_id, memory_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Memory '{memory_id}' not found")
    return {"deleted": True, "id": memory_id}


@router.post("/clear")
def clear_memories(user_id: str = Query("demo_user")):
    hindsight.clear_memories(user_id)
    return {"cleared": True}
