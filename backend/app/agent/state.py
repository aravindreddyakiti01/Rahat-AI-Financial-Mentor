from typing import Dict, Any, List, Optional, TypedDict


class FinancialMentorState(TypedDict, total=False):
    """
    Strongly typed LangGraph state for the Rahat Financial Mentor Agent workflow.
    Carries execution state across graph nodes without storing persistent data in state.
    """
    user_id: str
    user_message: str

    # Intent understanding
    intent: str  # 'record_income', 'record_expense', 'financial_summary', 'goal_progress',
                 # 'obligation_status', 'financial_planning', 'why_advice_query',
                 # 'outcome_report', 'general_financial_question', 'unknown'
    intent_params: Dict[str, Any]  # extracted amount, category, description, date, merchant, etc.

    # Financial Facts (retrieved from SQLite via repository)
    current_financial_state: Dict[str, Any]
    financial_state_error: Optional[str]

    # Experiential Memory (retrieved from Hindsight)
    hindsight_memories: List[Dict[str, Any]]
    memory_status: str  # 'available', 'no_memories_found', 'unavailable'
    memory_error: Optional[str]

    # Reasoning
    reasoning_plan: Dict[str, Any]
    llm_used: bool
    llm_response_text: Optional[str]  # Real LLM text when Gemini responds successfully
    llm_model: Optional[str]  # Which model produced the response (e.g. 'gemini-3.8-flash')

    # Actions
    action_decision: str  # 'answer', 'record_income', 'record_expense', 'create_plan', 'handle_error'
    action_result: Optional[Dict[str, Any]]

    # Responses
    final_response: str
    structured_response: Dict[str, Any]

    # Meaningful Outcome to persist in Hindsight
    new_outcome_to_record: Optional[Dict[str, Any]]

    # Global workflow errors
    error: Optional[str]
