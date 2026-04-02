from fastapi import APIRouter, HTTPException, Depends
from backend.auth import get_current_user, require_admin, require_superadmin, _load_users, _save_users

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
