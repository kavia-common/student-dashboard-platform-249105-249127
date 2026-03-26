import os
from dataclasses import dataclass


def _get_env(name: str, default: str | None = None) -> str | None:
    """Internal helper to read env vars consistently."""
    value = os.getenv(name)
    if value is None:
        return default
    value = value.strip()
    return value if value else default


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables."""

    app_name: str
    app_version: str
    jwt_secret_key: str
    jwt_algorithm: str
    access_token_exp_minutes: int

    # Database connection string, expected to be SQLAlchemy-compatible
    database_url: str

    # CORS
    allowed_origins: list[str]
    allowed_methods: list[str]
    allowed_headers: list[str]
    cors_max_age: int

    @staticmethod
    def from_env() -> "Settings":
        """Create Settings from environment variables.

        Required env vars:
        - JWT_SECRET_KEY: secret used to sign JWTs
        - POSTGRES_URL or DATABASE_URL: database url (e.g. postgresql://host:port/db)
          (This repo's DB container exposes POSTGRES_URL by default.)

        Optional env vars:
        - ALLOWED_ORIGINS, ALLOWED_METHODS, ALLOWED_HEADERS, CORS_MAX_AGE
        """
        jwt_secret = _get_env("JWT_SECRET_KEY")
        if not jwt_secret:
            # Fail fast with a clear error; orchestrator will add it to .env.
            raise RuntimeError(
                "Missing required env var JWT_SECRET_KEY. Please set it in the backend .env."
            )

        db_url = _get_env("DATABASE_URL") or _get_env("POSTGRES_URL")
        if not db_url:
            raise RuntimeError(
                "Missing required env var DATABASE_URL or POSTGRES_URL for Postgres connection."
            )

        allowed_origins_raw = _get_env("ALLOWED_ORIGINS", "*")
        allowed_methods_raw = _get_env("ALLOWED_METHODS", "*")
        allowed_headers_raw = _get_env("ALLOWED_HEADERS", "*")
        cors_max_age_raw = _get_env("CORS_MAX_AGE", "3600")

        return Settings(
            app_name=_get_env("APP_NAME", "Student Dashboard API") or "Student Dashboard API",
            app_version=_get_env("APP_VERSION", "0.1.0") or "0.1.0",
            jwt_secret_key=jwt_secret,
            jwt_algorithm=_get_env("JWT_ALGORITHM", "HS256") or "HS256",
            access_token_exp_minutes=int(_get_env("ACCESS_TOKEN_EXPIRE_MINUTES", "120") or "120"),
            database_url=db_url,
            allowed_origins=[
                o.strip()
                for o in allowed_origins_raw.split(",")
                if o.strip()
            ]
            if allowed_origins_raw != "*"
            else ["*"],
            allowed_methods=[
                m.strip()
                for m in allowed_methods_raw.split(",")
                if m.strip()
            ]
            if allowed_methods_raw != "*"
            else ["*"],
            allowed_headers=[
                h.strip()
                for h in allowed_headers_raw.split(",")
                if h.strip()
            ]
            if allowed_headers_raw != "*"
            else ["*"],
            cors_max_age=int(cors_max_age_raw or "3600"),
        )


# Singleton settings cache
_SETTINGS: Settings | None = None


# PUBLIC_INTERFACE
def get_settings() -> Settings:
    """Return application Settings (cached after first load)."""
    global _SETTINGS
    if _SETTINGS is None:
        _SETTINGS = Settings.from_env()
    return _SETTINGS
