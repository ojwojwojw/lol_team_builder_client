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


@router.post("/bootstrap-admin")
def bootstrap_admin(req: AuthBootstrapRequest = Body(...)):
    """Create the very first admin account exactly once."""
    return auth_service.bootstrap_admin(req.username, req.password)


@router.post("/login")
def login(req: LoginRequest = Body(...)):
    """Issue a JWT access token for one existing user."""
    return auth_service.login(req.username, req.password)


@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    """Return the current authenticated user."""
    return auth_service.get_me(current_user)


@router.get("/users")
def list_users(_: dict = Depends(require_admin_user)):
    """List known app users for the admin."""
    return auth_service.list_members()


@router.post("/users")
def create_user(
    req: CreateUserRequest = Body(...),
    _: dict = Depends(require_admin_user),
):
    """Create one friend account from the admin panel flow."""
    return auth_service.create_member(req.username, req.password)
