from app.database import SessionLocal
from app.origin import record_origin
from app.skills.base import Skill, SkillResult
from app.skills.reminders.parser import parse_reminder_message
from app.skills.reminders.service import create_reminder, delete_matching, list_reminders
from app.time import now_local


def _when(value) -> str:
    local = value.astimezone(now_local().tzinfo)
    return local.strftime("%d %b, %I:%M %p")


class RemindersSkill(Skill):
    id = "reminders"
    name = "Reminders"
    description = "Add reminders, list them, and get a Telegram alert when they are due."
    ready = True
    keywords = ("remind", "reminder", "remind me", "alarm", "ping me")
    examples = ("remind me to call dentist tomorrow 10am", "remind buy milk in 2 hours")
    commands = ("/reminders",)

    async def parse(self, text: str) -> SkillResult:
        lowered = text.lower().strip()
        if lowered in {"list", "my reminders", "show reminders", "reminders"} or lowered.startswith("list "):
            return SkillResult(skill_id=self.id, ok=True, message="list", data={"action": "list"})
        if lowered.startswith("delete") or lowered.startswith("remove"):
            query = text.split(" ", 1)[1].strip() if " " in text else ""
            return SkillResult(
                skill_id=self.id,
                ok=True,
                message="delete",
                data={"action": "delete", "query": query},
            )
        try:
            payload = await parse_reminder_message(text)
        except ValueError as exc:
            return SkillResult(skill_id=self.id, ok=False, message=str(exc))
        return SkillResult(
            skill_id=self.id,
            ok=True,
            message=f"{payload.title} · {_when(payload.due_at)}",
            data={"action": "create", **payload.model_dump(mode="json")},
            payload=payload,
        )

    async def execute(self, parsed: SkillResult, *, telegram_user_id: str | None = None) -> SkillResult:
        action = (parsed.data or {}).get("action") or "create"
        async with SessionLocal() as session:
            if action == "list":
                items = await list_reminders(session, telegram_user_id=None)
                if not items:
                    return SkillResult(skill_id=self.id, ok=True, message="No reminders yet.", data={"items": []})
                lines = ["<b>My reminders</b>"]
                for item in items:
                    lines.append(f"• {item.title} — {_when(item.due_at)}")
                return SkillResult(
                    skill_id=self.id,
                    ok=True,
                    message="\n".join(lines),
                    data={"items": [str(item.id) for item in items]},
                )
            if action == "delete":
                deleted = await delete_matching(
                    session,
                    (parsed.data or {}).get("query") or "",
                    telegram_user_id=None,
                )
                if not deleted:
                    return SkillResult(skill_id=self.id, ok=False, message="I could not find that reminder.")
                return SkillResult(skill_id=self.id, ok=True, message=f"Deleted reminder: {deleted.title}")

            payload = parsed.payload
            payload.source, payload.telegram_user_id = record_origin(
                telegram_user_id or payload.telegram_user_id
            )
            reminder = await create_reminder(session, payload)
        return SkillResult(
            skill_id=self.id,
            ok=True,
            message=f"Reminder set: <b>{reminder.title}</b>\nDue {_when(reminder.due_at)}",
            data={"id": str(reminder.id), **(parsed.data or {})},
            payload=reminder,
        )

    def register_bot_handlers(self, application) -> None:
        from app.skills.reminders.bot import register_handlers

        register_handlers(application)


reminders_skill = RemindersSkill()
