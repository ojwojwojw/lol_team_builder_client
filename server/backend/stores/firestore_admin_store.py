from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from .firestore_client import get_client


ALLOWED_COLLECTIONS = {
    "app_users",
    "riot_accounts",
    "matches",
    "match_participants",
}

TIMESTAMP_FIELDS_BY_COLLECTION = {
    "app_users": "created_at",
    "riot_accounts": "fetched_at",
    "matches": "game_start_timestamp",
    "match_participants": "game_start_timestamp",
}


def _validate_collection_name(collection_name: str) -> str:
    normalized = (collection_name or "").strip()
    if normalized not in ALLOWED_COLLECTIONS:
        raise ValueError(f"Unsupported collection: {collection_name}")
    return normalized


def _collection(collection_name: str):
    return get_client().collection(_validate_collection_name(collection_name))


def _chunked(values: list[str], size: int = 400):
    for index in range(0, len(values), size):
        yield values[index:index + size]


def _approx_json_size(payload: dict) -> int:
    return len(json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8"))


def get_collection_stats() -> list[dict]:
    """허용된 Firestore 컬렉션별 문서 수와 대략적인 JSON 크기를 집계한다."""
    rows = []
    for collection_name in sorted(ALLOWED_COLLECTIONS):
        doc_count = 0
        approx_bytes = 0
        for snapshot in _collection(collection_name).stream():
            payload = snapshot.to_dict() or {}
            approx_bytes += _approx_json_size(payload)
            doc_count += 1

        rows.append({
            "collection": collection_name,
            "documents": doc_count,
            "approx_json_bytes": approx_bytes,
        })
    return rows


def list_collection_documents(collection_name: str, limit: int) -> list[dict]:
    """컬렉션 문서 목록을 제한 개수만큼 읽어 모니터링 화면에 전달한다."""
    docs = _collection(collection_name).limit(limit).stream()
    result = []
    for snapshot in docs:
        payload = snapshot.to_dict() or {}
        result.append({
            "id": snapshot.id,
            "data": payload,
            "approx_json_bytes": _approx_json_size(payload),
        })
    return result


def get_collection_document(collection_name: str, document_id: str) -> dict | None:
    """한 문서를 상세 보기용으로 읽어 반환한다."""
    snapshot = _collection(collection_name).document(document_id).get()
    if not snapshot.exists:
        return None
    return {
        "id": snapshot.id,
        "data": snapshot.to_dict() or {},
    }


def delete_documents_by_ids(collection_name: str, document_ids: list[str]) -> dict:
    """선택한 문서 ID 목록을 배치 삭제한다."""
    validated_collection = _validate_collection_name(collection_name)
    normalized_ids = [doc_id.strip() for doc_id in document_ids if (doc_id or "").strip()]
    if not normalized_ids:
        return {"deleted_count": 0, "deleted_ids": []}

    deleted_ids: list[str] = []
    deleted_related_ids: list[str] = []

    if validated_collection == "matches":
        deleted_related_ids = _delete_participant_indexes_for_match_ids(normalized_ids)

    for chunk in _chunked(normalized_ids):
        batch = get_client().batch()
        for doc_id in chunk:
            batch.delete(_collection(validated_collection).document(doc_id))
            deleted_ids.append(doc_id)
        batch.commit()

    return {
        "deleted_count": len(deleted_ids),
        "deleted_ids": deleted_ids,
        "deleted_related_count": len(deleted_related_ids),
        "deleted_related_ids": deleted_related_ids,
    }


def clear_collection(collection_name: str) -> dict:
    """컬렉션 전체 문서를 모두 삭제한다."""
    validated_collection = _validate_collection_name(collection_name)

    if validated_collection == "matches":
        related = clear_collection("match_participants")
        doc_ids = [snapshot.id for snapshot in _collection(validated_collection).stream()]
        result = delete_documents_by_ids(validated_collection, doc_ids)
        result["collection"] = validated_collection
        result["cleared_related_collection"] = related
        return result

    doc_ids = [snapshot.id for snapshot in _collection(validated_collection).stream()]
    result = delete_documents_by_ids(validated_collection, doc_ids)
    result["collection"] = validated_collection
    return result


def delete_older_than_days(collection_name: str, days: int) -> dict:
    """기준 시점보다 오래된 문서를 컬렉션별 대표 시간 필드로 찾아 삭제한다."""
    validated_collection = _validate_collection_name(collection_name)
    field_name = TIMESTAMP_FIELDS_BY_COLLECTION.get(validated_collection)
    if not field_name:
        raise ValueError(f"No timestamp field configured for {collection_name}")

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    deleted_ids: list[str] = []

    for snapshot in _collection(validated_collection).stream():
        payload = snapshot.to_dict() or {}
        if _is_older_than(payload.get(field_name), cutoff):
            deleted_ids.append(snapshot.id)

    result = delete_documents_by_ids(validated_collection, deleted_ids)
    result.update({
        "collection": validated_collection,
        "days": days,
        "timestamp_field": field_name,
    })
    return result


def _delete_participant_indexes_for_match_ids(match_ids: list[str]) -> list[str]:
    """삭제 대상 경기와 연결된 참가자 인덱스 문서도 함께 지운다."""
    participant_collection = _collection("match_participants")
    related_ids: list[str] = []

    for snapshot in participant_collection.stream():
        payload = snapshot.to_dict() or {}
        if payload.get("match_id") in match_ids:
            related_ids.append(snapshot.id)

    for chunk in _chunked(related_ids):
        batch = get_client().batch()
        for doc_id in chunk:
            batch.delete(participant_collection.document(doc_id))
        batch.commit()

    return related_ids


def _is_older_than(value, cutoff: datetime) -> bool:
    if value is None:
        return False

    if isinstance(value, int):
        try:
            timestamp = datetime.fromtimestamp(value / 1000, tz=timezone.utc)
            return timestamp < cutoff
        except Exception:
            return False

    if isinstance(value, str):
        try:
            normalized = value.replace("Z", "+00:00")
            timestamp = datetime.fromisoformat(normalized)
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            return timestamp < cutoff
        except Exception:
            return False

    return False
