import hashlib
import time
import xml.etree.ElementTree as ET
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from config import wecom_config, app_config
from wecom.crypto import WeComCrypto, verify_callback_signature
from wecom.token_manager import token_manager
from wecom.user_service import user_service
from wecom.message_sender import message_sender
from wecom.conversation_store import cs as conversation_store

app = FastAPI(title="企业微信客服系统", version="1.0.0")

# 企业微信域名验证文件内容
WECOM_DOMAIN_VERIFY_CONTENT = "auBFdL1YIFnT5xwk"


@app.get("/WW_verify_auBFdL1YIFnT5xwk.txt")
async def wecom_domain_verify():
    """企业微信域名所有权验证文件"""
    return PlainTextResponse(content=WECOM_DOMAIN_VERIFY_CONTENT)


# 初始化加密组件
crypto = WeComCrypto(
    token=wecom_config["token"],
    encoding_aes_key=wecom_config["encoding_aes_key"],
    corp_id=wecom_config["corp_id"]
)


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok", "timestamp": time.time()}


@app.get("/customers")
async def get_customer_list(userid: str = Query(None, description="咨询师 userid")):
    """获取咨询师客户列表"""
    if not userid:
        return {"errcode": 400, "errmsg": "缺少 userid 参数"}

    customer_ids = user_service.get_contact_list(userid)
    customers = []
    for cid in customer_ids:
        detail = user_service.get_external_contact(cid)
        if detail:
            customers.append(detail)

    return {"errcode": 0, "errmsg": "ok", "data": {"count": len(customers), "customers": customers}}


@app.get("/customers/{external_userid}")
async def get_customer_detail(external_userid: str):
    """获取单个客户详情"""
    detail = user_service.get_external_contact(external_userid)
    if not detail:
        raise HTTPException(status_code=404, detail="客户不存在")
    return {"errcode": 0, "errmsg": "ok", "data": {"customer": detail}}


@app.get("/users")
async def get_user_list(department_id: int = Query(1, description="部门 ID")):
    """获取企业成员列表"""
    users = user_service.get_user_list(department_id)
    return {"errcode": 0, "errmsg": "ok", "data": {"count": len(users), "users": users}}


@app.get("/callback")
async def verify_callback(
    msg_signature: str = Query(...),
    timestamp: str = Query(...),
    nonce: str = Query(...),
    echostr: str = Query(...)
):
    """
    企业微信回调 URL 验证（GET 请求）

    企业微信会发送 GET 请求验证 URL 的有效性
    需要验证签名并解密 echostr 后返回
    """
    print(f"[Callback GET] 收到验证请求:")
    print(f"  msg_signature: {msg_signature}")
    print(f"  timestamp: {timestamp}")
    print(f"  nonce: {nonce}")
    print(f"  echostr: {echostr[:20]}...")

    # 验证签名
    if not crypto.verify_signature(timestamp, nonce, echostr, msg_signature):
        print("[Callback GET] 签名验证失败")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # 解密 echostr 并返回
    try:
        decrypted_echostr = crypto.decrypt_echostr(echostr)
        print(f"[Callback GET] 验证成功，返回：{decrypted_echostr}")
        return PlainTextResponse(content=decrypted_echostr)
    except Exception as e:
        print(f"[Callback GET] 解密失败：{e}")
        raise HTTPException(status_code=400, detail=f"Decrypt failed: {e}")


@app.post("/callback")
async def handle_message(request: Request):
    """
    接收企业微信消息（POST 请求）

    处理流程：
    1. 验证签名
    2. 解密消息体
    3. 获取用户信息
    4. 调用大模型生成回复（目前先返回测试消息）
    5. 发送回复给用户
    """
    print(f"[Callback POST] 收到消息请求")

    # 获取请求体
    body = await request.body()
    print(f"[Callback POST] 原始请求体：{body[:200]}...")

    # 获取 URL 参数用于验证
    msg_signature = request.query_params.get("msg_signature", "")
    timestamp = request.query_params.get("timestamp", "")
    nonce = request.query_params.get("nonce", "")

    # 解析请求体（企业微信发送的是 XML）
    try:
        root = ET.fromstring(body.decode("utf-8"))
        encrypt_node = root.find("Encrypt")
    except ET.ParseError as e:
        print(f"[Callback POST] XML 解析失败：{e}")
        raise HTTPException(status_code=400, detail="Invalid XML")

    if encrypt_node is None or not encrypt_node.text:
        print("[Callback POST] 未找到 Encrypt 字段")
        raise HTTPException(status_code=400, detail="Missing Encrypt field")

    encrypt_msg = encrypt_node.text

    # 验证签名（使用 token、timestamp、nonce、encrypt_msg）
    if not verify_callback_signature(wecom_config["token"], msg_signature, timestamp, nonce, encrypt_msg):
        print("[Callback POST] 签名验证失败")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # 解密消息
    try:
        decrypted_xml = crypto.decrypt_message(encrypt_msg)
        root = ET.fromstring(decrypted_xml)
        message_data = {child.tag: child.text or "" for child in root}
        print(f"[Callback POST] 解密后的消息：{message_data}")
    except Exception as e:
        print(f"[Callback POST] 解密失败：{e}")
        raise HTTPException(status_code=400, detail=f"Decrypt failed: {e}")

    # 提取消息内容
    from_user = message_data.get("FromUserName", "")
    to_user = message_data.get("ToUserName", "")
    msg_type = message_data.get("MsgType", "")
    content = message_data.get("Content", "")
    create_time = message_data.get("CreateTime", 0)

    print(f"[Callback POST] 消息详情:")
    print(f"  FromUserName: {from_user}")
    print(f"  MsgType: {msg_type}")
    print(f"  Content: {content[:50] if content else 'N/A'}...")

    # 如果是文本消息，获取用户信息并回复
    if msg_type == "text" and content:
        # 获取客户信息
        user_info = user_service.get_contact_info(from_user)
        print(f"[Callback POST] 用户信息：{user_info}")

        # TODO: 这里调用大模型 API
        # 目前先返回测试消息
        reply_content = f"""您好！我是 AI 客服助手 🤖

收到您的消息：{content}

---
用户信息：
{user_info}

（这是测试消息，大模型集成待配置）"""

        # 发送回复
        success = message_sender.send_text_message(from_user, reply_content)

        if success:
            print("[Callback POST] 回复发送成功")
        else:
            print("[Callback POST] 回复发送失败")

    # 返回成功响应（企业微信要求返回空或 success）
    return PlainTextResponse(content="success")


if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("企业微信客服系统 - 启动中...")
    print("=" * 60)
    print(f"CorpID: {wecom_config['corp_id']}")
    print(f"AgentID: {wecom_config['agent_id']}")
    print(f"Token: {wecom_config['token']}")
    print(f"EncodingAESKey: {wecom_config['encoding_aes_key'][:10]}...")
    print(f"监听地址：http://{app_config['host']}:{app_config['port']}")
    print(f"回调路径：/callback")
    print("=" * 60)
    print("\n启动 ngrok 后，将生成的 HTTPS URL + /callback 配置到企业微信后台")
    print("示例：https://xxxx.ngrok.io/callback\n")

    uvicorn.run(app, host=app_config["host"], port=app_config["port"])
