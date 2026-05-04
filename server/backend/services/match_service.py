from ..firestore_store import (
    get_accounts_by_game_name as load_accounts_by_game_name,
    get_match_detail as load_match_detail,
    get_recent_matches_by_puuid as load_recent_matches_by_puuid,
    get_recent_matches_by_riot_id as load_recent_matches_by_riot_id,
    list_accounts as load_accounts,
    search_accounts_by_game_name as search_accounts,
)


class MatchService:
    # Service assembles stored Firestore results into API-friendly response payloads.

    def list_accounts(self, limit: int) -> dict:
        accounts = load_accounts(limit)
        return {
            "count": len(accounts),
            "accounts": accounts,
        }

    def get_accounts_by_game_name(self, game_name: str) -> dict:
        accounts = load_accounts_by_game_name(game_name)
        return {
            "game_name": game_name,
            "count": len(accounts),
            "accounts": accounts,
        }

    def search_accounts_by_game_name(self, keyword: str, limit: int) -> dict:
        accounts = search_accounts(keyword, limit)
        return {
            "keyword": keyword,
            "count": len(accounts),
            "accounts": accounts,
        }

    def get_recent_matches_by_puuid(self, puuid: str, limit: int) -> dict:
        matches = load_recent_matches_by_puuid(puuid, limit)
        return {
            "puuid": puuid,
            "count": len(matches),
            "matches": matches,
        }

    def get_recent_matches_by_riot_id(
        self, game_name: str, tag_line: str, limit: int
    ) -> dict:
        matches = load_recent_matches_by_riot_id(game_name, tag_line, limit)
        return {
            "game_name": game_name,
            "tag_line": tag_line,
            "count": len(matches),
            "matches": matches,
        }

    def get_match_detail(self, match_id: str) -> dict:
        detail = load_match_detail(match_id)
        if detail is None:
            return {
                "error": "Match not found in Firestore",
                "match_id": match_id,
            }
        return detail
