from urllib.parse import quote

import requests


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
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code != 200:
        return None, riot_error_response(response, error_msg)
    return response.json(), None


def fetch_account(game_name: str, tag_line: str, api_key: str) -> dict:
    """Fetch Riot account info from Riot ID."""
    url = (
        "https://asia.api.riotgames.com/riot/account/v1/accounts/by-riot-id/"
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


def fetch_match_ids(puuid: str, api_key: str, count: int = 5) -> dict:
    """Fetch recent match ids for one puuid."""
    url = (
        "https://asia.api.riotgames.com/lol/match/v5/matches/by-puuid/"
        f"{quote(puuid, safe='')}/ids?start=0&count={count}"
    )
    match_ids, error = fetch_riot_json(url, api_key, "Failed to get match IDs")
    if error:
        return error
    return {"puuid": puuid, "match_ids": match_ids, "count": count}


def fetch_match_detail(match_id: str, api_key: str) -> dict:
    """Fetch one match detail and pre-build a small summary structure."""
    url = (
        "https://asia.api.riotgames.com/lol/match/v5/matches/"
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
