from fastapi import APIRouter, Query

from ..services.match_service import MatchService


router = APIRouter()
match_service = MatchService()


@router.get("/accounts")
def list_accounts(limit: int = Query(100, ge=1, le=1000)):
    """Return stored riot_account rows ordered by latest fetch time."""
    return match_service.list_accounts(limit)


@router.get("/accounts/by-game-name")
def get_accounts_by_game_name(game_name: str = Query(..., min_length=1)):
    """Return stored riot_account rows for one game name."""
    return match_service.get_accounts_by_game_name(game_name.strip())


@router.get("/accounts/search")
def search_accounts_by_game_name(
    keyword: str = Query(..., min_length=1),
    limit: int = Query(1000, ge=1, le=1000),
):
    """Return stored riot_account rows using a game_name LIKE search."""
    return match_service.search_accounts_by_game_name(keyword.strip(), limit)


@router.get("/matches/recent/by-puuid")
def get_recent_matches_by_puuid(
    puuid: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=100),
):
    """Return recent stored matches for one puuid."""
    return match_service.get_recent_matches_by_puuid(puuid.strip(), limit)


@router.get("/matches/recent/by-riot-id")
def get_recent_matches_by_riot_id(
    game_name: str = Query(..., min_length=1),
    tag_line: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=100),
):
    """Return recent stored matches for one Riot ID."""
    return match_service.get_recent_matches_by_riot_id(
        game_name.strip().rstrip("#"),
        tag_line.strip().lstrip("#"),
        limit,
    )


@router.get("/matches/{match_id}")
def get_match_detail(match_id: str):
    """Return one stored match with summary, teams, and participants."""
    return match_service.get_match_detail(match_id.strip())
