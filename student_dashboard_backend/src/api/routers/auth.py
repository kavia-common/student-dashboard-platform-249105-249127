from __future__ import annotations

from datetime import timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.core.auth import authenticate_user, create_access_token, get_current_user, get_user_roles
from src.api.core.db import get_db
from src.api.models import User
from src.api.schemas import ErrorResponse, LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={401: {"model": ErrorResponse}},
    summary="Login and obtain a JWT access token",
    description="Authenticates a user using email+password and returns a JWT containing role claims.",
)
def login(payload: LoginRequest, db: Annotated[Session, Depends(get_db)]) -> TokenResponse:
    user = authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    roles = get_user_roles(db, user.id)
    token, expires_at = create_access_token(user_id=user.id, email=user.email, roles=roles)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=int((expires_at - expires_at.replace(tzinfo=timezone.utc)).total_seconds() or 0)
        if expires_at.tzinfo is None
        else int((expires_at - expires_at.astimezone(timezone.utc)).total_seconds() or 0),
        user_id=user.id,
        roles=roles,
    )


@router.post(
    "/dev-login",
    response_model=TokenResponse,
    responses={401: {"model": ErrorResponse}},
    summary="DEV ONLY: Login using seeded demo users without password verification",
    description=(
        "Seeded demo users have placeholder password hashes. "
        "This endpoint issues a JWT for an existing email WITHOUT password verification. "
        "Disable/remove in production."
    ),
)
def dev_login(payload: LoginRequest, db: Annotated[Session, Depends(get_db)]) -> TokenResponse:
    user = db.query(User).filter(User.email == str(payload.email)).one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    roles = get_user_roles(db, user.id)
    token, expires_at = create_access_token(user_id=user.id, email=user.email, roles=roles)
    expires_in = int((expires_at - expires_at.astimezone(timezone.utc)).total_seconds())
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=expires_in,
        user_id=user.id,
        roles=roles,
    )


@router.get(
    "/me",
    response_model=dict,
    summary="Get current authenticated user info",
    description="Returns basic identity info about the currently authenticated user.",
)
def me(user: Annotated[User, Depends(get_current_user)], db: Annotated[Session, Depends(get_db)]) -> dict:
    roles = get_user_roles(db, user.id)
    return {"user_id": str(user.id), "email": user.email, "roles": roles}
