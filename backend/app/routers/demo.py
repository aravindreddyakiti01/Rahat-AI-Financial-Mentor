from fastapi import APIRouter
from app.db import repository
from app.memory.hindsight import hindsight
from app.core.redis_state import redis_state

router = APIRouter(prefix="/demo", tags=["Demo Management"])

@router.post("/reset")
def reset_demo():
    """
    Resets the database and Hindsight memory to the clean, deterministic demo state.
    """
    repository.seed_factual_demo_data("demo_user")
    hindsight.seed_demo_memories("demo_user")
    redis_state.delete("session:token_demo_user")
    return {
        "status": "success",
        "message": "Demo data reset successfully to the multi-week gig-worker case study."
    }
