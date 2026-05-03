import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from repositories.dataset_repository import (
    clear_auth_token,
    load_auth_token,
    load_server_base_url,
)


class MatchApiClient:
    """Client for the local FastAPI match analysis server."""

    def __init__(self, base_url=None, timeout=10):
        self.base_url = (base_url or load_server_base_url()).rstrip("/")
        self.timeout = timeout

    def search_accounts(self, keyword, limit=20):
        """Call GET /accounts/search."""
        return self._get(
            "/accounts/search",
            {"keyword": keyword, "limit": limit},
        )

    def get_recent_matches_by_riot_id(self, game_name, tag_line, limit=10):
        """Call GET /matches/recent/by-riot-id."""
        return self._get(
            "/matches/recent/by-riot-id",
            {
                "game_name": game_name,
                "tag_line": tag_line,
                "limit": limit,
            },
        )

    def get_match_detail(self, match_id):
        """Call GET /matches/{match_id}."""
        encoded_match_id = quote(match_id, safe="")
        return self._get(f"/matches/{encoded_match_id}")

    def login(self, username, password):
        """Call POST /auth/login."""
        return self._post(
            "/auth/login",
            {"username": username, "password": password},
            use_auth=False,
        )

    def bootstrap_admin(self, username, password):
        """Call POST /auth/bootstrap-admin."""
        return self._post(
            "/auth/bootstrap-admin",
            {"username": username, "password": password},
            use_auth=False,
        )

    def get_me(self):
        """Call GET /auth/me."""
        return self._get("/auth/me")

    def _get(self, path, params=None):
        query = f"?{urlencode(params)}" if params else ""
        url = f"{self.base_url}{path}{query}"
        request = Request(url, method="GET", headers=self._build_headers())
        return self._send(request)

    def _post(self, path, payload=None, use_auth=True):
        url = f"{self.base_url}{path}"
        body = json.dumps(payload or {}).encode("utf-8")
        request = Request(
            url,
            data=body,
            method="POST",
            headers=self._build_headers(use_auth=use_auth, include_json=True),
        )
        return self._send(request)

    def _build_headers(self, use_auth=True, include_json=False):
        headers = {}
        if include_json:
            headers["Content-Type"] = "application/json"

        if use_auth:
            token = load_auth_token().strip()
            if token:
                headers["Authorization"] = f"Bearer {token}"
        return headers

    def _send(self, request):

        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = response.read().decode("utf-8")
                return json.loads(body)
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            if exc.code == 401:
                clear_auth_token()
            raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise RuntimeError(
                f"Cannot connect to API server: {self.base_url}"
            ) from exc
