from app.llm import complete_json


async def parse_news_message(text: str) -> dict:
    data = await complete_json(
        """You extract a tech / AI news request from a short user message.
Return ONLY JSON:
{
  "topic": "AI",
  "query": "latest LLM releases",
  "limit": 5
}
topic should be AI, tech, or general.
limit is 3 to 10.
""",
        text,
    )
    if not data or data.get("error"):
        return {"topic": "tech", "query": text, "limit": 5, "raw_message": text}
    limit = data.get("limit") or 5
    try:
        limit = max(3, min(10, int(limit)))
    except (TypeError, ValueError):
        limit = 5
    return {
        "topic": data.get("topic") or "tech",
        "query": data.get("query") or text,
        "limit": limit,
        "raw_message": text,
    }
