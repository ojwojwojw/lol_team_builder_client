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
# Controller only handles HTTP input/output.
# Business flow stays in the service layer.
riot_service = RiotService()


@router.post("/get_puuid")
def get_puuid(req: RiotAccountRequest = Body(...)):
    """Normalize Riot ID input and delegate puuid lookup to the service."""
    game_name = req.game_name.strip().rstrip("#")
    tag_line = req.tag_line.strip().lstrip("#")
    return riot_service.get_puuid(game_name, tag_line, req.api_key)


@router.post("/get_match_ids")
def get_match_ids(req: MatchIdsRequest = Body(...)):
    """Receive a puuid and return recent match ids."""
    return riot_service.get_match_ids(req.puuid.strip(), req.api_key, req.count)


@router.post("/get_match_detail")
def get_match_detail(req: MatchDetailRequest = Body(...)):
    """Receive a match id and return summarized match detail."""
    return riot_service.get_match_detail(req.match_id.strip(), req.api_key)


@router.post("/store_recent_matches")
def store_recent_matches(req: StoreRecentMatchesRequest = Body(...)):
    """Receive Riot ID info and trigger fetch + DB save for recent matches."""
    game_name = req.game_name.strip().rstrip("#")
    tag_line = req.tag_line.strip().lstrip("#")
    return riot_service.store_recent_matches(game_name, tag_line, req.api_key, req.count)


@router.post("/refresh_account_tier")
def refresh_account_tier(req: RiotAccountRequest = Body(...)):
    """Refresh and store only tier-related account metadata for one Riot ID."""
    game_name = req.game_name.strip().rstrip("#")
    tag_line = req.tag_line.strip().lstrip("#")
    return riot_service.refresh_account_tier(game_name, tag_line, req.api_key)


@router.post("/refresh_account_tier/by-stored-accounts")
def refresh_account_tier_by_stored_accounts(req: RefreshStoredAccountsRequest = Body(...)):
    """Refresh and store only tier metadata for selected riot_account rows."""
    accounts = [
        {
            "game_name": account.game_name.strip().rstrip("#"),
            "tag_line": account.tag_line.strip().lstrip("#"),
        }
        for account in req.accounts
    ]
    return riot_service.refresh_account_tiers_for_accounts(accounts, req.api_key)


@router.post("/store_recent_matches/by-stored-accounts")
def store_recent_matches_by_stored_accounts(req: StoreStoredAccountsRequest = Body(...)):
    """Store recent matches for selected accounts that already exist in riot_account."""
    accounts = [
        {
            "game_name": account.game_name.strip().rstrip("#"),
            "tag_line": account.tag_line.strip().lstrip("#"),
        }
        for account in req.accounts
    ]
    return riot_service.store_recent_matches_for_accounts(accounts, req.api_key, req.count)
