from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Optional
from backend.auth import get_current_user
from wecom.user_service import user_service
from wecom.conversation_store import conversation_store

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("")
async def get_customer_list(
    search: Optional[str] = Query(None, description="搜索关键词（external_userid 前缀匹配）"),
    _user: dict = Depends(get_current_user),
):
    """
    列出所有有对话记录的客户，按最近活跃排序。
    search 参数可按 external_userid 模糊过滤。
    """
    customers = conversation_store.list_all_customers()
    if search:
        customers = [c for c in customers if search.lower() in c.get("external_userid", "").lower()]
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
