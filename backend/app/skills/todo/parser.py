from datetime import datetime
from zoneinfo import ZoneInfo

from app.config import settings
from app.llm import complete_json
from app.skills.todo.schemas import TodoCreate
from app.time import now_local
from app.when import parse_when, strip_when


def _parse_due(value: str | None, original: str) -> datetime | None:
    if value in {None, "", "null", "none"}:
        return parse_when(original, default_hours=None)
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=ZoneInfo(settings.app_timezone))
        return parsed
    except ValueError:
        return parse_when(original, default_hours=None)


async def parse_todo_message(text: str) -> TodoCreate:
    today = now_local()
    data = await complete_json(
        f"""Extract a todo from a short message.
Return ONLY JSON:
{{
  "title": "Submit invoice",
  "notes": "",
  "due_at": null
}}
Rules:
- title is the task, without the word todo
- due_at is ISO-8601 in {settings.app_timezone}, or null if no time was given
- Today is {today.isoformat(timespec="minutes")}
""",
        text,
    )
    if data and not data.get("error"):
        title = (data.get("title") or "").strip()
        if title:
            return TodoCreate(
                title=title[:200],
                notes=(data.get("notes") or "")[:400],
                due_at=_parse_due(data.get("due_at"), text),
                raw_message=text,
            )

    title = strip_when(text)
    if not title:
        raise ValueError("Tell me the todo. Try: submit invoice tomorrow")
    return TodoCreate(
        title=title[:200],
        notes="",
        due_at=_parse_due(None, text),
        raw_message=text,
    )
