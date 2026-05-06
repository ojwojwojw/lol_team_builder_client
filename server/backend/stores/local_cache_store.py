from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from ..config import get_local_cache_db_path
from .firestore_client import utcnow_iso


ACCOUNT_NAMESPACE = "accounts"
MATCH_NAMESPACE = "matches"
CACHE_MISS = object()


def _cache_db_path() -> Path:
    return Path(get_local_cache_db_path())


@contextmanager
def _connect():
    db_path = _cache_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    try:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=NORMAL")
        _ensure_schema(connection)
        yield connection
        connection.commit()
    finally:
        connection.close()


def _ensure_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS cache_entries (
            cache_key TEXT PRIMARY KEY,
            dependency_token TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            cached_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS namespace_versions (
            namespace TEXT PRIMARY KEY,
            updated_at TEXT NOT NULL
        )
        """
    )


def _normalize_namespaces(namespaces: tuple[str, ...] | list[str]) -> list[str]:
    normalized = []
    seen = set()

    for namespace in namespaces:
        name = str(namespace or "").strip().lower()
        if not name or name in seen:
            continue
        seen.add(name)
        normalized.append(name)

    return normalized


def _build_dependency_token(connection: sqlite3.Connection, namespaces: list[str]) -> str:
    pieces = []
    for namespace in namespaces:
        row = connection.execute(
            "SELECT updated_at FROM namespace_versions WHERE namespace = ?",
            (namespace,),
        ).fetchone()
        updated_at = row[0] if row else ""
        pieces.append(f"{namespace}:{updated_at}")
    return "|".join(pieces)


def load_cached_json(cache_key: str, *namespaces: str):
    normalized_namespaces = _normalize_namespaces(namespaces)
    with _connect() as connection:
        row = connection.execute(
            """
            SELECT dependency_token, payload_json
            FROM cache_entries
            WHERE cache_key = ?
            """,
            (cache_key,),
        ).fetchone()
        if not row:
            return CACHE_MISS

        dependency_token, payload_json = row
        expected_token = _build_dependency_token(connection, normalized_namespaces)
        if dependency_token != expected_token:
            connection.execute(
                "DELETE FROM cache_entries WHERE cache_key = ?",
                (cache_key,),
            )
            return CACHE_MISS

        return json.loads(payload_json)


def save_cached_json(cache_key: str, payload, *namespaces: str) -> None:
    normalized_namespaces = _normalize_namespaces(namespaces)
    with _connect() as connection:
        dependency_token = _build_dependency_token(connection, normalized_namespaces)
        connection.execute(
            """
            INSERT INTO cache_entries (cache_key, dependency_token, payload_json, cached_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(cache_key) DO UPDATE SET
                dependency_token = excluded.dependency_token,
                payload_json = excluded.payload_json,
                cached_at = excluded.cached_at
            """,
            (
                cache_key,
                dependency_token,
                json.dumps(payload, ensure_ascii=False),
                utcnow_iso(),
            ),
        )


def touch_cache_namespace(namespace: str) -> None:
    normalized = str(namespace or "").strip().lower()
    if not normalized:
        return

    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO namespace_versions (namespace, updated_at)
            VALUES (?, ?)
            ON CONFLICT(namespace) DO UPDATE SET
                updated_at = excluded.updated_at
            """,
            (normalized, utcnow_iso()),
        )


def get_cache_stats() -> dict:
    db_path = _cache_db_path()
    with _connect() as connection:
        entry_count = connection.execute(
            "SELECT COUNT(*) FROM cache_entries"
        ).fetchone()[0]
        namespace_rows = connection.execute(
            """
            SELECT namespace, updated_at
            FROM namespace_versions
            ORDER BY namespace ASC
            """
        ).fetchall()

    return {
        "cache_db_path": str(db_path),
        "cache_db_exists": db_path.exists(),
        "cache_db_size_bytes": db_path.stat().st_size if db_path.exists() else 0,
        "entry_count": int(entry_count or 0),
        "namespaces": [
            {
                "namespace": row[0],
                "updated_at": row[1],
            }
            for row in namespace_rows
        ],
    }
