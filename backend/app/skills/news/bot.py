from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from app.skills.news.service import get_news
from app.skills.news.skill import format_news


async def send_news(update: Update, context: ContextTypes.DEFAULT_TYPE, topic: str) -> None:
    payload = await get_news(topic, limit=6)
    await update.effective_message.reply_text(
        format_news(payload),
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


def register_handlers(application) -> None:
    return None
