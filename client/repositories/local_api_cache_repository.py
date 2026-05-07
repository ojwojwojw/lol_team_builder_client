from __future__ import annotations

import json
import sqlite3
import threading
import time
from pathlib import Path

from repositories.dataset_repository import DATA_DIR


CACHE_DB_PATH = DATA_DIR / "team_builder_cache.sqlite3"
_CACHE_LOCK = threading.RLock()
_LAST_CACHE_ERROR = ""


class LocalApiCacheRepository:
    @staticmethod
    def ensure_ready() -> bool:
        with _CACHE_LOCK:
            try:
                connection = LocalApiCacheRepository._connect()
                connection.close()
                return True
            except (sqlite3.Error, OSError) as exc:
                LocalApiCacheRepository._remember_error(exc)
                return False

    @staticmethod
    def _connect() -> sqlite3.Connection:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(str(CACHE_DB_PATH), timeout=5, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=NORMAL")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS api_cache_entries (
                cache_key TEXT PRIMARY KEY,
                payload_json TEXT NOT NULL,
                expires_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_api_cache_entries_expires_at
            ON api_cache_entries (expires_at)
            """
        )
        connection.commit()
        return connection

    @staticmethod
    def _remember_error(exc: Exception) -> None:
        global _LAST_CACHE_ERROR
        _LAST_CACHE_ERROR = str(exc)

    @staticmethod
    def get(cache_key: str):
        now = int(time.time())
        with _CACHE_LOCK:
            try:
                connection = LocalApiCacheRepository._connect()
                row = connection.execute(
                    """
                    SELECT payload_json, expires_at
                    FROM api_cache_entries
                    WHERE cache_key = ?
                    """,
                    (cache_key,),
                ).fetchone()

                if row is None:
                    return None

                if int(row["expires_at"]) <= now:
                    connection.execute(
                        "DELETE FROM api_cache_entries WHERE cache_key = ?",
                        (cache_key,),
                    )
                    connection.commit()
                    return None

                return json.loads(row["payload_json"])
            except (sqlite3.Error, OSError, ValueError, TypeError) as exc:
                LocalApiCacheRepository._remember_error(exc)
                return None
            finally:
                try:
                    connection.close()
                except Exception:
                    pass

    @staticmethod
    def set(cache_key: str, payload, ttl_seconds: int) -> None:
        ttl_seconds = max(1, int(ttl_seconds))
        now = int(time.time())
        expires_at = now + ttl_seconds
        payload_json = json.dumps(payload, ensure_ascii=False)

        with _CACHE_LOCK:
            try:
                connection = LocalApiCacheRepository._connect()
                connection.execute(
                    """
                    INSERT INTO api_cache_entries (
                        cache_key,
                        payload_json,
                        expires_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(cache_key) DO UPDATE SET
                        payload_json = excluded.payload_json,
                        expires_at = excluded.expires_at,
                        updated_at = excluded.updated_at
                    """,
                    (cache_key, payload_json, expires_at, now),
                )
                LocalApiCacheRepository._prune_locked(connection, now)
                connection.commit()
            except (sqlite3.Error, OSError, TypeError, ValueError) as exc:
                LocalApiCacheRepository._remember_error(exc)
            finally:
                try:
                    connection.close()
                except Exception:
                    pass

    @staticmethod
    def clear() -> None:
        with _CACHE_LOCK:
            try:
                connection = LocalApiCacheRepository._connect()
                connection.execute("DELETE FROM api_cache_entries")
                connection.commit()
            except (sqlite3.Error, OSError) as exc:
                LocalApiCacheRepository._remember_error(exc)
            finally:
                try:
                    connection.close()
                except Exception:
                    pass

    @staticmethod
    def invalidate_after_loader_sync() -> None:
        LocalApiCacheRepository.clear()

    @staticmethod
    def get_stats() -> dict:
        with _CACHE_LOCK:
            try:
                connection = LocalApiCacheRepository._connect()
                row = connection.execute(
                    """
                    SELECT
                        COUNT(*) AS entry_count,
                        COALESCE(SUM(LENGTH(payload_json)), 0) AS payload_bytes,
                        COALESCE(MIN(updated_at), 0) AS oldest_updated_at,
                        COALESCE(MAX(updated_at), 0) AS newest_updated_at
                    FROM api_cache_entries
                    """
                ).fetchone()
            except (sqlite3.Error, OSError) as exc:
                LocalApiCacheRepository._remember_error(exc)
                row = {
                    "entry_count": 0,
                    "payload_bytes": 0,
                    "oldest_updated_at": 0,
                    "newest_updated_at": 0,
                }
            finally:
                try:
                    connection.close()
                except Exception:
                    pass

        file_path = Path(CACHE_DB_PATH)
        return {
            "cache_db_path": str(file_path),
            "cache_db_exists": file_path.exists(),
            "cache_db_size_bytes": file_path.stat().st_size if file_path.exists() else 0,
            "entry_count": int(row["entry_count"] or 0),
            "payload_bytes": int(row["payload_bytes"] or 0),
            "oldest_updated_at": int(row["oldest_updated_at"] or 0),
            "newest_updated_at": int(row["newest_updated_at"] or 0),
            "last_cache_error": _LAST_CACHE_ERROR,
        }

    @staticmethod
    def _prune_locked(connection: sqlite3.Connection, now: int) -> None:
        connection.execute(
            "DELETE FROM api_cache_entries WHERE expires_at <= ?",
            (now,),
        )
