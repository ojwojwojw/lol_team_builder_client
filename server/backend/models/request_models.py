from pydantic import BaseModel


# Request models define the HTTP body shape accepted by controllers.
class RiotAccountRequest(BaseModel):
    """Input body for puuid lookup."""

    api_key: str
    game_name: str
    tag_line: str


class MatchIdsRequest(BaseModel):
    """Input body for recent match id lookup."""

    api_key: str
    puuid: str
    count: int = 5


class MatchDetailRequest(BaseModel):
    """Input body for one match detail lookup."""

    api_key: str
    match_id: str


class StoreRecentMatchesRequest(BaseModel):
    """Input body for fetch-and-store batch flow."""

    api_key: str
    game_name: str
    tag_line: str
    count: int = 5


class StoredRiotAccountRef(BaseModel):
    """Stored Riot ID reference used for batch save requests."""

    game_name: str
    tag_line: str


class StoreStoredAccountsRequest(BaseModel):
    """Input body for batch storing selected accounts already saved in riot_account."""

    api_key: str
    count: int = 5
    accounts: list[StoredRiotAccountRef]
