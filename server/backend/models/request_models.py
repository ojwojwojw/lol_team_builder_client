from pydantic import BaseModel


# Request models define the HTTP body shape accepted by controllers.
class RiotAccountRequest(BaseModel):
    """Input body for puuid lookup."""

    api_key: str | None = None
    game_name: str
    tag_line: str


class MatchIdsRequest(BaseModel):
    """Input body for recent match id lookup."""

    api_key: str | None = None
    puuid: str
    count: int = 5


class MatchDetailRequest(BaseModel):
    """Input body for one match detail lookup."""

    api_key: str | None = None
    match_id: str


class StoreRecentMatchesRequest(BaseModel):
    """Input body for fetch-and-store batch flow."""

    api_key: str | None = None
    game_name: str
    tag_line: str
    count: int = 5


class StoredRiotAccountRef(BaseModel):
    """Stored Riot ID reference used for batch save requests."""

    game_name: str
    tag_line: str


class StoreStoredAccountsRequest(BaseModel):
    """Input body for batch storing selected accounts already saved in riot_account."""

    api_key: str | None = None
    count: int = 5
    accounts: list[StoredRiotAccountRef]


class RefreshStoredAccountsRequest(BaseModel):
    """Input body for batch refreshing tier data for stored riot accounts."""

    api_key: str | None = None
    accounts: list[StoredRiotAccountRef]


class AuthBootstrapRequest(BaseModel):
    """Input body for one-time admin bootstrap."""

    username: str
    password: str


class LoginRequest(BaseModel):
    """Input body for login."""

    username: str
    password: str


class CreateUserRequest(BaseModel):
    """Input body for admin-created member accounts."""

    username: str
    password: str


class FirestoreDeleteDocumentsRequest(BaseModel):
    """Input body for deleting selected Firestore documents by ID."""

    collection: str
    document_ids: list[str]


class FirestoreDeleteOlderThanRequest(BaseModel):
    """Input body for deleting Firestore documents older than a day range."""

    collection: str
    days: int
