import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from repositories.dataset_repository import (
    clear_auth_token,
    load_auth_token,
    load_server_base_url,
    save_auth_username,
)

class BaseApiClient:
    """Shared HTTP client for FastAPI requests."""

    def __init__(self, base_url=None, timeout=10):
        self.base_url = (base_url or load_server_base_url()).rstrip("/")
        self.timeout = timeout

    def _get(self, path, params=None, use_auth=True):
        query = f"?{urlencode(params)}" if params else ""
        url = f"{self.base_url}{path}{query}"
        request = Request(
            url,
            method="GET",
            headers=self._build_headers(use_auth=use_auth),
        )
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
                save_auth_username("")
            raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise RuntimeError(
                f"Cannot connect to API server: {self.base_url}"
            ) from exc
