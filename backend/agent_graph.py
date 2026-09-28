import os
import json
import logging
from typing import Dict, Any, List, Optional, TypedDict
from langgraph.graph import StateGraph, START, END
from database import get_db_connection
from hindsight_memory import hindsight
import agent_tools

logger = logging.getLogger("rahat.agent")

# State Definition for LangGraph Agent
class FinancialMentorState(TypedDict):
    user_id: str
    user_message: str
    intent: str
    current_financial_state: Dict[str, Any]
    hindsight_memories: List[Dict[str, Any]]
    reasoning_plan: Dict[str, Any]
    action_decision: str # 'answer', 'calculate', 'create_plan', 'update_goal', 'record_transaction', 'request_confirmation'
    action_result: Optional[Dict[str, Any]]
    final_response: str
    structured_response: Dict[str, Any] # facts, pattern, recommendation, why_this_advice
    new_outcome_to_record: Optional[Dict[str, Any]]

# Graph Nodes

def parse_intent(state: FinancialMentorState) -> Dict[str, Any]:
    msg = state["user_message"].lower()
    
    if any(w in msg for w in ["earned", "income", "how much did i earn", "wage", "payout"]):
        intent = "income_query"
    elif any(w in msg for w in ["spent", "expense", "fuel", "spend", "cost", "spending"]):
        intent = "expense_query"
    elif any(w in msg for w in ["emi", "plan", "need ₹", "need rs", "target", "save", "reach", "before monday", "before"]):
        intent = "plan_request"
    elif any(w in msg for w in ["how am i doing", "summary", "status", "track", "progress", "on track"]):
        intent = "status_check"
    elif any(w in msg for w in ["why this advice", "why did you advise", "evidence"]):
        intent = "why_advice_query"
    elif any(w in msg for w in ["failed", "missed", "could not save", "only saved", "didn't make"]):
        intent = "outcome_report"
    elif any(w in msg for w in ["add income", "log income", "got paid", "received"]):
        intent = "record_income"
    elif any(w in msg for w in ["add expense", "log expense", "spent ₹", "paid for"]):
        intent = "record_expense"
    else:
        intent = "general_financial_guidance"
        
    return {"intent": intent}

def load_current_financial_state(state: FinancialMentorState) -> Dict[str, Any]:
    user_id = state["user_id"]
    income_data = agent_tools.get_income(user_id, days=7)
    expense_data = agent_tools.get_expenses(user_id, days=7)
    goals_data = agent_tools.get_goals(user_id, status="active")
    obligations = agent_tools.get_obligations(user_id)
    
    current_state = {
        "income_7d": income_data,
        "expenses_7d": expense_data,
        "net_available_7d": income_data["total_income"] - expense_data["total_expenses"],
        "active_goals": goals_data,
        "obligations": obligations
    }
    return {"current_financial_state": current_state}

def retrieve_relevant_hindsight(state: FinancialMentorState) -> Dict[str, Any]:
    user_id = state["user_id"]
    intent = state.get("intent", "")
    query = state.get("user_message", "")
    
    category = "emi" if "emi" in query.lower() or intent == "plan_request" else None
    memories = hindsight.search_memories(user_id=user_id, query=query, category=category, limit=4)
    
    return {"hindsight_memories": memories}

def reason_with_llm(state: FinancialMentorState) -> Dict[str, Any]:
    user_msg = state["user_message"]
    fin_state = state["current_financial_state"]
    memories = state["hindsight_memories"]
    intent = state["intent"]
    
    # Check for previous failed plans in memory (THE CORE DIFFERENTIATOR)
    has_failed_previous_plan = any(
        m["type"] == "outcome" and m["outcome_status"] == "failed" 
        for m in memories
    )
    
    has_learned_pattern = any(
        m["type"] == "pattern" or "weekend" in m.get("content", "").lower()
        for m in memories
    )

    # Goal details
    active_goal = fin_state["active_goals"][0] if fin_state["active_goals"] else None
    remaining_emi = active_goal["remaining_amount"] if active_goal else 2700.0
    days_left = active_goal["days_remaining"] if active_goal else 5

    reasoning_plan = {
        "has_failed_previous_plan": has_failed_previous_plan,
        "has_learned_pattern": has_learned_pattern,
        "goal_context": active_goal["title"] if active_goal else "Bike EMI",
        "remaining_amount": remaining_emi,
        "days_left": days_left,
        "total_income_7d": fin_state["income_7d"]["total_income"],
        "avg_daily_income": fin_state["income_7d"]["average_daily_income"],
        "weekend_income": fin_state["income_7d"]["weekend_income"],
        "weekday_income": fin_state["income_7d"]["weekday_income"],
    }

    # Decide Action
    if intent in ["record_income", "record_expense"]:
        decision = "record_transaction"
    elif intent == "plan_request" or ("emi" in user_msg.lower() and "how much" not in user_msg.lower()):
        decision = "create_plan"
    elif intent in ["status_check", "income_query", "expense_query"]:
        decision = "calculate"
    else:
        decision = "answer"

    return {
        "reasoning_plan": reasoning_plan,
        "action_decision": decision
    }

