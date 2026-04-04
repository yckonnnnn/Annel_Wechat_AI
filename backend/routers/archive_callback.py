"""
会话内容存档回调处理

企微会在有新消息时推送事件到此端点（最小间隔 15 秒）
收到事件后：拉取消息 → 解密 → 过滤外部客户消息 → 调 LLM → （记录待发回复）
"""

import json
import time
from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse

from backend.core_config import wecom_config, llm_config
from backend.llm_client import llm_client
from wecom.conversation_store import conversation_store
from wecom.finance_sdk import get_finance_sdk

router = APIRouter(tags=["archive"])

# 记录已处理到的最大 seq，避免重复处理
_last_seq: int = 0


def _is_external_message(msg: dict) -> bool:
    """判断是否是外部联系人发给内部员工的文本消息"""
    # msgtype = "text"，from 是外部用户（external_userid 格式以 "wm" 开头）
    if msg.get("msgtype") != "text":
        return False
    sender = msg.get("from", "")
    # 企业内部员工 ID 不以 wm 开头；外部联系人 external_userid 以 wm 开头
    return sender.startswith("wm")


def _get_employee_from_msg(msg: dict) -> str:
    """从消息中找到接收方的内部员工 userid"""
    tolist = msg.get("tolist", [])
    for uid in tolist:
        if not uid.startswith("wm"):   # 内部员工
            return uid
    return wecom_config.get("default_userid", "")


@router.post("/archive/callback")
async def archive_callback(request: Request):
    """
    企微会话存档事件推送接收端点

    企微推送格式为 JSON，包含 corpid 等字段（不含消息内容，消息要主动拉取）
    收到事件后立即拉取新消息并处理。
    """
    global _last_seq

    try:
        body = await request.json()
    except Exception:
        body = {}

    print(f"[ArchiveCallback] 收到事件推送: {body}")

    # 初始化 Finance SDK
    try:
        sdk = get_finance_sdk(
            corp_id=wecom_config["corp_id"],
            secret=wecom_config.get("msgaudit_secret", ""),
        )
    except FileNotFoundError as e:
        print(f"[ArchiveCallback] SDK 未就绪: {e}")
        return PlainTextResponse("ok")

    # 拉取从上次 seq 开始的新消息
    try:
        messages = sdk.get_chat_data(seq=_last_seq, limit=100)
    except Exception as e:
        print(f"[ArchiveCallback] 拉取消息失败: {e}")
        return PlainTextResponse("ok")

    if not messages:
        return PlainTextResponse("ok")

    # 更新 seq
    max_seq = max(m.get("_seq", 0) for m in messages)
    _last_seq = max_seq + 1

    print(f"[ArchiveCallback] 拉取到 {len(messages)} 条消息，max_seq={max_seq}")

    # 处理每条消息
    for msg in messages:
        if not _is_external_message(msg):
            continue

        external_userid = msg["from"]
        employee_userid = _get_employee_from_msg(msg)
        text_content = msg.get("text", {}).get("content", "")

        if not text_content:
            continue

        print(f"[ArchiveCallback] 外部客户消息: {external_userid} → {employee_userid}: {text_content[:50]}")

        # 保存客户消息到对话历史
        conversation_store.add_message(external_userid, "text", text_content, "user")

        # 构建对话上下文
        history = conversation_store.get_messages(external_userid, limit=llm_config["max_context"])
        openai_messages = [
            {
                "role": "user" if m.get("from") == "user" else "assistant",
                "content": m.get("content", ""),
            }
            for m in history
        ]

        # 调用大模型生成回复
        reply = llm_client.chat(openai_messages)
        print(f"[ArchiveCallback] LLM 回复: {reply[:80]}")

        # 保存 AI 回复到对话历史
        conversation_store.add_message(
            external_userid, "text", reply, "system",
            extra={"owner": employee_userid, "source": "archive_callback"},
        )

        # TODO: 发送回复（当前企微无法直接注入私聊，此处记录待人工或其他方式发送）
        print(f"[ArchiveCallback] 待发回复 ({employee_userid} → {external_userid}): {reply[:80]}")

    return PlainTextResponse("ok")
