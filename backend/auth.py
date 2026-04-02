import jwt
import time
import json
import os
import requests
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.core_config import wecom_config
from wecom.token_manager import token_manager

SECRET_KEY = os.environ.get("JWT_SECRET", "change-me-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_SECONDS = 8 * 3600

# 数据目录在项目根 data/，不在 backend/data/
USERS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "users.json")

def _load_users() -> list:
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def _save_users(users: list):
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode["exp"] = time.time() + ACCESS_TOKEN_EXPIRE_SECONDS
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception:
        return None

security = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    users = _load_users()
    user = next((u for u in users if u.get("userid") == payload.get("userid")), None)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") not in ("admin", "superadmin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

async def require_superadmin(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "superadmin":
        raise HTTPException(status_code=403, detail="Superadmin access required")
    return user

def get_or_create_user(userid: str) -> dict:
    users = _load_users()
    existing = next((u for u in users if u.get("userid") == userid), None)
    if existing:
        return existing
    # 首次登录，从企微获取详情
    user_info = _fetch_user_info(userid)
    role = "superadmin" if not users else "staff"
    new_user = {
        "userid": userid,
        "name": user_info.get("name", userid),
        "avatar": user_info.get("avatar", ""),
        "role": role,
        "status": "active",
        "created_at": int(time.time()),
    }
    users.append(new_user)
    _save_users(users)
    return new_user

def _fetch_user_info(userid: str) -> dict:
    token = token_manager.get_token()
    if not token:
        return {}
    try:
        r = requests.get(
            "https://qyapi.weixin.qq.com/cgi-bin/user/get",
            params={"access_token": token, "userid": userid},
            timeout=10,
        )
        r.raise_for_status()
        d = r.json()
        if d.get("errcode") == 0:
            return d
    except Exception as e:
        print(f"[Auth] fetch user info failed: {e}")
    return {}

def exchange_code_for_userid(code: str) -> Optional[str]:
    token = token_manager.get_token()
    if not token:
        return None
    try:
        r = requests.get(
            "https://qyapi.weixin.qq.com/cgi-bin/user/getuserinfo",
            params={"access_token": token, "code": code},
            timeout=10,
        )
        r.raise_for_status()
        d = r.json()
        if d.get("errcode") == 0:
            return d.get("UserId") or d.get("userid")
    except Exception as e:
        print(f"[Auth] exchange code failed: {e}")
    return None
