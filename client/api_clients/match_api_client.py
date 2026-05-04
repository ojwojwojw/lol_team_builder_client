from urllib.parse import quote

from api_clients.base_api_client import BaseApiClient


class MatchApiClient(BaseApiClient):
    """Match/account read API client."""

    def list_accounts(self, limit=20):
        return self._get(
            "/accounts",
            {"limit": limit},
        )

    def search_accounts(self, keyword, limit=20):
        return self._get(
            "/accounts/search",
            {"keyword": keyword, "limit": limit},
        )

    def get_recent_matches_by_riot_id(self, game_name, tag_line, limit=10):
        return self._get(
            "/matches/recent/by-riot-id",
            {
                "game_name": game_name,
                "tag_line": tag_line,
                "limit": limit,
            },
        )

    def get_match_detail(self, match_id):
        encoded_match_id = quote(match_id, safe="")
        return self._get(f"/matches/{encoded_match_id}")
