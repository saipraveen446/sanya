import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from app.bot.callbacks import handle_callback, handle_home_label
from app.bot.menus import HOME_LABELS, full_menu_keyboard, home_keyboard, menu_text, skill_keyboard
from app.config import settings
from app.skills.registry import all_skills, get_skill
from app.skills.router import resolve_skill, strip_skill_prefix

logger = logging.getLogger(__name__)

_AWAITING_SKILL = {
    "expense_add": "expense_tracking",
    "reminder_add": "reminders",
    "todo_add": "todo",
}


def _allowed(user) -> bool:
    if user is None:
        return False
    allowed = settings.allowed_user_ids
    if not allowed:
        return True
    if str(user.id) in allowed:
        return True
    username = (user.username or "").lower()
    return bool(username) and username in {item.lower() for item in allowed}


async def reject_if_private(update: Update) -> bool:
    user = update.effective_user
    if _allowed(user):
        return False
    logger.warning(
        "Ignored Telegram user id=%s username=%s",
        getattr(user, "id", None),
        getattr(user, "username", None),
    )
    target = update.effective_message
    if target:
        await target.reply_text(
            "This bot is private. Your Telegram user is not in ALLOWED_TELEGRAM_USER_IDS."
        )
    return True


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await reject_if_private(update):
        return
    context.user_data.pop("awaiting", None)
    await update.effective_message.reply_text(
        menu_text(),
        parse_mode=ParseMode.HTML,
        reply_markup=home_keyboard(),
    )
    await update.effective_message.reply_text(
        "Actions",
        reply_markup=full_menu_keyboard(),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await start(update, context)


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await start(update, context)


async def skills_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await reject_if_private(update):
        return
    pinned = context.user_data.get("active_skill") or settings.default_skill
    lines = ["<b>Sanya skills</b>"]
    for skill in all_skills():
        mark = " ← pinned" if skill.id == pinned else ""
        status = "ready" if skill.ready else "soon"
        lines.append(f"• {skill.name} <code>/{skill.id}</code> ({status}){mark}")
    await update.effective_message.reply_text(
        "\n".join(lines),
        parse_mode=ParseMode.HTML,
        reply_markup=home_keyboard(),
    )


async def use_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await reject_if_private(update):
        return
    name = " ".join(context.args or []).strip().lower()
    skill = get_skill(name)
    if not skill:
        names = " | ".join(item.id for item in all_skills())
        await update.effective_message.reply_text(f"Usage: /use {names}")
        return
    context.user_data["active_skill"] = skill.id
    await update.effective_message.reply_text(
        f"Pinned skill: {skill.name}.",
        reply_markup=skill_keyboard(skill.id),
    )


async def _dispatch(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, preferred: str | None = None) -> None:
    user = update.effective_user
    skill = await resolve_skill(text, preferred=preferred)
    parsed_text = strip_skill_prefix(text)
    logger.info("Telegram %s from id=%s text=%s", skill.id, user.id, parsed_text)
    result = await skill.handle(parsed_text, telegram_user_id=str(user.id))
    if result.ok:
        context.user_data.pop("awaiting", None)
    try:
        await update.effective_message.reply_text(result.message, parse_mode=ParseMode.HTML)
    except Exception:
        await update.effective_message.reply_text(result.message)


async def capture_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if await reject_if_private(update):
        return
    text = (update.message.text or "").strip()
    if not text:
        return

    home = HOME_LABELS.get(text)
    if home:
        await handle_home_label(update, context, home)
        return

    awaiting = context.user_data.get("awaiting")
    if awaiting in {"reminder_delete", "todo_delete"}:
        skill_id = "reminders" if awaiting == "reminder_delete" else "todo"
        action = f"delete {text}"
        await _dispatch(update, context, action, preferred=skill_id)
        return
    if awaiting in _AWAITING_SKILL:
        await _dispatch(update, context, text, preferred=_AWAITING_SKILL[awaiting])
        return

    await _dispatch(update, context, text, preferred=context.user_data.get("active_skill"))


def _skill_command(skill_id: str):
    async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if await reject_if_private(update):
            return
        skill = get_skill(skill_id)
        text = " ".join(context.args or []).strip()
        if not text:
            context.user_data["active_skill"] = skill_id
            context.user_data.pop("awaiting", None)
            await update.effective_message.reply_text(
                f"<b>{skill.name if skill else skill_id}</b>\nPick an action.",
                parse_mode=ParseMode.HTML,
                reply_markup=skill_keyboard(skill_id),
            )
            return
        await _dispatch(update, context, text, preferred=skill_id)

    return handler


def build_bot() -> Application:
    application = Application.builder().token(settings.telegram_bot_token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("menu", menu_command))
    application.add_handler(CommandHandler("skills", skills_command))
    application.add_handler(CommandHandler("tools", skills_command))
    application.add_handler(CommandHandler("use", use_command))
    application.add_handler(CallbackQueryHandler(handle_callback))
    for skill in all_skills():
        application.add_handler(CommandHandler(skill.id, _skill_command(skill.id)))
        skill.register_bot_handlers(application)
    application.add_handler(CommandHandler("expenses", _skill_command("expense_tracking")))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, capture_message))
    return application
