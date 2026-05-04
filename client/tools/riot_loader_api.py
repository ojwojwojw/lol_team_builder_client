from __future__ import annotations

from pprint import pformat
from urllib.parse import urlencode

import requests

from domain.constants import ACCOUNT_SEARCH_LIMIT
from repositories.dataset_repository import load_server_base_url
from application.team_app import team_app


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
        self.firestore_stats_url = f"{self.api_base_url}/admin/firestore/stats"
        self.firestore_collection_url = f"{self.api_base_url}/admin/firestore/collections"
        self.firestore_delete_documents_url = f"{self.api_base_url}/admin/firestore/delete-documents"
        self.firestore_clear_collection_url = f"{self.api_base_url}/admin/firestore/clear-collection"
        self.firestore_delete_older_than_url = f"{self.api_base_url}/admin/firestore/delete-older-than"

    def auth_headers(self):
        token = team_app.load_auth_token().strip()
        headers = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

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
            team_app.clear_auth_token()
            team_app.save_auth_username("")
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

    def fetch_puuid(self, api_key: str, game_name: str, tag_line: str):
        payload = {
            "api_key": api_key,
            "game_name": game_name,
            "tag_line": tag_line,
        }
        return self.request("POST", self.puuid_url, payload=payload, timeout=30)

    def fetch_match_ids(self, api_key: str, puuid: str, count: int):
        payload = {
            "api_key": api_key,
            "puuid": puuid,
            "count": count,
        }
        return self.request("POST", self.match_ids_url, payload=payload, timeout=30)

    def fetch_match_detail(self, api_key: str, match_id: str):
        payload = {
            "api_key": api_key,
            "match_id": match_id,
        }
        return self.request("POST", self.match_detail_url, payload=payload, timeout=30)

    def store_recent_matches(
        self, api_key: str, game_name: str, tag_line: str, count: int
    ):
        payload = {
            "api_key": api_key,
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

    def store_selected_accounts(self, api_key: str, count: int, accounts: list[dict]):
        payload = {
            "api_key": api_key,
            "count": count,
            "accounts": accounts,
        }
        return self.request(
            "POST",
            self.store_selected_accounts_url,
            payload=payload,
            timeout=300,
        )

    def refresh_selected_tiers(self, api_key: str, accounts: list[dict]):
        payload = {
            "api_key": api_key,
            "accounts": accounts,
        }
        return self.request(
            "POST",
            self.refresh_selected_tiers_url,
            payload=payload,
            timeout=300,
        )

    def get_firestore_stats(self):
        return self.request("GET", self.firestore_stats_url, timeout=60)

    def list_firestore_documents(self, collection: str, limit: int):
        url = f"{self.firestore_collection_url}/{collection}/documents?{urlencode({'limit': limit})}"
        return self.request("GET", url, timeout=60)

    def get_firestore_document(self, collection: str, document_id: str):
        url = f"{self.firestore_collection_url}/{collection}/documents/{document_id}"
        return self.request("GET", url, timeout=60)

    def delete_firestore_documents(self, collection: str, document_ids: list[str]):
        payload = {
            "collection": collection,
            "document_ids": document_ids,
        }
        return self.request(
            "POST",
            self.firestore_delete_documents_url,
            payload=payload,
            timeout=60,
        )

    def clear_firestore_collection(self, collection: str):
        payload = {
            "collection": collection,
            "document_ids": [],
        }
        return self.request(
            "POST",
            self.firestore_clear_collection_url,
            payload=payload,
            timeout=120,
        )

    def delete_firestore_older_than(self, collection: str, days: int):
        payload = {
            "collection": collection,
            "days": days,
        }
        return self.request(
            "POST",
            self.firestore_delete_older_than_url,
            payload=payload,
            timeout=120,
        )
