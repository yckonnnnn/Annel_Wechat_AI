import xml.etree.ElementTree as ET
from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse
from backend.core_config import wecom_config
from wecom.crypto import WeComCrypto, verify_callback_signature
from wecom.token_manager import token_manager
from wecom.user_service import user_service
from wecom.message_sender import message_sender
from wecom.conversation_store import conversation_store

crypto = WeComCrypto(
    token=wecom_config["token"],
    encoding_aes_key=wecom_config["encoding_aes_key"],
    corp_id=wecom_config["corp_id"],
)

router = APIRouter(tags=["callback"])


def _xml_to_dict(xml_str: str) -> dict:
    root = ET.fromstring(xml_str)
    return {child.tag: child.text or "" for child in root}


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
        root = ET.fromstring(body.decode("utf-8"))
        encrypt_node = root.find("Encrypt")
    except ET.ParseError as e:
        raise HTTPException(status_code=400, detail="Invalid XML")

    if encrypt_node is None or not encrypt_node.text:
        raise HTTPException(status_code=400, detail="Missing Encrypt field")

    encrypt_msg = encrypt_node.text

    if not verify_callback_signature(wecom_config["token"], msg_signature, timestamp, nonce, encrypt_msg):
        raise HTTPException(status_code=400, detail="Invalid signature")
    try:
        decrypted_xml = crypto.decrypt_message(encrypt_msg)
        message_data = _xml_to_dict(decrypted_xml)
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
