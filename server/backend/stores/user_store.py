from __future__ import annotations

from .firestore_client import get_client, utcnow_iso


def _normalize_username(username: str) -> str:
    """사용자 문서 ID 비교를 위해 아이디를 소문자 기준으로 정규화한다."""
    return (username or "").strip().lower()


def _user_collection():
    """앱 사용자 정보를 담는 Firestore 컬렉션을 반환한다."""
    return get_client().collection("app_users")


def count_users() -> int:
    """현재 저장된 앱 사용자 수를 센다."""
    return sum(1 for _ in _user_collection().stream())


def get_user_by_username(username: str) -> dict | None:
    """아이디로 사용자 문서를 읽어 화면/인증에서 쓸 dict 형태로 반환한다."""
    doc_id = _normalize_username(username)
    if not doc_id:
        return None

    snapshot = _user_collection().document(doc_id).get()
    if not snapshot.exists:
        return None

    data = snapshot.to_dict() or {}
    data["id"] = snapshot.id
    return data


def get_user_by_id(user_id: str) -> dict | None:
    """JWT의 sub 값으로 저장된 사용자 ID를 다시 사용자 문서로 조회한다."""
    return get_user_by_username(user_id)


def create_user(
    username: str,
    password_hash: str,
    password_salt: str,
    is_admin: bool = False,
) -> dict:
    """새 앱 사용자를 생성하고, 생성 직후 표준 응답 형태로 다시 읽어 반환한다."""
    doc_id = _normalize_username(username)
    payload = {
        "username": username,
        "password_hash": password_hash,
        "password_salt": password_salt,
        "is_admin": bool(is_admin),
        "is_active": True,
        "created_at": utcnow_iso(),
    }
    _user_collection().document(doc_id).set(payload)
    return get_user_by_id(doc_id) or {}


def list_users() -> list[dict]:
    """관리자 화면에서 쓸 전체 사용자 목록을 생성 시각 기준으로 정렬해 반환한다."""
    users = []
    for snapshot in _user_collection().stream():
        data = snapshot.to_dict() or {}
        data["id"] = snapshot.id
        users.append(data)

    users.sort(key=lambda user: (user.get("created_at", ""), user.get("id", "")))
    return users
