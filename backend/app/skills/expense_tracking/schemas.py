from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ExpenseCreate(BaseModel):
    amount: Decimal = Field(gt=0)
    currency: str = "INR"
    category: str
    merchant: str | None = None
    description: str = ""
    spent_at: datetime | None = None
    source: str = "web"
    telegram_user_id: str = ""
    raw_message: str | None = None


class ExpenseOut(BaseModel):
    id: UUID
    source: str
    telegram_user_id: str
    amount: Decimal
    currency: str
    category: str
    merchant: str | None
    description: str
    spent_at: datetime
    raw_message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class BreakdownItem(BaseModel):
    name: str
    total: Decimal
    count: int


class SummaryOut(BaseModel):
    period: str
    start: datetime
    end: datetime
    total: Decimal
    count: int
    currency: str
    by_category: list[BreakdownItem]
    by_merchant: list[BreakdownItem]


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    group_name: str = Field(default="Daily life", max_length=64)
    keywords: str = ""
    examples: str = ""


class CategoryOut(BaseModel):
    id: UUID
    name: str
    group_name: str
    keywords: str
    examples: str
    sort_order: int
    is_active: bool

    model_config = {"from_attributes": True}
