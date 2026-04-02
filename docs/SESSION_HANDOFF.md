# 会话交接文档

> 生成时间：2026-04-02  
> 用途：下次新会话直接加载，无需重新回顾历史

---

## 项目简介

企业微信 AI 客服管理系统。后端 FastAPI + JWT，前端 React 18 + Vite + Tailwind CSS v4。
已部署在 Aneel 服务器，域名 `https://www.hairclub.com.cn`，SSL 已配置。

---

## 当前线上状态（已验证可用）

| 层 | 状态 |
|---|---|
| HTTPS + Nginx | ✅ 运行中，`/api/` 代理后端，`/` 静态前端 |
| FastAPI 后端 | ✅ 运行中（pid 文件：`/root/wechat_ai_new/uvicorn.pid`） |
| 前端页面 | ✅ `https://www.hairclub.com.cn` 正常加载 |
| 企微 OAuth 登录 | ✅ 流程完整，回调地址 `https://www.hairclub.com.cn/auth/callback` |

---

## 服务器关键路径

| 路径 | 说明 |
|---|---|
| `/root/wechat_ai_new/` | 当前运行的代码目录 |
| `/root/wechat_ai_new/.env` | 所有配置（wecom 密钥 + JWT_SECRET） |
| `/root/wechat_ai_new/data/` | 数据目录（conversations/, scheduled_tasks.json） |
| `/root/wechat_ai_new/uvicorn.log` | 后端运行日志 |
| `/root/wechat_ai_new/uvicorn.pid` | 后端进程 PID |
| `/var/www/wechat_ai/` | 前端静态文件（nginx 从这里 serve） |
| `/etc/nginx/conf.d/wechat-ai.conf` | Nginx 配置 |
| `/root/wechat_ai/venv/` | Python venv（Python 3.8） |

### 重启后端命令
```bash
kill $(cat /root/wechat_ai_new/uvicorn.pid)
cd /root/wechat_ai_new
PYTHONPATH=/root/wechat_ai_new nohup /root/wechat_ai/venv/bin/uvicorn backend.main:app \
  --host 0.0.0.0 --port 8000 > uvicorn.log 2>&1 &
echo $! > uvicorn.pid
```

---

## 本地开发目录

`/Users/yckonnnn/Desktop/Coding/github-project/wechat_ai/`

### 本地启动
```bash
# 后端
source venv_dev/bin/activate && PYTHONPATH=. python backend/main.py

# 前端
cd frontend && npm run dev   # http://localhost:5173
```

### 部署流程（每次更新后）
```bash
# 1. 本地构建前端
cd frontend && npm run build

# 2. 强制 add dist（gitignore 排除了）
git add -f frontend/dist/
git add backend/ frontend/src/ ...
git commit -m "version..."
git push origin main

# 3. 服务器拉代码
# (通过 MCP Aneel 执行)
cd /root/wechat_ai_new && git pull origin main

# 4. 同步前端静态文件
cp -r /root/wechat_ai_new/frontend/dist/* /var/www/wechat_ai/

# 5. 重启后端（如有 Python 文件变动）
kill $(cat uvicorn.pid) && [重启命令]
```

---

## 代码结构

```
wechat_ai/
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── auth.py              # JWT + 企微 OAuth，用户存 data/users.json
│   ├── core_config.py       # 读项目根目录 .env
│   └── routers/
│       ├── auth.py          # /api/auth/wecom-login-url, /callback, /me
│       ├── callback.py      # /callback 企微消息回调
│       ├── customers.py     # /api/customers (list/detail/messages)
│       ├── proactive.py     # /api/proactive (立即发送 + 定时任务)
│       ├── system.py        # /api/system/health
│       └── users.py         # /api/users (角色/状态管理)
├── wecom/                   # 企微 SDK（被 backend/ 代码引用）
│   ├── token_manager.py
│   ├── conversation_store.py
│   ├── message_sender.py
│   ├── user_service.py
│   ├── scheduler.py         # APScheduler 定时任务
│   └── crypto.py
├── frontend/
│   ├── dist/                # 构建产物（已提交 git，服务器直接用）
│   └── src/
│       ├── lib/auth.ts      # token 存取
│       ├── lib/api.ts       # GET/POST/DELETE 封装，401 跳登录
│       ├── contexts/AuthContext.tsx
│       ├── components/Layout.tsx      # 深色侧边栏
│       ├── components/PrivateRoute.tsx
│       └── pages/
│           ├── LoginPage.tsx          # 渐变背景 + 毛玻璃卡片
│           ├── AuthCallbackPage.tsx   # OAuth code → JWT → 跳转
│           ├── DashboardPage.tsx      # 彩色统计卡片
│           ├── CustomersPage.tsx      # 客户列表 + 搜索
│           ├── CustomerDetailPage.tsx # 对话气泡
│           └── ProactivePage.tsx      # 立即发送 + 定时任务
└── data/
    ├── conversations/       # 每个客户一个 JSON 文件
    └── scheduled_tasks.json
```

---

## 已知的 import 规则（重要）

- `backend/` 下的文件用 `backend.xxx` 互相引用
- **wecom SDK 统一用根包** `from wecom.xxx import ...`（不是 `backend.wecom`）
- `backend/auth.py` 的 USERS_FILE 路径是 `../data/users.json`（相对 backend/）
- `backend/core_config.py` 的 `.env` 路径是 `parent.parent`（项目根目录）

---

## 未完成的功能

| 页面/功能 | 状态 | 说明 |
|---|---|---|
| `/faq` | ❌ 未建 | 导航有入口但无页面 |
| `/settings` | ❌ 未建 | 导航有入口但无页面（后端 users.py 已有接口） |
| Dashboard 真实统计 | ⚠️ 部分 | 客户数/消息数已接真实数据，其他指标待扩展 |
| 企微 OAuth 端到端测试 | ⏳ 待验证 | 代码完整，需用真实账号在域名上测试 |

---

## 企微配置信息（勿泄露）

- corp_id: `ww3a42a0c7158120be`
- agent_id: `1000023`
- 回调域名: `www.hairclub.com.cn`
- OAuth 回调地址（需在企微后台配置）: `https://www.hairclub.com.cn/auth/callback`
