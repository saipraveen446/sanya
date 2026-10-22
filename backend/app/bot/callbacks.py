from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from app.bot.menus import AWAITING_PROMPTS, full_menu_keyboard, home_keyboard, skill_keyboard
from app.skills.expense_tracking.bot import list_command, month
from app.skills.news.bot import send_news
from app.skills.reminders.bot import remove_reminder_by_id, show_reminders
from app.skills.todo.bot import complete_todo, remove_todo_by_id, show_todos


async def _ask(update: Update, context: ContextTypes.DEFAULT_TYPE, awaiting: str, skill_id: str) -> None:
    context.user_data["awaiting"] = awaiting
    context.user_data["active_skill"] = skill_id
    await update.effective_message.reply_text(
        AWAITING_PROMPTS[awaiting],
        parse_mode=ParseMode.HTML,
        reply_markup=home_keyboard(),
    )


async def handle_home_label(update: Update, context: ContextTypes.DEFAULT_TYPE, skill_key: str) -> None:
    mapping = {
        "expenses": ("expense_tracking", "💰 Expenses"),
        "reminders": ("reminders", "⏰ Reminders"),
        "todo": ("todo", "✅ Todo"),
        "news": ("news", "📰 Tech & AI News"),
    }
    skill_id, title = mapping[skill_key]
    context.user_data["active_skill"] = skill_id
    context.user_data.pop("awaiting", None)
    await update.effective_message.reply_text(
        f"<b>{title}</b>\nPick an action.",
        parse_mode=ParseMode.HTML,
        reply_markup=skill_keyboard(skill_id),
    )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from app.bot.telegram_bot import reject_if_private

    query = update.callback_query
    if query:
        await query.answer()
    if await reject_if_private(update):
        return

    data = (query.data if query else "") or ""
    if data == "menu:home":
        await update.effective_message.reply_text(
            "Home menu",
            reply_markup=full_menu_keyboard(),
        )
        return
    if data == "menu:expense:add":
        await _ask(update, context, "expense_add", "expense_tracking")
        return
    if data == "menu:expense:summary":
        await month(update, context)
        return
    if data == "menu:expense:history":
        await list_command(update, context)
        return
    if data == "menu:reminder:add":
        await _ask(update, context, "reminder_add", "reminders")
        return
    if data == "menu:reminder:list":
        await show_reminders(update, context)
        return
    if data == "menu:reminder:delete":
        context.user_data["awaiting"] = "reminder_delete"
        await show_reminders(update, context, deleting=True)
        return
    if data == "menu:todo:add":
        await _ask(update, context, "todo_add", "todo")
        return
    if data == "menu:todo:list":
        await show_todos(update, context, status="open")
        return
    if data == "menu:todo:done":
        await show_todos(update, context, status="done")
        return
    if data == "menu:todo:delete":
        context.user_data["awaiting"] = "todo_delete"
        await show_todos(update, context, status="all", deleting=True)
        return
    if data == "menu:news:ai":
        await send_news(update, context, "ai")
        return
    if data == "menu:news:tech":
        await send_news(update, context, "tech")
        return
    if data == "menu:news:top":
        await send_news(update, context, "top")
        return
    if data.startswith("rem:del:"):
        await remove_reminder_by_id(update, data.split(":", 2)[2])
        return
    if data.startswith("todo:del:"):
        await remove_todo_by_id(update, data.split(":", 2)[2])
        return
    if data.startswith("todo:ok:"):
        await complete_todo(update, data.split(":", 2)[2])
        return
