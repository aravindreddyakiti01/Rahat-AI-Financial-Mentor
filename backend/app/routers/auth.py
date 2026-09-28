from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Header
from app.db.database import get_db_connection
from app.core.redis_state import redis_state
from app.memory.hindsight import hindsight
from app.schemas.schemas import UserSignupRequest, UserLoginRequest

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup")
def signup(req: UserSignupRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (req.email,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="An account with this email already exists.")
    
    user_id = f"user_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    cursor.execute("""
    INSERT INTO users (id, name, email, password_hash, role, pay_frequency, primary_obligation)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, req.name, req.email, "hashed_pw", req.role, req.pay_frequency, req.primary_obligation))
    conn.commit()
    conn.close()

    hindsight.store_memory(
        user_id=user_id,
        memory_type="profile_fact",
        title="Gig Worker Profile",
        content=f"Works as {req.role} with {req.pay_frequency} payouts. Primary financial obligation: {req.primary_obligation}.",
        category="profile",
        outcome_status="observed",
        relevance_tags=["profile", (req.role or "").lower(), "onboarding"]
    )

    token = f"token_{user_id}"
    redis_state.set_json(f"session:{token}", {"user_id": user_id, "name": req.name, "email": req.email})
    return {"token": token, "user": {"id": user_id, "name": req.name, "email": req.email, "role": req.role}}

@router.post("/login")
def login(req: UserLoginRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (req.email,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        if req.email in ["demo@rahat.app", "ramesh.demo@rahat.app"]:
            token = "token_demo_user"
            return {"token": token, "user": {"id": "demo_user", "name": "Ramesh Kumar", "email": req.email, "role": "Delivery Partner (Zomato/Swiggy)"}}
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    u_dict = dict(user)
    token = f"token_{u_dict['id']}"
    redis_state.set_json(f"session:{token}", {"user_id": u_dict["id"], "name": u_dict["name"], "email": u_dict["email"]})
    return {"token": token, "user": {"id": u_dict["id"], "name": u_dict["name"], "email": u_dict["email"], "role": u_dict["role"]}}

@router.get("/me")
def get_current_user(authorization: Optional[str] = Header(None)):
    user_id = "demo_user"
    if authorization and authorization.startswith("Bearer token_"):
        token = authorization.replace("Bearer ", "")
        cached = redis_state.get_json(f"session:{token}")
        if cached:
            user_id = cached.get("user_id", "demo_user")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, role, pay_frequency, primary_obligation, created_at FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if user:
        return dict(user)
    return {
        "id": "demo_user",
        "name": "Ramesh Kumar",
        "email": "ramesh.demo@rahat.app",
        "role": "Delivery Partner (Zomato/Swiggy)",
        "pay_frequency": "Daily",
        "primary_obligation": "Bike EMI (₹4,500)"
    }
