from __future__ import annotations

from pprint import pformat
from urllib.parse import urlencode

import requests

from core.auth_session import build_auth_headers, clear_saved_session
from domain.constants import ACCOUNT_SEARCH_LIMIT
from repositories.dataset_repository import load_server_base_url


class RiotLoaderApi:
    def __init__(self):
        self.refresh_urls()

    def refresh_urls(self):
        self.api_base_url = load_server_base_url().rstrip("/")
        self.puuid_url = f"{self.api_base_url}/get_puuid"
        self.match_ids_url = f"{self.api_base_url}/get_match_ids"
        self.match_detail_url = f"{self.api_base_url}/get_match_detail"
        self.store_matches_url = f"{self.api_base_url}/store_recent_matches"
        self.list_accounts_url = f"{self.api_base_url}/accounts"
        self.search_accounts_url = f"{self.api_base_url}/accounts/search"
        self.store_selected_accounts_url = (
            f"{self.api_base_url}/store_recent_matches/by-stored-accounts"
        )
        self.refresh_selected_tiers_url = (
            f"{self.api_base_url}/refresh_account_tier/by-stored-accounts"
        )

    def auth_headers(self):
        return build_auth_headers(include_accept=True)

    def request(self, method, url, *, payload=None, timeout=30):
        response = requests.request(
            method,
            url,
            json=payload,
            headers=self.auth_headers(),
            timeout=timeout,
        )
        data = self.parse_json_response(response)
        if response.status_code == 401:
            clear_saved_session()
        return response, data

    def parse_json_response(self, response):
        try:
            return response.json()
        except Exception:
            return None

    def format_response_text(self, response, data):
        if data is None:
            return f"HTTP {response.status_code}\n\n{response.text}"
        return f"HTTP {response.status_code}\n\n{pformat(data, sort_dicts=False)}"

    def fetch_puuid(self, game_name: str, tag_line: str):
        payload = {
            "game_name": game_name,
            "tag_line": tag_line,
        }
        return self.request("POST", self.puuid_url, payload=payload, timeout=30)

    def fetch_match_ids(self, puuid: str, count: int):
        payload = {
            "puuid": puuid,
            "count": count,
        }
        return self.request("POST", self.match_ids_url, payload=payload, timeout=30)

    def fetch_match_detail(self, match_id: str):
        payload = {
            "match_id": match_id,
        }
        return self.request("POST", self.match_detail_url, payload=payload, timeout=30)

    def store_recent_matches(self, game_name: str, tag_line: str, count: int):
        payload = {
            "game_name": game_name,
            "tag_line": tag_line,
            "count": count,
        }
        return self.request("POST", self.store_matches_url, payload=payload, timeout=60)

    def search_accounts(self, keyword: str, limit: int = ACCOUNT_SEARCH_LIMIT):
        url = f"{self.search_accounts_url}?{urlencode({'keyword': keyword, 'limit': limit})}"
        return self.request("GET", url, timeout=30)

    def list_accounts(self, limit: int = ACCOUNT_SEARCH_LIMIT):
        url = f"{self.list_accounts_url}?{urlencode({'limit': limit})}"
        return self.request("GET", url, timeout=30)

    def store_selected_accounts(self, count: int, accounts: list[dict]):
        payload = {
            "count": count,
            "accounts": accounts,
        }
        return self.request(
            "POST",
            self.store_selected_accounts_url,
            payload=payload,
            timeout=300,
        )

    def refresh_selected_tiers(self, accounts: list[dict]):
        payload = {
            "accounts": accounts,
        }
        return self.request(
            "POST",
            self.refresh_selected_tiers_url,
            payload=payload,
            timeout=300,
        )
