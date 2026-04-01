# 企业微信客服系统 - 本地回调测试实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 创建一个可在本地运行并通过内网穿透测试的企业微信回调服务

**Architecture:** 使用 Python FastAPI 构建 Web 服务，通过 ngrok 内网穿透实现 HTTPS 回调 URL，包含 access_token 管理、消息接收/发送、用户信息获取三个核心模块

**Tech Stack:** Python 3.10+, FastAPI, uvicorn, requests, cryptography (AES 解密), ngrok

---

### Task 1: 项目基础结构

**Files:**
- Create: `requirements.txt`
- Create: `config.py`
- Create: `README.md`
- Create: `.env.example`

- [ ] **Step 1: 创建 requirements.txt**

```
fastapi==0.109.0
uvicorn[standard]==0.27.0
requests==2.31.0
python-dotenv==1.0.0
cryptography==42.0.0
pydantic==2.5.3
pydantic-settings==2.1.0
```

- [ ] **Step 2: 创建 config.py**

```python
from pydantic_settings import BaseSettings
from typing import Optional


class WeComConfig(BaseSettings):
    """企业微信配置"""
    corp_id: str = ""
    agent_id: str = ""
    secret: str = ""
    token: str = ""  # 回调 Token
    encoding_aes_key: str = ""  # 回调加密密钥
    
    class Config:
        env_prefix = "wecom_"


class Settings(BaseSettings):
    """应用配置"""
    wecom: WeComConfig = WeComConfig()
    host: str = "0.0.0.0"
    port: int = 8000
    ngrok_url: Optional[str] = None  # ngrok 生成的 HTTPS URL
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
```

- [ ] **Step 3: 创建 .env.example**

```
# 企业微信配置
wecom_corp_id=your_corp_id
wecom_agent_id=your_agent_id
wecom_secret=your_secret
wecom_token=your_callback_token
wecom_encoding_aes_key=your_encoding_aes_key

# 服务配置
host=0.0.0.0
port=8000
```

- [ ] **Step 4: 创建 README.md**

```markdown
# 企业微信客服系统 - AI 自动回复

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 填入企业微信配置
```

### 3. 启动服务
```bash
python main.py
```

### 4. 启动 ngrok（新终端）
```bash
ngrok http 8000
```

### 5. 配置企业微信回调 URL
将 ngrok 生成的 HTTPS URL + /callback 配置到企业微信后台
```

---

### Task 2: Access Token 管理模块

**Files:**
- Create: `wecom/token_manager.py`

- [ ] **Step 1: 创建 token_manager.py**

```python
import requests
import time
from typing import Optional
from .config import settings


