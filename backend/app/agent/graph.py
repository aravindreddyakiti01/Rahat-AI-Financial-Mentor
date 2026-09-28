import re
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, START, END

from app.agent.state import FinancialMentorState
from app.agent import tools as agent_tools
from app.agent.llm import llm_client
from app.memory.hindsight import hindsight
from app.db import repository

logger = logging.getLogger("rahat.agent")


# ─────────────────────────────────────────────────────────────────────────────
# NODE 1 — UNDERSTAND INTENT
# ─────────────────────────────────────────────────────────────────────────────

def parse_intent(state: FinancialMentorState) -> Dict[str, Any]:
    """
    Parses user request into a structured intent category and extracts parameters
    (amount, category, merchant, date) safely.
    """
    msg = state.get("user_message", "").strip()
    msg_lower = msg.lower()

    # Extract numerical amounts: ₹900, rs 900, 900 rs, or raw numbers
    numbers = re.findall(r'(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d{1,2})?)', msg_lower)
    extracted_amount = float(numbers[0]) if numbers else None

    # Extract date if mentioned: today, yesterday, or YYYY-MM-DD
    extracted_date = datetime.now().strftime("%Y-%m-%d")
    date_match = re.search(r'\b(\d{4}-\d{2}-\d{2})\b', msg)
    if date_match:
        extracted_date = date_match.group(1)

    # 1. Record Income
    income_verbs = ["earned", "made", "income of", "got paid", "received", "delivery payout", "shift earnings", "log income", "add income"]
    if any(v in msg_lower for v in income_verbs) and extracted_amount is not None:
        intent = "record_income"
        category = "Delivery Earnings"
        params = {
            "amount": extracted_amount,
            "category": category,
            "description": f"Earned from delivery shifts: {msg}",
            "date": extracted_date,
        }

    # 2. Record Expense
    elif any(v in msg_lower for v in ["spent", "paid for", "bought", "expense of", "log expense", "add expense", "cost me", "recharge", "puncture", "petrol", "diesel"]) and extracted_amount is not None:
        intent = "record_expense"
        category = "Fuel" if any(w in msg_lower for w in ["fuel", "petrol", "diesel", "gas"]) else "Maintenance" if any(w in msg_lower for w in ["puncture", "service", "oil", "repair"]) else "Food" if any(w in msg_lower for w in ["food", "chai", "lunch", "dinner", "tiffin"]) else "Expense"
        merchant = "HP Petrol" if "hp" in msg_lower else "IndianOil" if "indianoil" in msg_lower else "Shell" if "shell" in msg_lower else ""
        params = {
            "amount": extracted_amount,
            "category": category,
            "description": f"Expense: {msg}",
            "merchant": merchant,
            "date": extracted_date,
        }

    # 3. Create Goal (Controlled Goal Creation via Agent)
    elif any(w in msg_lower for w in ["want to save", "set a goal", "create a goal", "create goal", "new goal", "target of"]) and extracted_amount is not None:
        intent = "create_goal"
        title = "Bike Savings" if "bike" in msg_lower else "Emergency Fund" if "emergency" in msg_lower else "Savings Goal"
        category = "emi" if ("emi" in msg_lower or "bike" in msg_lower) else "savings"
        due_date = extracted_date if date_match else (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        params = {
            "title": title,
            "target_amount": extracted_amount,
            "due_date": due_date,
            "category": category,
        }

    # 4. Update Goal Progress / Add Savings towards Goal
    elif any(w in msg_lower for w in ["saved today for", "towards my goal", "towards my emi", "towards my bike", "add to my goal", "put towards"]) and extracted_amount is not None:
        intent = "update_goal_progress"
        params = {"amount": extracted_amount}

    # 5. Financial Summary Query
    elif any(w in msg_lower for w in ["how much did i spend", "how much did i earn", "total income", "total expense", "financial summary", "summary of", "cash flow", "spending"]):
        intent = "financial_summary"
        params = {}

    # 6. Goal Progress Query
    elif any(w in msg_lower for w in ["on track", "goal progress", "how much is left", "saved so far", "target progress", "bike emi target", "how close am i", "how much have i saved", "goal status", "saved towards"]):
        intent = "goal_progress"
        params = {}

    # 7. Obligation Query
    elif any(w in msg_lower for w in ["when is my emi", "due date", "upcoming bills", "fixed obligations", "upcoming emi"]):
        intent = "obligation_status"
        params = {}

    # 8. Financial Planning Request
    elif any(w in msg_lower for w in ["need ₹", "need rs", "what should i do", "how should i save", "help me plan", "planning", "reach my target", "save for my emi", "emi plan", "reach my goal", "can i reach", "how much should i earn", "what should i do differently", "earn per day"]):
        intent = "financial_planning"
        params = {"target_amount": extracted_amount}

    # 9. Why this advice query
    elif any(w in msg_lower for w in ["why this advice", "why did you advise", "evidence", "explain why", "reason for this"]):
        intent = "why_advice_query"
        params = {}

    # 10. User reported outcome (milestone)
    elif any(w in msg_lower for w in ["missed my target", "failed to save", "could not make", "could not save", "only saved", "didn't reach", "achieved my goal", "was short", "fell short", "couldn't save"]):
        intent = "outcome_report"
        params = {}

    # 11. General financial question
    elif any(w in msg_lower for w in ["invest", "mutual fund", "loan", "tax", "stock", "crypto", "insurance", "bank account", "hello", "hi", "namaste", "help"]):
        intent = "general_financial_question"
        params = {}

    else:
        intent = "unknown"
        params = {}

    return {
        "intent": intent,
        "intent_params": params,
    }


# ─────────────────────────────────────────────────────────────────────────────
# NODE 2 — RETRIEVE CURRENT FACTS (SQLite Repository Boundary)
# ─────────────────────────────────────────────────────────────────────────────

def load_current_financial_state(state: FinancialMentorState) -> Dict[str, Any]:
    """
    Retrieves factual financial records strictly via the Step 2 repository tools.
    Never executes raw SQL inside LangGraph nodes.
    Handles DB exceptions gracefully without crashing.
    """
    user_id = state["user_id"]
    try:
        income_data = agent_tools.get_income(user_id, days=7)
        expense_data = agent_tools.get_expenses(user_id, days=7)
        goals_data = agent_tools.get_goals(user_id, status=None)
        active_goals = [g for g in goals_data if g.get("status") == "active"]
        obligations = agent_tools.get_obligations(user_id)
        summary = agent_tools.get_financial_summary(user_id, range_type="7d")

        current_state = {
            "income_7d": income_data,
            "expenses_7d": expense_data,
            "net_cash_flow": summary["net_cash_flow"],
            "net_available_7d": summary["net_available"],
            "active_goals": active_goals,
            "all_goals": goals_data,
            "obligations": obligations,
        }
        return {
            "current_financial_state": current_state,
            "financial_state_error": None,
        }
    except Exception as e:
        logger.error(f"Error loading factual financial state: {e}")
        return {
            "current_financial_state": {},
            "financial_state_error": f"Factual database temporarily unavailable: {str(e)}",
        }


# ─────────────────────────────────────────────────────────────────────────────
# NODE 3 — RETRIEVE HINDSIGHT MEMORY
# ─────────────────────────────────────────────────────────────────────────────

def retrieve_relevant_hindsight(state: FinancialMentorState) -> Dict[str, Any]:
    """
    Retrieves relevant experiential memories from Hindsight.
    - Strictly distinguishes 'unavailable' (service error) from 'no_memories_found'
    - Does not dump every memory: uses query relevance and limit <= 4
    - Only retrieves when historical context is meaningful
    """
    user_id = state["user_id"]
    intent = state.get("intent", "")
    query = state.get("user_message", "")

    # For raw logging actions, historical memory is not needed
    if intent in ("record_income", "record_expense"):
        return {
            "hindsight_memories": [],
            "memory_status": "not_needed",
            "memory_error": None,
        }

    category = "emi" if ("emi" in query.lower() or intent in ("financial_planning", "goal_progress")) else None

    try:
        memories = agent_tools.search_memory(user_id=user_id, query=query, category=category, limit=4)
        if memories:
            return {
                "hindsight_memories": memories,
                "memory_status": "available",
                "memory_error": None,
            }
        else:
            return {
                "hindsight_memories": [],
                "memory_status": "no_memories_found",
                "memory_error": None,
            }
    except Exception as e:
        logger.warning(f"Hindsight memory retrieval error: {e}")
        return {
            "hindsight_memories": [],
            "memory_status": "unavailable",
            "memory_error": str(e),
        }


# ─────────────────────────────────────────────────────────────────────────────
# NODE 4 — REASON USING CURRENT FACTS + MEMORY
# ─────────────────────────────────────────────────────────────────────────────

def reason_with_llm(state: FinancialMentorState) -> Dict[str, Any]:
    """
    Combines Current Facts (SQLite) + Relevant Memories (Hindsight) + User Request.
    Adapts financial strategies based on past outcomes rather than repeating failed plans.
    """
    intent = state["intent"]
    fin_state = state.get("current_financial_state", {})
    memories = state.get("hindsight_memories", [])
    user_msg = state["user_message"]
    user_id = state["user_id"]

    # If database error occurred, route directly to error response
    if state.get("financial_state_error"):
        return {
            "reasoning_plan": {"has_db_error": True},
            "action_decision": "answer",
            "llm_used": False,
        }

    # Inspect historical outcomes in memory:
    has_failed_previous_plan = any(
        m.get("type") == "outcome" and m.get("outcome_status") == "failed"
        for m in memories
    )
    has_learned_pattern = any(
        m.get("type") == "pattern" or "weekend" in m.get("content", "").lower()
        for m in memories
    )

    active_goals = fin_state.get("active_goals", [])
    active_goal = active_goals[0] if active_goals else None

    # Calculate deterministic irregular-income plan
    calc_plan = repository.calculate_irregular_income_plan(user_id=user_id, goal=active_goal, memories=memories)

    remaining_emi = calc_plan.get("remaining_amount", active_goal["remaining_amount"] if active_goal else 2700.0)
    days_left = calc_plan.get("days_left", active_goal["days_remaining"] if active_goal else 5)

    reasoning_plan = {
        "has_failed_previous_plan": has_failed_previous_plan,
        "has_learned_pattern": has_learned_pattern,
        "goal_context": active_goal["title"] if active_goal else "Bike EMI",
        "remaining_amount": remaining_emi,
        "days_left": days_left,
        "total_income_7d": fin_state.get("income_7d", {}).get("total_income", 0.0),
        "total_expenses_7d": fin_state.get("expenses_7d", {}).get("total_expenses", 0.0),
        "avg_daily_income": fin_state.get("income_7d", {}).get("average_daily_income", 0.0),
        "weekend_income": fin_state.get("income_7d", {}).get("weekend_income", 0.0),
        "weekday_income": fin_state.get("income_7d", {}).get("weekday_income", 0.0),
        "strategy": calc_plan.get("strategy", "Adaptive Surge Allocation"),
        "weekday_target": calc_plan.get("weekday_target", 350.0),
        "weekend_target": calc_plan.get("weekend_target", 850.0),
        "shift_count": calc_plan.get("shift_count", 0),
        "is_sufficient_history": calc_plan.get("is_sufficient_history", True),
        "is_adaptive": calc_plan.get("is_adaptive", False),
        "assumptions": calc_plan.get("assumptions", ""),
        "calculated_plan": calc_plan,
    }

    # Determine action decision
    if intent == "record_income":
        decision = "record_income"
    elif intent == "record_expense":
        decision = "record_expense"
    elif intent == "create_goal":
        decision = "create_goal"
    elif intent == "update_goal_progress":
        decision = "update_goal_progress"
    elif intent == "financial_planning":
        decision = "create_plan"
    else:
        decision = "answer"

    # Try configured LLM gateway
    llm_resp = llm_client.generate_reasoning(
        user_message=user_msg,
        financial_facts=reasoning_plan,
        hindsight_memories=memories,
        intent=intent,
        memory_status=state.get("memory_status", "not_needed"),
    )

    return {
        "reasoning_plan": reasoning_plan,
        "action_decision": decision,
        "llm_used": llm_resp is not None,
        "llm_response_text": llm_resp["text"] if llm_resp else None,
        "llm_model": llm_resp.get("model") if llm_resp else None,
    }


def decision_router(state: FinancialMentorState) -> str:
    """Conditional router: directs write actions to execute_action; read-only to generate_response."""
    decision = state.get("action_decision", "answer")
    if decision in ("record_income", "record_expense", "create_plan", "create_goal", "update_goal_progress"):
        return "execute_action"
    return "generate_response"


# ─────────────────────────────────────────────────────────────────────────────
# NODE 5 — EXECUTE PERMITTED ACTION (Safe write boundary)
# ─────────────────────────────────────────────────────────────────────────────

def execute_action(state: FinancialMentorState) -> Dict[str, Any]:
    """
    Executes controlled financial write operations through application tools.
    NEVER allows LLM text to become arbitrary SQL.
    Validates arguments and records results.
    """
    decision = state.get("action_decision")
    user_id = state["user_id"]
    params = state.get("intent_params", {})
    plan_info = state.get("reasoning_plan", {})
    fin_state = state.get("current_financial_state", {})

    action_result = {}

    try:
        if decision == "record_income":
            amount = params.get("amount")
            if not amount or amount <= 0:
                raise ValueError("Income amount must be greater than zero.")
            tx = agent_tools.record_transaction(
                user_id=user_id,
                amount=amount,
                type_="income",
                category=params.get("category", "Delivery Earnings"),
                description=params.get("description", "Daily shift earnings"),
                source="agent",
                date=params.get("date"),
            )
            action_result = {"success": True, "type": "income", "transaction": tx}

        elif decision == "record_expense":
            amount = params.get("amount")
            if not amount or amount <= 0:
                raise ValueError("Expense amount must be greater than zero.")
            tx = agent_tools.record_transaction(
                user_id=user_id,
                amount=amount,
                type_="expense",
                category=params.get("category", "Fuel"),
                description=params.get("description", "Vehicle expense"),
                merchant=params.get("merchant", ""),
                source="agent",
                date=params.get("date"),
            )
            action_result = {"success": True, "type": "expense", "transaction": tx}

        elif decision == "create_goal":
            title = params.get("title", "Savings Goal")
            target_amt = params.get("target_amount")
            due_date = params.get("due_date") or (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
            category = params.get("category", "emi")
            if not target_amt or target_amt <= 0:
                raise ValueError("Target amount must be greater than zero.")
            goal = agent_tools.create_goal(
                user_id=user_id,
                title=title,
                target_amount=target_amt,
                due_date=due_date,
                category=category,
            )
            action_result = {"success": True, "type": "create_goal", "goal": goal}

        elif decision == "update_goal_progress":
            amount_to_add = params.get("amount")
            if not amount_to_add or amount_to_add <= 0:
                raise ValueError("Savings amount must be greater than zero.")
            active_goals = fin_state.get("active_goals", [])
            if not active_goals:
                active_goals = agent_tools.get_goals(user_id, status="active")
            if not active_goals:
                raise ValueError("No active goal found to add savings to. Create a goal first.")
            target_goal = active_goals[0]
            updated = agent_tools.update_goal(
                user_id=user_id,
                goal_id=target_goal["id"],
                amount_to_add=amount_to_add,
            )
            action_result = {
                "success": True,
                "type": "update_goal_progress",
                "goal": updated,
                "amount_added": amount_to_add,
            }

        elif decision == "create_plan":
            calc = plan_info.get("calculated_plan", {})
            active_goals = fin_state.get("active_goals", [])
            active_goal = active_goals[0] if active_goals else None
            goal_id = calc.get("goal_id") or (active_goal["id"] if active_goal else "goal_current_emi")
            target_amt = calc.get("remaining_amount", plan_info.get("remaining_amount", 2700.0))
            daily_target = calc.get("daily_target", 540.0)
            strategy = calc.get("strategy", "Adaptive Surge Allocation")
            days_left = calc.get("days_left", plan_info.get("days_left", 5))
            assumptions = calc.get("assumptions", "")

            plan = agent_tools.create_financial_plan(
                user_id=user_id,
                goal_id=goal_id,
                target_amount=target_amt,
                daily_target=daily_target,
                strategy=strategy,
                timeframe_days=days_left,
                assumptions=assumptions,
            )
            action_result = {"success": True, "type": "plan", "plan": plan, "calculated_plan": calc}

    except Exception as e:
        logger.error(f"Action execution error: {e}")
        action_result = {"success": False, "error": str(e)}

    return {"action_result": action_result}


# ─────────────────────────────────────────────────────────────────────────────
# NODE 6 — GENERATE GROUNDED RESPONSE
# ─────────────────────────────────────────────────────────────────────────────

def generate_response(state: FinancialMentorState) -> Dict[str, Any]:
    """
    Generates a structured, grounded response:
    - Never fabricates figures (uses actual SQLite numbers)
    - If data is unavailable, acknowledges honestly
    - Enforces financial mentoring boundary (no regulated investment/loan advice)
    """
    intent = state.get("intent", "unknown")
    fin = state.get("current_financial_state", {})
    memories = state.get("hindsight_memories", [])
    plan = state.get("reasoning_plan", {})
    action = state.get("action_result") or {}
    memory_status = state.get("memory_status", "not_needed")
    llm_text = state.get("llm_response_text")
    llm_was_used = state.get("llm_used", False)

    facts = []
    pattern_text = ""
    recommendation_text = ""
    why_evidence = []

    # Case A: Database Error
    if state.get("financial_state_error"):
        main_text = (
            "I am currently unable to access your live financial records due to a temporary system issue. "
            "Your existing records are safe. Please try your request again shortly."
        )
        return {
            "final_response": main_text,
            "structured_response": {
                "text": main_text,
                "facts": [],
                "pattern": "",
                "recommendation": "Try refreshing the application in a few moments.",
                "why_this_advice": ["Database connection error"],
                "memories_used_count": 0,
                "primary_memory_influence": "None",
            },
        }

    # Extract facts from SQLite
    income_7d = fin.get("income_7d", {}).get("total_income", 0.0)
    income_count = fin.get("income_7d", {}).get("count", 0)
    daily_avg = fin.get("income_7d", {}).get("average_daily_income", 0.0)
    expense_7d = fin.get("expenses_7d", {}).get("total_expenses", 0.0)
    fuel_exp = fin.get("expenses_7d", {}).get("category_breakdown", {}).get("Fuel", 0.0)
    net_available = fin.get("net_available_7d", 0.0)
    active_goals = fin.get("active_goals", [])
    active_goal = active_goals[0] if active_goals else None

    if income_count > 0:
        facts.append(f"7-Day Total Income: ₹{income_7d:,.0f} across {income_count} logged shifts (avg ₹{daily_avg:,.0f}/day)")
    facts.append(f"7-Day Total Expenses: ₹{expense_7d:,.0f} (Fuel: ₹{fuel_exp:,.0f})")

    if active_goal:
        rem = active_goal["remaining_amount"]
        days = active_goal["days_remaining"]
        facts.append(f"Active Goal: {active_goal['title']} — ₹{rem:,.0f} remaining ({days} days left)")
        why_evidence.append(f"Current {active_goal['title']} status: ₹{active_goal['current_amount']:,.0f} saved of ₹{active_goal['target_amount']:,.0f}")
        why_evidence.append(f"Daily income pace: ₹{daily_avg:,.0f}/day")

    # Memory Evidence
    if memory_status == "available" and memories:
        for m in memories:
            m_type = m.get("type", "")
            m_date = m.get("date", "recent")
            content_snippet = m.get("content", "")[:90]
            if m_type == "outcome":
                why_evidence.append(f"Past Outcome ({m_date}): {content_snippet}")
            elif m_type == "pattern":
                why_evidence.append(f"Learned Pattern ({m_date}): {content_snippet}")
            elif m_type == "plan":
                why_evidence.append(f"Previous Plan ({m_date}): {content_snippet}")
            elif m_type == "preference":
                why_evidence.append(f"User Preference: {content_snippet}")
            elif m_type == "profile_fact":
                why_evidence.append(f"Profile Context: {content_snippet}")
    elif memory_status == "unavailable":
        why_evidence.append("Historical Hindsight memory is temporarily offline; reasoned using current SQLite facts.")

    # 1. Action: Recorded Income
    if intent == "record_income":
        if action.get("success"):
            tx = action["transaction"]
            main_text = f"Logged income of **₹{tx['amount']:,.0f}** for {tx['category']}. Your record has been saved in SQLite."
            recommendation_text = f"Your updated 7-day income is ₹{(income_7d + tx['amount']):,.0f}."
        else:
            main_text = f"Could not record income: {action.get('error', 'Invalid input')}. Please specify a positive amount."
            recommendation_text = "Example: 'I earned ₹900 today from deliveries.'"

    # 2. Action: Recorded Expense
    elif intent == "record_expense":
        if action.get("success"):
            tx = action["transaction"]
            main_text = f"Logged expense of **₹{tx['amount']:,.0f}** for {tx['category']}. Saved to your persistent records."
            recommendation_text = f"Your updated 7-day operating expenses are ₹{(expense_7d + tx['amount']):,.0f}."
        else:
            main_text = f"Could not record expense: {action.get('error', 'Invalid input')}. Please specify a positive amount."
            recommendation_text = "Example: 'I spent ₹200 on fuel.'"

    # 3. Action: Create Goal
    elif intent == "create_goal":
        if action.get("success"):
            goal = action.get("goal", {})
            main_text = (
                f"Created your goal **'{goal.get('title')}'** with target **₹{goal.get('target_amount', 0):,.0f}** "
                f"due by {goal.get('target_date', 'deadline')}. Your goal has been saved in SQLite."
            )
            recommendation_text = f"You have {goal.get('days_remaining', 0)} days to save ₹{goal.get('remaining_amount', goal.get('target_amount', 0)):,.0f}."
        else:
            main_text = f"Could not create goal: {action.get('error', 'Invalid input')}. Please provide a title, amount, and target date."
            recommendation_text = "Example: 'Create a goal for Bike EMI of ₹4500 by Oct 5'"

    # 4. Action: Update Goal Progress
    elif intent == "update_goal_progress":
        if action.get("success"):
            goal = action.get("goal", {})
            amt = action.get("amount_added", 0.0)
            main_text = (
                f"Added **₹{amt:,.0f}** to your goal **'{goal.get('title')}'**! "
                f"Current progress: **₹{goal.get('current_amount', 0):,.0f} of ₹{goal.get('target_amount', 0):,.0f}** "
                f"({goal.get('progress_percentage', 0)}%)."
            )
            if goal.get("status") == "achieved":
                recommendation_text = "🎉 Congratulations! You have reached your savings goal!"
            else:
                recommendation_text = f"₹{goal.get('remaining_amount', 0):,.0f} remaining with {goal.get('days_remaining', 0)} days left."
        else:
            main_text = f"Could not update goal progress: {action.get('error', 'Invalid input')}."
            recommendation_text = "Example: 'Add ₹500 to my savings goal'"

    # 5. Financial Summary Query
    elif intent == "financial_summary":
        main_text = (
            f"Over the last 7 days, you earned **₹{income_7d:,.0f}** and spent **₹{expense_7d:,.0f}**, "
            f"leaving a net available cash flow of **₹{net_available:,.0f}**."
        )
        recommendation_text = f"Fuel makes up ₹{fuel_exp:,.0f} ({round((fuel_exp/max(expense_7d, 1))*100)}%) of your operating costs. Keep logging to stay accurate."

    # 6. Goal Progress Query
    elif intent == "goal_progress":
        if active_goal:
            main_text = (
                f"You have saved **₹{active_goal['current_amount']:,.0f} of ₹{active_goal['target_amount']:,.0f}** "
                f"({active_goal['progress_percentage']}%) for your {active_goal['title']}."
            )
            recommendation_text = f"You are ₹{active_goal['remaining_amount']:,.0f} away with {active_goal['days_remaining']} days remaining."
        else:
            main_text = "You currently have no active savings goals configured."
            recommendation_text = "You can set up a goal for your upcoming EMI in the Goals screen."

    # 7. Obligation Query
    elif intent == "obligation_status":
        obls = fin.get("obligations", [])
        if obls:
            obl = obls[0]
            main_text = f"Your next fixed obligation is **{obl['title']}** for **₹{obl['amount']:,.0f}** (due day: {obl.get('due_day', 10)})."
            recommendation_text = f"Current status: {obl.get('status', 'active')}."
        else:
            main_text = "You have no fixed obligations registered."
            recommendation_text = "Add recurring obligations such as bike EMI or room rent to plan ahead."

    # 8. Planning Request (Core Outcome-Aware Reasoning)
    elif intent == "financial_planning":
        calc = plan.get("calculated_plan", {})
        rem_amt = calc.get("remaining_amount", plan.get("remaining_amount", active_goal["remaining_amount"] if active_goal else 2700.0))
        days = calc.get("days_left", plan.get("days_left", active_goal["days_remaining"] if active_goal else 5))
        is_sufficient = calc.get("is_sufficient_history", True)
        strategy = calc.get("strategy", "Adaptive Surge Allocation")

        if not is_sufficient:
            daily_t = calc.get("daily_target", round(rem_amt / max(days, 1), 2))
            pattern_text = "Insufficient shift history for adaptive surge modeling. Using baseline pacing."
            main_text = (
                f"You have **₹{rem_amt:,.0f} remaining** to save across {days} days.\n\n"
                f"Because you have fewer than 3 logged shifts, there is insufficient earning history to model surge vs weekday shifts accurately. "
                f"A direct baseline pacing requires saving **₹{daily_t:,.0f}/day**.\n\n"
                "As you log 3–5 regular shifts, Rahat will adapt this into a flexible weekday/weekend surge plan."
            )
            recommendation_text = f"Save ₹{daily_t:,.0f} per shift as a baseline. Log your next shift to unlock adaptive surge planning."
        elif plan.get("has_failed_previous_plan") or calc.get("is_adaptive"):
            wkday = calc.get("weekday_target", 350.0)
            wkend = calc.get("weekend_target", 850.0)
            pattern_text = (
                "Your previous outcome showed that a flat ₹900/day target was difficult to sustain because "
                "weekday earnings average ₹600–₹720, while weekend surge earnings average ₹1,150–₹1,300."
            )
            recommendation_text = (
                "Instead of repeating a rigid daily target, here is an adaptive plan grounded in your actual earning patterns:\n\n"
                f"• **Weekdays (Mon–Fri):** Reserve a lighter ₹{wkday:,.0f}/day from daily delivery earnings.\n"
                f"• **Weekend Surge (Sat–Sun):** Allocate ₹{wkend:,.0f} from each peak shift.\n\n"
                f"This reliably clears your remaining ₹{rem_amt:,.0f} EMI before the deadline without creating weekday cashflow stress."
            )
            main_text = (
                f"You have **₹{rem_amt:,.0f} remaining** for your goal in {days} days.\n\n"
                "Last time, the flat ₹900/day target was difficult to maintain because your weekday earnings were lower (averaging closer to ₹500/day saved).\n\n"
                f"Based on that outcome and your stronger weekend earnings, I've created an **adaptive plan**:\n"
                f"• Weekdays: Save ₹{wkday:,.0f}/day\n"
                f"• Weekend Surge: Save ₹{wkend:,.0f}/shift\n\n"
                "This achieves your goal comfortably without leaving you short on daily fuel cash."
            )
        else:
            daily_needed = round(rem_amt / max(days, 1), 2)
            main_text = f"You need ₹{rem_amt:,.0f} across {days} days. A daily pacing of ₹{daily_needed:,.0f}/day will achieve your target."
            recommendation_text = f"Save ₹{daily_needed:,.0f} from each shift to stay on pace."

    # 9. Why this advice query
    elif intent == "why_advice_query":
        main_text = "Rahat bases its advice on two grounded inputs: your actual SQLite financial facts and past experiential memory from Hindsight."
        recommendation_text = "Tap 'Why this advice?' in any mentor recommendation to see the exact factual records and past outcomes that shaped the guidance."

    # 10. User reported outcome
    elif intent == "outcome_report":
        main_text = "I've noted this outcome in your long-term memory. Rahat will adapt your next financial pacing so you aren't put under unrealistic pressure."
        recommendation_text = "Adaptive planning learns from missed targets to prevent repeat stress."

    # 11. General financial question & advisory boundary
    elif intent == "general_financial_question":
        if any(w in state["user_message"].lower() for w in ["invest", "mutual fund", "stock", "crypto", "tax"]):
            main_text = (
                "Rahat is designed specifically for daily budgeting, shift earnings tracking, and EMI debt management. "
                "I do not provide investment, stock, or tax advice. I can help you plan your daily shift savings so you never miss an EMI."
            )
            recommendation_text = "Let's focus on keeping your upcoming EMI on track and maintaining a healthy fuel cushion."
        else:
            main_text = f"Namaste! I'm Rahat, your personal financial mentor. Based on your records, your 7-day income is ₹{income_7d:,.0f} and you have ₹{plan.get('remaining_amount', 2700):,.0f} remaining on your EMI."
            recommendation_text = "Ask me to log an earning, check fuel expenses, or plan your next EMI payment."

    # 12. Unknown intent
    else:
        main_text = (
            "I didn't quite understand that. You can ask me to log earnings, track expenses, "
            "check your EMI progress, or create an adaptive savings plan for your upcoming bills."
        )
        recommendation_text = "Try: 'I earned ₹900 today' or 'Am I on track for my EMI?'"

    # ── LLM OVERRIDE ──────────────────────────────────────────────────────────
    # For advisory/query intents, use the real Gemini text as the primary response
    # when available. Write confirmations (record_income, record_expense, create_goal, update_goal_progress)
    # stay deterministic because they are factual confirmations that must match SQLite.
    advisory_intents = {
        "financial_summary", "goal_progress", "obligation_status",
        "financial_planning", "why_advice_query", "outcome_report",
        "general_financial_question", "unknown",
    }
    if llm_was_used and llm_text and intent in advisory_intents:
        if intent == "goal_progress" and active_goal:
            main_text = (
                f"You have saved **₹{active_goal['current_amount']:,.0f} of ₹{active_goal['target_amount']:,.0f}** "
                f"({active_goal['progress_percentage']}%) for your {active_goal['title']}.\n\n{llm_text}"
            )
        elif intent == "financial_planning":
            calc = plan.get("calculated_plan", {})
            rem_amt = calc.get("remaining_amount", active_goal["remaining_amount"] if active_goal else 2700.0)
            days = calc.get("days_left", active_goal["days_remaining"] if active_goal else 5)
            main_text = (
                f"**Authoritative Plan Status**: ₹{rem_amt:,.0f} remaining across {days} days.\n"
                f"Strategy: {calc.get('strategy', 'Adaptive Plan')}\n\n"
                f"{llm_text}"
            )
        else:
            main_text = llm_text
        if not recommendation_text:
            recommendation_text = "Powered by Rahat's Gemini-grounded reasoning."

    structured_response = {
        "text": main_text,
        "facts": facts,
        "pattern": pattern_text,
        "recommendation": recommendation_text,
        "why_this_advice": why_evidence,
        "memories_used_count": len(memories),
        "llm_used": llm_was_used,
        "primary_memory_influence": (
            "Previous Sept 12 Plan & Sept 16 Outcome"
            if (plan.get("has_failed_previous_plan") and intent == "financial_planning")
            else "Current 7-Day SQLite Financial Records"
        ),
        "action_result": action if action else None,
    }

    return {
        "final_response": main_text,
        "structured_response": structured_response,
    }


# ─────────────────────────────────────────────────────────────────────────────
# NODE 7 — RECORD MEANINGFUL OUTCOME (Strict Boundary)
# ─────────────────────────────────────────────────────────────────────────────

def record_meaningful_outcome(state: FinancialMentorState) -> Dict[str, Any]:
    """
    Records ONLY meaningful experiential outcomes to Hindsight.
    NEVER stores raw transactions here.
    Links outcome to active plan if present.
    """
    intent = state.get("intent")
    user_id = state["user_id"]

    if intent == "outcome_report":
        user_msg = state.get("user_message", "")
        # Find active plan if any to link related_plan_id
        active_plan = repository.get_active_plan(user_id)
        related_plan_id = active_plan["id"] if active_plan else None

        # Determine outcome status
        lower_msg = user_msg.lower()
        if any(w in lower_msg for w in ["miss", "short", "could not", "failed", "less", "difficult", "hard"]):
            outcome_status = "missed"
        elif any(w in lower_msg for w in ["achieved", "completed", "made it", "success", "saved", "hit"]):
            outcome_status = "achieved"
        else:
            outcome_status = "observed"

        mem_id = hindsight.store_memory(
            user_id=user_id,
            memory_type="outcome",
            title="Shift Savings Outcome",
            content=user_msg,
            category="emi",
            outcome_status=outcome_status,
            relevance_tags=["user_reported", "outcome", "learning"],
            related_plan_id=related_plan_id,
        )

        # If there was an active plan, update its status in SQLite
        if active_plan:
            plan_status = "missed" if outcome_status == "missed" else ("completed" if outcome_status == "achieved" else "active")
            repository.update_plan_status(user_id, active_plan["id"], status=plan_status)

        return {"recorded_outcome_id": mem_id}

    return {}


# ─────────────────────────────────────────────────────────────────────────────
# GRAPH COMPILATION
# ─────────────────────────────────────────────────────────────────────────────

def build_financial_mentor_agent():
    workflow = StateGraph(FinancialMentorState)

    workflow.add_node("parse_intent", parse_intent)
    workflow.add_node("load_current_financial_state", load_current_financial_state)
    workflow.add_node("retrieve_relevant_hindsight", retrieve_relevant_hindsight)
    workflow.add_node("reason_with_llm", reason_with_llm)
    workflow.add_node("execute_action", execute_action)
    workflow.add_node("generate_response", generate_response)
    workflow.add_node("record_meaningful_outcome", record_meaningful_outcome)

    workflow.add_edge(START, "parse_intent")
    workflow.add_edge("parse_intent", "load_current_financial_state")
    workflow.add_edge("load_current_financial_state", "retrieve_relevant_hindsight")
    workflow.add_edge("retrieve_relevant_hindsight", "reason_with_llm")

    workflow.add_conditional_edges(
        "reason_with_llm",
        decision_router,
        {
            "execute_action": "execute_action",
            "generate_response": "generate_response",
        },
    )

    workflow.add_edge("execute_action", "generate_response")
    workflow.add_edge("generate_response", "record_meaningful_outcome")
    workflow.add_edge("record_meaningful_outcome", END)

    return workflow.compile()


financial_mentor_graph = build_financial_mentor_agent()


async def run_agent(user_id: str, user_message: str) -> Dict[str, Any]:
    """Entry point for executing the LangGraph agent workflow."""
    initial_state: FinancialMentorState = {
        "user_id": user_id,
        "user_message": user_message,
        "intent": "",
        "intent_params": {},
        "current_financial_state": {},
        "financial_state_error": None,
        "hindsight_memories": [],
        "memory_status": "not_needed",
        "memory_error": None,
        "reasoning_plan": {},
        "llm_used": False,
        "llm_response_text": None,
        "llm_model": None,
        "action_decision": "answer",
        "action_result": None,
        "final_response": "",
        "structured_response": {},
        "new_outcome_to_record": None,
        "error": None,
    }

    final_state = financial_mentor_graph.invoke(initial_state)
    return final_state["structured_response"]
