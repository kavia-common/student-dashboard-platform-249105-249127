from __future__ import annotations

from datetime import datetime, time
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr


class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Human-readable error message.")


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token.")
    token_type: Literal["bearer"] = Field("bearer", description="Token type, always 'bearer'.")
    expires_in: int = Field(..., description="Token lifetime in seconds.")
    user_id: UUID = Field(..., description="Authenticated user's UUID.")
    roles: list[str] = Field(..., description="Roles assigned to the user (e.g., student, teacher, admin).")


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email.")
    password: str = Field(..., min_length=1, description="User password.")


class ProfileOut(BaseModel):
    user_id: UUID
    display_name: str
    avatar_url: str | None = None
    grade_level: str | None = None
    major: str | None = None
    bio: str | None = None

    class Config:
        from_attributes = True


class ProfileUpdate(BaseModel):
    display_name: str | None = Field(None, description="Display name.")
    avatar_url: str | None = Field(None, description="Avatar URL.")
    grade_level: str | None = Field(None, description="Grade level (optional).")
    major: str | None = Field(None, description="Major (optional).")
    bio: str | None = Field(None, description="Bio (optional).")


class ClassOut(BaseModel):
    id: UUID
    code: str
    name: str
    description: str | None = None
    term: str | None = None
    location: str | None = None
    meeting_days: list[str] | None = None
    start_time: time | None = None
    end_time: time | None = None

    class Config:
        from_attributes = True


class ClassCreate(BaseModel):
    code: str = Field(..., min_length=1, description="Class code (unique), e.g. MATH-101")
    name: str = Field(..., min_length=1, description="Class name.")
    description: str | None = Field(None, description="Optional description.")
    term: str | None = Field(None, description="Academic term, e.g. Spring 2026.")
    location: str | None = Field(None, description="Location, e.g. Room 204.")
    meeting_days: list[str] | None = Field(None, description="Meeting days list, e.g. ['Mon','Wed'].")
    start_time: time | None = Field(None, description="Start time.")
    end_time: time | None = Field(None, description="End time.")


class ClassUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    term: str | None = None
    location: str | None = None
    meeting_days: list[str] | None = None
    start_time: time | None = None
    end_time: time | None = None


class AssignmentOut(BaseModel):
    id: UUID
    class_id: UUID
    title: str
    description: str | None = None
    due_at: datetime | None = None
    max_points: float | None = None
    status: str

    class Config:
        from_attributes = True


class AssignmentCreate(BaseModel):
    class_id: UUID = Field(..., description="Owning class UUID.")
    title: str = Field(..., min_length=1, description="Assignment title.")
    description: str | None = Field(None, description="Assignment description.")
    due_at: datetime | None = Field(None, description="Due date/time (UTC recommended).")
    max_points: float | None = Field(None, ge=0, description="Maximum points.")


class AssignmentUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    due_at: datetime | None = None
    max_points: float | None = Field(None, ge=0)
    status: str | None = Field(None, description="Assignment status enum value.")


class GradeOut(BaseModel):
    id: UUID
    assignment_id: UUID
    student_user_id: UUID
    points_earned: float
    feedback: str | None = None
    graded_by_user_id: UUID | None = None
    graded_at: datetime

    class Config:
        from_attributes = True


class GradeCreate(BaseModel):
    assignment_id: UUID = Field(..., description="Assignment UUID.")
    student_user_id: UUID = Field(..., description="Student user UUID.")
    points_earned: float = Field(..., ge=0, description="Points earned.")
    feedback: str | None = Field(None, description="Optional feedback.")


class AnnouncementOut(BaseModel):
    id: UUID
    class_id: UUID | None = None
    title: str
    body: str
    posted_by_user_id: UUID | None = None
    posted_at: datetime
    is_pinned: bool

    class Config:
        from_attributes = True


class AnnouncementCreate(BaseModel):
    class_id: UUID | None = Field(None, description="Optional class UUID (null = global).")
    title: str = Field(..., min_length=1, description="Announcement title.")
    body: str = Field(..., min_length=1, description="Announcement body.")
    is_pinned: bool = Field(False, description="Whether announcement is pinned.")


class AnnouncementUpdate(BaseModel):
    title: str | None = None
    body: str | None = None
    is_pinned: bool | None = None


class TodoOut(BaseModel):
    id: UUID
    user_id: UUID
    class_id: UUID | None = None
    title: str
    details: str | None = None
    due_at: datetime | None = None
    status: str
    completed_at: datetime | None = None

    class Config:
        from_attributes = True


class TodoCreate(BaseModel):
    class_id: UUID | None = Field(None, description="Optional class UUID.")
    title: str = Field(..., min_length=1, description="Todo title.")
    details: str | None = Field(None, description="Optional details.")
    due_at: datetime | None = Field(None, description="Optional due date/time.")


class TodoUpdate(BaseModel):
    title: str | None = None
    details: str | None = None
    due_at: datetime | None = None
    status: str | None = Field(None, description="Todo status enum value.")
    completed_at: datetime | None = None


class NotificationOut(BaseModel):
    id: UUID
    user_id: UUID
    type: str
    title: str
    body: str | None = None
    is_read: bool
    metadata: dict[str, Any]
    created_at: datetime
    read_at: datetime | None = None

    class Config:
        from_attributes = True
