from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache
import os

from google.cloud import firestore

from ..config import (
    get_firestore_database,
    get_firestore_emulator_host,
    get_firestore_project,
)


def utcnow_iso() -> str:
    """Firestore 문서에 저장할 UTC 현재 시각을 ISO 문자열로 반환한다."""
    return datetime.now(timezone.utc).isoformat()


@lru_cache(maxsize=1)
def get_client() -> firestore.Client:
    """환경변수 설정을 반영한 Firestore 클라이언트를 재사용한다."""
    client_kwargs: dict[str, str] = {}

    emulator_host = get_firestore_emulator_host()
    if emulator_host:
        # 로컬 개발에서는 에뮬레이터 주소를 명시적으로 주입하고,
        # 배포 환경에서는 이 값이 비어 있으므로 실제 Firestore에 연결된다.
        os.environ["FIRESTORE_EMULATOR_HOST"] = emulator_host

    project = get_firestore_project()
    if project:
        client_kwargs["project"] = project

    database = get_firestore_database()
    if database:
        client_kwargs["database"] = database

    return firestore.Client(**client_kwargs)
