# 企业微信 AI 客服系统 — Web 应用建设计划

> 版本：v0.1 · 日期：2026-04-02  
> 基于现有 FastAPI 后端，扩展为完整 Web 应用

---

## 一、目标概述

将现有的企业微信后端服务升级为一个**可视化 Web 管理系统**，涵盖：

| 模块 | 核心功能 |
|------|---------|
| 主动关怀 | 群发消息、定时任务管理、消息模板 |
| 智能客服 | AI 辅助回答（员工端）+ 后续自动回复架构 |
| FAQ 管理 | 常见问题增删改查、分类管理 |
| 知识库 | 文档上传、内容管理、RAG 检索 |
| 大模型配置 | DeepSeek/其他模型接入、Prompt 管理 |
| 用户与权限 | 企业微信扫码登录、管理员/员工角色 |
| 客户管理 | 查看员工客户列表、客户详情 |

---

## 二、技术栈

### 前端
| 技术 | 选型 | 原因 |
|------|------|------|
| 框架 | React 18 + TypeScript | 生态成熟，UI 组件丰富 |
| 构建 | Vite | 快，HMR 好用 |
| 样式 | Tailwind CSS | 精细控制，审美友好 |
| 组件库 | shadcn/ui | 现代设计风格，可完全自定义 |
| 路由 | React Router v6 | 标准方案 |
| 数据请求 | TanStack Query (React Query) | 缓存、loading、错误处理一套搞定 |
| 状态管理 | Zustand | 轻量，够用 |
| 图标 | Lucide React | 与 shadcn/ui 配套 |

### 后端（现有基础扩展）
| 技术 | 选型 |
|------|------|
| 框架 | FastAPI（已有） |
| 鉴权 | 企业微信 OAuth2 扫码 + JWT |
| AI | DeepSeek API（OpenAI 兼容 SDK） |
| 知识库 | 文档解析 + 本地向量检索（先用 TF-IDF，后续接 embedding） |
| 存储 | JSON 文件（现阶段）→ 后续迁移 PostgreSQL |
| 进程管理 | systemd（已有） |

### 部署（Aneel 服务器）
```
Nginx（80/443）
  ├── / → React 静态文件（打包后放 /var/www/wecom_ai/）
  └── /api → FastAPI（localhost:8000）
```

---

## 三、目录结构规划

```
wechat_ai/
├── backend/                  # 现有代码迁入
│   ├── main.py
│   ├── config.py
│   ├── wecom/
│   ├── ai/                   # 新增：AI 模块
│   │   ├── deepseek_client.py
│   │   ├── rag.py            # 知识库检索
│   │   └── prompt_manager.py
│   ├── routers/              # 新增：按模块拆路由
│   │   ├── auth.py           # 登录鉴权
│   │   ├── customers.py      # 客户管理
│   │   ├── proactive.py      # 主动关怀
│   │   ├── faq.py            # FAQ
│   │   ├── knowledge.py      # 知识库
│   │   └── ai_config.py      # 模型配置
│   └── data/                 # JSON 数据文件
│       ├── users.json        # 用户与权限
│       ├── faq.json
│       ├── knowledge/        # 上传的文档
│       ├── ai_config.json    # 模型配置（不含密钥）
│       └── scheduled_tasks.json
├── frontend/                 # 新增：React 项目
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── store/
│   │   └── api/
│   ├── public/
│   └── package.json
├── .env                      # 密钥（gitignore）
├── .env.example              # 密钥模板（可提交）
└── .gitignore
```

---

## 四、页面规划

### 整体布局
- 左侧固定导航栏（收缩/展开）
- 顶部栏：用户信息、企业名称、退出登录
- 主内容区

### 各页面

#### 1. 登录页 `/login`
- 企业微信扫码登录（二维码展示）
- 首次登录自动创建管理员账号

#### 2. 仪表盘 `/dashboard`
- 今日发送消息数、客户总数、任务执行状态
- 最近群发任务记录

#### 3. 客户管理 `/customers`
- 按员工筛选客户列表
- 客户详情（头像、姓名、添加时间）
- 支持搜索

#### 4. 主动关怀 `/proactive`
- **立即群发**：选员工 → 选客户（全选/多选）→ 填写内容/选模板 → 发送
- **定时任务**：任务列表、新建/编辑/删除、下次执行时间
- **消息模板**：文本模板、链接卡片模板 CRUD

#### 5. 智能客服 `/ai-service`
- **问答助手**（现阶段）：输入客户问题 → AI 基于知识库 + FAQ 给出回答建议
- **对话记录**：历史问答列表
- **自动回复配置**（架构预留，接入会话存档后启用）：
  - 开关：启用/禁用自动回复
  - 触发规则配置
  - 白名单员工设置

