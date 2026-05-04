from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache

from google.cloud import firestore

from ..config import get_firestore_database, get_firestore_project


def utcnow_iso() -> str:
    """Firestore 문서에 저장할 UTC 현재 시각을 ISO 문자열로 반환한다."""
    return datetime.now(timezone.utc).isoformat()


@lru_cache(maxsize=1)
def get_client() -> firestore.Client:
    """환경변수 설정을 반영한 Firestore 클라이언트를 재사용한다."""
    client_kwargs: dict[str, str] = {}

    project = get_firestore_project()
    if project:
        client_kwargs["project"] = project

    database = get_firestore_database()
    if database:
        client_kwargs["database"] = database

    return firestore.Client(**client_kwargs)
