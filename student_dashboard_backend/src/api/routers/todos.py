from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.core.auth import get_current_user
from src.api.core.db import get_db
from src.api.models import Todo, User
from src.api.schemas import ErrorResponse, TodoCreate, TodoOut, TodoUpdate

router = APIRouter(prefix="/todos", tags=["Todos"])


@router.get(
    "",
    response_model=list[TodoOut],
    summary="List current user's todos",
)
def list_todos(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[TodoOut]:
    stmt = select(Todo).where(Todo.user_id == user.id).order_by(Todo.due_at.asc().nullslast(), Todo.created_at.desc())
    todos = db.scalars(stmt).all()
    return [TodoOut.model_validate(t) for t in todos]


@router.post(
    "",
    response_model=TodoOut,
    summary="Create a todo item",
)
def create_todo(
    payload: TodoCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> TodoOut:
    todo = Todo(
        user_id=user.id,
        class_id=payload.class_id,
        title=payload.title,
        details=payload.details,
        due_at=payload.due_at,
    )
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return TodoOut.model_validate(todo)


@router.patch(
    "/{todo_id}",
    response_model=TodoOut,
    responses={404: {"model": ErrorResponse}},
    summary="Update a todo item",
)
def update_todo(
    todo_id: UUID,
    payload: TodoUpdate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> TodoOut:
    todo = db.get(Todo, todo_id)
    if not todo or todo.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")

    data = payload.model_dump(exclude_unset=True)
    # If status transitions to done and completed_at not provided, set it
    if data.get("status") == "done" and "completed_at" not in data:
        data["completed_at"] = datetime.now(timezone.utc)

    for k, v in data.items():
        setattr(todo, k, v)

    db.add(todo)
    db.commit()
    db.refresh(todo)
    return TodoOut.model_validate(todo)


@router.delete(
    "/{todo_id}",
    status_code=204,
    responses={404: {"model": ErrorResponse}},
    summary="Delete a todo item",
)
def delete_todo(
    todo_id: UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    todo = db.get(Todo, todo_id)
    if not todo or todo.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    db.delete(todo)
    db.commit()
    return None
