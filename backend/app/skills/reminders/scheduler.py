import asyncio
import logging

from app.database import SessionLocal
from app.skills.reminders.notify import bind_bot, notify_due, notify_soon
from app.skills.reminders.service import (
    list_due_reminders,
    list_pre_due_reminders,
    mark_notified,
    mark_pre_notified,
)
from app.skills.todo.service import list_due_todos, mark_notified as mark_todo_notified
from app.time import now_local

logger = logging.getLogger(__name__)


def _when(value) -> str:
    return value.astimezone(now_local().tzinfo).strftime("%d %b, %I:%M %p")


async def dispatch_alerts(bot) -> None:
    from app.skills.news.service import get_news

    for topic in ("ai", "tech", "top"):
        try:
            await get_news(topic, limit=12)
        except Exception:
            logger.exception("Daily %s news digest failed", topic)

    if bot is None:
        return
    async with SessionLocal() as session:
        upcoming = await list_pre_due_reminders(session)
        reminders = await list_due_reminders(session)
        todos = await list_due_todos(session)
        for reminder in upcoming:
            try:
                await notify_soon(reminder)
            except Exception:
                logger.exception("Failed to send 15-minute reminder for %s", reminder.id)
            await mark_pre_notified(session, reminder.id)
        for reminder in reminders:
            try:
                await notify_due(reminder)
            except Exception:
                logger.exception("Failed to send due reminder for %s", reminder.id)
            await mark_notified(session, reminder.id)
        for todo in todos:
            from html import escape as html_escape
            from app.skills.reminders.notify import chat_id_for, send_telegram

            chat_id = chat_id_for(todo.telegram_user_id)
            if chat_id:
                await send_telegram(f"✅ Todo due: <b>{html_escape(todo.title)}</b>", todo.telegram_user_id)
            await mark_todo_notified(session, todo.id)


async def run_alert_loop(get_bot) -> None:
    bind_bot(get_bot)
    await asyncio.sleep(8)
    while True:
        try:
            application = get_bot()
            bot = application.bot if application else None
            await dispatch_alerts(bot)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Alert loop failed")
        await asyncio.sleep(30)
