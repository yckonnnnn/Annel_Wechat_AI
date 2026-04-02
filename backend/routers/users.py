from fastapi import APIRouter, HTTPException, Depends
from backend.auth import get_current_user, require_admin, require_superadmin, _load_users, _save_users
from wecom.customer_cache import customer_cache

router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(get_current_user)])

@router.get("")
async def list_users(user: dict = Depends(require_admin)):
    return {"errcode": 0, "data": _load_users()}

@router.patch("/{userid}/role")
async def update_role(userid: str, role: str, admin: dict = Depends(require_superadmin)):
    if role not in ("staff", "admin", "superadmin"):
        raise HTTPException(status_code=400, detail="Invalid role")
    users = _load_users()
    target = next((u for u in users if u.get("userid") == userid), None)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    target["role"] = role
    _save_users(users)
    return {"errcode": 0, "errmsg": "ok"}

@router.patch("/{userid}/status")
async def update_status(userid: str, status: str, admin: dict = Depends(require_admin)):
    if status not in ("active", "disabled"):
        raise HTTPException(status_code=400, detail="Invalid status")
    users = _load_users()
    target = next((u for u in users if u.get("userid") == userid), None)
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    target["status"] = status
    _save_users(users)
    return {"errcode": 0, "errmsg": "ok"}


@router.post("/sync-all-customers")
async def sync_all_customers(admin: dict = Depends(require_superadmin)):
    """
    全量同步企业所有员工的所有客户数据

    用于首次初始化或定期刷新缓存。
    注意：该操作会调用企微 API 拉取所有员工的所有客户详情，可能耗时较长。
    """
    result = customer_cache.sync_all_customers_full()
    return {"errcode": 0, "data": result}


@router.get("/sync-stats")
async def get_sync_stats(_user: dict = Depends(get_current_user)):
    """获取同步缓存统计信息"""
    stats = customer_cache.get_stats()
    return {"errcode": 0, "data": stats}
