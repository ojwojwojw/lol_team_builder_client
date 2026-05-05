from __future__ import annotations

from fastapi import HTTPException, status

from ..stores.user_store import (
    count_users,
    create_user,
    get_user_by_username,
    list_users,
)
from ..security import create_access_token, hash_password, verify_password


class AuthService:
    def get_setup_status(self) -> dict:
        """최초 관리자 생성이 아직 필요한 상태인지 반환한다."""
        return {
            "needs_bootstrap": count_users() == 0,
        }

    def bootstrap_admin(self, username: str, password: str) -> dict:
        """사용자가 한 명도 없을 때 최초 관리자 계정을 한 번만 생성한다."""
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
        """아이디/비밀번호를 검증하고 JWT access token을 발급한다."""
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
        """관리자가 일반 사용자 계정을 추가할 때 사용하는 생성 함수다."""
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
        """관리자 화면에 보여줄 전체 사용자 목록을 직렬화해서 반환한다."""
        return {
            "users": [self._serialize_user(user) for user in list_users()]
        }

    def get_me(self, current_user: dict) -> dict:
        """현재 로그인한 사용자의 공개 가능한 정보만 반환한다."""
        return self._serialize_user(current_user)

    def _serialize_user(self, user: dict) -> dict:
        """비밀번호 관련 민감정보를 제외한 사용자 응답 형태를 만든다."""
        return {
            "id": user["id"],
            "username": user["username"],
            "is_admin": bool(user.get("is_admin")),
            "is_active": bool(user.get("is_active", True)),
            "created_at": user.get("created_at"),
        }

    def _validate_username_and_password(self, username: str, password: str) -> None:
        """최소 길이 기준으로 아이디/비밀번호 형식을 검증한다."""
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