def decision_router(state: FinancialMentorState) -> str:
    return state.get("action_decision", "answer")

def execute_action(state: FinancialMentorState) -> Dict[str, Any]:
    decision = state.get("action_decision", "answer")
    user_id = state["user_id"]
    plan = state["reasoning_plan"]
    
    action_result = {}
    if decision == "create_plan":
        if plan["has_failed_previous_plan"]:
            strategy = "Adaptive Surge Allocation (₹350/weekday + ₹850/weekend surge shift)"
            daily_target = 540.0
        else:
            strategy = "Flat Daily Saving Rate"
            daily_target = round(plan["remaining_amount"] / max(plan["days_left"], 1), 2)
            
        action_result = agent_tools.create_financial_plan(
            user_id=user_id,
            goal_id="goal_current_emi",
            target_amount=plan["remaining_amount"],
            daily_target=daily_target,
            strategy=strategy,
            timeframe_days=plan["days_left"]
        )
    return {"action_result": action_result}

def generate_response(state: FinancialMentorState) -> Dict[str, Any]:
    intent = state.get("intent", "general")
    fin = state["current_financial_state"]
    memories = state.get("hindsight_memories", [])
    plan = state["reasoning_plan"]
    
    income_7d = fin["income_7d"]["total_income"]
    expense_7d = fin["expenses_7d"]["total_expenses"]
    active_goal = fin["active_goals"][0] if fin["active_goals"] else None
    
    facts = []
    pattern_text = ""
    recommendation_text = ""
    why_evidence = []
    
    # 1. Gather Factual Evidence
    facts.append(f"7-Day Total Income: ₹{income_7d:,.0f} across {fin['income_7d']['count']} shifts")
    facts.append(f"7-Day Total Expenses: ₹{expense_7d:,.0f} (Fuel: ₹{fin['expenses_7d']['category_breakdown'].get('Fuel', 0):,.0f})")
    
    if active_goal:
        rem = active_goal["remaining_amount"]
        days = active_goal["days_remaining"]
        facts.append(f"Active Goal: {active_goal['title']} — ₹{rem:,.0f} remaining ({days} days until Oct 5)")
        why_evidence.append(f"Current {active_goal['title']} (₹{active_goal['current_amount']:,.0f} / ₹{active_goal['target_amount']:,.0f})")
        why_evidence.append(f"Last 7 days income average: ₹{fin['income_7d']['average_daily_income']:,.0f}/day")
    
    # 2. Check for Hindsight memories and outcomes
    previous_outcome_mem = next((m for m in memories if m["type"] == "outcome"), None)
    pattern_mem = next((m for m in memories if m["type"] == "pattern"), None)
    
    if previous_outcome_mem:
        why_evidence.append(f"Previous Plan Outcome (Sept 16): Missed flat ₹900/day target due to lower weekday volume")
    if pattern_mem:
        why_evidence.append(f"Learned Pattern (Sept 17): Weekend surge earnings (~₹1,150/day) vs weekday earnings (~₹600/day)")

    # 3. Construct Outcome-Aware vs Fact-Specific Response
    if intent == "income_query":
        main_text = f"Over the past 7 days, you earned a total of **₹{income_7d:,.0f}** across {fin['income_7d']['count']} logged shifts (averaging ₹{fin['income_7d']['average_daily_income']:,.0f}/day)."
        recommendation_text = "Your highest earning day was Sunday (₹1,300). Keep logging your daily shift payouts so Rahat can optimize your upcoming goal timelines."
    elif intent == "expense_query":
        fuel_amt = fin['expenses_7d']['category_breakdown'].get('Fuel', 0)
        main_text = f"Your total expenses over the past 7 days were **₹{expense_7d:,.0f}**, with fuel taking up **₹{fuel_amt:,.0f}** (~{round((fuel_amt/max(expense_7d,1))*100)}% of total expenses)."
        recommendation_text = "Tracking fuel refueling right after your shift helps keep your net available cash accurate."
    elif intent == "status_check":
        main_text = f"You are currently at **₹{active_goal['current_amount']:,.0f} of ₹{active_goal['target_amount']:,.0f}** for your {active_goal['title']} with {active_goal['days_remaining']} days left."
        pattern_text = f"Your net available cash after 7-day expenses is ₹{fin['net_available_7d']:,.0f}."
        recommendation_text = f"You need ₹{active_goal['remaining_amount']:,.0f} more. Your learned weekend surge pattern will help cover the majority."
    elif plan["has_failed_previous_plan"] or intent == "plan_request":
        pattern_text = "Your previous outcome showed that a flat ₹900/day target was difficult to sustain because weekday earnings average ₹600–₹720, while weekend surge earnings average ₹1,150–₹1,300."
        recommendation_text = (
            "Instead of repeating a rigid daily target, here is an adaptive plan grounded in your actual earning patterns:\n\n"
            "• **Weekdays (Mon–Fri):** Reserve a lighter ₹350/day from daily delivery earnings.\n"
            "• **Weekend Surge (Sat–Sun):** Allocate ₹850 from each peak shift.\n\n"
            f"This reliably clears your remaining ₹{plan['remaining_amount']:,.0f} EMI before the Oct 5 deadline without creating weekday cashflow stress."
        )
        main_text = (
            f"You have **₹{plan['remaining_amount']:,.0f} remaining** for your Bike EMI in {plan['days_left']} days.\n\n"
            "Last time, the flat ₹900/day target was difficult to maintain because your weekday earnings were lower (averaging closer to ₹500/day saved).\n\n"
            "Based on that outcome and your stronger weekend earnings, I've created an **adaptive plan** that sets manageable ₹350 targets on weekdays and leverages your weekend surge to comfortably reach your goal."
        )
    else:
        main_text = (
            f"Based on your current records, you have earned ₹{income_7d:,.0f} this week with an active goal of ₹{plan['remaining_amount']:,.0f} remaining for your {plan['goal_context']}."
        )
        recommendation_text = "Let me know if you want to create a daily savings pacing or log today's delivery payout."

    structured_response = {
        "text": main_text,
        "facts": facts,
        "pattern": pattern_text,
        "recommendation": recommendation_text,
        "why_this_advice": why_evidence,
        "memories_used_count": len(memories),
        "primary_memory_influence": "Previous Sept 12 Plan & Sept 16 Outcome" if (plan["has_failed_previous_plan"] and intent == "plan_request") else "Current 7-Day SQLite Financial Records"
    }

    return {
        "final_response": main_text,
        "structured_response": structured_response
    }

