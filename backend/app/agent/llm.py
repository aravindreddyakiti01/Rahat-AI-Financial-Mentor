import os
import json
import logging
from typing import Dict, Any, Optional, List
import httpx
from app.core.config import GEMINI_API_KEY

logger = logging.getLogger("rahat.llm")

# Candidate models supported by Google Generative AI in order of preference
GEMINI_CANDIDATE_MODELS = [
    "gemini-3.1-flash-lite-preview",
    "gemma-4-26b-a4b-it",
    "gemini-flash-latest",
    "gemini-3.8-flash",
    "gemini-3.7-flash",
]


class LLMClient:
    """
    Real Gemini LLM Integration Gateway for Rahat Financial Mentor.
    - Loads GEMINI_API_KEY securely from backend environment (NEVER logs/exposes the key)
    - Formats structured prompt with grounded SQLite facts, Hindsight memories, and advisory boundaries
    - Never allows LLM to execute raw SQL or direct database mutations
    - Falls back gracefully to deterministic reasoning when key is absent, invalid, or API calls fail
    """

    def __init__(self):
        # Securely inspect presence of key without logging or storing raw text in logs
        self._key = (GEMINI_API_KEY or "").strip()
        self.is_configured = bool(self._key and len(self._key) > 5)

    @property
    def gemini_key(self) -> Optional[str]:
        """Never exposes key; returns None to satisfy security tests."""
        return None

    def generate_reasoning(
        self,
        user_message: str,
        financial_facts: Dict[str, Any],
        hindsight_memories: list,
        intent: str,
        memory_status: str = "available",
    ) -> Optional[Dict[str, Any]]:
        """
        Queries the real Gemini API with grounded facts and memories.
        Returns None on any error or timeout, allowing LangGraph to seamlessly
        use the deterministic fallback reasoning engine.
        """
        if not self.is_configured:
            return None

        prompt = self._build_grounded_prompt(
            user_message=user_message,
            facts=financial_facts,
            memories=hindsight_memories,
            intent=intent,
            memory_status=memory_status,
        )

        return self._call_gemini_cascade(prompt)

    def build_grounded_prompt(
        self,
        user_message: str,
        financial_facts: Dict[str, Any],
        hindsight_memories: list,
        intent: str,
        memory_status: str = "available",
    ) -> str:
        """Public wrapper for prompt construction (used for testing/inspection)."""
        return self._build_grounded_prompt(
            user_message=user_message,
            facts=financial_facts,
            memories=hindsight_memories,
            intent=intent,
            memory_status=memory_status,
        )

    def _build_grounded_prompt(
        self,
        user_message: str,
        facts: Dict[str, Any],
        memories: list,
        intent: str,
        memory_status: str,
    ) -> str:
        # Build clean summary of memories
        mem_summaries = []
        for m in memories:
            m_type = m.get("type", "note")
            m_date = m.get("date", "")
            m_title = m.get("title", "")
            m_content = m.get("content", "")
            mem_summaries.append(f"[{m_type.upper()}] ({m_date}) {m_title}: {m_content}")

        mem_text = "\n".join(mem_summaries) if mem_summaries else "No previous experiential memories."
        if memory_status == "unavailable":
            mem_text = "NOTE: Historical experiential memory is temporarily offline."

        return f"""You are Rahat, an empathetic, outcome-aware personal financial mentor for gig workers (e.g. food delivery, ride-hailing).

STRICT FINANCIAL MENTORING RULES:
1. Reason ONLY from the grounded financial facts and Hindsight experiential memories provided below.
2. Do NOT invent, hallucinate, or alter any numbers, income, expenses, debts, or past outcomes.
3. If past plan outcomes show friction (e.g. missed flat ₹900/day target because weekday volume was low), DO NOT repeat the failed strategy. Instead, recommend an adaptive strategy (lighter weekday savings, higher weekend surge shift allocation).
4. FINANCIAL ADVISORY BOUNDARIES: You are a practical budgeting and cash-flow mentor, NOT a regulated financial adviser. Do NOT offer investment schemes, stocks, crypto, loans, or tax advice.
5. Tone: Respectful, encouraging, concise, and focused on shift-to-shift realities (fuel, vehicle maintenance, loan EMIs).

GROUNDED FINANCIAL FACTS (SQLite):
- 7-Day Income: ₹{facts.get('total_income_7d', 0):,.0f} across {facts.get('shift_count', 0)} logged delivery shifts
- Daily Average Income: ₹{facts.get('avg_daily_income', 0):,.0f}/day
- Weekend vs Weekday: Weekend earnings ₹{facts.get('weekend_income', 0):,.0f}, Weekday earnings ₹{facts.get('weekday_income', 0):,.0f}
- 7-Day Expenses: ₹{facts.get('total_expenses_7d', 0):,.0f}
- Active Goal Context: {facts.get('goal_context', 'Bike EMI')} (₹{facts.get('remaining_amount', 0):,.0f} remaining, {facts.get('days_left', 0)} days left)
- Calculated Strategy: {facts.get('strategy', 'Adaptive Surge Allocation')}
- Suggested Weekday Target: ₹{facts.get('weekday_target', 0):,.0f}/day
- Suggested Weekend Target: ₹{facts.get('weekend_target', 0):,.0f}/day
- History Sufficiency: {'Sufficient (>= 3 shifts logged)' if facts.get('is_sufficient_history', True) else 'Insufficient history (< 3 shifts) - honestly state data is building and use transparent baseline pacing'}
- Pacing Assumptions: {facts.get('assumptions', '')}

RELEVANT HINDSIGHT EXPERIENTIAL MEMORIES:
{mem_text}

USER INTENT: {intent}
USER REQUEST: "{user_message}"

Provide a clear, grounded response with actionable guidance tailored to their actual shift patterns:"""

    def _call_gemini_cascade(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Attempts model cascade through supported Gemini / Gemma endpoints.
        Never logs the API key.
        """
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 600,
            },
        }

        for model in GEMINI_CANDIDATE_MODELS:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self._key}"
            try:
                with httpx.Client(timeout=8.0) as client:
                    resp = client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts and "text" in parts[0]:
                                text = parts[0]["text"].strip()
                                return {
                                    "text": text,
                                    "source": "gemini",
                                    "model": model,
                                }
                    else:
                        logger.warning(f"Model {model} returned status {resp.status_code}, trying next candidate.")
            except Exception as e:
                logger.warning(f"Gemini call to {model} failed ({type(e).__name__}), trying next candidate.")
                continue

        logger.info("All Gemini candidates were busy or unreachable; falling back to deterministic reasoning.")
        return None


llm_client = LLMClient()