#### 6. FAQ 管理 `/faq`
- 分类管理
- 问答对 CRUD
- 支持批量导入（CSV）
- 搜索测试：输入问题 → 预览 AI 会匹配到哪条 FAQ

#### 7. 知识库 `/knowledge`
- 文档上传（PDF、TXT、Word）
- 文档列表（名称、大小、上传时间、状态）
- 文档删除
- 知识库状态：总条目数、最后更新时间

#### 8. 大模型配置 `/ai-config`
- 当前模型：DeepSeek（下拉可切换）
- API Key 输入（前端只显示 `sk-****`，明文只走 HTTPS 到后端）
- 模型参数：temperature、max_tokens
- System Prompt 编辑
- 连通性测试按钮

#### 9. 用户管理 `/users`（管理员可见）
- 用户列表（企业微信账号、角色、状态）
- 设置/取消管理员
- 禁用账号

---

## 五、权限设计

| 角色 | 权限 |
|------|------|
| **超级管理员** | 全部功能 + 用户管理 + 模型配置 |
| **管理员** | 全部功能，不能管理其他管理员 |
| **员工** | 查看/操作自己的客户、使用 AI 问答助手 |

登录流程：
```
前端展示企业微信二维码
    ↓
用户扫码 → 企业微信回调 /api/auth/callback?code=xxx
    ↓
后端用 code 换取 userid（企业微信 OAuth2）
    ↓
查 users.json：新用户自动注册为员工，首个用户为超级管理员
    ↓
签发 JWT → 前端存 localStorage → 后续请求带 Authorization header
```

---

## 六、AI 模块设计

### DeepSeek 接入
```python
# 使用 OpenAI SDK（DeepSeek 兼容）
from openai import OpenAI
client = OpenAI(api_key=..., base_url="https://api.deepseek.com")
```

### RAG 检索流程（知识库问答）
```
用户问题
    ↓
关键词提取 + TF-IDF 匹配（本地，无需向量数据库）
    ↓
召回相关 FAQ 条目 + 知识库片段（Top 3）
    ↓
拼入 System Prompt → 调用 DeepSeek
    ↓
返回回答
```

> 后续升级：接入 embedding API，替换为语义检索

### 智能客服自动回复（预留架构）
```python
# routers/ai_service.py 中预留：
async def auto_reply_pipeline(external_userid, message_content):
    """
    会话存档接入后启用：
    1. 判断是否在自动回复白名单
    2. 调用 RAG 检索
    3. 调用 DeepSeek 生成回复
    4. 通过群发助手/客服API发送
    """
    pass  # TODO: 接入会话存档后实现
```

---

## 七、安全规范

- `.env` 加入 `.gitignore`，**永远不提交密钥**
- 提供 `.env.example` 作为模板
- API Key 仅在后端使用，前端不可见
- JWT 有效期 8 小时，支持刷新
- 所有 API 接口需携带有效 JWT（`/api/auth/*` 除外）
- Nginx 开启 HTTPS（Let's Encrypt）

---

## 八、实施阶段

### Phase 1 — 基础框架（约 3-4 天）
- [ ] 后端：拆分路由，统一 API 前缀 `/api/`
- [ ] 后端：企业微信扫码登录 + JWT 鉴权中间件
- [ ] 前端：React + Vite + Tailwind + shadcn/ui 初始化
- [ ] 前端：登录页 + 主布局框架（导航、路由）
- [ ] 部署：Nginx 配置反向代理

### Phase 2 — 核心业务模块（约 4-5 天）
- [ ] 客户管理页（对接现有 `/customers` API）
- [ ] 主动关怀页（立即群发 + 定时任务 + 消息模板）
- [ ] 用户管理页 + 权限控制

### Phase 3 — AI 功能（约 3-4 天）
- [ ] DeepSeek 接入 + 模型配置页
- [ ] FAQ 管理页（CRUD + 批量导入）
- [ ] 知识库上传 + 文档解析
- [ ] AI 问答助手页

### Phase 4 — 优化与预留（约 2 天）
- [ ] 仪表盘数据展示
- [ ] 自动回复架构预留（接口 + 配置 UI）
- [ ] .env 安全检查 + gitignore 完善
- [ ] 生产环境测试

---

## 九、待确认事项

> 开始开发前需最终确认：

1. **企业微信网页授权**：需要在企业微信后台「应用 → 企业微信授权登录」配置回调域名，确认域名是 `www.hairclub.com.cn` 还是 IP？
2. **DeepSeek API Key**：开始 Phase 3 时提供即可，不需要现在给
3. **数据迁移时机**：JSON → 数据库迁移放 Phase 4 之后单独做，还是 Phase 4 内做？

---

*本文档随开发推进持续更新*
