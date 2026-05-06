from urllib.parse import quote

from api_clients.base_api_client import BaseApiClient
from repositories.local_api_cache_repository import LocalApiCacheRepository


ACCOUNT_LIST_TTL_SECONDS = 10 * 60
ACCOUNT_SEARCH_TTL_SECONDS = 10 * 60
RECENT_MATCHES_TTL_SECONDS = 10 * 60
MATCH_DETAIL_TTL_SECONDS = 30 * 24 * 60 * 60


class MatchApiClient(BaseApiClient):
    """Match/account read API client."""

    def list_accounts(self, limit=20):
        params = {"limit": limit}
        cache_key = self._cache_key("/accounts", params)
        cached = LocalApiCacheRepository.get(cache_key)
        if cached is not None:
            return cached

        data = self._get("/accounts", params)
        LocalApiCacheRepository.set(cache_key, data, ACCOUNT_LIST_TTL_SECONDS)
        return data

    def search_accounts(self, keyword, limit=20):
        params = {"keyword": keyword, "limit": limit}
        cache_key = self._cache_key("/accounts/search", params)
        cached = LocalApiCacheRepository.get(cache_key)
        if cached is not None:
            return cached

        data = self._get("/accounts/search", params)
        LocalApiCacheRepository.set(cache_key, data, ACCOUNT_SEARCH_TTL_SECONDS)
        return data

    def get_recent_matches_by_riot_id(self, game_name, tag_line, limit=10):
        params = {
            "game_name": game_name,
            "tag_line": tag_line,
            "limit": limit,
        }
        cache_key = self._cache_key("/matches/recent/by-riot-id", params)
        cached = LocalApiCacheRepository.get(cache_key)
        if cached is not None:
            return cached

        data = self._get("/matches/recent/by-riot-id", params)
        LocalApiCacheRepository.set(cache_key, data, RECENT_MATCHES_TTL_SECONDS)
        return data

    def get_match_detail(self, match_id):
        encoded_match_id = quote(match_id, safe="")
        cache_key = self._cache_key(f"/matches/{encoded_match_id}")
        cached = LocalApiCacheRepository.get(cache_key)
        if cached is not None:
            return cached

        data = self._get(f"/matches/{encoded_match_id}")
        LocalApiCacheRepository.set(cache_key, data, MATCH_DETAIL_TTL_SECONDS)
        return data

    def _cache_key(self, path, params=None):
        base = self.base_url.rstrip("/")
        if not params:
            return f"{base}{path}"

        ordered = "&".join(
            f"{key}={params[key]}"
            for key in sorted(params)
        )
        return f"{base}{path}?{ordered}"
