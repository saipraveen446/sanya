from app.skills.base import Skill

_SKILLS: dict[str, Skill] = {}
_LOADED = False
_ALIASES = {
    "expense": "expense_tracking",
    "expenses": "expense_tracking",
    "reminder": "reminders",
    "remind": "reminders",
    "todos": "todo",
    "task": "todo",
    "tasks": "todo",
}


def register(skill: Skill) -> None:
    _SKILLS[skill.id] = skill


def get_skill(skill_id: str | None) -> Skill | None:
    load_skills()
    if not skill_id:
        return None
    return _SKILLS.get(_ALIASES.get(skill_id.strip().lower(), skill_id.strip().lower()))


def all_skills() -> list[Skill]:
    load_skills()
    return list(_SKILLS.values())


def load_skills() -> None:
    global _LOADED
    if _LOADED:
        return
    from app.skills.expense_tracking.skill import expense_tracking_skill
    from app.skills.news.skill import news_skill
    from app.skills.reminders.skill import reminders_skill
    from app.skills.todo.skill import todo_skill

    for skill in (expense_tracking_skill, reminders_skill, todo_skill, news_skill):
        register(skill)
    _LOADED = True
