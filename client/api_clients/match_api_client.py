from urllib.parse import quote

from api_clients.base_api_client import BaseApiClient
from core.account_records import dedupe_accounts
from repositories.local_api_cache_repository import LocalApiCacheRepository


ACCOUNT_LIST_TTL_SECONDS = 10 * 60
ACCOUNT_SEARCH_TTL_SECONDS = 10 * 60
RECENT_MATCHES_TTL_SECONDS = 10 * 60
MATCH_DETAIL_TTL_SECONDS = 30 * 24 * 60 * 60


class MatchApiClient(BaseApiClient):
    """Match/account read API client."""

    @staticmethod
    def _dedupe_accounts_payload(payload):
        if not isinstance(payload, dict):
            return payload

        accounts = payload.get("accounts")
        if not isinstance(accounts, list):
            return payload

        normalized = dict(payload)
        normalized["accounts"] = dedupe_accounts(accounts)
        normalized["count"] = len(normalized["accounts"])
        return normalized

    def list_accounts(self, limit=20):
        params = {"limit": limit}
        cache_key = self._cache_key("/accounts", params)
        cached = LocalApiCacheRepository.get(cache_key)
        if cached is not None:
            return self._dedupe_accounts_payload(cached)

        data = self._get("/accounts", params)
        normalized = self._dedupe_accounts_payload(data)
        LocalApiCacheRepository.set(cache_key, normalized, ACCOUNT_LIST_TTL_SECONDS)
        return normalized

    def search_accounts(self, keyword, limit=20):
        params = {"keyword": keyword, "limit": limit}
        cache_key = self._cache_key("/accounts/search", params)
        cached = LocalApiCacheRepository.get(cache_key)
        if cached is not None:
            return self._dedupe_accounts_payload(cached)

        data = self._get("/accounts/search", params)
        normalized = self._dedupe_accounts_payload(data)
        LocalApiCacheRepository.set(cache_key, normalized, ACCOUNT_SEARCH_TTL_SECONDS)
        return normalized

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
