from html import escape

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from app.database import SessionLocal
from app.skills.reminders.service import delete_reminder, list_reminders
from app.time import now_local


def _when(value) -> str:
    local = value.astimezone(now_local().tzinfo)
    return local.strftime("%d %b, %I:%M %p")


async def show_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE, *, deleting: bool = False) -> None:
    async with SessionLocal() as session:
        items = await list_reminders(session, include_done=False)
    target = update.effective_message
    if not items:
        await target.reply_text("No reminders yet. Tap ➕ Add Reminder.")
        return
    context.user_data["delete_reminder_ids"] = [str(item.id) for item in items]
    if deleting:
        keyboard = [
            [InlineKeyboardButton(f"🗑 {item.title[:28]}", callback_data=f"rem:del:{item.id}")]
            for item in items[:8]
        ]
        await target.reply_text(
            "Tap a reminder to delete it.",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return
    lines = ["<b>My reminders</b>"]
    for item in items:
        badge = " · alerted" if item.notified_at else ""
        lines.append(f"• {escape(item.title)} — {_when(item.due_at)}{badge}")
    await target.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)


async def remove_reminder_by_id(update: Update, reminder_id: str) -> None:
    from uuid import UUID

    async with SessionLocal() as session:
        deleted = await delete_reminder(session, UUID(reminder_id))
    target = update.effective_message
    if not deleted:
        await target.reply_text("That reminder is already gone.")
        return
    await target.reply_text(f"Deleted reminder: {deleted.title}")


def register_handlers(application) -> None:
    return None
