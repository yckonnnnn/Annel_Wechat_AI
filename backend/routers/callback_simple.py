import xml.etree.ElementTree as ET
from fastapi import APIRouter, Request, Query
from fastapi.responses import PlainTextResponse

router = APIRouter(tags=["callback"])

@router.get("/callback")
async def verify_callback(
    msg_signature: str = Query(...),
    timestamp: str = Query(...),
    nonce: str = Query(...),
    echostr: str = Query(...)
):
    # 简单返回 echostr，用于验证 URL
    return PlainTextResponse(content=echostr)

@router.post("/callback")
async def handle_message(request: Request):
    body = await request.body()
    body_str = body.decode("utf-8", errors="replace")

    # 记录到文件
    with open("/tmp/callback_test.log", "a") as f:
        f.write(f"=== POST RECEIVED ===\n")
        f.write(f"Body: {body_str[:2000]}\n\n")

    # 直接返回 success，不做任何处理
    return PlainTextResponse(content="success")
