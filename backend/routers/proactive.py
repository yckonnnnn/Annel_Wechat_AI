from fastapi import APIRouter, Request, Query, Depends
from typing import Optional, List
from backend.auth import get_current_user, require_admin
from backend.wecom.user_service import user_service
from backend.wecom.message_sender import message_sender
from backend.wecom.scheduler import add_task, remove_task, list_tasks
import time

router = APIRouter(prefix="/proactive", tags=["proactive"], dependencies=[Depends(get_current_user)])

@router.post("")
async def send_proactive(request: Request):
    data = await request.json()
    sender = data.get("sender", "")
    content = data.get("content", "")
    external_userids = data.get("external_userids")
    attachments = data.get("attachments")
    if not sender or not content:
        return {"errcode": 400, "errmsg": "missing sender or content"}
    ids = external_userids or user_service.get_contact_list(sender)
    if not ids:
        return {"errcode": 404, "errmsg": "no customers found"}
    result = message_sender.send_proactive_msg(sender, ids, content, attachments)
    return {"errcode": 0 if result["success"] else 500, "errmsg": "ok" if result["success"] else result.get("errmsg", ""), "data": result}

@router.get("/result")
async def proactive_result(msgid: str = Query(...), userid: str = Query(...)):
    result = message_sender.get_send_result(msgid, userid)
    return result

@router.post("/schedule")
async def schedule_add(request: Request):
    data = await request.json()
    tid = data.get("task_id")
    sender = data.get("sender")
    content = data.get("content")
    cron = data.get("cron")
    if not all([tid, sender, content, cron]):
        return {"errcode": 400, "errmsg": "missing fields"}
    add_task(tid, sender, content, cron, data.get("external_userids"))
    return {"errcode": 0, "errmsg": "ok", "task_id": tid}

@router.delete("/schedule/{task_id}")
async def schedule_del(task_id: str):
    remove_task(task_id)
    return {"errcode": 0, "errmsg": "ok"}

@router.get("/schedule")
async def schedule_list():
    return {"errcode": 0, "data": list_tasks()}
