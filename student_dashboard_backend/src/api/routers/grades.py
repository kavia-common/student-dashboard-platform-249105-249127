from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.api.core.auth import get_current_user, require_roles
from src.api.core.db import get_db
from src.api.models import Grade, User
from src.api.schemas import ErrorResponse, GradeCreate, GradeOut

router = APIRouter(prefix="/grades", tags=["Grades"])


@router.get(
    "",
    response_model=list[GradeOut],
    summary="List grades for current user",
    description="Students see their own grades; teachers/admins can also use /grades/by-student/{student_id}.",
)
def list_my_grades(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[GradeOut]:
    stmt = select(Grade).where(Grade.student_user_id == user.id).order_by(Grade.graded_at.desc())
    grades = db.scalars(stmt).all()
    return [GradeOut.model_validate(g) for g in grades]


@router.get(
    "/by-student/{student_user_id}",
    response_model=list[GradeOut],
    responses={403: {"model": ErrorResponse}},
    summary="List grades for a specific student (teacher/admin)",
)
def list_student_grades(
    student_user_id: UUID,
    _: Annotated[User, Depends(require_roles({"teacher", "admin"}))],
    db: Annotated[Session, Depends(get_db)],
) -> list[GradeOut]:
    stmt = select(Grade).where(Grade.student_user_id == student_user_id).order_by(Grade.graded_at.desc())
    grades = db.scalars(stmt).all()
    return [GradeOut.model_validate(g) for g in grades]


@router.post(
    "",
    response_model=GradeOut,
    responses={400: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
    summary="Create/overwrite a grade (teacher/admin)",
    description="Creates a grade; if (assignment_id, student_user_id) already exists, returns a 400.",
)
def create_grade(
    payload: GradeCreate,
    grader: Annotated[User, Depends(require_roles({"teacher", "admin"}))],
    db: Annotated[Session, Depends(get_db)],
) -> GradeOut:
    grade = Grade(
        assignment_id=payload.assignment_id,
        student_user_id=payload.student_user_id,
        points_earned=payload.points_earned,
        feedback=payload.feedback,
        graded_by_user_id=grader.id,
    )
    db.add(grade)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Grade for this student+assignment already exists",
        ) from exc
    db.refresh(grade)
    return GradeOut.model_validate(grade)
