from datetime import date
from typing import Literal

from fastapi import APIRouter, Query

from app.skills.news.service import get_news, list_news_days

router = APIRouter()
Topic = Literal["ai", "tech", "top"]


@router.get("/news/days")
async def news_days(topic: Topic = Query(default="ai")):
    return await list_news_days(topic)


@router.get("/news")
async def news(
    topic: Topic = Query(default="tech"),
    limit: int = Query(default=12, ge=10, le=15),
    day: date | None = Query(default=None),
    refresh: bool = Query(default=False),
):
    return await get_news(topic, limit=limit, day=day, refresh=refresh)
