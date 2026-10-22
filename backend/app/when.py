"""Parse casual due times used by reminders and todos."""

import re
from datetime import datetime, timedelta

from app.time import now_local

_IN_RE = re.compile(r"\bin\s+(\d+)\s+(minutes?|mins?|hours?|hrs?|days?)\b", re.I)
_AT_TIME_RE = re.compile(r"\b(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", re.I)
_CLOCK_RE = re.compile(r"\b(\d{1,2}):(\d{2})\b")
_LEAD_RE = re.compile(
    r"^(?:remind(?:\s+me(?:\s+to)?)?|reminder|todo|task|add)\s+",
    re.I,
)

_WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def _apply_time(base: datetime, hour: int, minute: int) -> datetime:
    return base.replace(hour=hour, minute=minute, second=0, microsecond=0)


def _clock(hour: int, minute: int, meridian: str | None) -> tuple[int, int]:
    hour = max(0, min(23, hour))
    minute = max(0, min(59, minute))
    if meridian:
        meridian = meridian.lower()
        hour = hour % 12
        if meridian == "pm":
            hour += 12
    return hour, minute


def parse_when(text: str, *, default_hours: int | None = 1) -> datetime | None:
    now = now_local()
    lowered = text.lower()

    relative = _IN_RE.search(text)
    if relative:
        count = int(relative.group(1))
        unit = relative.group(2).lower()
        if unit.startswith("min"):
            return now + timedelta(minutes=count)
        if unit.startswith("h"):
            return now + timedelta(hours=count)
        return now + timedelta(days=count)

    base = now
    used_day = False
    if "day after tomorrow" in lowered:
        base = now + timedelta(days=2)
        used_day = True
    elif "tomorrow" in lowered:
        base = now + timedelta(days=1)
        used_day = True
    elif re.search(r"\btoday\b", lowered):
        used_day = True
    else:
        for name, weekday in _WEEKDAYS.items():
            if re.search(rf"\b{name}\b", lowered):
                delta = (weekday - now.weekday()) % 7
                if delta == 0:
                    delta = 7
                base = now + timedelta(days=delta)
                used_day = True
                break

    stamped = _AT_TIME_RE.search(text)
    if stamped:
        hour, minute = _clock(int(stamped.group(1)), int(stamped.group(2) or 0), stamped.group(3))
        due = _apply_time(base, hour, minute)
        if due <= now and not used_day:
            due += timedelta(days=1)
        return due

    clock = _CLOCK_RE.search(text)
    if clock:
        hour, minute = _clock(int(clock.group(1)), int(clock.group(2)), None)
        due = _apply_time(base, hour, minute)
        if due <= now and not used_day:
            due += timedelta(days=1)
        return due

    if used_day:
        return _apply_time(base, 9, 0)

    if default_hours is None:
        return None
    return now + timedelta(hours=default_hours)


def strip_when(text: str) -> str:
    cleaned = _LEAD_RE.sub("", text.strip())
    cleaned = _IN_RE.sub(" ", cleaned)
    cleaned = _AT_TIME_RE.sub(" ", cleaned)
    cleaned = re.sub(r"\b(day after tomorrow|tomorrow|today|at|on)\b", " ", cleaned, flags=re.I)
    for name in _WEEKDAYS:
        cleaned = re.sub(rf"\b{name}\b", " ", cleaned, flags=re.I)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .,:-")
    return cleaned
