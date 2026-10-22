from decimal import Decimal

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes

from app.database import SessionLocal
from app.skills.expense_tracking.category import create_category, list_categories
from app.skills.expense_tracking.schemas import CategoryCreate
from app.skills.expense_tracking.service import delete_last_expense, get_summary, list_expenses


def _money(amount: Decimal, currency: str) -> str:
    return f"{currency} {amount:,.2f}"


def _format_summary(summary) -> str:
    lines = [
        f"<b>{summary.period.title()} summary</b>",
        f"Total: <b>{_money(summary.total, summary.currency)}</b> across {summary.count} spends",
        "",
    ]
    if summary.by_category:
        lines.append("<b>Where by category</b>")
        for item in summary.by_category[:8]:
            lines.append(f"• {item.name}: {_money(item.total, summary.currency)} ({item.count})")
        lines.append("")
    if summary.by_merchant:
        lines.append("<b>Where by place</b>")
        for item in summary.by_merchant[:8]:
            lines.append(f"• {item.name}: {_money(item.total, summary.currency)} ({item.count})")
    if summary.count == 0:
        lines.append("No expenses in this period yet.")
    return "\n".join(lines).strip()


async def _reply_summary(update: Update, period: str) -> None:
    from app.bot.telegram_bot import reject_if_private

    if await reject_if_private(update):
        return
    async with SessionLocal() as session:
        summary = await get_summary(session, period)
    await update.effective_message.reply_text(_format_summary(summary), parse_mode=ParseMode.HTML)


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply_summary(update, "today")


async def week(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply_summary(update, "week")


async def month(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _reply_summary(update, "month")


async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from app.bot.telegram_bot import reject_if_private

    if await reject_if_private(update):
        return
    async with SessionLocal() as session:
        expenses = await list_expenses(session, limit=10)
    if not expenses:
        await update.effective_message.reply_text("No expenses yet.")
        return
    lines = ["<b>Recent expenses</b>"]
    for item in expenses:
        place = f" at {item.merchant}" if item.merchant else ""
        when = item.spent_at.strftime("%d %b")
        lines.append(f"• {when} {_money(item.amount, item.currency)} {item.category}{place}")
    await update.effective_message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)


async def categories_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from app.bot.telegram_bot import reject_if_private

    if await reject_if_private(update):
        return
    async with SessionLocal() as session:
        categories = await list_categories(session)
    lines = ["<b>Categories</b>"]
    current_group = None
    for item in categories:
        if item.group_name != current_group:
            current_group = item.group_name
            lines.append(f"\n<b>{current_group}</b>")
        extra = f" — {item.examples}" if item.examples else ""
        lines.append(f"• {item.name}{extra}")
    await update.effective_message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)


async def add_category_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from app.bot.telegram_bot import reject_if_private

    if await reject_if_private(update):
        return
    name = " ".join(context.args or []).strip()
    if not name:
        await update.effective_message.reply_text("Usage: /addcategory Category Name")
        return
    async with SessionLocal() as session:
        category = await create_category(session, CategoryCreate(name=name))
    await update.effective_message.reply_text(f"Added category: {category.name}")


async def undo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from app.bot.telegram_bot import reject_if_private

    if await reject_if_private(update):
        return
    user = update.effective_user
    async with SessionLocal() as session:
        deleted = await delete_last_expense(session, str(user.id))
    if not deleted:
        await update.effective_message.reply_text("Nothing to undo.")
        return
    await update.effective_message.reply_text(
        f"Removed {_money(deleted.amount, deleted.currency)} {deleted.category}."
    )


def register_handlers(application) -> None:
    application.add_handler(CommandHandler("today", today))
    application.add_handler(CommandHandler("week", week))
    application.add_handler(CommandHandler("month", month))
    application.add_handler(CommandHandler("list", list_command))
    application.add_handler(CommandHandler("categories", categories_command))
    application.add_handler(CommandHandler("addcategory", add_category_command))
    application.add_handler(CommandHandler("undo", undo))
