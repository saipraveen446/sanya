import re
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo

from app.config import settings
from app.time import now_local
from app.database import SessionLocal
from app.llm import complete_json
from app.skills.expense_tracking.models import Category
from app.skills.expense_tracking.schemas import ExpenseCreate
from app.skills.expense_tracking.category import list_categories

FALLBACK_CATEGORY = "Miscellaneous"

_MONTHS = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}

_DATE_RE = re.compile(
    r"""
    \b(?:
        (?P<mon>jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|
                jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)
        \s+(?P<day>\d{1,2})\s*(?:st|nd|rd|th)?
      |
        (?P<day2>\d{1,2})\s*(?:st|nd|rd|th)?
        \s+(?P<mon2>jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|
                   jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)
      |
        (?P<mon3>jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|
                 jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)
        \s+(?P<ord>st|nd|rd)\b
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)

_ITEM_AMOUNT_RE = re.compile(
    r"^(?P<name>.+?)\s+(?:rs\.?|inr|₹)?\s*(?P<amount>\d+(?:\.\d{1,2})?)\s*(?:rs\.?|inr|₹)?\s*$",
    re.IGNORECASE,
)
_AMOUNT_NAME_RE = re.compile(
    r"^(?:rs\.?|inr|₹)?\s*(?P<amount>\d+(?:\.\d{1,2})?)\s*(?:rs\.?|inr|₹)?\s+(?P<name>.+)$",
    re.IGNORECASE,
)
_PAIR_RE = re.compile(
    r"(?P<name>[A-Za-z][A-Za-z0-9 &.'/-]*?)\s+(?:rs\.?|inr|₹)?\s*(?P<amount>\d+(?:\.\d{1,2})?)\b\s*(?:rs\.?|inr|₹)?",
    re.IGNORECASE,
)
_AT_RE = re.compile(r"\b(?:at|from)\s+([A-Za-z0-9 &.'-]{2,40})", re.IGNORECASE)


def _month_from(name: str | None) -> int | None:
    if not name:
        return None
    return _MONTHS.get(name.lower())


def extract_date(text: str) -> datetime | None:
    match = _DATE_RE.search(text or "")
    if not match:
        return None
    month = _month_from(match.group("mon") or match.group("mon2") or match.group("mon3"))
    ordinal_day = {"st": 1, "nd": 2, "rd": 3}.get((match.group("ord") or "").lower())
    day = int(match.group("day") or match.group("day2") or ordinal_day or 0)
    if not month or not 1 <= day <= 31:
        return None
    current = now_local()
    year = current.year
    try:
        parsed = current.replace(year=year, month=month, day=day, hour=12, minute=0, second=0, microsecond=0)
    except ValueError:
        return None
    if parsed - current > timedelta(days=180):
        parsed = parsed.replace(year=year - 1)
    return parsed


def strip_date(text: str) -> str:
    cleaned = _DATE_RE.sub(" ", text or "")
    cleaned = re.sub(r"\b(?:st|nd|rd|th)\b", " ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(
        r"^\s*(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
        r"jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\b",
        " ",
        cleaned,
        flags=re.IGNORECASE,
    )
    return re.sub(r"\s+", " ", cleaned).strip(" -,")


def guess_category(text: str, categories: list[Category]) -> str:
    lowered = text.lower()
    ranked: list[tuple[int, str, str]] = []
    for item in categories:
        for keyword in [part.strip().lower() for part in item.keywords.split(",") if part.strip()]:
            ranked.append((len(keyword), keyword, item.name))
        ranked.append((len(item.name), item.name.lower(), item.name))
    ranked.sort(reverse=True)
    for _, keyword, name in ranked:
        if keyword and keyword in lowered:
            return name
    return FALLBACK_CATEGORY


def _spent_at(value: datetime | None) -> datetime:
    return value or now_local()


def _parse_chunk(chunk: str, categories: list[Category], spent_at: datetime | None) -> ExpenseCreate | None:
    raw = chunk.strip(" -,")
    if not raw:
        return None
    local_date = extract_date(raw) or spent_at
    cleaned = strip_date(raw)
    if not cleaned:
        return None

    name = ""
    amount: Decimal | None = None
    item_match = _ITEM_AMOUNT_RE.match(cleaned)
    flip_match = _AMOUNT_NAME_RE.match(cleaned)
    if item_match:
        name = item_match.group("name").strip()
        amount = Decimal(item_match.group("amount"))
    elif flip_match:
        name = flip_match.group("name").strip()
        amount = Decimal(flip_match.group("amount"))
    else:
        numbers = list(re.finditer(r"\d+(?:\.\d{1,2})?", cleaned))
        if numbers:
            last = numbers[-1]
            amount = Decimal(last.group())
            name = f"{cleaned[: last.start()]} {cleaned[last.end() :]}".strip()
    if amount is None or amount <= 0 or not name:
        return None

    merchant_match = _AT_RE.search(name)
    merchant = merchant_match.group(1).strip(" .") if merchant_match else None
    description = name
    if merchant:
        description = re.sub(rf"\b(?:at|from)\s+{re.escape(merchant)}\b", " ", description, flags=re.I)
    description = re.sub(r"\s+", " ", description).strip(" -") or "Expense"
    names = {item.name for item in categories} or {FALLBACK_CATEGORY}
    category = guess_category(f"{description} {name}", categories)
    if category not in names:
        category = FALLBACK_CATEGORY if FALLBACK_CATEGORY in names else next(iter(names))
    return ExpenseCreate(
        amount=amount,
        currency=settings.default_currency,
        category=category,
        merchant=merchant,
        description=description[:120],
        spent_at=_spent_at(local_date),
        raw_message=raw,
    )


def fallback_parse_many(text: str, categories: list[Category]) -> list[ExpenseCreate]:
    shared_date = extract_date(text)
    items: list[ExpenseCreate] = []
    for line in re.split(r"[\n;]+", text or ""):
        line = line.strip()
        if not line:
            continue
        line_date = extract_date(line)
        cleaned = strip_date(line)
        if line_date and not cleaned:
            shared_date = line_date
            continue
        spent_at = line_date or shared_date
        for chunk in re.split(r",+", cleaned):
            chunk = chunk.strip(" -")
            if not chunk:
                continue
            pairs = [(name.strip(), amount) for name, amount in _PAIR_RE.findall(chunk) if name.strip()]
            if len(pairs) > 1:
                for name, amount in pairs:
                    parsed = _parse_chunk(f"{name} {amount}", categories, spent_at)
                    if parsed:
                        items.append(parsed)
                continue
            parsed = _parse_chunk(chunk, categories, spent_at)
            if parsed:
                items.append(parsed)
    return items


def fallback_parse(text: str, categories: list[Category]) -> ExpenseCreate:
    items = fallback_parse_many(text, categories)
    if items:
        return items[0]
    raise ValueError("I could not find an amount. Try: tiffin 80 or oct 1 tiffin 135")


def _amount_is_date_day(amount: Decimal, text: str) -> bool:
    date = extract_date(text)
    if not date or amount != Decimal(date.day):
        return False
    return bool(re.search(r"\d+(?:\.\d{1,2})?", strip_date(text)))


def _parse_iso_date(value: str | None, fallback: datetime | None) -> datetime:
    if value:
        try:
            parsed = datetime.strptime(value, "%Y-%m-%d")
            tz = ZoneInfo(settings.app_timezone)
            current = now_local()
            return parsed.replace(tzinfo=tz, hour=current.hour, minute=current.minute, second=current.second)
        except ValueError:
            pass
    return fallback or now_local()


def _system_prompt(categories: list[Category]) -> str:
    lines = []
    for item in categories:
        extra = f" — e.g. {item.examples}" if item.examples else ""
        lines.append(f"- {item.name}{extra}")
    joined = "\n".join(lines)
    return f"""You extract one or more daily expenses from a short user message.
Dates like "Oct 1" or "October 2nd" are DATES, never amounts.
The amount is the rupee number after the item name: "oct 1 tiffin 135" → amount 135, date 2026-10-01.
Multiple lines or comma-separated items are SEPARATE expenses.
A date on its own line applies to the items below it.

Return ONLY JSON:
{{
  "items": [
    {{
      "amount": 135,
      "currency": "INR",
      "category": "Tiffin",
      "merchant": null,
      "description": "tiffin",
      "date": "2026-10-01"
    }}
  ]
}}

category MUST be exactly one of:
{joined}
"""


async def parse_expense_messages(text: str) -> list[ExpenseCreate]:
    async with SessionLocal() as session:
        categories = await list_categories(session)

    fallback_items = fallback_parse_many(text, categories)
    if fallback_items:
        return fallback_items

    today = now_local().date().isoformat()
    data = await complete_json(
        _system_prompt(categories),
        f"Today is {today}. Timezone is {settings.app_timezone}. Message:\n{text}",
    )
    raw_items = (data or {}).get("items") if isinstance(data, dict) else None
    if data and not raw_items and data.get("amount") not in (None, ""):
        raw_items = [data]
    if not raw_items:
        raise ValueError("I could not find an amount. Try: tiffin 80 or oct 1 tiffin 135")

    names = [item.name for item in categories]
    parsed: list[ExpenseCreate] = []
    shared = extract_date(text)
    for row in raw_items:
        try:
            amount = Decimal(str(row.get("amount")))
        except (InvalidOperation, TypeError, AttributeError):
            continue
        if amount <= 0 or _amount_is_date_day(amount, text):
            continue
        category = row.get("category") or FALLBACK_CATEGORY
        if category not in names:
            category = guess_category(str(row.get("description") or text), categories)
        merchant = row.get("merchant") or None
        if merchant in {"null", "None", "unknown", "Unknown"}:
            merchant = None
        parsed.append(
            ExpenseCreate(
                amount=amount,
                currency=row.get("currency") or settings.default_currency,
                category=category,
                merchant=merchant,
                description=(row.get("description") or text)[:200],
                spent_at=_parse_iso_date(row.get("date"), shared),
                raw_message=text,
            )
        )
    if parsed:
        return parsed
    raise ValueError("I could not find an amount. Try: tiffin 80 or oct 1 tiffin 135")


async def parse_expense_message(text: str) -> ExpenseCreate:
    items = await parse_expense_messages(text)
    return items[0]
