from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.core.config import get_settings
from src.api.routers.announcements import router as announcements_router
from src.api.routers.assignments import router as assignments_router
from src.api.routers.auth import router as auth_router
from src.api.routers.classes import router as classes_router
from src.api.routers.grades import router as grades_router
from src.api.routers.profile import router as profile_router
from src.api.routers.timetable import router as timetable_router
from src.api.routers.todos import router as todos_router

settings = get_settings()

openapi_tags = [
    {"name": "Auth", "description": "Authentication and current-user endpoints."},
    {"name": "Profile", "description": "Student/teacher profile management."},
    {"name": "Timetable", "description": "Class schedule / enrolled classes."},
    {"name": "Classes", "description": "Class catalog and class management (teacher/admin for writes)."},
    {"name": "Assignments", "description": "Assignments for enrolled classes (teacher/admin for writes)."},
    {"name": "Grades", "description": "Grades endpoints (teacher/admin for posting grades)."},
    {"name": "Announcements", "description": "Announcements endpoints (teacher/admin for writes)."},
    {"name": "Todos", "description": "Personal to-do list items."},
]

app = FastAPI(
    title=settings.app_name,
    description=(
        "Monolithic backend API for the Student Dashboard app.\n\n"
        "Auth:\n"
        "- Use `POST /auth/login` for password-based login.\n"
        "- Use `POST /auth/dev-login` for demo login against seeded users (dev only).\n\n"
        "Security:\n"
        "- Most endpoints require an `Authorization: Bearer <token>` header.\n"
        "- Role-based access is enforced for teacher/admin-only operations."
    ),
    version=settings.app_version,
    openapi_tags=openapi_tags,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=settings.allowed_methods,
    allow_headers=settings.allowed_headers,
    max_age=settings.cors_max_age,
)


@app.get(
    "/",
    tags=["System"],
    summary="Health check",
    description="Simple health check endpoint.",
)
def health_check():
    """Health check endpoint."""
    return {"message": "Healthy"}


@app.get(
    "/docs/auth",
    tags=["System"],
    summary="Auth usage help",
    description="Quick instructions for using JWT auth with this API.",
)
def auth_help():
    """Return brief instructions for authenticating with the API."""
    return {
        "how_to_login": {
            "password_login": {"method": "POST", "path": "/auth/login", "body": {"email": "user@example.com", "password": "..."},},
            "dev_login": {"method": "POST", "path": "/auth/dev-login", "body": {"email": "student1@example.com", "password": "ignored"},},
        },
        "how_to_call_authenticated_endpoints": {
            "header": "Authorization: Bearer <access_token>",
        },
    }


# Routers
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(timetable_router)
app.include_router(classes_router)
app.include_router(assignments_router)
app.include_router(grades_router)
app.include_router(announcements_router)
app.include_router(todos_router)
