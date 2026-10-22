from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TodoCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    notes: str = ""
    due_at: datetime | None = None
    source: str = "web"
    telegram_user_id: str = ""
    raw_message: str | None = None


class TodoUpdate(BaseModel):
    is_done: bool | None = None
    title: str | None = None
    notes: str | None = None
    due_at: datetime | None = None


class TodoOut(BaseModel):
    id: UUID
    source: str
    telegram_user_id: str
    title: str
    notes: str
    due_at: datetime | None
    is_done: bool
    completed_at: datetime | None
    notified_at: datetime | None
    raw_message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
