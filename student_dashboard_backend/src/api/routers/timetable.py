from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.core.auth import get_current_user
from src.api.core.db import get_db
from src.api.models import Class, ClassEnrollment, User
from src.api.schemas import ClassOut

router = APIRouter(prefix="/timetable", tags=["Timetable"])


@router.get(
    "",
    response_model=list[ClassOut],
    summary="Get current user's timetable (enrolled classes)",
    description="Returns a list of classes the authenticated user is enrolled in.",
)
def get_my_timetable(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> list[ClassOut]:
    stmt = (
        select(Class)
        .join(ClassEnrollment, ClassEnrollment.class_id == Class.id)
        .where(ClassEnrollment.user_id == user.id)
        .order_by(Class.code.asc())
    )
    classes = db.scalars(stmt).all()
    return [ClassOut.model_validate(c) for c in classes]
