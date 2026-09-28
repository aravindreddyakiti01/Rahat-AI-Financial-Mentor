from typing import List, Optional
from pydantic import BaseModel, field_validator, model_validator
from datetime import datetime


# ─────────────────────────────────────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────────────────────────────────────

class UserSignupRequest(BaseModel):
    name: str
    email: str
    password: str
    role: Optional[str] = "Delivery"
    pay_frequency: Optional[str] = "Daily"
    primary_obligation: Optional[str] = "Bike EMI"

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name must not be empty")
        return v.strip()

    @field_validator("email")
    @classmethod
    def email_not_empty(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("Invalid email address")
        return v.strip().lower()


class UserLoginRequest(BaseModel):
    email: str
    password: str


# ─────────────────────────────────────────────────────────────────────────────
# TRANSACTIONS
# ─────────────────────────────────────────────────────────────────────────────

class TransactionCreateRequest(BaseModel):
    amount: float
    category: str
    description: Optional[str] = ""
    note: Optional[str] = ""
    merchant: Optional[str] = ""
    date: Optional[str] = None
    source: Optional[str] = "manual"

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Amount must be greater than zero")
        return round(v, 2)

    @field_validator("category")
    @classmethod
    def category_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Category must not be empty")
        return v.strip()

    @field_validator("date")
    @classmethod
    def date_valid_format(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("Date must be in YYYY-MM-DD format")
        return v


# ─────────────────────────────────────────────────────────────────────────────
# GOALS
# ─────────────────────────────────────────────────────────────────────────────

class GoalCreateRequest(BaseModel):
    title: str
    target_amount: float
    due_date: str
    category: Optional[str] = "emi"
    initial_amount: Optional[float] = 0.0

    @field_validator("target_amount")
    @classmethod
    def target_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Target amount must be greater than zero")
        return round(v, 2)

    @field_validator("due_date")
    @classmethod
    def due_date_valid(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("due_date must be in YYYY-MM-DD format")
        return v

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Title must not be empty")
        return v.strip()

    @field_validator("initial_amount")
    @classmethod
    def initial_non_negative(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError("Initial amount must be >= 0")
        return round(v, 2) if v is not None else 0.0


class GoalUpdateRequest(BaseModel):
    amount_to_add: Optional[float] = None
    new_current_amount: Optional[float] = None
    status: Optional[str] = None

    @model_validator(mode="after")
    def at_least_one_field(self) -> "GoalUpdateRequest":
        if self.amount_to_add is None and self.new_current_amount is None and self.status is None:
            raise ValueError("Provide at least one of: amount_to_add, new_current_amount, status")
        return self

    @field_validator("amount_to_add")
    @classmethod
    def add_positive(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v <= 0:
            raise ValueError("amount_to_add must be greater than zero")
        return v

    @field_validator("new_current_amount")
    @classmethod
    def new_amount_non_negative(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError("new_current_amount must be >= 0")
        return v

    @field_validator("status")
    @classmethod
    def status_valid(cls, v: Optional[str]) -> Optional[str]:
        allowed = {"active", "achieved", "missed"}
        if v is not None and v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v


# ─────────────────────────────────────────────────────────────────────────────
# OBLIGATIONS
# ─────────────────────────────────────────────────────────────────────────────

class ObligationCreateRequest(BaseModel):
    title: str
    amount: float
    frequency: Optional[str] = "monthly"
    due_day: Optional[int] = 10
    next_due_date: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Amount must be greater than zero")
        return round(v, 2)

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Title must not be empty")
        return v.strip()

    @field_validator("due_day")
    @classmethod
    def due_day_valid(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not (1 <= v <= 31):
            raise ValueError("due_day must be between 1 and 31")
        return v

    @field_validator("next_due_date")
    @classmethod
    def next_due_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("next_due_date must be in YYYY-MM-DD format")
        return v


class ObligationUpdateRequest(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def status_valid(cls, v: str) -> str:
        allowed = {"active", "paid", "overdue"}
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v


# ─────────────────────────────────────────────────────────────────────────────
# AGENT / VOICE
# ─────────────────────────────────────────────────────────────────────────────

class AgentChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "demo_user"


class VoiceInputRequest(BaseModel):
    transcript: str
    user_id: Optional[str] = "demo_user"


# ─────────────────────────────────────────────────────────────────────────────
# MEMORY
# ─────────────────────────────────────────────────────────────────────────────

VALID_MEMORY_TYPES = {"profile_fact", "preference", "plan", "outcome", "pattern"}

class MemoryCreateRequest(BaseModel):
    type: str
    title: str
    content: str
    category: Optional[str] = "emi"
    outcome_status: Optional[str] = "observed"
    related_goal_id: Optional[str] = None
    related_plan_id: Optional[str] = None
    importance: Optional[float] = 1.0
    source: Optional[str] = "user_reported"
    date: Optional[str] = None
    relevance_tags: Optional[List[str]] = []

    @field_validator("type")
    @classmethod
    def type_valid(cls, v: str) -> str:
        norm = v.strip().lower()
        if norm not in VALID_MEMORY_TYPES:
            raise ValueError(f"type must be one of {VALID_MEMORY_TYPES}, got '{v}'")
        return norm

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("title must not be empty")
        return v.strip()

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("content must not be empty")
        return v.strip()

    @field_validator("importance")
    @classmethod
    def importance_range(cls, v: Optional[float]) -> float:
        if v is None:
            return 1.0
        return max(0.1, min(5.0, float(v)))
