import json
from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse
from backend.core_config import wecom_config
from backend.wecom.crypto import WeComCrypto, verify_callback_signature
from backend.wecom.token_manager import token_manager
from backend.wecom.user_service import user_service
from backend.wecom.message_sender import message_sender
from backend.wecom.conversation_store import cs as conversation_store

crypto = WeComCrypto(
    token=wecom_config["token"],
    encoding_aes_key=wecom_config["encoding_aes_key"],
    corp_id=wecom_config["corp_id"],
)

router = APIRouter(tags=["callback"])

@router.get("/callback")
async def verify_callback(
    msg_signature: str = Query(...),
    timestamp: str = Query(...),
    nonce: str = Query(...),
    echostr: str = Query(...),
):
    if not crypto.verify_signature(timestamp, nonce, echostr, msg_signature):
        raise HTTPException(status_code=400, detail="Invalid signature")
    try:
        return PlainTextResponse(content=crypto.decrypt_echostr(echostr))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Decrypt failed: {e}")

@router.post("/callback")
async def handle_message(request: Request):
    body = await request.body()
    msg_signature = request.query_params.get("msg_signature", "")
    timestamp = request.query_params.get("timestamp", "")
    nonce = request.query_params.get("nonce", "")

    try:
        encrypted_data = json.loads(body)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    encrypt_msg = encrypted_data.get("encrypt", "")
    if not encrypt_msg:
        message_data = encrypted_data
    else:
        if not verify_callback_signature(wecom_config["token"], msg_signature, timestamp, nonce):
            raise HTTPException(status_code=400, detail="Invalid signature")
        try:
            message_data = crypto.decrypt_message(encrypt_msg)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Decrypt failed: {e}")

    from_user = message_data.get("FromUserName", "")
    msg_type = message_data.get("MsgType", "")
    content = message_data.get("Content", "")

    if msg_type == "text" and content:
        conversation_store.add_message(from_user, "text", content, "user")
        reply = f"收到：{content}"
        message_sender.send_text_message(from_user, reply)
        conversation_store.add_message(from_user, "text", reply, "system")

    return PlainTextResponse(content="success")
