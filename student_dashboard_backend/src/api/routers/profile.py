from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.core.auth import get_current_user
from src.api.core.db import get_db
from src.api.models import Profile, User
from src.api.schemas import ErrorResponse, ProfileOut, ProfileUpdate

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.get(
    "",
    response_model=ProfileOut,
    responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}},
    summary="Get current user's profile",
    description="Fetches profile data for the authenticated user.",
)
def get_my_profile(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ProfileOut:
    profile = db.get(Profile, user.id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return ProfileOut.model_validate(profile)


@router.patch(
    "",
    response_model=ProfileOut,
    responses={404: {"model": ErrorResponse}, 401: {"model": ErrorResponse}},
    summary="Update current user's profile",
    description="Updates mutable fields on the authenticated user's profile.",
)
def update_my_profile(
    payload: ProfileUpdate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ProfileOut:
    profile = db.get(Profile, user.id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(profile, k, v)

    db.add(profile)
    db.commit()
    db.refresh(profile)
    return ProfileOut.model_validate(profile)
