from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.core.auth import get_current_user, require_roles
from src.api.core.db import get_db
from src.api.models import Announcement, User
from src.api.schemas import AnnouncementCreate, AnnouncementOut, AnnouncementUpdate, ErrorResponse

router = APIRouter(prefix="/announcements", tags=["Announcements"])


@router.get(
    "",
    response_model=list[AnnouncementOut],
    summary="List announcements",
    description="Lists announcements, optionally filtered by class_id.",
)
def list_announcements(
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    class_id: UUID | None = Query(None, description="Optional class filter."),
) -> list[AnnouncementOut]:
    stmt = select(Announcement).order_by(Announcement.is_pinned.desc(), Announcement.posted_at.desc())
    if class_id:
        stmt = stmt.where(Announcement.class_id == class_id)
    rows = db.scalars(stmt).all()
    return [AnnouncementOut.model_validate(a) for a in rows]


@router.post(
    "",
    response_model=AnnouncementOut,
    responses={403: {"model": ErrorResponse}},
    summary="Create announcement (teacher/admin)",
)
def create_announcement(
    payload: AnnouncementCreate,
    user: Annotated[User, Depends(require_roles({"teacher", "admin"}))],
    db: Annotated[Session, Depends(get_db)],
) -> AnnouncementOut:
    ann = Announcement(
        class_id=payload.class_id,
        title=payload.title,
        body=payload.body,
        posted_by_user_id=user.id,
        is_pinned=payload.is_pinned,
    )
    db.add(ann)
    db.commit()
    db.refresh(ann)
    return AnnouncementOut.model_validate(ann)


@router.patch(
    "/{announcement_id}",
    response_model=AnnouncementOut,
    responses={404: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
    summary="Update announcement (teacher/admin)",
)
def update_announcement(
    announcement_id: UUID,
    payload: AnnouncementUpdate,
    _: Annotated[User, Depends(require_roles({"teacher", "admin"}))],
    db: Annotated[Session, Depends(get_db)],
) -> AnnouncementOut:
    ann = db.get(Announcement, announcement_id)
    if not ann:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(ann, k, v)
    db.add(ann)
    db.commit()
    db.refresh(ann)
    return AnnouncementOut.model_validate(ann)


@router.delete(
    "/{announcement_id}",
    status_code=204,
    responses={404: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
    summary="Delete announcement (teacher/admin)",
)
def delete_announcement(
    announcement_id: UUID,
    _: Annotated[User, Depends(require_roles({"teacher", "admin"}))],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    ann = db.get(Announcement, announcement_id)
    if not ann:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found")
    db.delete(ann)
    db.commit()
    return None
