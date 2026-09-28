from fastapi import APIRouter, Query
from app.db import repository

router = APIRouter(prefix="/insights", tags=["Insights & Analytics"])


@router.get("")
def get_insights(user_id: str = Query("demo_user")):
    """
    Returns computed insights from SQLite financial data.
    The Flutter InsightsScreen reads these fields directly to render dynamic cards.
    All numbers are calculated from live SQLite data — never hardcoded.
    """
    income = repository.get_income_records(user_id, 7)
    expenses = repository.get_expense_records(user_id, 7)
    goals = repository.get_active_goals(user_id, "active")

    active_goal = goals[0] if goals else None

    # Flat fields consumed by Flutter InsightsScreen
    response = {
        # Income fields
        "total_income_7d": income["total_income"],
        "weekend_income_7d": income["weekend_income"],
        "weekday_income_7d": income["weekday_income"],
        "daily_avg_income_7d": income["average_daily_income"],

        # Expense fields
        "total_expenses_7d": expenses["total_expenses"],
        "expense_category_breakdown_7d": expenses["category_breakdown"],

        # Goal fields (null-safe)
        "active_goal_title": active_goal["title"] if active_goal else None,
        "goal_progress_percent": active_goal["progress_percentage"] if active_goal else 0.0,
        "goal_remaining_amount": active_goal["remaining_amount"] if active_goal else 0.0,
        "goal_days_remaining": active_goal["days_remaining"] if active_goal else 0,
        "goal_target_amount": active_goal["target_amount"] if active_goal else 0.0,
        "goal_current_amount": active_goal["current_amount"] if active_goal else 0.0,

        # Computed narrative items (for any consumer that wants pre-built insight cards)
        "insight_cards": _build_insight_cards(income, expenses, active_goal),
    }
    return response


def _build_insight_cards(income: dict, expenses: dict, active_goal) -> list:
    cards = []

    if income["weekend_income"] > 0:
        ratio = round((income["weekend_income"] / max(income["total_income"], 0.01)) * 100)
        cards.append({
            "id": "ins_weekend",
            "type": "positive",
            "title": "Weekend Surge Advantage",
            "description": (
                f"Weekend earnings contributed {ratio}% of your 7-day total. "
                "Saturday and Sunday shifts consistently generate higher per-hour returns."
            ),
            "metric": f"₹{income['weekend_income']:,.0f} on Sat-Sun",
        })

    if expenses["total_expenses"] > 0 and expenses["category_breakdown"]:
        top_cat = max(expenses["category_breakdown"], key=lambda k: expenses["category_breakdown"][k])
        top_amt = expenses["category_breakdown"][top_cat]
        exp_pct = round((top_amt / max(expenses["total_expenses"], 0.01)) * 100)
        cards.append({
            "id": "ins_expense",
            "type": "neutral",
            "title": f"{top_cat} Spend Track",
            "description": (
                f"{top_cat} represents ₹{top_amt:,.0f} ({exp_pct}%) of your operating costs "
                "over the last 7 days."
            ),
            "metric": f"₹{top_amt:,.0f} {top_cat}",
        })

    if active_goal:
        cards.append({
            "id": "ins_goal",
            "type": "warning" if active_goal["days_remaining"] <= 5 else "positive",
            "title": f"{active_goal['title']} Pace",
            "description": (
                f"You are ₹{active_goal['remaining_amount']:,.0f} away from your target "
                f"with {active_goal['days_remaining']} days remaining."
            ),
            "metric": f"₹{active_goal['remaining_amount']:,.0f} remaining",
        })

    if income["average_daily_income"] > 0:
        cards.append({
            "id": "ins_daily_avg",
            "type": "neutral",
            "title": "Daily Earning Pace",
            "description": (
                f"Your 7-day daily average is ₹{income['average_daily_income']:,.0f}. "
                "Focus on peak-hour shifts to improve your daily pace."
            ),
            "metric": f"₹{income['average_daily_income']:,.0f}/day avg",
        })

    return cards
