from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.core.config import get_settings
from src.api.core.db import get_db
from src.api.models import User, UserRoleRow

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _unauthorized(detail: str = "Not authenticated") -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


def _forbidden(detail: str = "Not enough permissions") -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


# PUBLIC_INTERFACE
def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a plain password against a stored hash.

    Note: seeded demo users contain placeholder hashes, so verification will fail
    unless the user was created/updated with real hashes. Use /auth/dev-login for
    demo-only flows.
    """
    return pwd_context.verify(plain_password, password_hash)


# PUBLIC_INTERFACE
def hash_password(plain_password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(plain_password)


# PUBLIC_INTERFACE
def create_access_token(*, user_id: UUID, email: str, roles: list[str]) -> tuple[str, datetime]:
    """Create a signed JWT access token with role claims."""
    settings = get_settings()
    expire = _utcnow() + timedelta(minutes=settings.access_token_exp_minutes)
    payload = {
        "sub": str(user_id),
        "email": email,
        "roles": roles,
        "exp": expire,
        "iat": _utcnow(),
        "type": "access",
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, expire


def _decode_token(token: str) -> dict:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except Exception as exc:  # noqa: BLE001
        raise _unauthorized("Invalid token") from exc


# PUBLIC_INTERFACE
def get_user_roles(db: Session, user_id: UUID) -> list[str]:
    """Fetch roles for a user from the database."""
    rows = db.execute(select(UserRoleRow.role).where(UserRoleRow.user_id == user_id)).all()
    return [r[0].value for r in rows]


# PUBLIC_INTERFACE
def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Authenticate by email + password."""
    user = db.scalar(select(User).where(User.email == email))
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


# PUBLIC_INTERFACE
def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """FastAPI dependency: get current authenticated user from JWT."""
    payload = _decode_token(token)
    sub = payload.get("sub")
    if not sub:
        raise _unauthorized("Invalid token payload")
    try:
        user_id = UUID(sub)
    except Exception as exc:  # noqa: BLE001
        raise _unauthorized("Invalid token subject") from exc

    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise _unauthorized("User not found or inactive")
    return user


# PUBLIC_INTERFACE
def require_roles(required: set[str]):
    """Factory for a dependency that enforces at least one required role."""

    def _dep(
        user: Annotated[User, Depends(get_current_user)],
        db: Annotated[Session, Depends(get_db)],
    ) -> User:
        roles = set(get_user_roles(db, user.id))
        if roles.isdisjoint(required):
            raise _forbidden()
        return user

    return _dep
