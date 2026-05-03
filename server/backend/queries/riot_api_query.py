from urllib.parse import quote

import requests


ASIA_ROUTING_BASE_URL = "https://asia.api.riotgames.com"
KR_PLATFORM_BASE_URL = "https://kr.api.riotgames.com"


def riot_error_response(response: requests.Response, default_msg: str) -> dict:
    """Normalize Riot API errors into one consistent response shape."""
    try:
        detail = response.json()
    except Exception:
        detail = response.text
    return {
        "error": default_msg,
        "status": response.status_code,
        "riot_response": detail,
    }


def fetch_riot_json(url: str, api_key: str, error_msg: str):
    """Perform one Riot GET request with shared header and error handling."""
    headers = {"X-Riot-Token": api_key}
    try:
        response = requests.get(url, headers=headers, timeout=10)
    except requests.RequestException as exc:
        return None, {
            "error": error_msg,
            "status": 0,
            "riot_response": str(exc),
        }
    if response.status_code != 200:
        return None, riot_error_response(response, error_msg)
    return response.json(), None


def fetch_account(game_name: str, tag_line: str, api_key: str) -> dict:
    """Fetch Riot account info from Riot ID."""
    url = (
        f"{ASIA_ROUTING_BASE_URL}/riot/account/v1/accounts/by-riot-id/"
        f"{quote(game_name, safe='')}/{quote(tag_line, safe='')}"
    )
    account, error = fetch_riot_json(url, api_key, "Failed to get account by Riot ID")
    if error:
        return error
    return {
        "game_name": account.get("gameName"),
        "tag_line": account.get("tagLine"),
        "puuid": account.get("puuid"),
        "raw_account": account,
    }


def fetch_summoner_by_puuid(puuid: str, api_key: str) -> dict:
    """Fetch summoner payload needed for ranked lookup."""
    url = (
        f"{KR_PLATFORM_BASE_URL}/lol/summoner/v4/summoners/by-puuid/"
        f"{quote(puuid, safe='')}"
    )
    summoner, error = fetch_riot_json(url, api_key, "Failed to get summoner by puuid")
    if error:
        return error

    return {
        "id": summoner.get("id"),
        "account_id": summoner.get("accountId"),
        "puuid": summoner.get("puuid"),
        "name": summoner.get("name"),
        "profile_icon_id": summoner.get("profileIconId"),
        "summoner_level": summoner.get("summonerLevel"),
        "raw_summoner": summoner,
    }


def fetch_ranked_entries(puuid: str, api_key: str) -> dict:
    """Fetch ranked queue entries for one encrypted puuid."""
    url = (
        f"{KR_PLATFORM_BASE_URL}/lol/league/v4/entries/by-puuid/"
        f"{quote(puuid, safe='')}"
    )
    entries, error = fetch_riot_json(url, api_key, "Failed to get ranked entries")
    if error:
        return error

    return {
        "puuid": puuid,
        "entries": entries or [],
    }


def select_preferred_ranked_entry(entries: list[dict]) -> dict | None:
    """Prefer solo queue over flex when multiple ranked entries exist."""
    if not entries:
        return None

    queue_priority = {
        "RANKED_SOLO_5x5": 0,
        "RANKED_FLEX_SR": 1,
    }

    sorted_entries = sorted(
        entries,
        key=lambda entry: (
            queue_priority.get(entry.get("queueType"), 9),
            -(entry.get("leaguePoints") or 0),
        ),
    )
    return sorted_entries[0]


def fetch_match_ids(puuid: str, api_key: str, count: int = 5) -> dict:
    """Fetch recent match ids for one puuid."""
    url = (
        f"{ASIA_ROUTING_BASE_URL}/lol/match/v5/matches/by-puuid/"
        f"{quote(puuid, safe='')}/ids?start=0&count={count}"
    )
    match_ids, error = fetch_riot_json(url, api_key, "Failed to get match IDs")
    if error:
        return error
    return {"puuid": puuid, "match_ids": match_ids, "count": count}


def fetch_match_detail(match_id: str, api_key: str) -> dict:
    """Fetch one match detail and pre-build a small summary structure."""
    url = (
        f"{ASIA_ROUTING_BASE_URL}/lol/match/v5/matches/"
        f"{quote(match_id, safe='')}"
    )
    match_data, error = fetch_riot_json(url, api_key, "Failed to get match detail")
    if error:
        return error

    info = match_data.get("info", {})
    metadata = match_data.get("metadata", {})
    participants = []
    for participant in info.get("participants", []):
        participants.append(
            {
                "summoner_name": participant.get("summonerName"),
                "riot_id_game_name": participant.get("riotIdGameName"),
                "riot_id_tagline": participant.get("riotIdTagline"),
                "champion_name": participant.get("championName"),
                "kills": participant.get("kills"),
                "deaths": participant.get("deaths"),
                "assists": participant.get("assists"),
                "win": participant.get("win"),
            }
        )

    return {
        "match_id": metadata.get("matchId"),
        "game_mode": info.get("gameMode"),
        "queue_id": info.get("queueId"),
        "game_start_timestamp": info.get("gameStartTimestamp"),
        "participants": participants,
        "raw_match": match_data,
    }
