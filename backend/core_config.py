import os
from pathlib import Path
from typing import Optional

# 获取 .env 文件路径
BASE_DIR = Path(__file__).parent.parent   # 项目根目录
ENV_FILE = BASE_DIR / ".env"

# 从 .env 文件读取环境变量
if ENV_FILE.exists():
    from dotenv import load_dotenv
    load_dotenv(ENV_FILE)


def get_wecom_config():
    """获取企业微信配置"""
    return {
        "corp_id": os.environ.get("wecom_corp_id", ""),
        "agent_id": os.environ.get("wecom_agent_id", ""),
        "secret": os.environ.get("wecom_secret", ""),
        "token": os.environ.get("wecom_token", ""),
        "encoding_aes_key": os.environ.get("wecom_encoding_aes_key", ""),
    }


def get_app_config():
    """获取应用配置"""
    return {
        "host": os.environ.get("host", "0.0.0.0"),
        "port": int(os.environ.get("port", "8000")),
        "ngrok_url": os.environ.get("ngrok_url", None),
    }


def get_llm_config():
    """获取大模型配置"""
    return {
        "api_key": os.environ.get("llm_api_key", ""),
        "base_url": os.environ.get("llm_base_url", "https://api.anthropic.com/v1"),
        "model": os.environ.get("llm_model", "claude-sonnet-4-6"),
        "system_prompt": os.environ.get(
            "llm_system_prompt",
            "你是一位专业的企业微信客服助手，帮助员工回复客户消息。语气亲切、专业，尽量简洁明了。",
        ),
        "max_context": int(os.environ.get("llm_max_context", "10")),
        "mock_mode": os.environ.get("llm_mock_mode", "true").lower() in ("true", "1", "yes", "on"),
        "mock_reply": os.environ.get("llm_mock_reply", "收到您的消息，测试发送。"),
        "default_userid": os.environ.get("auto_reply_default_userid", ""),
    }


# 全局配置对象
wecom_config = get_wecom_config()
app_config = get_app_config()
llm_config = get_llm_config()
