from __future__ import annotations

from google.cloud import firestore

from .firestore_client import get_client, utcnow_iso


def _account_collection():
    """Riot 계정 메타데이터를 저장하는 컬렉션을 반환한다."""
    return get_client().collection("riot_accounts")


def _with_id(snapshot: firestore.DocumentSnapshot) -> dict:
    """Firestore 스냅샷에 문서 ID를 합쳐 API 응답용 dict로 바꾼다."""
    data = snapshot.to_dict() or {}
    data["id"] = snapshot.id
    return data


def upsert_account(account: dict) -> None:
    """PUUID 기준으로 Riot 계정 메타데이터를 생성 또는 갱신한다."""
    payload = dict(account)
    payload["fetched_at"] = utcnow_iso()
    _account_collection().document(payload["puuid"]).set(payload, merge=True)


def list_accounts(limit: int) -> list[dict]:
    """최근 동기화된 Riot 계정부터 관리자 목록 화면에 보여줄 데이터를 가져온다."""
    docs = (
        _account_collection()
        .order_by("fetched_at", direction=firestore.Query.DESCENDING)
        .limit(limit)
        .stream()
    )
    return [_with_id(snapshot) for snapshot in docs]


def get_accounts_by_game_name(game_name: str) -> list[dict]:
    """같은 게임 닉네임을 가진 저장 계정들을 최근 동기화 순으로 조회한다."""
    docs = (
        _account_collection()
        .where("game_name", "==", game_name)
        .order_by("fetched_at", direction=firestore.Query.DESCENDING)
        .stream()
    )
    return [_with_id(snapshot) for snapshot in docs]


def search_accounts_by_game_name(keyword: str, limit: int) -> list[dict]:
    """게임 닉네임 부분 검색으로 계정 후보를 찾아 관리자 도구에 제공한다."""
    keyword_lower = (keyword or "").strip().lower()
    if not keyword_lower:
        return []

    matches = []
    for snapshot in _account_collection().stream():
        data = snapshot.to_dict() or {}
        game_name = str(data.get("game_name", "") or "")
        if keyword_lower not in game_name.lower():
            continue
        data["id"] = snapshot.id
        matches.append(data)

    matches.sort(key=lambda account: account.get("fetched_at", ""), reverse=True)
    return matches[:limit]
