"""Where a row came from: Telegram or the web."""

SOURCE_WEB = "web"
SOURCE_TELEGRAM = "telegram"


def record_origin(telegram_user_id: str | None = None, source: str | None = None) -> tuple[str, str]:
    """Return (source, telegram_user_id). Web rows keep telegram_user_id empty."""
    tid = (telegram_user_id or "").strip()
    if tid == SOURCE_WEB:
        tid = ""
    src = (source or "").strip().lower()
    if tid:
        return SOURCE_TELEGRAM, tid
    if src == SOURCE_TELEGRAM:
        return SOURCE_TELEGRAM, ""
    return SOURCE_WEB, ""
