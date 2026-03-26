from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.core.auth import get_current_user, require_roles
from src.api.core.db import get_db
from src.api.models import Assignment, ClassEnrollment, User
from src.api.schemas import AssignmentCreate, AssignmentOut, AssignmentUpdate, ErrorResponse

router = APIRouter(prefix="/assignments", tags=["Assignments"])


@router.get(
    "",
    response_model=list[AssignmentOut],
    responses={401: {"model": ErrorResponse}},
    summary="List assignments for current user",
    description="Lists assignments for classes the authenticated user is enrolled in.",
)
def list_my_assignments(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    class_id: UUID | None = Query(None, description="Optional class filter."),
) -> list[AssignmentOut]:
    stmt = (
        select(Assignment)
        .join(ClassEnrollment, ClassEnrollment.class_id == Assignment.class_id)
        .where(ClassEnrollment.user_id == user.id)
        .order_by(Assignment.due_at.asc().nullslast(), Assignment.title.asc())
    )
    if class_id:
        stmt = stmt.where(Assignment.class_id == class_id)

    rows = db.scalars(stmt).all()
    return [AssignmentOut.model_validate(a) for a in rows]


@router.get(
    "/{assignment_id}",
    response_model=AssignmentOut,
    responses={404: {"model": ErrorResponse}},
    summary="Get assignment by id",
)
def get_assignment(
    assignment_id: UUID,
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> AssignmentOut:
    assignment = db.get(Assignment, assignment_id)
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
    return AssignmentOut.model_validate(assignment)


@router.post(
    "",
    response_model=AssignmentOut,
    responses={400: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
    summary="Create assignment (teacher/admin)",
)
def create_assignment(
    payload: AssignmentCreate,
    user: Annotated[User, Depends(require_roles({"teacher", "admin"}))],
    db: Annotated[Session, Depends(get_db)],
) -> AssignmentOut:
    assignment = Assignment(
        class_id=payload.class_id,
        title=payload.title,
        description=payload.description,
        due_at=payload.due_at,
        max_points=payload.max_points,
        created_by_user_id=user.id,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return AssignmentOut.model_validate(assignment)


@router.patch(
    "/{assignment_id}",
    response_model=AssignmentOut,
    responses={404: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
    summary="Update assignment (teacher/admin)",
)
def update_assignment(
    assignment_id: UUID,
    payload: AssignmentUpdate,
    _: Annotated[User, Depends(require_roles({"teacher", "admin"}))],
    db: Annotated[Session, Depends(get_db)],
) -> AssignmentOut:
    assignment = db.get(Assignment, assignment_id)
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(assignment, k, v)
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return AssignmentOut.model_validate(assignment)


@router.delete(
    "/{assignment_id}",
    status_code=204,
    responses={404: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
    summary="Delete assignment (teacher/admin)",
)
def delete_assignment(
    assignment_id: UUID,
    _: Annotated[User, Depends(require_roles({"teacher", "admin"}))],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    assignment = db.get(Assignment, assignment_id)
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
    db.delete(assignment)
    db.commit()
    return None
