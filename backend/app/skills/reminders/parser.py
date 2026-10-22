from datetime import datetime
from zoneinfo import ZoneInfo

from app.config import settings
from app.llm import complete_json
from app.skills.reminders.schemas import ReminderCreate
from app.time import now_local
from app.when import parse_when, strip_when


def _parse_due(value: str | None, original: str) -> datetime:
    if value:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=ZoneInfo(settings.app_timezone))
            return parsed
        except ValueError:
            pass
    due = parse_when(original, default_hours=1)
    if due is None:
        raise ValueError("I need a time. Try: call dentist tomorrow 10am")
    return due


async def parse_reminder_message(text: str) -> ReminderCreate:
    today = now_local()
    data = await complete_json(
        f"""Extract a reminder from a short message.
Return ONLY JSON:
{{
  "title": "Call dentist",
  "notes": "",
  "due_at": "{today.isoformat(timespec="minutes")}"
}}
Rules:
- title is the thing to remember, without the word remind
- due_at is ISO-8601 in timezone {settings.app_timezone}
- If no time is given, use one hour from now
- If they say tomorrow and no clock time, use 09:00
- Today is {today.isoformat(timespec="minutes")}
""",
        text,
    )
    if data and not data.get("error"):
        title = (data.get("title") or "").strip()
        if title:
            return ReminderCreate(
                title=title[:200],
                notes=(data.get("notes") or "")[:400],
                due_at=_parse_due(data.get("due_at"), text),
                raw_message=text,
            )

    title = strip_when(text)
    if not title:
        raise ValueError("Tell me what to remind you. Try: call dentist tomorrow 10am")
    return ReminderCreate(
        title=title[:200],
        notes="",
        due_at=_parse_due(None, text),
        raw_message=text,
    )
