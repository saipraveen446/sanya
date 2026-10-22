from html import escape

from app.skills.base import Skill, SkillResult
from app.skills.news.parser import parse_news_message
from app.skills.news.service import get_news


def format_news(payload: dict) -> str:
    lines = [f"<b>{escape(payload.get('label') or 'News')}</b>"]
    items = payload.get("items") or []
    if not items:
        lines.append("No headlines right now. Try again in a minute.")
        return "\n".join(lines)
    for index, item in enumerate(items, start=1):
        title = escape(item.get("title") or "Untitled")
        url = item.get("url") or ""
        source = escape(item.get("source") or "")
        if url:
            lines.append(f"{index}. <a href=\"{escape(url)}\">{title}</a>")
        else:
            lines.append(f"{index}. {title}")
        if source:
            lines.append(f"   {source}")
    return "\n".join(lines)


class NewsSkill(Skill):
    id = "news"
    name = "Tech / AI News"
    description = "Read AI, tech, and top headlines from Telegram or the dashboard."
    ready = True
    keywords = ("news", "headline", "ai news", "tech news", "what happened", "briefing", "top news")
    examples = ("ai news today", "tech headlines", "top news")
    commands = ("/news",)

    async def parse(self, text: str) -> SkillResult:
        data = await parse_news_message(text)
        topic = (data.get("topic") or "tech").lower()
        if "ai" in text.lower() or topic == "ai":
            topic = "ai"
        elif "top" in text.lower() or topic == "general":
            topic = "top"
        elif "tech" in text.lower():
            topic = "tech"
        data["topic"] = topic
        return SkillResult(
            skill_id=self.id,
            ok=True,
            message=f"{topic} news",
            data=data,
        )

    async def execute(self, parsed: SkillResult, *, telegram_user_id: str | None = None) -> SkillResult:
        payload = await get_news(
            (parsed.data or {}).get("topic") or "tech",
            query=(parsed.data or {}).get("query") or "",
            limit=int((parsed.data or {}).get("limit") or 12),
        )
        return SkillResult(
            skill_id=self.id,
            ok=True,
            message=format_news(payload),
            data=payload,
        )

    def register_bot_handlers(self, application) -> None:
        from app.skills.news.bot import register_handlers

        register_handlers(application)


news_skill = NewsSkill()
