from uuid import UUID
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.skills.reminders.notify import notify_created
from app.skills.reminders.schemas import ReminderCreate, ReminderOut, ReminderUpdate
from app.skills.reminders.service import create_reminder, delete_reminder, list_reminders, update_reminder

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/reminders", response_model=list[ReminderOut])
async def get_reminders(
    include_done: bool = False,
    db: AsyncSession = Depends(get_db),
):
    return await list_reminders(db, include_done=include_done)


@router.post("/reminders", response_model=ReminderOut)
async def add_reminder(payload: ReminderCreate, db: AsyncSession = Depends(get_db)):
    reminder = await create_reminder(db, payload)
    try:
        await notify_created(reminder)
    except Exception:
        logger.exception("Could not send Telegram notification for new reminder")
    return reminder


@router.patch("/reminders/{reminder_id}", response_model=ReminderOut)
async def edit_reminder(reminder_id: UUID, payload: ReminderUpdate, db: AsyncSession = Depends(get_db)):
    updated = await update_reminder(db, reminder_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return updated


@router.delete("/reminders/{reminder_id}")
async def remove_reminder(reminder_id: UUID, db: AsyncSession = Depends(get_db)):
    deleted = await delete_reminder(db, reminder_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return {"ok": True}
