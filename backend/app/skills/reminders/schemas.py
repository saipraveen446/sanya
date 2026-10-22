from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ReminderCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    notes: str = ""
    due_at: datetime
    source: str = "web"
    telegram_user_id: str = ""
    raw_message: str | None = None


class ReminderUpdate(BaseModel):
    title: str | None = None
    notes: str | None = None
    due_at: datetime | None = None
    is_done: bool | None = None


class ReminderOut(BaseModel):
    id: UUID
    source: str
    telegram_user_id: str
    title: str
    notes: str
    due_at: datetime
    is_done: bool
    notified_at: datetime | None
    pre_notified_at: datetime | None = None
    raw_message: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
