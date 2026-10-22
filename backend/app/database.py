from collections.abc import AsyncGenerator
import ssl

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.models.base import Base


def _async_database_url(url: str) -> tuple[str, dict]:
    connect_args: dict = {}
    needs_ssl = "sslmode=require" in url or "supabase.co" in url or "supabase.com" in url
    if "sslmode=require" in url:
        url = url.replace("?sslmode=require", "").replace("&sslmode=require", "")
    if needs_ssl:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        connect_args["ssl"] = ctx
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url, connect_args


DATABASE_URL, CONNECT_ARGS = _async_database_url(settings.database_url)

engine = create_async_engine(DATABASE_URL, echo=False, connect_args=CONNECT_ARGS)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    from app import models  # noqa: F401 — register skill tables on Base.metadata

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        await connection.execute(text("ALTER TABLE expenses ALTER COLUMN category TYPE VARCHAR(128)"))
        await connection.execute(text("ALTER TABLE reminders ADD COLUMN IF NOT EXISTS pre_notified_at TIMESTAMPTZ"))
        for table in ("expenses", "reminders", "todos"):
            await connection.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS source VARCHAR(16) NOT NULL DEFAULT 'web'"))
            await connection.execute(
                text(
                    f"""
                    UPDATE {table}
                    SET source = 'telegram'
                    WHERE telegram_user_id IS NOT NULL
                      AND btrim(telegram_user_id) <> ''
                      AND telegram_user_id <> 'web'
                    """
                )
            )
            await connection.execute(
                text(
                    f"""
                    UPDATE {table}
                    SET telegram_user_id = ''
                    WHERE telegram_user_id IS NULL OR telegram_user_id = 'web'
                    """
                )
            )
            await connection.execute(text(f"CREATE INDEX IF NOT EXISTS idx_{table}_source ON {table} (source)"))
    from app.skills.expense_tracking.category import seed_categories

    async with SessionLocal() as session:
        await seed_categories(session)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session
