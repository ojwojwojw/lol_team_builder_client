from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import get_jwt_secret as get_env_jwt_secret
from .queries.auth_query import get_user_by_id


PROJECT_ROOT = Path(__file__).resolve().parents[1]
JWT_SECRET_FILE = PROJECT_ROOT / ".jwt_secret"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7
PASSWORD_HASH_ITERATIONS = 200_000
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    raw_salt = bytes.fromhex(salt) if salt else secrets.token_bytes(16)
    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        raw_salt,
        PASSWORD_HASH_ITERATIONS,
    )
    return hashed.hex(), raw_salt.hex()


def verify_password(password: str, stored_hash: str, stored_salt: str) -> bool:
    candidate_hash, _ = hash_password(password, stored_salt)
    return hmac.compare_digest(candidate_hash, stored_hash)


def create_access_token(
    user: dict,
    expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES,
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user["id"]),
        "username": user["username"],
        "is_admin": bool(user.get("is_admin")),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
    }
    return _encode_jwt(payload)


def decode_access_token(token: str) -> dict:
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
    except ValueError as exc:
        raise _unauthorized("Invalid access token format.") from exc

    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected_signature = _sign(signing_input)
    actual_signature = _urlsafe_b64decode(signature_b64)

    if not hmac.compare_digest(expected_signature, actual_signature):
        raise _unauthorized("Token signature mismatch.")

    payload = json.loads(_urlsafe_b64decode(payload_b64).decode("utf-8"))
    exp = int(payload.get("exp", 0))
    now_timestamp = int(datetime.now(timezone.utc).timestamp())
    if exp <= now_timestamp:
        raise _unauthorized("Token expired.")

    return payload


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized("Authentication required.")

    payload = decode_access_token(credentials.credentials)
    user_id = int(payload.get("sub", 0) or 0)
    user = get_user_by_id(user_id)
    if not user or not user.get("is_active"):
        raise _unauthorized("User is missing or inactive.")

    return user


def require_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required.",
        )
    return current_user


def get_jwt_secret() -> str:
    env_secret = get_env_jwt_secret()
    if env_secret:
        return env_secret

    if JWT_SECRET_FILE.exists():
        return JWT_SECRET_FILE.read_text(encoding="utf-8").strip()

    secret = secrets.token_urlsafe(48)
    JWT_SECRET_FILE.write_text(secret, encoding="utf-8")
    return secret


def _encode_jwt(payload: dict) -> str:
    header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
    header_b64 = _urlsafe_b64encode(
        json.dumps(header, separators=(",", ":")).encode("utf-8")
    )
    payload_b64 = _urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
    )
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature_b64 = _urlsafe_b64encode(_sign(signing_input))
    return f"{header_b64}.{payload_b64}.{signature_b64}"


def _sign(message: bytes) -> bytes:
    secret = get_jwt_secret().encode("utf-8")
    return hmac.new(secret, message, hashlib.sha256).digest()


def _urlsafe_b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("utf-8")


def _urlsafe_b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )
