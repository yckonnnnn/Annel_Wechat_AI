import json,os
from apscheduler.schedulers.background import BackgroundScheduler
from wecom.user_service import user_service
from wecom.message_sender import message_sender

TASKS_FILE=os.path.join(os.path.dirname(__file__).replace("/wecom",""),"data","scheduled_tasks.json")

def _load():
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE) as f:return json.load(f)
    return []

def _save(t):
    os.makedirs(os.path.dirname(TASKS_FILE),exist_ok=True)
    with open(TASKS_FILE,"w") as f:json.dump(t,f,ensure_ascii=False,indent=2)

scheduler=BackgroundScheduler(timezone="Asia/Shanghai")

def _run_task(task_id,sender,content,external_userids):
    ids=external_userids or user_service.get_contact_list(sender)
    result=message_sender.send_proactive_msg(sender,ids,content)
    print(f"[Scheduler] task={task_id} result={result}")

def add_task(task_id,sender,content,cron_expr,external_userids=None):
    if scheduler.get_job(task_id):scheduler.remove_job(task_id)
    scheduler.add_job(_run_task,"cron",id=task_id,
        kwargs={"task_id":task_id,"sender":sender,"content":content,"external_userids":external_userids},
        **cron_expr)
    tasks=[t for t in _load() if t["id"]!=task_id]
    tasks.append({"id":task_id,"sender":sender,"content":content,"cron":cron_expr,"external_userids":external_userids})
    _save(tasks);return True

def remove_task(task_id):
    if scheduler.get_job(task_id):scheduler.remove_job(task_id)
    _save([t for t in _load() if t["id"]!=task_id]);return True

def list_tasks():return _load()

def restore_tasks():
    for t in _load():
        try:add_task(t["id"],t["sender"],t["content"],t["cron"],t.get("external_userids"))
        except Exception as e:print("[Scheduler] restore fail",e)

scheduler.start()
restore_tasks()
