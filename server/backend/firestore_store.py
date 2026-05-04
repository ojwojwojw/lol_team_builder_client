from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache

from google.cloud import firestore

from .config import get_firestore_database, get_firestore_project


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_username(username: str) -> str:
    return (username or "").strip().lower()


@lru_cache(maxsize=1)
def get_client() -> firestore.Client:
    client_kwargs: dict[str, str] = {}

    project = get_firestore_project()
    if project:
        client_kwargs["project"] = project

    database = get_firestore_database()
    if database:
        client_kwargs["database"] = database

    return firestore.Client(**client_kwargs)


def _account_collection():
    return get_client().collection("riot_accounts")


def _match_collection():
    return get_client().collection("matches")


def _participant_index_collection():
    return get_client().collection("match_participants")


def _user_collection():
    return get_client().collection("app_users")


def count_users() -> int:
    return sum(1 for _ in _user_collection().stream())


def get_user_by_username(username: str) -> dict | None:
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
    doc_id = _normalize_username(user_id)
    if not doc_id:
        return None
    snapshot = _user_collection().document(doc_id).get()
    if not snapshot.exists:
        return None
    data = snapshot.to_dict() or {}
    data["id"] = snapshot.id
    return data


def create_user(
    username: str,
    password_hash: str,
    password_salt: str,
    is_admin: bool = False,
) -> dict:
    doc_id = _normalize_username(username)
    now = utcnow_iso()
    payload = {
        "username": username,
        "password_hash": password_hash,
        "password_salt": password_salt,
        "is_admin": bool(is_admin),
        "is_active": True,
        "created_at": now,
    }
    _user_collection().document(doc_id).set(payload)
    return get_user_by_id(doc_id) or {}


def list_users() -> list[dict]:
    users = []
    for snapshot in _user_collection().stream():
        data = snapshot.to_dict() or {}
        data["id"] = snapshot.id
        users.append(data)

    users.sort(key=lambda user: (user.get("created_at", ""), user.get("id", "")))
    return users


def upsert_account(account: dict) -> None:
    payload = dict(account)
    payload["fetched_at"] = utcnow_iso()
    _account_collection().document(payload["puuid"]).set(payload, merge=True)


def list_accounts(limit: int) -> list[dict]:
    docs = _account_collection().order_by("fetched_at", direction=firestore.Query.DESCENDING).limit(limit).stream()
    return [_with_id(snapshot) for snapshot in docs]


def get_accounts_by_game_name(game_name: str) -> list[dict]:
    docs = (
        _account_collection()
        .where("game_name", "==", game_name)
        .order_by("fetched_at", direction=firestore.Query.DESCENDING)
        .stream()
    )
    return [_with_id(snapshot) for snapshot in docs]


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

    matches.sort(key=lambda account: account.get("fetched_at", ""), reverse=True)
    return matches[:limit]


def get_existing_match_ids(match_ids: list[str]) -> set[str]:
    normalized = [match_id.strip() for match_id in match_ids if (match_id or "").strip()]
    if not normalized:
        return set()

    refs = [_match_collection().document(match_id) for match_id in normalized]
    snapshots = get_client().get_all(refs)
    return {snapshot.id for snapshot in snapshots if snapshot.exists}


def store_match_bundle(match_id: str, match_data: dict) -> None:
    info = match_data.get("info", {})
    metadata = match_data.get("metadata", {})
    teams = info.get("teams", [])
    participants = info.get("participants", [])

    match_payload = {
        "match_id": match_id,
        "data_version": metadata.get("dataVersion"),
        "game_creation": info.get("gameCreation"),
        "game_duration": info.get("gameDuration"),
        "game_end_timestamp": info.get("gameEndTimestamp"),
        "game_id": info.get("gameId"),
        "game_mode": info.get("gameMode"),
        "game_name": info.get("gameName"),
        "game_start_timestamp": info.get("gameStartTimestamp"),
        "game_type": info.get("gameType"),
        "game_version": info.get("gameVersion"),
        "map_id": info.get("mapId"),
        "platform_id": info.get("platformId"),
        "queue_id": info.get("queueId"),
        "tournament_code": info.get("tournamentCode"),
        "participant_count": len(participants),
        "teams": teams,
        "participants": participants,
        "raw_json": match_data,
        "stored_at": utcnow_iso(),
    }
    _match_collection().document(match_id).set(match_payload)

    batch = get_client().batch()
    for participant in participants:
        participant_payload = _build_participant_index_payload(match_id, participant, match_payload)
        doc_id = f"{match_id}_{participant.get('puuid', '')}"
        batch.set(_participant_index_collection().document(doc_id), participant_payload)
    batch.commit()


def get_recent_matches_by_puuid(puuid: str, limit: int) -> list[dict]:
    docs = (
        _participant_index_collection()
        .where("puuid", "==", puuid)
        .order_by("game_start_timestamp", direction=firestore.Query.DESCENDING)
        .limit(limit)
        .stream()
    )
    return [_with_id(snapshot) for snapshot in docs]


def get_recent_matches_by_riot_id(game_name: str, tag_line: str, limit: int) -> list[dict]:
    docs = (
        _participant_index_collection()
        .where("riot_id_game_name", "==", game_name)
        .where("riot_id_tagline", "==", tag_line)
        .order_by("game_start_timestamp", direction=firestore.Query.DESCENDING)
        .limit(limit)
        .stream()
    )
    return [_with_id(snapshot) for snapshot in docs]


