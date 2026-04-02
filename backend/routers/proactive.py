from fastapi import APIRouter, Query, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from backend.auth import get_current_user
from wecom.user_service import user_service
from wecom.message_sender import message_sender
from wecom.scheduler import add_task, remove_task, list_tasks

router = APIRouter(prefix="/proactive", tags=["proactive"], dependencies=[Depends(get_current_user)])


class SendRequest(BaseModel):
    sender: str
    content: str
    external_userids: Optional[List[str]] = None
    attachments: Optional[List[Dict[str, Any]]] = None


class ScheduleRequest(BaseModel):
    task_id: str
    sender: str
    content: str
    cron: Dict[str, Any]   # APScheduler cron kwargs: { hour, minute, day_of_week? ... }
    external_userids: Optional[List[str]] = None


@router.post("")
async def send_proactive(req: SendRequest):
    """立即群发消息"""
    ids = req.external_userids or user_service.get_contact_list(req.sender)
    if not ids:
        raise HTTPException(status_code=404, detail="找不到任何客户")
    result = message_sender.send_proactive_msg(req.sender, ids, req.content, req.attachments)
    if not result["success"]:
        raise HTTPException(status_code=502, detail=result.get("errmsg", "发送失败"))
    return {"errcode": 0, "errmsg": "ok", "data": result}


@router.get("/schedule")
async def schedule_list():
    """获取定时任务列表"""
    return {"errcode": 0, "errmsg": "ok", "data": list_tasks()}


@router.post("/schedule")
async def schedule_add(req: ScheduleRequest):
    """新建定时任务"""
    if not req.cron:
        raise HTTPException(status_code=400, detail="cron 不能为空")
    add_task(req.task_id, req.sender, req.content, req.cron, req.external_userids)
    return {"errcode": 0, "errmsg": "ok", "task_id": req.task_id}


@router.delete("/schedule/{task_id}")
async def schedule_del(task_id: str):
    """删除定时任务"""
    remove_task(task_id)
    return {"errcode": 0, "errmsg": "ok"}
