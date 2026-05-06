from fastapi import APIRouter, Depends

from ..security import require_admin_user
from ..stores.local_cache_store import get_cache_stats


router = APIRouter(
    prefix="/admin/cache",
    tags=["cache-admin"],
    dependencies=[Depends(require_admin_user)],
)


@router.get("/stats")
def get_stats():
    return get_cache_stats()
