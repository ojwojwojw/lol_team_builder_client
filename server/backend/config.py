from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = PROJECT_ROOT / "riot_matches.db"


def get_db_path() -> Path:
    raw_path = os.getenv("TEAM_BUILDER_DB_PATH", "").strip()
    if not raw_path:
        return DEFAULT_DB_PATH

    return Path(raw_path).expanduser().resolve()


def get_jwt_secret() -> str | None:
    secret = os.getenv("TEAM_BUILDER_JWT_SECRET", "").strip()
    return secret or None


def get_riot_api_key() -> str | None:
    api_key = os.getenv("TEAM_BUILDER_RIOT_API_KEY", "").strip()
    if api_key:
        return api_key

    legacy_api_key = os.getenv("RIOT_API_KEY", "").strip()
    return legacy_api_key or None


def get_firestore_project() -> str | None:
    project = os.getenv("TEAM_BUILDER_FIRESTORE_PROJECT", "").strip()
    return project or None


def get_firestore_database() -> str | None:
    database = os.getenv("TEAM_BUILDER_FIRESTORE_DATABASE", "").strip()
    return database or None


def get_allowed_origins() -> list[str]:
    raw_origins = os.getenv("TEAM_BUILDER_CORS_ORIGINS", "").strip()
    if not raw_origins:
        return []

    return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
