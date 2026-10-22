from datetime import datetime, timedelta, timezone
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import Select, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.origin import record_origin
from app.skills.reminders.models import Reminder
from app.skills.reminders.schemas import ReminderCreate, ReminderUpdate
from app.time import now_local


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=ZoneInfo(settings.app_timezone))
    return value


async def create_reminder(session: AsyncSession, payload: ReminderCreate) -> Reminder:
    source, telegram_user_id = record_origin(payload.telegram_user_id, payload.source)
    reminder = Reminder(
        source=source,
        telegram_user_id=telegram_user_id,
        title=payload.title.strip(),
        notes=payload.notes or "",
        due_at=_aware(payload.due_at),
        raw_message=payload.raw_message,
    )
    session.add(reminder)
    await session.commit()
    await session.refresh(reminder)
    return reminder


async def list_reminders(
    session: AsyncSession,
    *,
    telegram_user_id: str | None = None,
    include_done: bool = False,
    limit: int = 50,
) -> list[Reminder]:
    query: Select[tuple[Reminder]] = select(Reminder).order_by(Reminder.is_done, Reminder.due_at).limit(limit)
    if telegram_user_id:
        query = query.where(Reminder.telegram_user_id == telegram_user_id)
    if not include_done:
        query = query.where(Reminder.is_done.is_(False))
    result = await session.execute(query)
    return list(result.scalars().all())


async def get_reminder(session: AsyncSession, reminder_id: UUID) -> Reminder | None:
    return await session.get(Reminder, reminder_id)


async def update_reminder(session: AsyncSession, reminder_id: UUID, payload: ReminderUpdate) -> Reminder | None:
    reminder = await session.get(Reminder, reminder_id)
    if not reminder:
        return None
    if payload.title is not None:
        reminder.title = payload.title.strip()
    if payload.notes is not None:
        reminder.notes = payload.notes
    if payload.due_at is not None:
        reminder.due_at = _aware(payload.due_at)
        reminder.notified_at = None
        reminder.pre_notified_at = None
        reminder.is_done = False
    if payload.is_done is not None:
        reminder.is_done = payload.is_done
    await session.commit()
    await session.refresh(reminder)
    return reminder


async def delete_reminder(session: AsyncSession, reminder_id: UUID) -> Reminder | None:
    reminder = await session.get(Reminder, reminder_id)
    if not reminder:
        return None
    await session.delete(reminder)
    await session.commit()
    return reminder


async def delete_matching(
    session: AsyncSession,
    query_text: str,
    *,
    telegram_user_id: str | None = None,
) -> Reminder | None:
    reminders = await list_reminders(session, telegram_user_id=telegram_user_id, include_done=True)
    needle = query_text.strip().lower()
    if needle.isdigit():
        index = int(needle) - 1
        if 0 <= index < len(reminders):
            return await delete_reminder(session, reminders[index].id)
    for item in reminders:
        if needle and needle in item.title.lower():
            return await delete_reminder(session, item.id)
    return None


async def list_due_reminders(session: AsyncSession) -> list[Reminder]:
    now = now_local()
    result = await session.execute(
        select(Reminder)
        .where(
            Reminder.is_done.is_(False),
            Reminder.notified_at.is_(None),
            Reminder.due_at <= now,
        )
        .order_by(Reminder.due_at)
    )
    return list(result.scalars().all())


async def list_pre_due_reminders(session: AsyncSession) -> list[Reminder]:
    now = now_local()
    soon = now + timedelta(minutes=15)
    lead = timedelta(minutes=15)
    result = await session.execute(
        select(Reminder)
        .where(
            Reminder.is_done.is_(False),
            Reminder.pre_notified_at.is_(None),
            Reminder.due_at > now,
            Reminder.due_at <= soon,
            Reminder.created_at <= Reminder.due_at - lead,
        )
        .order_by(Reminder.due_at)
    )
    return list(result.scalars().all())


async def mark_pre_notified(session: AsyncSession, reminder_id: UUID) -> Reminder | None:
    reminder = await session.get(Reminder, reminder_id)
    if not reminder:
        return None
    reminder.pre_notified_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(reminder)
    return reminder


async def mark_notified(session: AsyncSession, reminder_id: UUID) -> Reminder | None:
    reminder = await session.get(Reminder, reminder_id)
    if not reminder:
        return None
    reminder.notified_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(reminder)
    return reminder


async def latest_reminder(session: AsyncSession, telegram_user_id: str) -> Reminder | None:
    result = await session.execute(
        select(Reminder)
        .where(Reminder.telegram_user_id == telegram_user_id)
        .order_by(desc(Reminder.created_at))
        .limit(1)
    )
    return result.scalar_one_or_none()
