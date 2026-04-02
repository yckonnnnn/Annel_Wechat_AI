from fastapi import APIRouter, Query, Depends
from typing import Optional
from backend.auth import get_current_user
from backend.wecom.user_service import user_service

router = APIRouter(prefix="/customers", tags=["customers"], dependencies=[Depends(get_current_user)])

@router.get("")
async def get_customer_list(userid: Optional[str] = Query(None)):
    if not userid:
        return {"errcode": 400, "errmsg": "缺少 userid 参数"}
    customer_ids = user_service.get_contact_list(userid)
    customers = []
    for cid in customer_ids:
        detail = user_service.get_external_contact(cid)
        if detail:
            customers.append(detail)
    return {"errcode": 0, "errmsg": "ok", "data": {"count": len(customers), "customers": customers}}

@router.get("/{external_userid}")
async def get_customer_detail(external_userid: str):
    detail = user_service.get_external_contact(external_userid)
    if not detail:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="客户不存在")
    return {"errcode": 0, "errmsg": "ok", "data": {"customer": detail}}
