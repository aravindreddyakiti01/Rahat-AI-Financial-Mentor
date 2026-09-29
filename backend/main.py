import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Header, Depends, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import init_db, seed_demo_data, get_db_connection
from hindsight_memory import hindsight
from redis_state import redis_state
from agent_graph import run_agent
import agent_tools

app = FastAPI(
    title="RAHAT API",
    description="Backend API and Agent Gateway for Rahat — Personal Financial Mentor for Gig Workers",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database and seed demo data on startup
@app.on_event("startup")
def on_startup():
    init_db()
    seed_demo_data("demo_user")
    hindsight.seed_demo_memories("demo_user")
    print("Rahat backend initialized with SQLite, Hindsight, and Redis temporary state fallback.")

# Pydantic Request Models
class UserSignupRequest(BaseModel):
    name: str
    email: str
    password: str
    role: Optional[str] = "Delivery"
    pay_frequency: Optional[str] = "Daily"
    primary_obligation: Optional[str] = "Bike EMI"

class UserLoginRequest(BaseModel):
    email: str
    password: str

class TransactionCreateRequest(BaseModel):
    amount: float
    type: str # 'income' or 'expense'
    category: str
    description: Optional[str] = ""
    date: Optional[str] = None
    source: Optional[str] = "manual"

class GoalCreateRequest(BaseModel):
    title: str
    target_amount: float
    due_date: str
    category: Optional[str] = "emi"

class AgentChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "demo_user"

class VoiceInputRequest(BaseModel):
    transcript: str
    user_id: Optional[str] = "demo_user"

class MemoryCreateRequest(BaseModel):
    type: str
    title: str
    content: str
    category: Optional[str] = "emi"
    outcome_status: Optional[str] = "observed"
    relevance_tags: Optional[List[str]] = []

# --- Health & Status ---
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "product": "Rahat",
        "agent": "LangGraph Financial Mentor",
        "memory_layer": "Hindsight",
        "timestamp": datetime.now().isoformat()
    }

# --- Authentication ---
@app.post("/auth/signup")
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

    # Initialize memory for user
    hindsight.store_memory(
        user_id=user_id,
        memory_type="profile_fact",
        title="Gig Worker Profile",
        content=f"Works as {req.role} with {req.pay_frequency} payouts. Primary financial obligation: {req.primary_obligation}.",
        category="profile",
        outcome_status="observed",
        relevance_tags=["profile", req.role.lower(), "onboarding"]
    )

    token = f"token_{user_id}"
    redis_state.set_json(f"session:{token}", {"user_id": user_id, "name": req.name, "email": req.email})
    return {"token": token, "user": {"id": user_id, "name": req.name, "email": req.email, "role": req.role}}

