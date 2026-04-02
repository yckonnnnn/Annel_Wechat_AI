from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Optional
from backend.auth import get_current_user
from wecom.user_service import user_service
from wecom.conversation_store import conversation_store

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("")
async def get_customer_list(
    search: Optional[str] = Query(None, description="搜索关键词（外部联系人 userid / 姓名）"),
    user: dict = Depends(get_current_user),
):
    """
    列出当前登录员工名下的所有外部联系人（从企微 API 拉取），合并本地对话记录。
    """
    # 1. 从企微 API 拉取该员工名下所有外部联系人 ID
    external_ids = user_service.get_contact_list(user["userid"])

    # 2. 若企微 API 返回空，回退到本地对话记录
    if not external_ids:
        customers = conversation_store.list_all_customers()
        if search:
            customers = [c for c in customers if search.lower() in c.get("external_userid", "").lower()]
        return {"errcode": 0, "errmsg": "ok", "data": {"count": len(customers), "customers": customers}}

    # 3. 逐个拉取客户详情，合并对话摘要
    conv_map = {c["external_userid"]: c for c in conversation_store.list_all_customers()}
    customers = []
    for eid in external_ids:
        info = user_service.get_external_contact(eid) or {}
        conv = conv_map.get(eid, {})
        entry = {
            "external_userid": eid,
            "name": info.get("name", ""),
            "avatar": info.get("avatar", ""),
            "corp_name": info.get("corp_name", ""),
            "message_count": conv.get("message_count", 0),
            "last_updated": conv.get("last_updated", 0),
        }
        if not search or search.lower() in eid.lower() or search.lower() in entry["name"].lower():
            customers.append(entry)

    customers.sort(key=lambda c: c["last_updated"], reverse=True)
    return {"errcode": 0, "errmsg": "ok", "data": {"count": len(customers), "customers": customers}}


@router.get("/{external_userid}/messages")
async def get_customer_messages(
    external_userid: str,
    limit: int = Query(50, ge=1, le=200),
    _user: dict = Depends(get_current_user),
):
    """获取客户对话消息列表"""
    messages = conversation_store.get_messages(external_userid, limit=limit)
    return {"errcode": 0, "errmsg": "ok", "data": {"messages": messages}}


@router.get("/{external_userid}")
async def get_customer_detail(
    external_userid: str,
    _user: dict = Depends(get_current_user),
):
    """获取客户详情（企微资料 + 对话摘要）"""
    summary = conversation_store.get_conversation_summary(external_userid)
    wecom_info = user_service.get_external_contact(external_userid) or {}
    if not summary and not wecom_info:
        raise HTTPException(status_code=404, detail="客户不存在")
    return {
        "errcode": 0,
        "errmsg": "ok",
        "data": {
            "external_userid": external_userid,
            "name": wecom_info.get("name", ""),
            "avatar": wecom_info.get("avatar", ""),
            "gender": wecom_info.get("gender", 0),
            "corp_name": wecom_info.get("corp_name", ""),
            "position": wecom_info.get("position", ""),
            "conversation_summary": summary,
        },
    }
