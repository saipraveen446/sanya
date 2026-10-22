import json
import re
import time
import xml.etree.ElementTree as ET
from datetime import date
from html import unescape

import httpx
from sqlalchemy import desc, select

from app.database import SessionLocal
from app.llm import complete_json
from app.skills.news.models import NewsDigest
from app.time import now_local

FEEDS = {
    "ai": [
        "https://hnrss.org/newest?q=AI+OR+LLM+OR+OpenAI+OR+Anthropic",
        "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    ],
    "tech": [
        "https://hnrss.org/frontpage",
        "https://www.theverge.com/rss/index.xml",
    ],
    "top": [
        "https://hnrss.org/best",
        "https://hnrss.org/frontpage",
    ],
}

LABELS = {"ai": "AI News", "tech": "Tech News", "top": "Top News"}
_CACHE: dict[str, tuple[float, list[dict]]] = {}
_TTL = 8 * 60


def _text(node, *names) -> str:
    if node is None:
        return ""
    for name in names:
        child = node.find(name)
        if child is None:
            continue
        if child.text:
            return unescape(child.text).strip()
        href = child.get("href")
        if href:
            return href
    return unescape((node.text or "")).strip()


def _items_from_xml(raw: str) -> list[dict]:
    root = ET.fromstring(raw)
    found: list[dict] = []
    for item in list(root.findall(".//item")) + list(root.findall(".//{http://www.w3.org/2005/Atom}entry")):
        title = _text(item, "title", "{http://www.w3.org/2005/Atom}title")
        link = _text(item, "link", "{http://www.w3.org/2005/Atom}link")
        if not link:
            link_el = item.find("link") or item.find("{http://www.w3.org/2005/Atom}link")
            if link_el is not None:
                link = link_el.get("href") or (link_el.text or "")
        summary = re.sub(r"<[^>]+>", " ", _text(item, "description", "summary", "{http://www.w3.org/2005/Atom}summary"))
        summary = re.sub(r"(Article URL:|Comments URL:).*", "", summary, flags=re.I)
        summary = re.sub(r"\s+", " ", summary).strip()
        published = _text(
            item,
            "pubDate",
            "published",
            "updated",
            "{http://www.w3.org/2005/Atom}published",
            "{http://www.w3.org/2005/Atom}updated",
        )
        if title and link:
            found.append(
                {
                    "title": title[:180],
                    "url": link.strip(),
                    "summary": summary[:240],
                    "published": published[:80],
                    "source": "News",
                }
            )
    return found


async def _fetch_feed(url: str) -> list[dict]:
    headers = {"User-Agent": "SanyaPersonalAssistant/1.0"}
    async with httpx.AsyncClient(timeout=8.0, follow_redirects=True, headers=headers) as client:
        response = await client.get(url)
        response.raise_for_status()
        items = _items_from_xml(response.text)
        host = url.split("/")[2].replace("www.", "")
        for item in items:
            item["source"] = host
        return items


async def _llm_briefing(topic: str, query: str, limit: int) -> list[dict]:
    data = await complete_json(
        f"""Give {limit} current {topic} headlines a well-informed assistant would mention today.
Return ONLY JSON:
{{
  "items": [
    {{"title": "...", "url": "https://...", "summary": "one line", "source": "publication"}}
  ]
}}
Prefer real publications. If unsure of a URL, use a search URL.
""",
        query or topic,
    )
    items = (data or {}).get("items") or []
    cleaned = []
    for item in items[:limit]:
        title = (item.get("title") or "").strip()
        if not title:
            continue
        cleaned.append(
            {
                "title": title[:180],
                "url": item.get("url") or "",
                "summary": (item.get("summary") or "")[:240],
                "published": "",
                "source": item.get("source") or "Briefing",
            }
        )
    return cleaned


def _pack(topic: str, day: date, items: list[dict], query: str = "") -> dict:
    return {
        "topic": topic,
        "label": LABELS.get(topic, "News"),
        "day": day.isoformat(),
        "query": query,
        "items": items,
        "count": len(items),
    }


async def _load_digest(topic: str, day: date) -> dict | None:
    async with SessionLocal() as session:
        result = await session.execute(
            select(NewsDigest).where(NewsDigest.topic == topic, NewsDigest.day == day)
        )
        row = result.scalar_one_or_none()
        if not row:
            return None
        try:
            items = json.loads(row.items_json)
        except json.JSONDecodeError:
            items = []
        return _pack(topic, day, items)


async def _save_digest(topic: str, day: date, items: list[dict]) -> None:
    async with SessionLocal() as session:
        result = await session.execute(
            select(NewsDigest).where(NewsDigest.topic == topic, NewsDigest.day == day)
        )
        row = result.scalar_one_or_none()
        payload = json.dumps(items)
        if row:
            row.items_json = payload
        else:
            session.add(NewsDigest(topic=topic, day=day, items_json=payload))
        await session.commit()


async def list_news_days(topic: str = "ai") -> list[dict]:
    key = topic if topic in FEEDS else "tech"
    async with SessionLocal() as session:
        rows = await session.execute(
            select(NewsDigest).where(NewsDigest.topic == key).order_by(desc(NewsDigest.day)).limit(7)
        )
        found = []
        for row in rows.scalars().all():
            try:
                count = len(json.loads(row.items_json))
            except json.JSONDecodeError:
                count = 0
            found.append({"day": row.day.isoformat(), "count": count, "topic": key})
        return found


async def get_news(
    topic: str = "tech",
    *,
    query: str = "",
    limit: int = 12,
    day: date | None = None,
    refresh: bool = False,
) -> dict:
    key = topic if topic in FEEDS else "tech"
    today = now_local().date()
    chosen_day = day or today
    limit = max(10, min(15, int(limit or 12)))

    if not refresh:
        saved = await _load_digest(key, chosen_day)
        if saved and saved["items"]:
            return saved

    # Older days only show a digest that was already saved. Do not fetch
    # today's feeds and store them under a past date.
    if chosen_day != today:
        return _pack(key, chosen_day, [], query)

    cache_key = f"{key}:{chosen_day.isoformat()}"
    cached = _CACHE.get(cache_key)
    now = time.time()
    if cached and now - cached[0] < _TTL and not refresh:
        items = cached[1]
    else:
        items = []
        for url in FEEDS[key]:
            try:
                items.extend(await _fetch_feed(url))
            except Exception:
                continue
        seen: set[str] = set()
        unique = []
        for item in items:
            marker = item["title"].lower()
            if marker in seen:
                continue
            seen.add(marker)
            unique.append(item)
        items = unique
        if items:
            _CACHE[cache_key] = (now, items)

    if not items:
        items = await _llm_briefing(key, query, limit)

    picked = items[:limit]
    if picked:
        await _save_digest(key, chosen_day, picked)
    return _pack(key, chosen_day, picked, query)