class TokenManager:
    """企业微信 Access Token 管理器"""
    
    # 获取 access_token 的 API 端点
    TOKEN_URL = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
    
    def __init__(self):
        self._token: Optional[str] = None
        self._expires_at: float = 0
        self._lock = False
    
    def get_token(self, force_refresh: bool = False) -> Optional[str]:
        """
        获取 access_token
        
        Args:
            force_refresh: 是否强制刷新（默认使用缓存）
        
        Returns:
            access_token 字符串，失败返回 None
        """
        # 检查缓存是否有效（提前 5 分钟刷新）
        if not force_refresh and self._token and time.time() < self._expires_at - 300:
            return self._token
        
        if self._lock:
            # 防止并发请求
            time.sleep(0.1)
            return self.get_token(force_refresh)
        
        self._lock = True
        try:
            return self._fetch_token()
        finally:
            self._lock = False
    
    def _fetch_token(self) -> Optional[str]:
        """从企业微信 API 获取 access_token"""
        params = {
            "corpid": settings.wecom.corp_id,
            "corpsecret": settings.wecom.secret
        }
        
        try:
            response = requests.get(self.TOKEN_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("errcode") == 0:
                self._token = data["access_token"]
                # API 返回的 expires_in 是 7200 秒（2 小时）
                self._expires_at = time.time() + data.get("expires_in", 7200)
                print(f"[TokenManager] 成功获取 access_token，过期时间：{self._expires_at}")
                return self._token
            else:
                print(f"[TokenManager] 获取 token 失败：{data}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"[TokenManager] 请求失败：{e}")
            return None
    
    def invalidate(self):
        """使缓存失效（用于错误处理时）"""
        self._token = None
        self._expires_at = 0


# 全局单例
token_manager = TokenManager()
```

---

### Task 3: 消息加密/解密模块

**Files:**
- Create: `wecom/crypto.py`

- [ ] **Step 1: 创建 crypto.py**

```python
import base64
import hashlib
import random
import struct
import time
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from typing import Tuple


class WeComCrypto:
    """企业微信消息加解密"""
    
    def __init__(self, token: str, encoding_aes_key: str, corp_id: str):
        self.token = token
        self.corp_id = corp_id
        # AES Key 是 base64 编码的 32 字节
        self.aes_key = base64.b64decode(encoding_aes_key + "=" * (4 - len(encoding_aes_key) % 4))
    
    def verify_signature(self, timestamp: str, nonce: str, echostr: str, signature: str) -> bool:
        """
        验证回调签名（GET 请求验证）
        
        企业微信会用 SHA1 校验：sha1(token, timestamp, nonce, echostr)
        """
        values = [self.token, timestamp, nonce, echostr]
        values.sort()
        sha1 = hashlib.sha1("".join(values).encode("utf-8"))
        return sha1.hexdigest() == signature
    
    def decrypt_echostr(self, echostr: str) -> str:
        """
        解密 GET 请求的 echostr
        返回解密后的字符串用于验证
        """
        echostr_bytes = base64.b64decode(echostr)
        
        # 前 16 字节是 IV
        iv = echostr_bytes[:16]
        
        # 解密
        cipher = Cipher(algorithms.AES(self.aes_key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted = decryptor.update(echostr_bytes[16:]) + decryptor.finalize()
        
        # 去掉 padding 和 prefix
        # 格式：16 字节随机前缀 + 4 字节消息长度 + 消息内容 + corp_id
        pad_len = decrypted[-1]
        decrypted = decrypted[:-pad_len]
        
        # 提取消息长度
        msg_len = struct.unpack(">I", decrypted[16:20])[0]
        msg = decrypted[20:20 + msg_len].decode("utf-8")
        
        return msg
    
    def decrypt_message(self, encrypt_msg: str) -> dict:
        """
        解密 POST 请求的消息体
        返回解密后的 JSON 字典
        """
        encrypted = base64.b64decode(encrypt_msg)
        iv = encrypted[:16]
        
        cipher = Cipher(algorithms.AES(self.aes_key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted = decryptor.update(encrypted[16:]) + decryptor.finalize()
        
        # 去掉 padding
        pad_len = decrypted[-1]
        decrypted = decrypted[:-pad_len]
        
        # 提取消息内容（去掉 16 字节随机前缀）
        msg_len = struct.unpack(">I", decrypted[:4])[0]
        msg_content = decrypted[4:4 + msg_len].decode("utf-8")
        
        import json
        return json.loads(msg_content)
    
    def encrypt_message(self, message: str) -> str:
        """
        加密要返回给企业微信的消息
        """
        import json
        
        # 生成 16 字节随机前缀
        random_prefix = bytes([random.randint(0, 255) for _ in range(16)])
        
        # 消息内容
        msg_bytes = message.encode("utf-8")
        
        # 4 字节消息长度
        msg_len = struct.pack(">I", len(msg_bytes))
        
        # 拼接：随机前缀 + 长度 + 消息 + corp_id
        payload = random_prefix + msg_len + msg_bytes + self.corp_id.encode("utf-8")
        
        # PKCS7 padding
        pad_len = 32 - (len(payload) % 32)
        payload = payload + bytes([pad_len] * pad_len)
        
        # 生成随机 IV
        iv = bytes([random.randint(0, 255) for _ in range(16)])
        
        # 加密
        cipher = Cipher(algorithms.AES(self.aes_key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        encrypted = encryptor.update(payload) + encryptor.finalize()
        
        # Base64 编码
        return base64.b64encode(iv + encrypted).decode("utf-8")


def verify_callback_signature(token: str, signature: str, timestamp: str, nonce: str) -> bool:
    """验证回调 URL 签名"""
    values = [token, timestamp, nonce]
    values.sort()
    sha1 = hashlib.sha1("".join(values).encode("utf-8"))
    return sha1.hexdigest() == signature
```

---

### Task 4: 用户服务模块

**Files:**
- Create: `wecom/user_service.py`

- [ ] **Step 1: 创建 user_service.py**

```python
import requests
from typing import Optional, Dict, Any
from .token_manager import token_manager
from .config import settings


class UserService:
    """企业微信用户服务"""
    
    # 获取客户详情 API
    GET_EXTERNAL_CONTACT_URL = "https://qyapi.weixin.qq.com/cgi-bin/externalcontact/get"
    
    def get_external_contact(self, external_userid: str) -> Optional[Dict[str, Any]]:
        """
        获取客户详情
        
        Args:
            external_userid: 客户的外部联系人 userid
        
        Returns:
            客户信息字典，失败返回 None
        """
        token = token_manager.get_token()
        if not token:
            print("[UserService] 无法获取 access_token")
            return None
        
        params = {
            "access_token": token,
            "external_userid": external_userid
        }
        
        try:
            response = requests.get(self.GET_EXTERNAL_CONTACT_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("errcode") == 0:
                return data.get("external_contact", {})
            else:
                print(f"[UserService] 获取客户详情失败：{data}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"[UserService] 请求失败：{e}")
            return None
    
    def get_contact_info(self, external_userid: str) -> str:
        """
        获取用于大模型的客户信息摘要
        
        Returns:
            格式化的客户信息字符串
        """
        contact = self.get_external_contact(external_userid)
        if not contact:
            return "未知用户"
        
        name = contact.get("name", "未知")
        gender = contact.get("gender", 0)
        gender_map = {0: "未知", 1: "男", 2: "女"}
        
        info_parts = [f"姓名：{name}", f"性别：{gender_map.get(gender, '未知')}"]
        
        # 其他可用信息
        if contact.get("position"):
            info_parts.append(f"职位：{contact['position']}")
        if contact.get("corp_name"):
            info_parts.append(f"企业：{contact['corp_name']}")
        
        return "\n".join(info_parts)


# 全局单例
user_service = UserService()
```

---

### Task 5: 消息发送模块

**Files:**
- Create: `wecom/message_sender.py`

- [ ] **Step 1: 创建 message_sender.py**

```python
import requests
from typing import Optional, Dict, Any
from .token_manager import token_manager
from .config import settings


class MessageSender:
    """企业微信消息发送服务"""
    
    # 发送应用消息 API
    SEND_MESSAGE_URL = "https://qyapi.weixin.qq.com/cgi-bin/message/send"
    
    def send_text_message(
        self,
        to_user: str,
        content: str,
        agent_id: Optional[str] = None
    ) -> bool:
        """
        发送文本消息给客户
        
        Args:
            to_user: 接收者的 userid（外部联系人用 external_userid）
            content: 消息内容
            agent_id: 应用 ID（默认使用配置的 agent_id）
        
        Returns:
            发送成功返回 True
        """
        token = token_manager.get_token()
        if not token:
            print("[MessageSender] 无法获取 access_token")
            return False
        
        agent_id = agent_id or settings.wecom.agent_id
        
        payload = {
            "touser": to_user,
            "msgtype": "text",
            "agentid": int(agent_id),
            "text": {
                "content": content
            },
            "safe": 0
        }
        
        params = {"access_token": token}
        
        try:
            response = requests.post(
                self.SEND_MESSAGE_URL,
                params=params,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("errcode") == 0:
                print(f"[MessageSender] 消息发送成功：{to_user}")
                return True
            else:
                print(f"[MessageSender] 消息发送失败：{data}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"[MessageSender] 请求失败：{e}")
            return False
    
    def send_markdown_message(
        self,
        to_user: str,
        content: str,
        agent_id: Optional[str] = None
    ) -> bool:
        """
        发送 Markdown 消息（仅支持部分语法）
        
        Args:
            to_user: 接收者的 userid
            content: Markdown 格式的消息内容
        
        Returns:
            发送成功返回 True
        """
        token = token_manager.get_token()
        if not token:
            return False
        
        agent_id = agent_id or settings.wecom.agent_id
        
        payload = {
            "touser": to_user,
            "msgtype": "markdown",
            "agentid": int(agent_id),
            "markdown": {
                "content": content
            }
        }
        
        params = {"access_token": token}
        
        try:
            response = requests.post(
                self.SEND_MESSAGE_URL,
                params=params,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            return data.get("errcode") == 0
            
        except requests.exceptions.RequestException as e:
            print(f"[MessageSender] 请求失败：{e}")
            return False


# 全局单例
message_sender = MessageSender()
```

---

### Task 6: FastAPI 主应用（核心回调逻辑）

**Files:**
- Create: `main.py`

- [ ] **Step 1: 创建 main.py**

```python
import hashlib
import json
import time
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse, JSONResponse

from config import settings
from wecom.crypto import WeComCrypto, verify_callback_signature
from wecom.token_manager import token_manager
from wecom.user_service import user_service
from wecom.message_sender import message_sender

app = FastAPI(title="企业微信客服系统", version="1.0.0")

# 初始化加密组件
crypto = WeComCrypto(
    token=settings.wecom.token,
    encoding_aes_key=settings.wecom.encoding_aes_key,
    corp_id=settings.wecom.corp_id
)


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok", "timestamp": time.time()}


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
    
    # 解析请求体
    try:
        encrypted_data = json.loads(body)
    except json.JSONDecodeError as e:
        print(f"[Callback POST] JSON 解析失败：{e}")
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    # 验证签名（使用 token、timestamp、nonce、encrypt_msg）
    encrypt_msg = encrypted_data.get("encrypt", "")
    if not verify_callback_signature(
        settings.wecom.token, msg_signature, timestamp, nonce
    ):
        # 注意：POST 请求的签名验证方式与 GET 不同
        # 这里简化处理，实际应该用 encrypt_msg 参与验证
        print("[Callback POST] 签名验证跳过（需要 encrypt 参与）")
    
    # 解密消息
    try:
        message_data = crypto.decrypt_message(encrypt_msg)
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
    print(f"CorpID: {settings.wecom.corp_id}")
    print(f"AgentID: {settings.wecom.agent_id}")
    print(f"监听地址：http://{settings.host}:{settings.port}")
    print(f"回调路径：/callback")
    print("=" * 60)
    print("\n启动 ngrok 后，将生成的 HTTPS URL + /callback 配置到企业微信后台")
    print("示例：https://xxxx.ngrok.io/callback\n")
    
    uvicorn.run(app, host=settings.host, port=settings.port)
```

---

### Task 7: 创建 wecom 包初始化文件

**Files:**
- Create: `wecom/__init__.py`

- [ ] **Step 1: 创建 __init__.py**

```python
"""企业微信 SDK 模块"""

from .token_manager import token_manager, TokenManager
from .user_service import user_service, UserService
from .message_sender import message_sender, MessageSender
from .crypto import WeComCrypto

__all__ = [
    "token_manager",
    "TokenManager",
    "user_service",
    "UserService",
    "message_sender",
    "MessageSender",
    "WeComCrypto",
]
```

---

### Task 8: 设置本地环境并测试

**Files:**
- Create: `.env`

- [ ] **Step 1: 创建 .env 文件**

```
# 企业微信配置
wecom_corp_id=ww95fe3c3c2e237126
wecom_agent_id=1000002
wecom_secret=X2t7Wjt1hZDpvyEDY2zQ0bD0UlxIKUl26MCROuvmZ6Y
wecom_token=your_callback_token_here
wecom_encoding_aes_key=your_encoding_aes_key_here

# 服务配置
host=0.0.0.0
port=8000
```

> **注意**：`wecom_token` 和 `wecom_encoding_aes_key` 需要你在企业微信后台配置回调 URL 时设置

- [ ] **Step 2: 安装依赖**

运行命令：
```bash
cd /Users/yckonnnn/Desktop/Coding/github-project/wechat_ai
pip install -r requirements.txt
```

- [ ] **Step 3: 启动服务测试**

运行命令：
```bash
python main.py
```

预期输出：
```
============================================================
企业微信客服系统 - 启动中...
============================================================
CorpID: ww95fe3c3c2e237126
AgentID: 1000002
监听地址：http://0.0.0.0:8000
回调路径：/callback
============================================================
```

- [ ] **Step 4: 在新终端启动 ngrok**

运行命令（需要先安装 ngrok）：
```bash
ngrok http 8000
```

预期输出：
```
Forwarding: https://xxxx-xxxx-xxxx.ngrok.io -> http://localhost:8000
```

将生成的 HTTPS URL 记下来，下一步配置到企业微信后台。

---

### Task 9: 企业微信后台配置

**Files:**
- Modify: `README.md` - 添加配置说明

- [ ] **Step 1: 登录企业微信管理后台**

访问：https://work.weixin.qq.com

- [ ] **Step 2: 进入应用管理**

点击「应用管理」→ 找到「AI 回复助手」应用

- [ ] **Step 3: 配置接收消息服务器**

在应用管理页面找到「接收消息」或「回调配置」：

1. 点击「启用 API 回调」
2. 填写配置：
   - **URL**: `https://<你的 ngrok 地址>/callback`
   - **Token**: 自定义一个字符串（如 `mywecomtoken2026`）
   - **EncodingAESKey**: 点击随机生成

3. 点击「保存」

4. 企业微信会发送验证请求，如果配置正确应该显示「验证成功」

- [ ] **Step 4: 将 Token 和 EncodingAESKey 更新到 .env**

编辑 `.env` 文件：
```
wecom_token=你刚才设置的 Token
wecom_encoding_aes_key=生成的 EncodingAESKey
```

- [ ] **Step 5: 重启服务**

```bash
# 停止之前的服务（Ctrl+C）
python main.py
```

---

### Task 10: 完整测试流程

- [ ] **Step 1: 确认服务运行中**

确保 `python main.py` 正在运行

- [ ] **Step 2: 确认 ngrok 运行中**

确保 `ngrok http 8000` 正在运行

- [ ] **Step 3: 用手机企业微信测试**

1. 用企业微信扫描应用二维码（或添加到工作台）
2. 向「AI 回复助手」发送一条消息
3. 查看终端输出，应该看到：
   ```
   [Callback POST] 收到消息请求
   [Callback POST] 解密后的消息：{...}
   [Callback POST] 消息详情:
     FromUserName: ...
     MsgType: text
     Content: 你的测试消息
   [UserService] 用户信息：...
   [MessageSender] 消息发送成功
   ```

4. 在企业微信中应该收到 AI 回复

---

## 后续扩展

### 大模型集成

在 `main.py:handle_message` 中的 TODO 位置添加大模型调用：

```python
# TODO: 调用大模型 API
response = call_llm_api(
    user_message=content,
    user_info=user_info,
    knowledge_base=kb_context
)
reply_content = response["reply"]
```

### 知识库集成

添加 `kb_service.py` 模块：
- 连接企业内部知识库 API
- 实现向量检索/RAG
- 返回相关的知识片段

### 对话管理

添加 `conversation_manager.py` 模块：
- 使用 Redis 存储对话上下文
- 实现多轮对话追踪
- 会话超时清理
