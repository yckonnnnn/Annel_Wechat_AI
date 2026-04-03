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

    # Debug: log raw request
    body_str = body.decode("utf-8", errors="replace")
    with open("/tmp/callback_raw.log", "a") as f:
        f.write(f"=== {timestamp} ===\n")
        f.write(f"sig={msg_signature[:30]}... ts={timestamp} nonce={nonce}\n")
        f.write(f"Body ({len(body)} bytes):\n")
        f.write(body_str[:3000] + "\n")

    try:
        root = ET.fromstring(body_str)
        encrypt_node = root.find("Encrypt")

        if encrypt_node is None:
            all_tags = [c.tag for c in root]
            with open("/tmp/callback_raw.log", "a") as f:
                f.write(f"ERROR: No Encrypt. Tags={all_tags}\n")
            raise HTTPException(status_code=400, detail=f"No Encrypt node. Tags: {all_tags}")

        raw_enc = encrypt_node.text or ""
        encrypt_msg = raw_enc.strip()

        with open("/tmp/callback_raw.log", "a") as f:
            f.write(f"Encrypt len={len(encrypt_msg)}\n")

        if not encrypt_msg:
            raise HTTPException(status_code=400, detail="Empty encrypt")

        # Verify signature
        if not verify_callback_signature(wecom_config["token"], msg_signature, timestamp, nonce, encrypt_msg):
            with open("/tmp/callback_raw.log", "a") as f:
                f.write(f"SIG FAIL\n")
            raise HTTPException(status_code=400, detail="Invalid signature")

        # Decrypt
        decrypted_xml = crypto.decrypt_message(encrypt_msg)
        message_data = _xml_to_dict(decrypted_xml)

        from_user = message_data.get("FromUserName", "")
        msg_type = message_data.get("MsgType", "")
        content = message_data.get("Content", "")

        # Find sender
        sender_userid = message_data.get("UserID", "") or message_data.get("userID", "")
        if not sender_userid:
            sender_userid = customer_cache.find_owner_by_external_userid(from_user)
        if not sender_userid and llm_config.get("default_userid"):
            sender_userid = llm_config["default_userid"]

        with open("/tmp/callback_raw.log", "a") as f:
            f.write(f"From={from_user}, Type={msg_type}, Sender={sender_userid}\n")
            f.write(f"Content={content[:50]}...\n")

        if msg_type == "text" and content:
            conversation_store.add_message(from_user, "text", content, "user")
            if sender_userid:
                history = conversation_store.get_messages(from_user, limit=llm_config["max_context"])
                openai_messages = [{"role": "user" if m.get("from")=="user" else "assistant", "content": m.get("content", "")} for m in history]
                reply = llm_client.chat(openai_messages)
                result = message_sender.send_external_text_message(sender_userid, from_user, reply)

                with open("/tmp/callback_raw.log", "a") as f:
                    f.write(f"Reply: {reply[:30]}... Result: {result}\n")

                if result.get("success"):
                    conversation_store.add_message(from_user, "text", reply, "system", extra={"sender": sender_userid})
                else:
                    conversation_store.add_message(from_user, "text", f"fail:{result.get('errmsg')}", "system", extra={"sender": sender_userid, "error": result})
            else:
                with open("/tmp/callback_raw.log", "a") as f:
                    f.write("WARNING: No sender_userid\n")

        with open("/tmp/callback_raw.log", "a") as f:
            f.write("SUCCESS\n\n")
        return PlainTextResponse(content="success")

    except HTTPException:
        raise
    except Exception as e:
        with open("/tmp/callback_raw.log", "a") as f:
            f.write(f"EXCEPTION: {e}\n")
        raise HTTPException(status_code=400, detail=str(e)[:200])
