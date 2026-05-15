import json
import re
from html import unescape
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from core.auth_session import build_auth_headers, clear_saved_session
from repositories.dataset_repository import load_server_base_url

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
        if not use_auth:
            return {"Content-Type": "application/json"} if include_json else {}
        return build_auth_headers(include_json=include_json)

    def _send(self, request):
        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = response.read().decode("utf-8")
                content_type = response.headers.get_content_type()
                if content_type != "application/json":
                    preview = self._summarize_error_body(body)
                    raise RuntimeError(
                        "API server returned a non-JSON response.\n"
                        f"URL: {request.full_url}\n"
                        f"Content-Type: {content_type}\n"
                        f"Body: {preview}"
                    )
                return json.loads(body)
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            if exc.code == 401:
                clear_saved_session()
            raise RuntimeError(
                self._format_http_error(exc.code, request.full_url, detail)
            ) from exc
        except URLError as exc:
            raise RuntimeError(
                "API server connection failed.\n"
                f"Server: {self.base_url}\n"
                "Check whether the server is running and whether /health responds."
            ) from exc

    def _format_http_error(self, status_code, url, detail):
        preview = self._summarize_error_body(detail)
        if status_code == 503:
            return (
                "The server is temporarily unavailable (HTTP 503).\n"
                f"URL: {url}\n"
                "The API process may still be starting, crashed after deploy, or the "
                "server address may be pointing at an unavailable service.\n"
                "Check whether /health returns {\"status\": \"ok\"}, then try again.\n"
                f"Server response: {preview}"
            )

        return (
            f"HTTP {status_code}\n"
            f"URL: {url}\n"
            f"Server response: {preview}"
        )

    def _summarize_error_body(self, body):
        text = (body or "").strip()
        if not text:
            return "(empty response body)"

        if "<html" in text.lower():
            text = unescape(re.sub(r"<[^>]+>", " ", text))

        text = re.sub(r"\s+", " ", text).strip()
        if len(text) > 240:
            return f"{text[:237]}..."
        return text
