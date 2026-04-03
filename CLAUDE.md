# 项目工作流 - wechat_ai

## 核心原则：本地是唯一代码源

**服务器上永远不手动修改代码。所有修改在本地完成，再部署到服务器。**

---

## 服务器信息

- 服务器 IP: `root@47.103.221.229`
- 项目目录: `/root/wechat_ai`
- 运行端口: `8000`
- 启动命令: `cd /root/wechat_ai && source venv/bin/activate && PYTHONPATH=/root/wechat_ai nohup uvicorn backend.main:app --host 0.0.0.0 --port 8000 > /tmp/uvicorn.log 2>&1 & echo $! > /tmp/uvicorn.pid`

---

## 部署工作流

### 情况A：单文件修改（小改动）

```bash
scp <本地文件路径> root@47.103.221.229:<服务器对应路径>
```

示例：
```bash
scp backend/routers/callback.py root@47.103.221.229:/root/wechat_ai/backend/routers/callback.py
```

### 情况B：多文件修改（或不确定改了哪些文件）

**全量重新部署，避免本地和服务器代码不一致：**

```bash
# 1. 停止服务器进程
ssh root@47.103.221.229 "kill \$(cat /tmp/uvicorn.pid) 2>/dev/null; pkill -f 'uvicorn backend.main' 2>/dev/null; sleep 2"

# 2. 删除旧代码（保留 .env 和 venv）
ssh root@47.103.221.229 "cd /root/wechat_ai && find . -maxdepth 1 ! -name '.' ! -name '.env' ! -name 'venv' ! -name 'data' -exec rm -rf {} + 2>/dev/null; true"

# 3. 同步本地代码到服务器（排除本地开发文件）
rsync -avz --exclude='venv_dev' --exclude='__pycache__' --exclude='.env' --exclude='*.pyc' --exclude='.git' \
  /Users/yckonnnn/Desktop/Coding/github-project/wechat_ai/ root@47.103.221.229:/root/wechat_ai/

# 4. 安装依赖（如果 requirements.txt 有变化）
ssh root@47.103.221.229 "cd /root/wechat_ai && source venv/bin/activate && pip install -r requirements.txt -q"

# 5. 重启服务
ssh root@47.103.221.229 "cd /root/wechat_ai && source venv/bin/activate && PYTHONPATH=/root/wechat_ai nohup uvicorn backend.main:app --host 0.0.0.0 --port 8000 > /tmp/uvicorn.log 2>&1 & echo \$! > /tmp/uvicorn.pid && sleep 2 && tail -20 /tmp/uvicorn.log"
```

### 情况C：初次部署 / 彻底清空重建

```bash
# 停止并完全清空
ssh root@47.103.221.229 "pkill -f uvicorn 2>/dev/null; rm -rf /root/wechat_ai; mkdir /root/wechat_ai"

# 同步代码
rsync -avz --exclude='venv_dev' --exclude='__pycache__' --exclude='.env' --exclude='*.pyc' --exclude='.git' \
  /Users/yckonnnn/Desktop/Coding/github-project/wechat_ai/ root@47.103.221.229:/root/wechat_ai/

# 建 venv + 装依赖
ssh root@47.103.221.229 "cd /root/wechat_ai && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"

# 上传 .env（含真实密钥，不进 git）
scp /Users/yckonnnn/Desktop/Coding/github-project/wechat_ai/.env root@47.103.221.229:/root/wechat_ai/.env

# 启动
ssh root@47.103.221.229 "cd /root/wechat_ai && source venv/bin/activate && PYTHONPATH=/root/wechat_ai nohup uvicorn backend.main:app --host 0.0.0.0 --port 8000 > /tmp/uvicorn.log 2>&1 & echo \$! > /tmp/uvicorn.pid && sleep 3 && tail -20 /tmp/uvicorn.log"
```

---

## 日常运维命令

```bash
# 查看日志（实时）
ssh root@47.103.221.229 "tail -f /tmp/uvicorn.log"

# 查看最新日志（50行）
ssh root@47.103.221.229 "tail -50 /tmp/uvicorn.log"

# 重启服务
ssh root@47.103.221.229 "kill \$(cat /tmp/uvicorn.pid) 2>/dev/null; sleep 1; cd /root/wechat_ai && source venv/bin/activate && PYTHONPATH=/root/wechat_ai nohup uvicorn backend.main:app --host 0.0.0.0 --port 8000 > /tmp/uvicorn.log 2>&1 & echo \$! > /tmp/uvicorn.pid"

# 健康检查
curl http://47.103.221.229:8000/health
```

---

## 业务功能说明

### 场景1：员工给自建应用发消息 → AI 回复员工

- 企业微信后台：自建应用「xxx」→ 接收消息 → 回调 URL = `http://47.103.221.229:8000/callback`
- 流程：员工发消息 → callback 触发 → DeepSeek 生成回复 → `send_text_message` 发回员工
- 判断依据：消息中无 `owner_userid`（非外部联系人）

### 场景2：客户给员工私聊 → AI 代员工回复客户

- 企业微信后台：外部联系人 → 聊天内容回调 → 回调 URL = `http://47.103.221.229:8000/callback`
- 流程：客户发消息给员工 → callback 触发 → 从 customer_cache 找归属员工 → DeepSeek 生成回复 → `send_external_text_message` 代员工发回客户
- 判断依据：消息中有 `UserID` 或 customer_cache 能查到归属员工

### 大模型配置

- 使用 DeepSeek API（兼容 OpenAI 格式）
- base_url: `https://api.deepseek.com/v1`
- model: `deepseek-chat`
- API Key 在 `.env` 中配置（不进 git）

---

## .env 模板（真实密钥在服务器上，不提交 git）

```
wecom_corp_id=ww3a42a0c7158120be
wecom_agent_id=1000023
wecom_secret=<secret>
wecom_token=<token>
wecom_encoding_aes_key=<key>
host=0.0.0.0
port=8000
llm_mock_mode=false
llm_api_key=<deepseek_api_key>
llm_base_url=https://api.deepseek.com/v1
llm_model=deepseek-chat
llm_system_prompt=你是一位专业的企业微信客服助手，帮助员工回复客户消息。语气亲切、专业，尽量简洁明了。
llm_max_context=10
auto_reply_default_userid=zackwang
```
