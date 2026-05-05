from __future__ import annotations

import os


def get_jwt_secret() -> str | None:
    secret = os.getenv("TEAM_BUILDER_JWT_SECRET", "").strip()
    return secret or None


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
