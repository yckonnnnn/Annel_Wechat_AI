from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import JSONResponse
from urllib.parse import quote
from backend.auth import exchange_code_for_userid, get_or_create_user, create_access_token
from backend.core_config import wecom_config

router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/wecom-login-url")
async def wecom_login_url(redirect_uri: str = Query(...)):
    """获取企业微信扫码登录 URL"""
    corp_id = wecom_config["corp_id"]
    encoded_uri = quote(redirect_uri, safe="")
    url = (
        f"https://open.weixin.qq.com/connect/oauth2/authorize?"
        f"appid={corp_id}&redirect_uri={encoded_uri}&response_type=code&"
        f"scope=snsapi_base&state=STATE#wechat_redirect"
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
async def get_me(request: Request):
    # 依赖注入由 main.py 中的全局依赖处理，或直接在这里用
    from backend.auth import get_current_user
    user = await get_current_user(request.scope.get("Authorization"))  # 简化处理，后续走依赖
    return {"errcode": 0, "user": user}
