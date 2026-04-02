from fastapi import APIRouter, HTTPException, Query, Depends
from urllib.parse import quote
from backend.auth import exchange_code_for_userid, get_or_create_user, create_access_token, get_current_user
from backend.core_config import wecom_config

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/wecom-login-url")
async def wecom_login_url(redirect_uri: str = Query(...)):
    """获取企业微信扫码登录 URL（PC 端扫码，适用于普通浏览器）"""
    corp_id = wecom_config["corp_id"]
    agent_id = wecom_config["agent_id"]
    encoded_uri = quote(redirect_uri, safe="")
    url = (
        f"https://open.work.weixin.qq.com/wwopen/sso/qrConnect?"
        f"appid={corp_id}&agentid={agent_id}&redirect_uri={encoded_uri}&state=STATE"
    )
    return {"errcode": 0, "url": url}

@router.get("/callback")
async def auth_callback(code: str = Query(...)):
    """企微扫码回调，用 code 换 token"""
    userid = exchange_code_for_userid(code)
    if not userid:
        raise HTTPException(status_code=400, detail="Failed to exchange code")
    user = get_or_create_user(userid)
    token = create_access_token({"userid": user["userid"], "role": user["role"]})
    return {
        "errcode": 0,
        "access_token": token,
        "user": {
            "userid": user["userid"],
            "name": user["name"],
            "avatar": user["avatar"],
            "role": user["role"],
        },
    }

@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    return {
        "errcode": 0,
        "user": {
            "userid": user["userid"],
            "name": user["name"],
            "avatar": user.get("avatar", ""),
            "role": user["role"],
        },
    }
