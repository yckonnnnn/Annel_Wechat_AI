# 项目进度记录

> 更新时间：2026-04-02

---

## 已完成

### 后端（全部本地验证可启动）

| 文件 | 说明 |
|------|------|
| `backend/main.py` | FastAPI 入口，`/api/` 前缀 |
| `backend/auth.py` | JWT 鉴权 + 企微 OAuth2 |
| `backend/routers/auth.py` | `/wecom-login-url` / `/callback` / `/me`（已修复） |
| `backend/routers/callback.py` | 企微消息回调（已修复 import） |
| `backend/routers/customers.py` | 客户列表 + 详情 + 消息（已重构） |
| `backend/routers/proactive.py` | 立即发送 + 定时任务 CRUD（已改 Pydantic body） |
| `backend/routers/system.py` | 健康检查 |
| `backend/routers/users.py` | 用户管理 |

### 前端（`npm run build` 通过，无 TS 错误）

| 路径 | 组件 | 功能 |
|------|------|------|
| `/login` | `LoginPage` | 企微扫码入口，自动跳过已登录 |
| `/auth/callback` | `AuthCallbackPage` | code → JWT → localStorage → 跳转 |
| `/dashboard` | `DashboardPage` | 占位统计卡片 |
| `/customers` | `CustomersPage` | 客户列表，实时搜索，按最近活跃排序 |
| `/customers/:id` | `CustomerDetailPage` | 资料 + 完整对话气泡（双色，含图片/事件） |
| `/proactive` | `ProactivePage` | 两 Tab：立即发送 / 定时任务（列表+新建+删除） |

**工具层：**
- `src/lib/auth.ts` — token 存取 / `fetchCurrentUser`
- `src/lib/api.ts` — 统一 GET/POST/DELETE，401 自动跳登录
- `src/contexts/AuthContext.tsx` — 全局 auth 状态
- `src/components/PrivateRoute.tsx` — 路由守卫
- `src/components/Layout.tsx` — 侧边导航 + 用户信息

---

## 未开始

### Phase 1 — Nginx 反向代理部署
- `/` → 前端 dist，`/api` → FastAPI 8000

### Phase 3 — FAQ / 知识库页面（`/faq`）
- 检查是否有后端接口
- 前端：FAQ 条目管理（增删改查）

### Phase 3 — 用户管理页面（`/settings` 或 `/users`）
- 后端 `routers/users.py` 已有接口，前端还未建

### Phase 4 — AI 模型配置
- DeepSeek API Key 管理

---

## 技术决策

1. 前端：React 18 + TypeScript + Vite + Tailwind CSS v4
2. 域名：`www.hairclub.com.cn`
3. 数据库：JSON 文件（后续迁移）
4. AI：DeepSeek API（OpenAI SDK 兼容）
5. 部署：Aneel 服务器

---

## 下次进来需要做的第一件事

**读 `backend/routers/users.py`**，然后决定：
1. 直接建用户管理页面 (`/settings/users`)
2. 还是先部署到服务器验证完整登录流程

**启动命令：**
```bash
# 后端
cd /Users/yckonnnn/Desktop/Coding/github-project/wechat_ai
source venv_dev/bin/activate && PYTHONPATH=. python backend/main.py

# 前端
cd frontend && npm run dev
```