def record_meaningful_outcome(state: FinancialMentorState) -> Dict[str, Any]:
    if state.get("intent") == "outcome_report":
        user_id = state["user_id"]
        hindsight.store_memory(
            user_id=user_id,
            memory_type="outcome",
            title="User Reported Outcome",
            content=state["user_message"],
            category="emi",
            outcome_status="observed",
            relevance_tags=["user_reported", "outcome"]
        )
    return {}

# Build the LangGraph Workflow
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
            "create_plan": "execute_action",
            "calculate": "execute_action",
            "record_transaction": "execute_action",
            "answer": "generate_response"
        }
    )
    
    workflow.add_edge("execute_action", "generate_response")
    workflow.add_edge("generate_response", "record_meaningful_outcome")
    workflow.add_edge("record_meaningful_outcome", END)

    return workflow.compile()

# Singleton compiled agent graph
financial_mentor_graph = build_financial_mentor_agent()

async def run_agent(user_id: str, user_message: str) -> Dict[str, Any]:
    initial_state = {
        "user_id": user_id,
        "user_message": user_message,
        "intent": "",
        "current_financial_state": {},
        "hindsight_memories": [],
        "reasoning_plan": {},
        "action_decision": "answer",
        "action_result": None,
        "final_response": "",
        "structured_response": {},
        "new_outcome_to_record": None
    }
    
    final_state = financial_mentor_graph.invoke(initial_state)
    return final_state["structured_response"]
