"""Send reminder alerts to Telegram."""

import logging
from html import escape

from app.config import settings
from app.time import now_local

logger = logging.getLogger(__name__)
_get_bot = lambda: None


def bind_bot(getter) -> None:
    global _get_bot
    _get_bot = getter


def chat_id_for(stored: str | None) -> int | None:
    if stored and stored.isdigit():
        return int(stored)
    for item in settings.allowed_user_ids:
        if item.isdigit():
            return int(item)
    return None


def format_when(value) -> str:
    return value.astimezone(now_local().tzinfo).strftime("%d %b, %I:%M %p")


def default_telegram_user_id(stored: str | None) -> str:
    if stored and stored not in {"web", ""}:
        return stored
    for item in settings.allowed_user_ids:
        if item.isdigit():
            return item
    return stored or "web"


async def send_telegram(text: str, user_id: str | None = None) -> bool:
    application = _get_bot()
    bot = application.bot if application else None
    if bot is None:
        logger.warning("Telegram bot is not running; skipped reminder notification")
        return False
    chat_id = chat_id_for(user_id)
    if not chat_id:
        logger.warning("No Telegram chat id for reminder notification")
        return False
    await bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
    return True


async def notify_created(reminder) -> None:
    when = format_when(reminder.due_at)
    await send_telegram(
        f"✅ Reminder set: <b>{escape(reminder.title)}</b>\n"
        f"Due {when}\n"
        f"I'll ping you 15 minutes before, and again at the due time.",
        reminder.telegram_user_id,
    )


async def notify_soon(reminder) -> None:
    when = format_when(reminder.due_at)
    await send_telegram(
        f"⏳ In 15 minutes: <b>{escape(reminder.title)}</b>\nDue {when}",
        reminder.telegram_user_id,
    )


async def notify_due(reminder) -> None:
    when = format_when(reminder.due_at)
    await send_telegram(
        f"⏰ Reminder: <b>{escape(reminder.title)}</b>\nDue {when}",
        reminder.telegram_user_id,
    )
