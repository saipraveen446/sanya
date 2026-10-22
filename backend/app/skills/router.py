from app.config import settings
from app.llm import complete_json
from app.skills.base import Skill
from app.skills.registry import all_skills, get_skill

_PREFIXES = {
    "expense": "expense_tracking",
    "expenses": "expense_tracking",
    "spend": "expense_tracking",
    "expense_tracking": "expense_tracking",
    "news": "news",
    "remind": "reminders",
    "reminder": "reminders",
    "reminders": "reminders",
    "todo": "todo",
    "todos": "todo",
    "task": "todo",
    "tasks": "todo",
}

_COMMAND_WORDS = set(_PREFIXES)


def strip_skill_prefix(text: str) -> str:
    stripped = text.strip()
    if ":" in stripped:
        head, rest = stripped.split(":", 1)
        if rest.strip() and head.strip().lower().lstrip("/") in _PREFIXES:
            return rest.strip()
    parts = stripped.split(" ", 1)
    first = parts[0].lower().lstrip("/")
    if first in _COMMAND_WORDS and len(parts) == 2:
        return parts[1].strip()
    return stripped


def _score(text: str, skill: Skill) -> int:
    lowered = text.lower()
    return sum(1 for keyword in skill.keywords if keyword and keyword in lowered)


def _from_prefix(text: str) -> Skill | None:
    stripped = text.strip()
    if ":" in stripped:
        head, rest = stripped.split(":", 1)
        key = head.strip().lower().lstrip("/")
        if rest.strip() and key in _PREFIXES:
            return get_skill(_PREFIXES[key])
    first = stripped.split(" ", 1)[0].lower().lstrip("/")
    if first in _PREFIXES and " " in stripped:
        return get_skill(_PREFIXES[first])
    return None


async def resolve_skill(text: str, preferred: str | None = None) -> Skill:
    prefixed = _from_prefix(text)
    if prefixed:
        return prefixed

    skills = all_skills()
    ranked = sorted(((_score(text, skill), skill) for skill in skills), key=lambda item: item[0], reverse=True)
    top_score, top_skill = ranked[0] if ranked else (0, get_skill(settings.default_skill))
    unique_winner = top_score > 0 and (len(ranked) == 1 or ranked[1][0] < top_score)
    if unique_winner:
        return top_skill

    classified = await _classify_with_llm(text)
    if classified:
        return classified

    if preferred:
        found = get_skill(preferred)
        if found:
            return found
    return get_skill(settings.default_skill) or top_skill


async def _classify_with_llm(text: str) -> Skill | None:
    skills = all_skills()
    lines = "\n".join(f"- {skill.id}: {skill.description}" for skill in skills)
    ids = {skill.id for skill in skills}
    data = await complete_json(
        (
            "You route a short user message to exactly one Sanya skill.\n"
            "Return ONLY JSON: {\"skill\": \"<id>\"}.\n"
            "Skills:\n"
            f"{lines}\n"
            "If the message is money or a shop, use expense_tracking. "
            "If it is remember/alert later, use reminders. "
            "If it is a task to complete, use todo. "
            "If it asks for headlines, use news."
        ),
        text,
    )
    skill_id = (data or {}).get("skill") or (data or {}).get("tool")
    if skill_id in ids:
        return get_skill(skill_id)
    return None
