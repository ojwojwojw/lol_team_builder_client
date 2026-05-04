from fastapi import APIRouter, Depends, Query

from ..security import get_current_user
from ..services.match_service import MatchService


router = APIRouter(dependencies=[Depends(get_current_user)])
match_service = MatchService()


@router.get("/accounts")
def list_accounts(limit: int = Query(100, ge=1, le=1000)):
    """저장된 Riot 계정 목록을 최신 동기화 순으로 반환한다."""
    return match_service.list_accounts(limit)


@router.get("/accounts/by-game-name")
def get_accounts_by_game_name(game_name: str = Query(..., min_length=1)):
    """같은 게임 닉네임을 가진 저장 계정 목록을 반환한다."""
    return match_service.get_accounts_by_game_name(game_name.strip())


@router.get("/accounts/search")
def search_accounts_by_game_name(
    keyword: str = Query(..., min_length=1),
    limit: int = Query(1000, ge=1, le=1000),
):
    """게임 닉네임 부분 검색으로 저장 계정 목록을 반환한다."""
    return match_service.search_accounts_by_game_name(keyword.strip(), limit)


@router.get("/matches/recent/by-puuid")
def get_recent_matches_by_puuid(
    puuid: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=100),
):
    """한 PUUID의 최근 저장 경기 목록을 반환한다."""
    return match_service.get_recent_matches_by_puuid(puuid.strip(), limit)


@router.get("/matches/recent/by-riot-id")
def get_recent_matches_by_riot_id(
    game_name: str = Query(..., min_length=1),
    tag_line: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=100),
):
    """한 Riot ID의 최근 저장 경기 목록을 반환한다."""
    return match_service.get_recent_matches_by_riot_id(
        game_name.strip().rstrip("#"),
        tag_line.strip().lstrip("#"),
        limit,
    )


@router.get("/matches/{match_id}")
def get_match_detail(match_id: str):
    """저장된 경기 한 건의 요약/팀/참가자 상세를 반환한다."""
    return match_service.get_match_detail(match_id.strip())
