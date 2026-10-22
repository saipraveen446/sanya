from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.skills.expense_tracking.catalog import DEFAULT_CATEGORIES
from app.skills.expense_tracking.models import Category
from app.skills.expense_tracking.schemas import CategoryCreate


async def list_categories(session: AsyncSession, active_only: bool = True) -> list[Category]:
    query = select(Category).order_by(Category.sort_order, Category.group_name, Category.name)
    if active_only:
        query = query.where(Category.is_active.is_(True))
    result = await session.execute(query)
    return list(result.scalars().all())


async def create_category(session: AsyncSession, payload: CategoryCreate) -> Category:
    existing = await session.execute(select(Category).where(Category.name.ilike(payload.name.strip())))
    found = existing.scalar_one_or_none()
    if found:
        found.is_active = True
        found.group_name = payload.group_name.strip() or found.group_name
        if payload.keywords:
            found.keywords = payload.keywords
        if payload.examples:
            found.examples = payload.examples
        await session.commit()
        await session.refresh(found)
        return found

    result = await session.execute(select(Category.sort_order).order_by(Category.sort_order.desc()).limit(1))
    next_order = (result.scalar_one_or_none() or 0) + 1
    category = Category(
        name=payload.name.strip(),
        group_name=payload.group_name.strip() or "Daily life",
        keywords=payload.keywords.strip(),
        examples=payload.examples.strip(),
        sort_order=next_order,
        is_active=True,
    )
    session.add(category)
    await session.commit()
    await session.refresh(category)
    return category


async def seed_categories(session: AsyncSession) -> None:
    existing = {row.name: row for row in (await session.execute(select(Category))).scalars().all()}
    for index, item in enumerate(DEFAULT_CATEGORIES):
        found = existing.get(item["name"])
        if found:
            found.group_name = item["group_name"]
            found.keywords = item["keywords"]
            found.examples = item["examples"]
            found.sort_order = index + 1
            found.is_active = True
            continue
        session.add(
            Category(
                name=item["name"],
                group_name=item["group_name"],
                keywords=item["keywords"],
                examples=item["examples"],
                sort_order=index + 1,
                is_active=True,
            )
        )
    await session.commit()