def get_match_detail(match_id: str) -> dict | None:
    snapshot = _match_collection().document(match_id).get()
    if not snapshot.exists:
        return None

    data = snapshot.to_dict() or {}
    summary = {
        "match_id": data.get("match_id"),
        "data_version": data.get("data_version"),
        "game_creation": data.get("game_creation"),
        "game_duration": data.get("game_duration"),
        "game_end_timestamp": data.get("game_end_timestamp"),
        "game_id": data.get("game_id"),
        "game_mode": data.get("game_mode"),
        "game_name": data.get("game_name"),
        "game_start_timestamp": data.get("game_start_timestamp"),
        "game_type": data.get("game_type"),
        "game_version": data.get("game_version"),
        "map_id": data.get("map_id"),
        "platform_id": data.get("platform_id"),
        "queue_id": data.get("queue_id"),
        "tournament_code": data.get("tournament_code"),
        "participant_count": data.get("participant_count"),
    }
    participants = [_participant_detail_from_raw(participant, match_id) for participant in data.get("participants", [])]
    teams = [_team_detail(team, match_id) for team in data.get("teams", [])]
    return {
        "match": summary,
        "teams": teams,
        "participants": participants,
    }


def _with_id(snapshot: firestore.DocumentSnapshot) -> dict:
    data = snapshot.to_dict() or {}
    data["id"] = snapshot.id
    return data


def _build_participant_index_payload(match_id: str, participant: dict, match_payload: dict) -> dict:
    challenges = participant.get("challenges", {})
    return {
        "match_id": match_id,
        "game_mode": match_payload.get("game_mode"),
        "queue_id": match_payload.get("queue_id"),
        "game_creation": match_payload.get("game_creation"),
        "game_start_timestamp": match_payload.get("game_start_timestamp"),
        "game_duration": match_payload.get("game_duration"),
        "puuid": participant.get("puuid"),
        "summoner_name": participant.get("summonerName"),
        "riot_id_game_name": participant.get("riotIdGameName"),
        "riot_id_tagline": participant.get("riotIdTagline"),
        "team_id": participant.get("teamId"),
        "team_position": participant.get("teamPosition"),
        "lane": participant.get("lane"),
        "role": participant.get("role"),
        "champion_name": participant.get("championName"),
        "win": bool(participant.get("win")),
        "kills": participant.get("kills"),
        "deaths": participant.get("deaths"),
        "assists": participant.get("assists"),
        "kda": challenges.get("kda"),
        "total_damage_dealt_to_champions": participant.get("totalDamageDealtToChampions"),
        "total_damage_taken": participant.get("totalDamageTaken"),
        "gold_earned": participant.get("goldEarned"),
        "total_minions_killed": participant.get("totalMinionsKilled"),
        "neutral_minions_killed": participant.get("neutralMinionsKilled"),
        "vision_score": participant.get("visionScore"),
        "item0": participant.get("item0"),
        "item1": participant.get("item1"),
        "item2": participant.get("item2"),
        "item3": participant.get("item3"),
        "item4": participant.get("item4"),
        "item5": participant.get("item5"),
        "item6": participant.get("item6"),
    }


def _participant_detail_from_raw(participant: dict, match_id: str) -> dict:
    challenges = participant.get("challenges", {})
    return {
        "match_id": match_id,
        "puuid": participant.get("puuid"),
        "participant_id": participant.get("participantId"),
        "team_id": participant.get("teamId"),
        "summoner_name": participant.get("summonerName"),
        "riot_id_game_name": participant.get("riotIdGameName"),
        "riot_id_tagline": participant.get("riotIdTagline"),
        "champion_name": participant.get("championName"),
        "team_position": participant.get("teamPosition"),
        "lane": participant.get("lane"),
        "role": participant.get("role"),
        "win": bool(participant.get("win")),
        "kills": participant.get("kills"),
        "deaths": participant.get("deaths"),
        "assists": participant.get("assists"),
        "kda": challenges.get("kda"),
        "total_damage_dealt_to_champions": participant.get("totalDamageDealtToChampions"),
        "total_damage_taken": participant.get("totalDamageTaken"),
        "gold_earned": participant.get("goldEarned"),
        "total_minions_killed": participant.get("totalMinionsKilled"),
        "neutral_minions_killed": participant.get("neutralMinionsKilled"),
        "vision_score": participant.get("visionScore"),
        "wards_placed": participant.get("wardsPlaced"),
        "wards_killed": participant.get("wardsKilled"),
        "detector_wards_placed": participant.get("detectorWardsPlaced"),
        "champ_level": participant.get("champLevel"),
        "item0": participant.get("item0"),
        "item1": participant.get("item1"),
        "item2": participant.get("item2"),
        "item3": participant.get("item3"),
        "item4": participant.get("item4"),
        "item5": participant.get("item5"),
        "item6": participant.get("item6"),
        "perks_json": participant.get("perks"),
        "challenges_json": participant.get("challenges"),
    }


def _team_detail(team: dict, match_id: str) -> dict:
    return {
        "match_id": match_id,
        "team_id": team.get("teamId"),
        "win": int(bool(team.get("win"))),
        "bans_json": team.get("bans"),
        "objectives_json": team.get("objectives"),
    }
