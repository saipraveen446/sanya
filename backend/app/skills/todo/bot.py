from html import escape

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from app.database import SessionLocal
from app.skills.todo.schemas import TodoUpdate
from app.skills.todo.service import delete_todo, list_todos, update_todo
from app.time import now_local


def _when(value) -> str:
    if not value:
        return ""
    local = value.astimezone(now_local().tzinfo)
    return local.strftime("%d %b, %I:%M %p")


async def show_todos(update: Update, context: ContextTypes.DEFAULT_TYPE, *, status: str = "open", deleting: bool = False) -> None:
    async with SessionLocal() as session:
        items = await list_todos(session, status=status)
    target = update.effective_message
    if not items:
        label = "completed todos" if status == "done" else "open todos"
        await target.reply_text(f"No {label} yet.")
        return
    context.user_data["delete_todo_ids"] = [str(item.id) for item in items]
    if deleting:
        keyboard = [
            [InlineKeyboardButton(f"🗑 {item.title[:28]}", callback_data=f"todo:del:{item.id}")]
            for item in items[:8]
        ]
        await target.reply_text("Tap a todo to delete it.", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    title = "Completed" if status == "done" else "Todo list"
    lines = [f"<b>{title}</b>"]
    keyboard = []
    for item in items[:10]:
        when = f" — {_when(item.due_at)}" if item.due_at else ""
        lines.append(f"• {escape(item.title)}{when}")
        if status == "open":
            keyboard.append(
                [InlineKeyboardButton(f"☑️ {item.title[:28]}", callback_data=f"todo:ok:{item.id}")]
            )
    markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    await target.reply_text("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=markup)


async def complete_todo(update: Update, todo_id: str) -> None:
    from uuid import UUID

    async with SessionLocal() as session:
        updated = await update_todo(session, UUID(todo_id), TodoUpdate(is_done=True))
    target = update.effective_message
    if not updated:
        await target.reply_text("That todo is already gone.")
        return
    await target.reply_text(f"Completed: {updated.title}")


async def remove_todo_by_id(update: Update, todo_id: str) -> None:
    from uuid import UUID

    async with SessionLocal() as session:
        deleted = await delete_todo(session, UUID(todo_id))
    target = update.effective_message
    if not deleted:
        await target.reply_text("That todo is already gone.")
        return
    await target.reply_text(f"Deleted todo: {deleted.title}")


def register_handlers(application) -> None:
    return None