@app.post("/auth/login")
def login(req: UserLoginRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (req.email,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        # If demo login
        if req.email in ["demo@rahat.app", "ramesh.demo@rahat.app"]:
            token = "token_demo_user"
            return {"token": token, "user": {"id": "demo_user", "name": "Ramesh Kumar", "email": req.email, "role": "Delivery Partner (Zomato/Swiggy)"}}
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    u_dict = dict(user)
    token = f"token_{u_dict['id']}"
    redis_state.set_json(f"session:{token}", {"user_id": u_dict["id"], "name": u_dict["name"], "email": u_dict["email"]})
    return {"token": token, "user": {"id": u_dict["id"], "name": u_dict["name"], "email": u_dict["email"], "role": u_dict["role"]}}

@app.get("/auth/me")
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

# --- Financial State & Transactions ---
@app.get("/finance/summary")
def get_finance_summary(user_id: str = "demo_user"):
    income = agent_tools.get_income(user_id, days=7)
    expenses = agent_tools.get_expenses(user_id, days=7)
    goals = agent_tools.get_goals(user_id, status="active")
    obligations = agent_tools.get_obligations(user_id)

    total_inc = income["total_income"]
    total_exp = expenses["total_expenses"]
    net_available = max(0.0, total_inc - total_exp)

    active_goal = goals[0] if goals else None
    goal_progress = active_goal["progress_percentage"] if active_goal else 0.0

    return {
        "total_income_7d": total_inc,
        "total_expenses_7d": total_exp,
        "net_available": net_available,
        "active_goal": active_goal,
        "goal_progress_percent": goal_progress,
        "daily_avg_income": income["average_daily_income"],
        "obligations": obligations
    }

@app.get("/finance/transactions")
def get_transactions(user_id: str = "demo_user", limit: int = 20):
    return agent_tools.get_recent_transactions(user_id, limit)

@app.post("/finance/income")
def add_income(req: TransactionCreateRequest, user_id: str = "demo_user"):
    tx = agent_tools.record_transaction(
        user_id=user_id,
        amount=req.amount,
        type_="income",
        category=req.category or "Delivery Earnings",
        description=req.description or "Daily shift earnings",
        source=req.source or "manual",
        date=req.date
    )
    return tx

@app.post("/finance/expense")
def add_expense(req: TransactionCreateRequest, user_id: str = "demo_user"):
    tx = agent_tools.record_transaction(
        user_id=user_id,
        amount=req.amount,
        type_="expense",
        category=req.category or "Fuel",
        description=req.description or "Vehicle fuel / expenses",
        source=req.source or "manual",
        date=req.date
    )
    return tx

@app.delete("/finance/transactions/{tx_id}")
def delete_transaction(tx_id: str, user_id: str = "demo_user"):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE id = ? AND user_id = ?", (tx_id, user_id))
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return {"deleted": success}

# --- Goals ---
@app.get("/goals")
def get_goals_endpoint(user_id: str = "demo_user"):
    return agent_tools.get_goals(user_id, status=None)

@app.post("/goals")
def create_goal_endpoint(req: GoalCreateRequest, user_id: str = "demo_user"):
    conn = get_db_connection()
    cursor = conn.cursor()
    goal_id = f"goal_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    cursor.execute("""
    INSERT INTO goals (id, user_id, title, target_amount, current_amount, due_date, category, status)
    VALUES (?, ?, ?, ?, 0.0, ?, ?, 'active')
    """, (goal_id, user_id, req.title, req.target_amount, req.due_date, req.category))
    conn.commit()
    conn.close()

    # Record in Hindsight
    hindsight.store_memory(
        user_id=user_id,
        memory_type="profile_fact",
        title=f"Goal Created: {req.title}",
        content=f"Set target of ₹{req.target_amount:,.0f} due on {req.due_date}.",
        category=req.category,
        outcome_status="active",
        related_goal_id=goal_id,
        relevance_tags=["goal", req.category, "target"]
    )

    return {"id": goal_id, "title": req.title, "target_amount": req.target_amount, "due_date": req.due_date}

# --- Memory Screen (What Rahat Remembers) ---
@app.get("/memory/timeline")
def get_memory_timeline(user_id: str = "demo_user"):
    """
    Returns the visible Hindsight chronological memory timeline.
    """
    return hindsight.get_timeline(user_id)

@app.get("/memory/search")
def search_memories(
    user_id: str = Query("demo_user"),
    query: str = Query(""),
    category: Optional[str] = Query(None),
    limit: int = Query(4, ge=1, le=10),
):
    return hindsight.search_memories(user_id=user_id, query=query, category=category, limit=limit)

@app.get("/memory/categories")
def get_memory_categories():
    return {
        "categories": [
            {"type": "profile_fact", "description": "Stable characteristics about the gig worker."},
            {"type": "preference", "description": "User preferences relevant to pacing and budgeting."},
            {"type": "plan", "description": "Formulated savings pacing strategy."},
            {"type": "outcome", "description": "Real-world result or friction after executing a plan."},
            {"type": "pattern", "description": "Derived behavioral or earning pattern."},
        ]
    }

@app.get("/memory/plan/{plan_id}/outcomes")
def get_plan_outcomes(plan_id: str, user_id: str = Query("demo_user")):
    return hindsight.get_plan_outcomes(user_id=user_id, plan_id=plan_id)

@app.get("/memory/{memory_id}")
def get_memory(memory_id: str, user_id: str = Query("demo_user")):
    mem = hindsight.get_memory_by_id(user_id, memory_id)
    if not mem:
        raise HTTPException(status_code=404, detail=f"Memory '{memory_id}' not found")
    return mem

@app.post("/memory")
def add_memory_endpoint(req: MemoryCreateRequest, user_id: str = "demo_user"):
    return hindsight.store_memory(
        user_id=user_id,
        memory_type=req.type,
        title=req.title,
        content=req.content,
        category=req.category,
        outcome_status=req.outcome_status,
        relevance_tags=req.relevance_tags
    )

@app.delete("/memory/{memory_id}")
def delete_memory_endpoint(memory_id: str, user_id: str = "demo_user"):
    deleted = hindsight.delete_memory(user_id, memory_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Memory '{memory_id}' not found")
    return {"deleted": deleted, "id": memory_id}

@app.post("/memory/clear")
def clear_memories_endpoint(user_id: str = "demo_user"):
    hindsight.clear_memories(user_id)
    return {"cleared": True}

# --- Agent Chat & Voice ---
@app.post("/agent/chat")
async def chat_with_agent(req: AgentChatRequest):
    response = await run_agent(user_id=req.user_id or "demo_user", user_message=req.message)
    return response

@app.post("/agent/voice")
async def voice_input(req: VoiceInputRequest):
    """
    Handles transcribed voice input safely.
    If speech mentions logging a transaction, extracts details and prompts for confirmation.
    Otherwise triggers the LangGraph Financial Mentor Agent.
    """
    transcript = req.transcript.strip()
    transcript_lower = transcript.lower()

    # Detect if user is stating a transaction that needs confirmation
    import re
    numbers = re.findall(r'₹?\s*(\d+)', transcript)
    amount = float(numbers[0]) if numbers else None

    if any(k in transcript_lower for k in ["spent", "petrol", "fuel", "bought", "paid"]) and amount:
        category = "Fuel" if "fuel" in transcript_lower or "petrol" in transcript_lower else "Expense"
        return {
            "type": "transaction_confirmation",
            "needs_confirmation": True,
            "proposed_transaction": {
                "amount": amount,
                "type": "expense",
                "category": category,
                "description": f"Voice log: {transcript}",
                "date": datetime.now().strftime("%Y-%m-%d")
            },
            "confirmation_message": f"I think you said you spent ₹{amount:,.0f} on {category}."
        }
    elif any(k in transcript_lower for k in ["earned", "made", "income", "received", "payout"]) and amount:
        return {
            "type": "transaction_confirmation",
            "needs_confirmation": True,
            "proposed_transaction": {
                "amount": amount,
                "type": "income",
                "category": "Delivery Earnings",
                "description": f"Voice log: {transcript}",
                "date": datetime.now().strftime("%Y-%m-%d")
            },
            "confirmation_message": f"I think you said you earned ₹{amount:,.0f} from deliveries."
        }

    # Otherwise route to LangGraph Agent
    response = await run_agent(user_id=req.user_id or "demo_user", user_message=transcript)
    return {
        "type": "agent_response",
        "needs_confirmation": False,
        "response": response
    }

# --- Receipt OCR Simulation with Confirmation ---
@app.post("/receipt/scan")
def scan_receipt_ocr():
    """
    Receipt scan OCR flow.
    Extracts merchant, amount, date and category, returning a confirmation structure.
    Never creates transactions without user confirmation.
    """
    # Deterministic OCR extraction for petrol receipt
    return {
        "success": True,
        "extracted_data": {
            "merchant": "Bharat Petroleum Station",
            "amount": 280.0,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "category": "Fuel",
            "items": ["Speed Petrol 2.65L"]
        },
        "confidence": 0.94,
        "confirmation_prompt": "Did I get this right? Bharat Petroleum — ₹280 for Fuel on " + datetime.now().strftime("%d %b")
    }

# --- Grounded Insights ---
@app.get("/insights")
def get_insights(user_id: str = "demo_user"):
    income = agent_tools.get_income(user_id, 7)
    expenses = agent_tools.get_expenses(user_id, 7)
    goals = agent_tools.get_goals(user_id, "active")

    insights = []
    
    # 1. Weekend Surge Earning Insight
    if income["weekend_income"] > 0:
        ratio = round((income["weekend_income"] / max(income["total_income"], 1)) * 100)
        insights.append({
            "id": "ins_1",
            "title": "Weekend Surge Advantage",
            "description": f"Weekend earnings contributed {ratio}% of your 7-day total income. Your Saturday and Sunday shifts consistently generate higher per-hour returns.",
            "type": "positive",
            "metric": f"₹{income['weekend_income']:,.0f} on Sat-Sun"
        })

    # 2. Fuel Expense Proportion
    fuel_exp = expenses["category_breakdown"].get("Fuel", 0)
    if fuel_exp > 0:
        insights.append({
            "id": "ins_2",
            "title": "Fuel Efficiency Track",
            "description": f"Fuel represents ₹{fuel_exp:,.0f} ({round((fuel_exp/max(expenses['total_expenses'],1))*100)}%) of your operating costs over the last 7 days.",
            "type": "neutral",
            "metric": f"₹{fuel_exp:,.0f} Fuel"
        })

    # 3. Goal Distance
    if goals:
        g = goals[0]
        insights.append({
            "id": "ins_3",
            "title": f"{g['title']} Target Pace",
            "description": f"You are ₹{g['remaining_amount']:,.0f} away from your target with {g['days_remaining']} days remaining until the Oct 5 due date.",
            "type": "warning" if g['days_remaining'] <= 5 else "positive",
            "metric": f"₹{g['remaining_amount']:,.0f} remaining"
        })

    return insights

# --- Demo Reset ---
@app.post("/demo/reset")
def reset_demo():
    """
    Resets the database and Hindsight memory to the clean, deterministic demo state.
    """
    seed_demo_data("demo_user")
    hindsight.seed_demo_memories("demo_user")
    redis_state.delete("session:token_demo_user")
    return {
        "status": "success",
        "message": "Demo data reset successfully to the multi-week gig-worker case study."
    }
