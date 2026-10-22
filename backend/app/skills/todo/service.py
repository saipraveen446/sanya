from datetime import datetime, timezone
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import Select, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.origin import record_origin
from app.skills.todo.models import Todo
from app.skills.todo.schemas import TodoCreate, TodoUpdate
from app.time import now_local


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=ZoneInfo(settings.app_timezone))
    return value


async def create_todo(session: AsyncSession, payload: TodoCreate) -> Todo:
    source, telegram_user_id = record_origin(payload.telegram_user_id, payload.source)
    todo = Todo(
        source=source,
        telegram_user_id=telegram_user_id,
        title=payload.title.strip(),
        notes=payload.notes or "",
        due_at=_aware(payload.due_at),
        raw_message=payload.raw_message,
    )
    session.add(todo)
    await session.commit()
    await session.refresh(todo)
    return todo


async def list_todos(
    session: AsyncSession,
    *,
    telegram_user_id: str | None = None,
    status: str = "open",
    limit: int = 80,
) -> list[Todo]:
    query: Select[tuple[Todo]] = select(Todo).order_by(Todo.is_done, Todo.created_at.desc()).limit(limit)
    if telegram_user_id:
        query = query.where(Todo.telegram_user_id == telegram_user_id)
    if status == "open":
        query = query.where(Todo.is_done.is_(False))
    elif status == "done":
        query = query.where(Todo.is_done.is_(True))
    result = await session.execute(query)
    return list(result.scalars().all())


async def get_todo(session: AsyncSession, todo_id: UUID) -> Todo | None:
    return await session.get(Todo, todo_id)


async def update_todo(session: AsyncSession, todo_id: UUID, payload: TodoUpdate) -> Todo | None:
    todo = await session.get(Todo, todo_id)
    if not todo:
        return None
    if payload.title is not None:
        todo.title = payload.title.strip()
    if payload.notes is not None:
        todo.notes = payload.notes
    if payload.due_at is not None:
        todo.due_at = _aware(payload.due_at)
    if payload.is_done is not None:
        todo.is_done = payload.is_done
        todo.completed_at = datetime.now(timezone.utc) if payload.is_done else None
    await session.commit()
    await session.refresh(todo)
    return todo


async def delete_todo(session: AsyncSession, todo_id: UUID) -> Todo | None:
    todo = await session.get(Todo, todo_id)
    if not todo:
        return None
    await session.delete(todo)
    await session.commit()
    return todo


async def delete_matching(
    session: AsyncSession,
    query_text: str,
    *,
    telegram_user_id: str | None = None,
) -> Todo | None:
    todos = await list_todos(session, telegram_user_id=telegram_user_id, status="all")
    needle = query_text.strip().lower()
    if needle.isdigit():
        index = int(needle) - 1
        if 0 <= index < len(todos):
            return await delete_todo(session, todos[index].id)
    for item in todos:
        if needle and needle in item.title.lower():
            return await delete_todo(session, item.id)
    return None


async def list_due_todos(session: AsyncSession) -> list[Todo]:
    now = now_local()
    result = await session.execute(
        select(Todo)
        .where(
            Todo.is_done.is_(False),
            Todo.notified_at.is_(None),
            Todo.due_at.is_not(None),
            Todo.due_at <= now,
        )
        .order_by(Todo.due_at)
    )
    return list(result.scalars().all())


async def mark_notified(session: AsyncSession, todo_id: UUID) -> Todo | None:
    todo = await session.get(Todo, todo_id)
    if not todo:
        return None
    todo.notified_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(todo)
    return todo
