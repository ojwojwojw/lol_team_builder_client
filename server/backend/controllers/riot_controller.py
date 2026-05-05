from fastapi import APIRouter, Body, Depends

from ..models.request_models import (
    MatchDetailRequest,
    MatchIdsRequest,
    RefreshStoredAccountsRequest,
    RiotAccountRequest,
    StoreStoredAccountsRequest,
    StoreRecentMatchesRequest,
)
from ..security import require_admin_user
from ..services.riot_service import RiotService


router = APIRouter(dependencies=[Depends(require_admin_user)])
riot_service = RiotService()


@router.post("/get_puuid")
def get_puuid(req: RiotAccountRequest = Body(...)):
    """입력된 Riot ID를 정규화한 뒤 PUUID 조회 서비스로 넘긴다."""
    game_name = req.game_name.strip().rstrip("#")
    tag_line = req.tag_line.strip().lstrip("#")
    return riot_service.get_puuid(game_name, tag_line)


@router.post("/get_match_ids")
def get_match_ids(req: MatchIdsRequest = Body(...)):
    """PUUID를 받아 최근 경기 ID 목록 조회를 서비스에 위임한다."""
    return riot_service.get_match_ids(req.puuid.strip(), req.count)


@router.post("/get_match_detail")
def get_match_detail(req: MatchDetailRequest = Body(...)):
    """match_id를 받아 경기 상세 조회를 서비스에 위임한다."""
    return riot_service.get_match_detail(req.match_id.strip())


@router.post("/store_recent_matches")
def store_recent_matches(req: StoreRecentMatchesRequest = Body(...)):
    """한 Riot 계정의 최근 경기 수집과 Firestore 저장을 요청한다."""
    game_name = req.game_name.strip().rstrip("#")
    tag_line = req.tag_line.strip().lstrip("#")
    return riot_service.store_recent_matches(game_name, tag_line, req.count)


@router.post("/refresh_account_tier")
def refresh_account_tier(req: RiotAccountRequest = Body(...)):
    """한 Riot 계정의 티어 메타데이터만 다시 읽어 저장한다."""
    game_name = req.game_name.strip().rstrip("#")
    tag_line = req.tag_line.strip().lstrip("#")
    return riot_service.refresh_account_tier(game_name, tag_line)


@router.post("/refresh_account_tier/by-stored-accounts")
def refresh_account_tier_by_stored_accounts(req: RefreshStoredAccountsRequest = Body(...)):
    """선택된 저장 계정들의 티어 메타데이터를 일괄 갱신한다."""
    accounts = [
        {
            "game_name": account.game_name.strip().rstrip("#"),
            "tag_line": account.tag_line.strip().lstrip("#"),
        }
        for account in req.accounts
    ]
    return riot_service.refresh_account_tiers_for_accounts(accounts)


@router.post("/store_recent_matches/by-stored-accounts")
def store_recent_matches_by_stored_accounts(req: StoreStoredAccountsRequest = Body(...)):
    """선택된 저장 계정들의 최근 경기를 일괄 수집해 Firestore에 저장한다."""
    accounts = [
        {
            "game_name": account.game_name.strip().rstrip("#"),
            "tag_line": account.tag_line.strip().lstrip("#"),
        }
        for account in req.accounts
    ]
    return riot_service.store_recent_matches_for_accounts(accounts, req.count)
