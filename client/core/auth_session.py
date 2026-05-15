from repositories.dataset_repository import (
    clear_auth_token,
    load_auth_token,
    save_auth_token,
    save_auth_username,
)


def build_auth_headers(*, include_accept=False, include_json=False):
    headers = {}
    if include_accept:
        headers["Accept"] = "application/json"
    if include_json:
        headers["Content-Type"] = "application/json"

    token = load_auth_token().strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def clear_saved_session():
    clear_auth_token()
    save_auth_username("")


def save_login_session(token, username):
    save_auth_token(token)
    save_auth_username(username)
