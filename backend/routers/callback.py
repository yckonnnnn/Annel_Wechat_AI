import xml.etree.ElementTree as ET
from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse
from backend.core_config import wecom_config, llm_config
from wecom.crypto import WeComCrypto, verify_callback_signature
from wecom.token_manager import token_manager
from wecom.user_service import user_service
from wecom.message_sender import message_sender
from wecom.conversation_store import conversation_store
from wecom.customer_cache import customer_cache
from backend.llm_client import llm_client

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

    body_str = body.decode("utf-8", errors="replace")
    with open("/tmp/callback_body.log", "a") as f:
        f.write(f"=== BODY ===\n{body_str}\n\n")
    try:
        root = ET.fromstring(body_str)
        encrypt_node = root.find("Encrypt")
    except ET.ParseError as e:
        raise HTTPException(status_code=400, detail="Invalid XML")

    if encrypt_node is None or not encrypt_node.text:
        raise HTTPException(status_code=400, detail="Missing Encrypt field")

    encrypt_msg = encrypt_node.text.strip() if encrypt_node.text else ""

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

    # 文本消息处理
    if msg_type == "text" and content:
        # 保存消息到对话历史
        conversation_store.add_message(from_user, "text", content, "user")

        # 构造上下文对话历史
        history = conversation_store.get_messages(from_user, limit=llm_config["max_context"])
        openai_messages = [
            {"role": "user" if m.get("from") == "user" else "assistant", "content": m.get("content", "")}
            for m in history
        ]

        # 调用大模型生成回复
        reply = llm_client.chat(openai_messages)

        # 判断是场景1（员工→自建应用）还是场景2（客户→员工外部联系人）
        # 优先从消息体中取员工 UserID，其次从客户缓存反查归属员工
        owner_userid = message_data.get("UserID", "") or message_data.get("userID", "")
        if not owner_userid:
            owner_userid = customer_cache.find_owner_by_external_userid(from_user)

        if owner_userid:
            # 场景2：外部客户给员工发消息 → 代员工回复外部客户
            result = message_sender.send_external_text_message(owner_userid, from_user, reply)
            sent = result.get("success", False)
            print(f"[Callback] 场景2 外部回复: {owner_userid} → {from_user}: {reply[:50]}... result={result}")
        else:
            # 场景1：员工给自建应用发消息 → 通过应用直接回复员工
            sent = message_sender.send_text_message(from_user, reply)
            result = {"success": sent}
            print(f"[Callback] 场景1 应用回复 → {from_user}: {reply[:50]}... sent={sent}")

        if sent:
            conversation_store.add_message(from_user, "text", reply, "system", extra={"owner": owner_userid})
        else:
            fail_msg = f"消息发送失败: {result.get('errmsg', 'unknown')}"
            print(f"[Callback] 发送失败: {fail_msg}")
            conversation_store.add_message(from_user, "text", fail_msg, "system", extra={"error": result})

    return PlainTextResponse(content="success")
