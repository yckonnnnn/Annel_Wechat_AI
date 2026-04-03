import xml.etree.ElementTree as ET
import traceback
import hashlib
from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse
from backend.core_config import wecom_config, llm_config
from wecom.crypto import WeComCrypto, verify_callback_signature
from wecom.conversation_store import conversation_store
from wecom.customer_cache import customer_cache
from wecom.message_sender import message_sender
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
async def verify_callback(msg_signature: str = Query(...), timestamp: str = Query(...), nonce: str = Query(...), echostr: str = Query(...)):
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

    # 原始 body 记录
    body_str = body.decode("utf-8", errors="replace")
    with open("/tmp/callback_raw.log", "a") as f:
        f.write(f"=== {timestamp} ===\n")
        f.write(f"Query: sig={msg_signature[:20]}... ts={timestamp} nonce={nonce}\n")
        f.write(f"Body ({len(body)} bytes):\n{body_str[:1000]}\n\n")

    try:
        root = ET.fromstring(body_str)
        encrypt_node = root.find("Encrypt")

        # 更详细的调试
        if encrypt_node is None:
            # 尝试查找所有子节点
            all_tags = [child.tag for child in root]
            with open("/tmp/callback_raw.log", "a") as f:
                f.write(f"ERROR: No Encrypt node. All tags: {all_tags}\n")
            raise HTTPException(status_code=400, detail=f"Missing Encrypt. Tags: {all_tags}")

        raw_enc = encrypt_node.text or ""
        encrypt_msg = raw_enc.strip()

        if not encrypt_msg:
            with open("/tmp/callback_raw.log", "a") as f:
                f.write(f"ERROR: Empty encrypt text. raw_enc={repr(raw_enc)}\n")
            raise HTTPException(status_code=400, detail="Empty encrypt content")

        # 调试签名计算
        values = [wecom_config["token"], timestamp, nonce, encrypt_msg]
        values.sort()
        calc_sig = hashlib.sha1("".join(values).encode("utf-8")).hexdigest()

        with open("/tmp/callback_raw.log", "a") as f:
            f.write(f"Encrypt len={len(encrypt_msg)}\n")
            f.write(f"Calc sig: {calc_sig}\n")
            f.write(f"Recv sig: {msg_signature}\n")
            f.write(f"Match: {calc_sig == msg_signature}\n")

        if not verify_callback_signature(wecom_config["token"], msg_signature, timestamp, nonce, encrypt_msg):
            raise HTTPException(status_code=400, detail="Invalid signature")

        decrypted_xml = crypto.decrypt_message(encrypt_msg)
        message_data = _xml_to_dict(decrypted_xml)

        from_user = message_data.get("FromUserName", "")
        msg_type = message_data.get("MsgType", "")
        content = message_data.get("Content", "")
        sender_userid = message_data.get("UserID", "") or message_data.get("userID", "")
        if not sender_userid:
            sender_userid = customer_cache.find_owner_by_external_userid(from_user)
        if not sender_userid and llm_config.get("default_userid"):
            sender_userid = llm_config["default_userid"]

        with open("/tmp/callback_raw.log", "a") as f:
            f.write(f"From: {from_user}, Type: {msg_type}, Sender: {sender_userid}\n")
            f.write(f"Content: {content[:50]}...\n")

        if msg_type == "text" and content:
            conversation_store.add_message(from_user, "text", content, "user")
            if sender_userid:
                history = conversation_store.get_messages(from_user, limit=llm_config["max_context"])
                openai_messages = [{"role": "user" if m.get("from")=="user" else "assistant", "content": m.get("content", "")} for m in history]
                reply = llm_client.chat(openai_messages)
                result = message_sender.send_external_text_message(sender_userid, from_user, reply)

                with open("/tmp/callback_raw.log", "a") as f:
                    f.write(f"Reply: {reply[:50]}..., Send result: {result}\n")

                if result.get("success"):
                    conversation_store.add_message(from_user, "text", reply, "system", extra={"sender": sender_userid})
                else:
                    conversation_store.add_message(from_user, "text", f"fail:{result.get('errmsg')}", "system", extra={"sender": sender_userid, "error": result})
            else:
                with open("/tmp/callback_raw.log", "a") as f:
                    f.write("WARNING: No sender_userid found\n")

        with open("/tmp/callback_raw.log", "a") as f:
            f.write("SUCCESS\n\n")
        return PlainTextResponse(content="success")
    except HTTPException:
        raise
    except Exception as e:
        with open("/tmp/callback_raw.log", "a") as f:
            f.write(f"ERROR: {e}\n{traceback.format_exc()}\n\n")
        raise HTTPException(status_code=400, detail=str(e)[:200])
