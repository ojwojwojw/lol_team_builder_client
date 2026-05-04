from fastapi import APIRouter, Body, Depends

from ..models.request_models import (
    AuthBootstrapRequest,
    CreateUserRequest,
    LoginRequest,
)
from ..security import get_current_user, require_admin_user
from ..services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["auth"])
auth_service = AuthService()


@router.get("/setup-status")
def get_setup_status():
    """최초 관리자 생성이 필요한지 클라이언트에 알려준다."""
    return auth_service.get_setup_status()


@router.post("/bootstrap-admin")
def bootstrap_admin(req: AuthBootstrapRequest = Body(...)):
    """최초 관리자 계정을 한 번만 생성하는 요청을 처리한다."""
    return auth_service.bootstrap_admin(req.username, req.password)


@router.post("/login")
def login(req: LoginRequest = Body(...)):
    """아이디와 비밀번호를 받아 로그인 토큰 발급을 요청한다."""
    return auth_service.login(req.username, req.password)


@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    """현재 Bearer 토큰이 가리키는 사용자 정보를 반환한다."""
    return auth_service.get_me(current_user)


@router.get("/users")
def list_users(_: dict = Depends(require_admin_user)):
    """관리자 전용 사용자 목록 조회 요청을 처리한다."""
    return auth_service.list_members()


@router.post("/users")
def create_user(
    req: CreateUserRequest = Body(...),
    _: dict = Depends(require_admin_user),
):
    """관리자가 일반 사용자 계정을 추가하는 요청을 처리한다."""
    return auth_service.create_member(req.username, req.password)
