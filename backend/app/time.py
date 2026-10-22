"""Sanya's clock. Every skill uses the same timezone (APP_TIMEZONE).

This is not a cron/scheduler. "What time is it?" lives here.
Scheduled work belongs on that skill, not in this file.
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.config import settings


def now_local() -> datetime:
    """Current time for you — one zone for all skills (default Asia/Kolkata)."""
    return datetime.now(ZoneInfo(settings.app_timezone))


def period_bounds(period: str) -> tuple[datetime, datetime]:
    """Start and end of today, this week, or this month in APP_TIMEZONE.

    Used for expense summaries. Other skills can reuse it, or define their own windows.
    """
    current = now_local()
    start_of_today = current.replace(hour=0, minute=0, second=0, microsecond=0)

    if period == "today":
        return start_of_today, start_of_today + timedelta(days=1)
    if period == "week":
        start = start_of_today - timedelta(days=start_of_today.weekday())
        return start, start + timedelta(days=7)
    if period == "month":
        start = start_of_today.replace(day=1)
        if start.month == 12:
            end = start.replace(year=start.year + 1, month=1)
        else:
            end = start.replace(month=start.month + 1)
        return start, end
    raise ValueError("period must be today, week, or month")
