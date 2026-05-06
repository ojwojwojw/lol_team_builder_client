from __future__ import annotations

import os
from pathlib import Path


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


def get_firestore_emulator_host() -> str | None:
    """로컬 개발용 Firestore Emulator 호스트를 환경변수에서 읽는다."""
    emulator_host = os.getenv("TEAM_BUILDER_FIRESTORE_EMULATOR_HOST", "").strip()
    if emulator_host:
        return emulator_host

    legacy_emulator_host = os.getenv("FIRESTORE_EMULATOR_HOST", "").strip()
    return legacy_emulator_host or None


def get_allowed_origins() -> list[str]:
    raw_origins = os.getenv("TEAM_BUILDER_CORS_ORIGINS", "").strip()
    if not raw_origins:
        return []

    return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]


def get_local_cache_db_path() -> str:
    raw_path = os.getenv("TEAM_BUILDER_LOCAL_CACHE_DB_PATH", "").strip()
    if raw_path:
        return raw_path

    project_root = Path(__file__).resolve().parents[2]
    return str(project_root / "server" / "data" / "team_builder_cache.sqlite3")
