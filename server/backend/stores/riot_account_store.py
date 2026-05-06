from __future__ import annotations

from google.cloud import firestore

from .firestore_client import get_client, utcnow_iso
from .local_cache_store import (
    ACCOUNT_NAMESPACE,
    CACHE_MISS,
    load_cached_json,
    save_cached_json,
    touch_cache_namespace,
)


def _account_collection():
    return get_client().collection("riot_accounts")


def _with_id(snapshot: firestore.DocumentSnapshot) -> dict:
    data = snapshot.to_dict() or {}
    data["id"] = snapshot.id
    return data


def upsert_account(account: dict) -> None:
    payload = dict(account)
    payload["fetched_at"] = utcnow_iso()
    _account_collection().document(payload["puuid"]).set(payload, merge=True)
    touch_cache_namespace(ACCOUNT_NAMESPACE)


def list_accounts(limit: int) -> list[dict]:
    cache_key = f"riot_accounts:list:{int(limit)}"
    cached = load_cached_json(cache_key, ACCOUNT_NAMESPACE)
    if cached is not CACHE_MISS:
        return cached

    docs = (
        _account_collection()
        .order_by("fetched_at", direction=firestore.Query.DESCENDING)
        .limit(limit)
        .stream()
    )
    accounts = [_with_id(snapshot) for snapshot in docs]
    save_cached_json(cache_key, accounts, ACCOUNT_NAMESPACE)
    return accounts


def get_accounts_by_game_name(game_name: str) -> list[dict]:
    normalized_game_name = game_name.strip()
    cache_key = f"riot_accounts:game_name:{normalized_game_name}"
    cached = load_cached_json(cache_key, ACCOUNT_NAMESPACE)
    if cached is not CACHE_MISS:
        return cached

    docs = (
        _account_collection()
        .where("game_name", "==", normalized_game_name)
        .order_by("fetched_at", direction=firestore.Query.DESCENDING)
        .stream()
    )
    accounts = [_with_id(snapshot) for snapshot in docs]
    save_cached_json(cache_key, accounts, ACCOUNT_NAMESPACE)
    return accounts


def search_accounts_by_game_name(keyword: str, limit: int) -> list[dict]:
    keyword_lower = (keyword or "").strip().lower()
    if not keyword_lower:
        return []

    cache_key = f"riot_accounts:search:{keyword_lower}:{int(limit)}"
    cached = load_cached_json(cache_key, ACCOUNT_NAMESPACE)
    if cached is not CACHE_MISS:
        return cached

    matches = []
    for snapshot in _account_collection().stream():
        data = snapshot.to_dict() or {}
        game_name = str(data.get("game_name", "") or "")
        if keyword_lower not in game_name.lower():
            continue
        data["id"] = snapshot.id
        matches.append(data)

    matches.sort(key=lambda account: account.get("fetched_at", ""), reverse=True)
    result = matches[:limit]
    save_cached_json(cache_key, result, ACCOUNT_NAMESPACE)
    return result


def get_account_by_riot_id(game_name: str, tag_line: str) -> dict | None:
    normalized_game_name = game_name.strip()
    normalized_tag_line = tag_line.strip()
    cache_key = f"riot_accounts:riot_id:{normalized_game_name}:{normalized_tag_line}"
    cached = load_cached_json(cache_key, ACCOUNT_NAMESPACE)
    if cached is not CACHE_MISS:
        return cached

    docs = (
        _account_collection()
        .where("game_name", "==", normalized_game_name)
        .where("tag_line", "==", normalized_tag_line)
        .limit(1)
        .stream()
    )
    for snapshot in docs:
        account = _with_id(snapshot)
        save_cached_json(cache_key, account, ACCOUNT_NAMESPACE)
        return account

    save_cached_json(cache_key, None, ACCOUNT_NAMESPACE)
    return None
