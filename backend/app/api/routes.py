from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.skills.expense_tracking.routes import router as expenses_router
from app.skills.news.routes import router as news_router
from app.skills.registry import all_skills, get_skill
from app.skills.reminders.routes import router as reminders_router
from app.skills.router import resolve_skill, strip_skill_prefix
from app.skills.todo.routes import router as todo_router

router = APIRouter()
router.include_router(expenses_router)
router.include_router(reminders_router)
router.include_router(todo_router)
router.include_router(news_router)


class ParseIn(BaseModel):
    text: str = Field(min_length=1)
    skill: str | None = None
    telegram_user_id: str = ""


@router.get("/skills")
async def list_skills():
    return [skill.as_dict() for skill in all_skills()]


@router.post("/skills/parse")
async def parse_for_skill(payload: ParseIn):
    skill = get_skill(payload.skill) if payload.skill else None
    if payload.skill and skill is None:
        raise HTTPException(status_code=404, detail=f"Unknown skill: {payload.skill}")
    if skill is None:
        skill = await resolve_skill(payload.text)
    result = await skill.parse(strip_skill_prefix(payload.text))
    return {
        "skill": result.skill_id,
        "ok": result.ok,
        "message": result.message,
        "data": result.data,
    }


@router.post("/skills/handle")
async def handle_for_skill(payload: ParseIn):
    skill = get_skill(payload.skill) if payload.skill else None
    if payload.skill and skill is None:
        raise HTTPException(status_code=404, detail=f"Unknown skill: {payload.skill}")
    if skill is None:
        skill = await resolve_skill(payload.text)
    result = await skill.handle(
        strip_skill_prefix(payload.text),
        telegram_user_id=payload.telegram_user_id or None,
    )
    return {
        "skill": result.skill_id,
        "ok": result.ok,
        "message": result.message,
        "data": result.data,
    }
