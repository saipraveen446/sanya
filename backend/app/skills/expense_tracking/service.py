from datetime import datetime
from decimal import Decimal
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import Select, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.origin import record_origin
from app.time import period_bounds
from app.skills.expense_tracking.models import Expense
from app.skills.expense_tracking.schemas import BreakdownItem, ExpenseCreate, SummaryOut


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=ZoneInfo(settings.app_timezone))
    return value


async def create_expense(session: AsyncSession, payload: ExpenseCreate) -> Expense:
    spent_at = payload.spent_at or datetime.now(ZoneInfo(settings.app_timezone))
    source, telegram_user_id = record_origin(payload.telegram_user_id, payload.source)
    expense = Expense(
        source=source,
        telegram_user_id=telegram_user_id,
        amount=payload.amount,
        currency=payload.currency or settings.default_currency,
        category=payload.category,
        merchant=payload.merchant,
        description=payload.description,
        spent_at=_aware(spent_at),
        raw_message=payload.raw_message,
    )
    session.add(expense)
    await session.commit()
    await session.refresh(expense)
    return expense


async def list_expenses(
    session: AsyncSession,
    period: str | None = None,
    telegram_user_id: str | None = None,
    limit: int = 100,
) -> list[Expense]:
    query: Select[tuple[Expense]] = select(Expense).order_by(desc(Expense.spent_at)).limit(limit)
    if period:
        start, end = period_bounds(period)
        query = query.where(Expense.spent_at >= start, Expense.spent_at < end)
    if telegram_user_id:
        query = query.where(Expense.telegram_user_id == telegram_user_id)
    result = await session.execute(query)
    return list(result.scalars().all())


async def delete_expense(session: AsyncSession, expense_id: UUID) -> bool:
    expense = await session.get(Expense, expense_id)
    if not expense:
        return False
    await session.delete(expense)
    await session.commit()
    return True


async def delete_last_expense(session: AsyncSession, telegram_user_id: str) -> Expense | None:
    result = await session.execute(
        select(Expense)
        .where(Expense.telegram_user_id == telegram_user_id)
        .order_by(desc(Expense.created_at))
        .limit(1)
    )
    expense = result.scalar_one_or_none()
    if not expense:
        return None
    await session.delete(expense)
    await session.commit()
    return expense


async def get_summary(
    session: AsyncSession,
    period: str,
    telegram_user_id: str | None = None,
) -> SummaryOut:
    start, end = period_bounds(period)
    filters = [Expense.spent_at >= start, Expense.spent_at < end]
    if telegram_user_id:
        filters.append(Expense.telegram_user_id == telegram_user_id)

    total_row = await session.execute(
        select(func.coalesce(func.sum(Expense.amount), 0), func.count(Expense.id)).where(*filters)
    )
    total, count = total_row.one()

    category_rows = await session.execute(
        select(Expense.category, func.sum(Expense.amount), func.count(Expense.id))
        .where(*filters)
        .group_by(Expense.category)
        .order_by(desc(func.sum(Expense.amount)))
    )
    merchant_rows = await session.execute(
        select(Expense.merchant, func.sum(Expense.amount), func.count(Expense.id))
        .where(*filters)
        .group_by(Expense.merchant)
        .order_by(desc(func.sum(Expense.amount)))
    )

    return SummaryOut(
        period=period,
        start=start,
        end=end,
        total=Decimal(total),
        count=int(count),
        currency=settings.default_currency,
        by_category=[
            BreakdownItem(name=name, total=Decimal(cat_total), count=int(cat_count))
            for name, cat_total, cat_count in category_rows.all()
        ],
        by_merchant=[
            BreakdownItem(name=name or "Unknown", total=Decimal(merch_total), count=int(merch_count))
            for name, merch_total, merch_count in merchant_rows.all()
        ],
    )
