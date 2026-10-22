from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.skills.todo.schemas import TodoCreate, TodoOut, TodoUpdate
from app.skills.todo.service import create_todo, delete_todo, list_todos, update_todo

router = APIRouter()
Status = Literal["open", "done", "all"]


@router.get("/todos", response_model=list[TodoOut])
async def get_todos(
    status: Status = Query(default="open"),
    db: AsyncSession = Depends(get_db),
):
    return await list_todos(db, status=status)


@router.post("/todos", response_model=TodoOut)
async def add_todo(payload: TodoCreate, db: AsyncSession = Depends(get_db)):
    return await create_todo(db, payload)


@router.patch("/todos/{todo_id}", response_model=TodoOut)
async def edit_todo(todo_id: UUID, payload: TodoUpdate, db: AsyncSession = Depends(get_db)):
    updated = await update_todo(db, todo_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Todo not found")
    return updated


@router.delete("/todos/{todo_id}")
async def remove_todo(todo_id: UUID, db: AsyncSession = Depends(get_db)):
    deleted = await delete_todo(db, todo_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Todo not found")
    return {"ok": True}
