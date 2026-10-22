from app.database import SessionLocal
from app.origin import record_origin
from app.skills.base import Skill, SkillResult
from app.skills.todo.parser import parse_todo_message
from app.skills.todo.schemas import TodoUpdate
from app.skills.todo.service import create_todo, delete_matching, list_todos, update_todo
from app.time import now_local


def _when(value) -> str:
    if not value:
        return ""
    local = value.astimezone(now_local().tzinfo)
    return local.strftime("%d %b, %I:%M %p")


class TodoSkill(Skill):
    id = "todo"
    name = "Todo"
    description = "Add tasks, see the open list, mark them done, and delete them."
    ready = True
    keywords = ("todo", "task", "tasks", "checklist", "to-do")
    examples = ("todo submit invoice tomorrow", "add todo buy groceries")
    commands = ("/todo",)

    async def parse(self, text: str) -> SkillResult:
        lowered = text.lower().strip()
        if lowered in {"list", "todo list", "my todos", "open", "pending"}:
            return SkillResult(skill_id=self.id, ok=True, message="list", data={"action": "list"})
        if lowered in {"completed", "done", "finished"}:
            return SkillResult(skill_id=self.id, ok=True, message="completed", data={"action": "completed"})
        if lowered.startswith("delete") or lowered.startswith("remove"):
            query = text.split(" ", 1)[1].strip() if " " in text else ""
            return SkillResult(
                skill_id=self.id,
                ok=True,
                message="delete",
                data={"action": "delete", "query": query},
            )
        if lowered.startswith("done ") or lowered.startswith("complete "):
            query = text.split(" ", 1)[1].strip()
            return SkillResult(
                skill_id=self.id,
                ok=True,
                message="complete",
                data={"action": "complete", "query": query},
            )
        try:
            payload = await parse_todo_message(text)
        except ValueError as exc:
            return SkillResult(skill_id=self.id, ok=False, message=str(exc))
        return SkillResult(
            skill_id=self.id,
            ok=True,
            message=payload.title,
            data={"action": "create", **payload.model_dump(mode="json")},
            payload=payload,
        )

    async def execute(self, parsed: SkillResult, *, telegram_user_id: str | None = None) -> SkillResult:
        action = (parsed.data or {}).get("action") or "create"
        async with SessionLocal() as session:
            if action == "list":
                items = await list_todos(session, status="open")
                if not items:
                    return SkillResult(skill_id=self.id, ok=True, message="No open todos.", data={"items": []})
                lines = ["<b>Todo list</b>"]
                for item in items:
                    when = f" — {_when(item.due_at)}" if item.due_at else ""
                    lines.append(f"• {item.title}{when}")
                return SkillResult(skill_id=self.id, ok=True, message="\n".join(lines))
            if action == "completed":
                items = await list_todos(session, status="done")
                if not items:
                    return SkillResult(skill_id=self.id, ok=True, message="No completed todos yet.")
                lines = ["<b>Completed</b>"]
                for item in items:
                    lines.append(f"• {item.title}")
                return SkillResult(skill_id=self.id, ok=True, message="\n".join(lines))
            if action == "delete":
                deleted = await delete_matching(session, (parsed.data or {}).get("query") or "")
                if not deleted:
                    return SkillResult(skill_id=self.id, ok=False, message="I could not find that todo.")
                return SkillResult(skill_id=self.id, ok=True, message=f"Deleted todo: {deleted.title}")
            if action == "complete":
                items = await list_todos(session, status="open")
                needle = ((parsed.data or {}).get("query") or "").lower()
                match = next((item for item in items if needle and needle in item.title.lower()), None)
                if not match:
                    return SkillResult(skill_id=self.id, ok=False, message="I could not find that open todo.")
                updated = await update_todo(session, match.id, TodoUpdate(is_done=True))
                return SkillResult(skill_id=self.id, ok=True, message=f"Completed: {updated.title}")

            payload = parsed.payload
            payload.source, payload.telegram_user_id = record_origin(
                telegram_user_id or payload.telegram_user_id
            )
            todo = await create_todo(session, payload)
        when = f"\nDue {_when(todo.due_at)}" if todo.due_at else ""
        return SkillResult(
            skill_id=self.id,
            ok=True,
            message=f"Todo added: <b>{todo.title}</b>{when}",
            data={"id": str(todo.id), **(parsed.data or {})},
            payload=todo,
        )

    def register_bot_handlers(self, application) -> None:
        from app.skills.todo.bot import register_handlers

        register_handlers(application)


todo_skill = TodoSkill()
