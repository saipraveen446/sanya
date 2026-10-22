from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class SkillResult:
    skill_id: str
    ok: bool
    message: str
    data: dict | None = None
    payload: Any = None


class Skill(ABC):
    id: str
    name: str
    description: str
    ready: bool = False
    keywords: tuple[str, ...] = ()
    examples: tuple[str, ...] = ()
    commands: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "ready": self.ready,
            "keywords": list(self.keywords),
            "examples": list(self.examples),
            "commands": list(self.commands),
        }

    @abstractmethod
    async def parse(self, text: str) -> SkillResult:
        """Turn natural language into this skill's structured payload."""

    async def execute(self, parsed: SkillResult, *, telegram_user_id: str | None = None) -> SkillResult:
        return parsed

    async def handle(self, text: str, *, telegram_user_id: str | None = None) -> SkillResult:
        parsed = await self.parse(text)
        if not parsed.ok:
            return parsed
        if not self.ready:
            preview = parsed.message or "I understood the request."
            return SkillResult(
                skill_id=self.id,
                ok=False,
                message=f"{self.name} is coming soon.\n\n{preview}",
                data=parsed.data,
            )
        return await self.execute(parsed, telegram_user_id=telegram_user_id)

    def register_bot_handlers(self, application) -> None:
        return None
