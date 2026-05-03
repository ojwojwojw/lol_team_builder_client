from __future__ import annotations

from fastapi import HTTPException, status

from ..queries.auth_query import (
    count_users,
    create_user,
    get_user_by_username,
    list_users,
)
from ..security import create_access_token, hash_password, verify_password


class AuthService:
    def bootstrap_admin(self, username: str, password: str) -> dict:
        username = username.strip()
        self._validate_username_and_password(username, password)

        if count_users() > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 사용자 계정이 존재합니다. 최초 관리자 생성은 한 번만 가능합니다.",
            )

        password_hash, password_salt = hash_password(password)
        user = create_user(username, password_hash, password_salt, is_admin=True)
        return {
            "message": "최초 관리자 계정이 생성되었습니다.",
            "user": self._serialize_user(user),
            "access_token": create_access_token(user),
            "token_type": "bearer",
        }

    def login(self, username: str, password: str) -> dict:
        username = username.strip()
        user = get_user_by_username(username)
        if not user or not verify_password(
            password,
            user["password_hash"],
            user["password_salt"],
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="아이디 또는 비밀번호가 올바르지 않습니다.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.get("is_active"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="비활성화된 계정입니다.",
            )

        return {
            "access_token": create_access_token(user),
            "token_type": "bearer",
            "user": self._serialize_user(user),
        }

    def create_member(self, username: str, password: str) -> dict:
        username = username.strip()
        self._validate_username_and_password(username, password)

        existing = get_user_by_username(username)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 존재하는 아이디입니다.",
            )

        password_hash, password_salt = hash_password(password)
        user = create_user(username, password_hash, password_salt, is_admin=False)
        return {
            "message": "사용자 계정이 생성되었습니다.",
            "user": self._serialize_user(user),
        }

    def list_members(self) -> dict:
        return {
            "users": [self._serialize_user(user) for user in list_users()]
        }

    def get_me(self, current_user: dict) -> dict:
        return self._serialize_user(current_user)

    def _serialize_user(self, user: dict) -> dict:
        return {
            "id": user["id"],
            "username": user["username"],
            "is_admin": bool(user.get("is_admin")),
            "is_active": bool(user.get("is_active", True)),
            "created_at": user.get("created_at"),
        }

    def _validate_username_and_password(self, username: str, password: str) -> None:
        if len(username) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="아이디는 3자 이상이어야 합니다.",
            )
        if len(password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="비밀번호는 8자 이상이어야 합니다.",
            )
