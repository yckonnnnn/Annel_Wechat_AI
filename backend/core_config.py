import os
from pathlib import Path
from typing import Optional

# 获取 .env 文件路径
BASE_DIR = Path(__file__).parent
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


# 全局配置对象
wecom_config = get_wecom_config()
app_config = get_app_config()
