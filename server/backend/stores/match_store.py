from __future__ import annotations

from google.cloud import firestore

from .firestore_client import get_client, utcnow_iso


def _match_collection():
    """경기 원본/요약 문서를 저장하는 컬렉션을 반환한다."""
    return get_client().collection("matches")


def _participant_index_collection():
    """참가자 단위 조회를 빠르게 하기 위한 인덱스 컬렉션을 반환한다."""
    return get_client().collection("match_participants")


def _with_id(snapshot: firestore.DocumentSnapshot) -> dict:
    """Firestore 스냅샷에 문서 ID를 포함한 응답용 dict를 만든다."""
    data = snapshot.to_dict() or {}
    data["id"] = snapshot.id
    return data


def get_existing_match_ids(match_ids: list[str]) -> set[str]:
    """적재 대상 match_id 중 Firestore에 이미 있는 것만 골라낸다."""
    normalized = [match_id.strip() for match_id in match_ids if (match_id or "").strip()]
    if not normalized:
        return set()

    refs = [_match_collection().document(match_id) for match_id in normalized]
    snapshots = get_client().get_all(refs)
    return {snapshot.id for snapshot in snapshots if snapshot.exists}


def store_match_bundle(match_id: str, match_data: dict) -> None:
    """한 경기의 원본 데이터와 참가자 인덱스를 함께 Firestore에 저장한다."""
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

    # 참가자별 조회 속도를 위해 match_participants 컬렉션에도 요약 인덱스를 만든다.
    batch = get_client().batch()
    for participant in participants:
        participant_payload = _build_participant_index_payload(match_id, participant, match_payload)
        doc_id = f"{match_id}_{participant.get('puuid', '')}"
        batch.set(_participant_index_collection().document(doc_id), participant_payload)
    batch.commit()


def get_recent_matches_by_puuid(puuid: str, limit: int) -> list[dict]:
    """한 사용자의 최근 경기 참가 이력을 PUUID 기준으로 가져온다."""
    docs = _participant_index_collection().where("puuid", "==", puuid).stream()
    matches = [_with_id(snapshot) for snapshot in docs]
    matches.sort(
        key=lambda match: int(match.get("game_start_timestamp") or 0),
        reverse=True,
    )
    return matches[:limit]


def get_recent_matches_by_riot_id(game_name: str, tag_line: str, limit: int) -> list[dict]:
    """닉네임/태그 조합으로 최근 경기 참가 이력을 조회한다."""
    docs = (
        _participant_index_collection()
        .where("riot_id_game_name", "==", game_name)
        .where("riot_id_tagline", "==", tag_line)
        .stream()
    )
    matches = [_with_id(snapshot) for snapshot in docs]
    matches.sort(
        key=lambda match: int(match.get("game_start_timestamp") or 0),
        reverse=True,
    )
    return matches[:limit]


def get_match_detail(match_id: str) -> dict | None:
    """저장된 경기 한 건을 팀/참가자 상세까지 포함한 응답 형태로 재구성한다."""
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


def _build_participant_index_payload(match_id: str, participant: dict, match_payload: dict) -> dict:
    """참가자 최근 경기 목록 화면에 필요한 최소 필드만 따로 추려 저장한다."""
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
    """경기 상세 화면에 필요한 참가자 정보를 원본 match 문서에서 펼친다."""
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
    """경기 상세 응답에 포함할 팀 단위 요약 정보를 만든다."""
    return {
        "match_id": match_id,
        "team_id": team.get("teamId"),
        "win": int(bool(team.get("win"))),
        "bans_json": team.get("bans"),
        "objectives_json": team.get("objectives"),
    }
