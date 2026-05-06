from __future__ import annotations

from google.cloud import firestore

from .firestore_client import get_client, utcnow_iso
from .local_cache_store import (
    CACHE_MISS,
    MATCH_NAMESPACE,
    load_cached_json,
    save_cached_json,
    touch_cache_namespace,
)


def _match_collection():
    return get_client().collection("matches")


def _participant_index_collection():
    return get_client().collection("match_participants")


def _with_id(snapshot: firestore.DocumentSnapshot) -> dict:
    data = snapshot.to_dict() or {}
    data["id"] = snapshot.id
    return data


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
    touch_cache_namespace(MATCH_NAMESPACE)


def rebuild_participant_indexes(match_ids: list[str]) -> list[str]:
    normalized = [match_id.strip() for match_id in match_ids if (match_id or "").strip()]
    if not normalized:
        return []

    rebuilt_match_ids = []
    for match_id in normalized:
        snapshot = _match_collection().document(match_id).get()
        if not snapshot.exists:
            continue

        data = snapshot.to_dict() or {}
        participants = data.get("participants", []) or []
        if not participants:
            continue

        match_payload = {
            "game_mode": data.get("game_mode"),
            "queue_id": data.get("queue_id"),
            "game_creation": data.get("game_creation"),
            "game_start_timestamp": data.get("game_start_timestamp"),
            "game_duration": data.get("game_duration"),
        }

        batch = get_client().batch()
        has_index_target = False
        for participant in participants:
            participant_payload = _build_participant_index_payload(match_id, participant, match_payload)
            doc_id = f"{match_id}_{participant.get('puuid', '')}"
            batch.set(_participant_index_collection().document(doc_id), participant_payload)
            has_index_target = True

        if not has_index_target:
            continue

        batch.commit()
        rebuilt_match_ids.append(match_id)

    if rebuilt_match_ids:
        touch_cache_namespace(MATCH_NAMESPACE)
    return rebuilt_match_ids


def get_recent_matches_by_puuid(puuid: str, limit: int) -> list[dict]:
    normalized_puuid = puuid.strip()
    cache_key = f"matches:recent:puuid:{normalized_puuid}:{int(limit)}"
    cached = load_cached_json(cache_key, MATCH_NAMESPACE)
    if cached is not CACHE_MISS:
        return cached

    docs = _participant_index_collection().where("puuid", "==", normalized_puuid).stream()
    matches = [_with_id(snapshot) for snapshot in docs]
    matches.sort(
        key=lambda match: int(match.get("game_start_timestamp") or 0),
        reverse=True,
    )
    result = matches[:limit]
    save_cached_json(cache_key, result, MATCH_NAMESPACE)
    return result


def get_recent_matches_by_riot_id(game_name: str, tag_line: str, limit: int) -> list[dict]:
    normalized_game_name = game_name.strip()
    normalized_tag_line = tag_line.strip()
    cache_key = (
        f"matches:recent:riot_id:{normalized_game_name}:{normalized_tag_line}:{int(limit)}"
    )
    cached = load_cached_json(cache_key, MATCH_NAMESPACE)
    if cached is not CACHE_MISS:
        return cached

    docs = (
        _participant_index_collection()
        .where("riot_id_game_name", "==", normalized_game_name)
        .where("riot_id_tagline", "==", normalized_tag_line)
        .stream()
    )
    matches = [_with_id(snapshot) for snapshot in docs]
    matches.sort(
        key=lambda match: int(match.get("game_start_timestamp") or 0),
        reverse=True,
    )
    result = matches[:limit]
    save_cached_json(cache_key, result, MATCH_NAMESPACE)
    return result


def get_match_detail(match_id: str) -> dict | None:
    normalized_match_id = match_id.strip()
    cache_key = f"matches:detail:{normalized_match_id}"
    cached = load_cached_json(cache_key, MATCH_NAMESPACE)
    if cached is not CACHE_MISS:
        return cached

    snapshot = _match_collection().document(normalized_match_id).get()
    if not snapshot.exists:
        save_cached_json(cache_key, None, MATCH_NAMESPACE)
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
    participants = [
        _participant_detail_from_raw(participant, normalized_match_id)
        for participant in data.get("participants", [])
    ]
    teams = [_team_detail(team, normalized_match_id) for team in data.get("teams", [])]
    detail = {
        "match": summary,
        "teams": teams,
        "participants": participants,
    }
    save_cached_json(cache_key, detail, MATCH_NAMESPACE)
    return detail


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
