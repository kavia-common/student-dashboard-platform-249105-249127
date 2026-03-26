from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.api.core.auth import get_current_user, require_roles
from src.api.core.db import get_db
from src.api.models import Class, ClassEnrollment, EnrollmentRole, User
from src.api.schemas import ClassCreate, ClassOut, ClassUpdate, ErrorResponse

router = APIRouter(prefix="/classes", tags=["Classes"])


@router.get(
    "",
    response_model=list[ClassOut],
    summary="List classes (all)",
    description="Lists all classes. (In a real app this might be restricted.)",
)
def list_classes(
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[ClassOut]:
    classes = db.scalars(select(Class).order_by(Class.code.asc())).all()
    return [ClassOut.model_validate(c) for c in classes]


@router.get(
    "/{class_id}",
    response_model=ClassOut,
    responses={404: {"model": ErrorResponse}},
    summary="Get a class by id",
)
def get_class(
    class_id: UUID,
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ClassOut:
    clazz = db.get(Class, class_id)
    if not clazz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    return ClassOut.model_validate(clazz)


@router.post(
    "",
    response_model=ClassOut,
    responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
    summary="Create a class (teacher/admin)",
)
def create_class(
    payload: ClassCreate,
    user: Annotated[User, Depends(require_roles({"teacher", "admin"}))],
    db: Annotated[Session, Depends(get_db)],
) -> ClassOut:
    clazz = Class(
        code=payload.code,
        name=payload.name,
        description=payload.description,
        term=payload.term,
        location=payload.location,
        meeting_days=payload.meeting_days,
        start_time=payload.start_time,
        end_time=payload.end_time,
        created_by_user_id=user.id,
    )
    db.add(clazz)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Class code must be unique") from exc

    db.refresh(clazz)

    # Auto-enroll creator as teacher
    enrollment = ClassEnrollment(class_id=clazz.id, user_id=user.id, enrollment_role=EnrollmentRole.teacher)
    db.add(enrollment)
    db.commit()

    return ClassOut.model_validate(clazz)


@router.patch(
    "/{class_id}",
    response_model=ClassOut,
    responses={404: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
    summary="Update a class (teacher/admin)",
)
def update_class(
    class_id: UUID,
    payload: ClassUpdate,
    _: Annotated[User, Depends(require_roles({"teacher", "admin"}))],
    db: Annotated[Session, Depends(get_db)],
) -> ClassOut:
    clazz = db.get(Class, class_id)
    if not clazz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(clazz, k, v)
    db.add(clazz)
    db.commit()
    db.refresh(clazz)
    return ClassOut.model_validate(clazz)


@router.delete(
    "/{class_id}",
    status_code=204,
    responses={404: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
    summary="Delete a class (teacher/admin)",
)
def delete_class(
    class_id: UUID,
    _: Annotated[User, Depends(require_roles({"teacher", "admin"}))],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    clazz = db.get(Class, class_id)
    if not clazz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    db.delete(clazz)
    db.commit()
    return None
