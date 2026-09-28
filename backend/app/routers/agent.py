import re
from datetime import datetime
from fastapi import APIRouter
from app.agent.graph import run_agent
from app.schemas.schemas import AgentChatRequest, VoiceInputRequest

router = APIRouter(prefix="/agent", tags=["AI Mentor Agent"])

@router.post("/chat")
async def chat_with_agent(req: AgentChatRequest):
    return await run_agent(user_id=req.user_id or "demo_user", user_message=req.message)

@router.post("/voice")
async def voice_input(req: VoiceInputRequest):
    transcript = req.transcript.strip()
    transcript_lower = transcript.lower()

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

    response = await run_agent(user_id=req.user_id or "demo_user", user_message=transcript)
    return {
        "type": "agent_response",
        "needs_confirmation": False,
        "response": response
    }
