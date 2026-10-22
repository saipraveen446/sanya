from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.skills.expense_tracking.schemas import CategoryCreate, CategoryOut, ExpenseCreate, ExpenseOut, SummaryOut
from app.skills.expense_tracking.category import create_category, list_categories
from app.skills.expense_tracking.service import create_expense, delete_expense, get_summary, list_expenses

router = APIRouter()
Period = Literal["today", "week", "month"]


@router.get("/expenses", response_model=list[ExpenseOut])
async def get_expenses(
    period: Period | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    return await list_expenses(db, period=period)


@router.post("/expenses", response_model=ExpenseOut)
async def add_expense(payload: ExpenseCreate, db: AsyncSession = Depends(get_db)):
    return await create_expense(db, payload)


@router.delete("/expenses/{expense_id}")
async def remove_expense(expense_id: UUID, db: AsyncSession = Depends(get_db)):
    deleted = await delete_expense(db, expense_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Expense not found")
    return {"ok": True}


@router.get("/summaries", response_model=SummaryOut)
async def summaries(
    period: Period = Query(default="month"),
    db: AsyncSession = Depends(get_db),
):
    return await get_summary(db, period)


@router.get("/categories", response_model=list[CategoryOut])
async def get_categories(db: AsyncSession = Depends(get_db)):
    return await list_categories(db)


@router.post("/categories", response_model=CategoryOut)
async def add_category(payload: CategoryCreate, db: AsyncSession = Depends(get_db)):
    return await create_category(db, payload)
