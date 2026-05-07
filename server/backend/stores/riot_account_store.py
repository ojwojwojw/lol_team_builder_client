from __future__ import annotations

from google.cloud import firestore

from .firestore_client import get_client, utcnow_iso


def _account_collection():
    return get_client().collection("riot_accounts")


def _with_id(snapshot: firestore.DocumentSnapshot) -> dict:
    data = snapshot.to_dict() or {}
    data["id"] = snapshot.id
    return data


def _sort_accounts_by_fetched_at_desc(accounts: list[dict]) -> list[dict]:
    return sorted(
        accounts,
        key=lambda account: (
            str(account.get("fetched_at") or ""),
            str(account.get("id") or ""),
        ),
        reverse=True,
    )


def _dedupe_accounts_by_riot_id(accounts: list[dict]) -> list[dict]:
    latest_by_riot_id = {}

    for account in _sort_accounts_by_fetched_at_desc(accounts):
        game_name = str(account.get("game_name") or "").strip()
        tag_line = str(account.get("tag_line") or "").strip()
        if not game_name or not tag_line:
            continue

        key = (game_name.lower(), tag_line.lower())
        if key in latest_by_riot_id:
            continue

        latest_by_riot_id[key] = account

    return list(latest_by_riot_id.values())


def upsert_account(account: dict) -> None:
    payload = dict(account)
    payload["fetched_at"] = utcnow_iso()
    _account_collection().document(payload["puuid"]).set(payload, merge=True)


def list_accounts(limit: int) -> list[dict]:
    docs = _account_collection().stream()
    accounts = [_with_id(snapshot) for snapshot in docs]
    deduped = _dedupe_accounts_by_riot_id(accounts)
    return deduped[:limit]


def get_accounts_by_game_name(game_name: str) -> list[dict]:
    normalized_game_name = game_name.strip()

    docs = (
        _account_collection()
        .where("game_name", "==", normalized_game_name)
        .stream()
    )
    accounts = [_with_id(snapshot) for snapshot in docs]
    return _dedupe_accounts_by_riot_id(accounts)


def search_accounts_by_game_name(keyword: str, limit: int) -> list[dict]:
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

    deduped = _dedupe_accounts_by_riot_id(matches)
    return deduped[:limit]


def get_account_by_riot_id(game_name: str, tag_line: str) -> dict | None:
    normalized_game_name = game_name.strip()
    normalized_tag_line = tag_line.strip()

    docs = (
        _account_collection()
        .where("game_name", "==", normalized_game_name)
        .where("tag_line", "==", normalized_tag_line)
        .stream()
    )
    accounts = [_with_id(snapshot) for snapshot in docs]
    deduped = _dedupe_accounts_by_riot_id(accounts)
    return deduped[0] if deduped else None
