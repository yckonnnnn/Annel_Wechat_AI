from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Optional
from backend.auth import get_current_user
from wecom.user_service import user_service
from wecom.conversation_store import conversation_store
from wecom.customer_cache import customer_cache

router = APIRouter(prefix="/customers", tags=["customers"], dependencies=[Depends(get_current_user)])


@router.get("")
async def get_customer_list(
    search: Optional[str] = Query(None, description="搜索关键词（外部联系人 userid / 姓名）"),
    user: dict = Depends(get_current_user),
):
    """
    列出当前登录员工名下的所有外部联系人

    使用缓存 + 增量同步策略：
    1. 先从本地缓存读取该员工的客户 ID 列表
    2. 调用企微 API 获取最新客户 ID 列表
    3. 如有新增客户，只拉取新增客户的详情（增量同步）
    4. 从缓存合并客户详情和对话摘要
    """
    userid = user["userid"]

    # 1. 从企微 API 获取最新客户 ID 列表
    external_ids = user_service.get_contact_list(userid)

    # 2. 如果 API 返回空，回退到本地对话记录
    if not external_ids:
        customers = conversation_store.list_all_customers()
        if search:
            customers = [c for c in customers if search.lower() in c.get("external_userid", "").lower()]
        return {"errcode": 0, "errmsg": "ok", "data": {"count": len(customers), "customers": customers}}

    # 3. 增量同步：比对缓存，只拉取新增客户详情
    sync_result = customer_cache.sync_user_customers(userid, force_full=False)

    # 4. 从缓存读取客户 ID 列表（已经包含本次同步的结果）
    cached_ids = customer_cache.get_user_customer_ids(userid)

    # 5. 批量获取客户详情（从缓存）
    conv_map = {c["external_userid"]: c for c in conversation_store.list_all_customers()}
    customers = []

    for eid in cached_ids:
        # 从缓存读取客户详情
        detail = customer_cache.get_customer_detail(eid) or {}
        conv = conv_map.get(eid, {})

        entry = {
            "external_userid": eid,
            "name": detail.get("name", ""),
            "avatar": detail.get("avatar", ""),
            "corp_name": detail.get("corp_name", ""),
            "message_count": conv.get("message_count", 0),
            "last_updated": conv.get("last_updated", 0),
        }

        # 搜索过滤
        if search and search.lower() not in eid.lower() and search.lower() not in entry["name"].lower():
            continue

        customers.append(entry)

    # 6. 按最后更新时间排序
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

    # 优先从缓存读取，没有再调用 API
    wecom_info = customer_cache.get_customer_detail(external_userid)
    if not wecom_info:
        wecom_info = user_service.get_external_contact(external_userid) or {}
        if wecom_info:
            customer_cache.save_customer_detail(external_userid, wecom_info)

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
