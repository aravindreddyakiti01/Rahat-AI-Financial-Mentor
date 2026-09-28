from fastapi import APIRouter, HTTPException, Query
from app.db import repository
from app.schemas.schemas import TransactionCreateRequest

router = APIRouter(prefix="/finance", tags=["Finance & Transactions"])


# ─── Summary ─────────────────────────────────────────────────────────────────

@router.get("/summary")
def get_finance_summary(
    user_id: str = Query("demo_user"),
    range: str = Query("7d", description="'today' | '7d' | 'month'"),
):
    """
    Returns financial summary from SQLite for the given range.
    Includes income, expenses, net cash flow, active goal, and obligations.
    """
    allowed_ranges = {"today", "7d", "month"}
    if range not in allowed_ranges:
        raise HTTPException(status_code=422, detail=f"range must be one of {allowed_ranges}")
    return repository.get_financial_summary(user_id, range_type=range)


# Keep backward-compatible separate endpoints
@router.get("/summary/today")
def get_summary_today(user_id: str = Query("demo_user")):
    return repository.get_financial_summary(user_id, range_type="today")


@router.get("/summary/month")
def get_summary_month(user_id: str = Query("demo_user")):
    return repository.get_financial_summary(user_id, range_type="month")


# ─── Transactions ─────────────────────────────────────────────────────────────

@router.get("/transactions")
def get_transactions(user_id: str = Query("demo_user"), limit: int = Query(20, ge=1, le=100)):
    return repository.get_recent_transactions(user_id, limit)


@router.get("/transactions/{tx_id}")
def get_transaction(tx_id: str, user_id: str = Query("demo_user")):
    tx = repository.get_transaction_by_id(user_id, tx_id)
    if not tx:
        raise HTTPException(status_code=404, detail=f"Transaction '{tx_id}' not found")
    return tx


@router.post("/income", status_code=201)
def add_income(req: TransactionCreateRequest, user_id: str = Query("demo_user")):
    """Record an income transaction. Amount must be > 0."""
    return repository.record_transaction_db(
        user_id=user_id,
        amount=req.amount,
        type_="income",
        category=req.category or "Delivery Earnings",
        description=req.description or "",
        source=req.source or "manual",
        date=req.date,
        note=req.note or "",
        merchant=req.merchant or "",
    )


@router.post("/expense", status_code=201)
def add_expense(req: TransactionCreateRequest, user_id: str = Query("demo_user")):
    """Record an expense transaction. Amount must be > 0."""
    return repository.record_transaction_db(
        user_id=user_id,
        amount=req.amount,
        type_="expense",
        category=req.category or "Fuel",
        description=req.description or "",
        source=req.source or "manual",
        date=req.date,
        note=req.note or "",
        merchant=req.merchant or "",
    )


@router.delete("/transactions/{tx_id}")
def delete_transaction(tx_id: str, user_id: str = Query("demo_user")):
    """Delete a transaction. Returns 404 if not found."""
    deleted = repository.delete_transaction_db(user_id, tx_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Transaction '{tx_id}' not found")
    return {"deleted": True, "id": tx_id}
