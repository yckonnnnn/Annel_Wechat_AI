# 企业微信客服系统 - AI 自动回复

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 启动服务
```bash
python main.py
```

### 3. 启动 ngrok（新终端）
```bash
ngrok http 8000
```

### 4. 配置企业微信回调 URL

1. 登录企业微信管理后台：https://work.weixin.qq.com
2. 进入「应用管理」→「AI 回复助手」
3. 找到「接收消息」配置
4. 填写：
   - **URL**: `https://<你的 ngrok 地址>/callback`
   - **Token**: 自定义一个字符串（如 `mywecomtoken2026`）
   - **EncodingAESKey**: 点击随机生成
5. 保存后，将 Token 和 EncodingAESKey 填入 `.env` 文件
6. 重启服务

### 5. 测试

用手机企业微信向「AI 回复助手」发送消息，应该收到 AI 回复。

## 项目结构

```
wechat_ai/
├── main.py              # FastAPI 主应用（回调处理）
├── config.py            # 配置管理
├── requirements.txt     # Python 依赖
├── .env                 # 环境变量配置
├── wecom/               # 企业微信 SDK 模块
│   ├── __init__.py
│   ├── token_manager.py   # access_token 管理
│   ├── crypto.py          # 消息加解密
│   ├── user_service.py    # 用户信息获取
│   └── message_sender.py  # 消息发送
└── docs/
    └── plans/           # 实现计划文档
```

## 环境变量

| 变量名 | 说明 | 来源 |
|--------|------|------|
| `wecom_corp_id` | 企业 ID | 企业微信后台 - 我的企业 |
| `wecom_agent_id` | 应用 ID | 企业微信后台 - 应用管理 |
| `wecom_secret` | 应用密钥 | 企业微信后台 - 应用管理 |
| `wecom_token` | 回调 Token | 企业微信后台 - 回调配置 |
| `wecom_encoding_aes_key` | 回调加密密钥 | 企业微信后台 - 回调配置 |

## 下一步

- [ ] 集成大模型 API
- [ ] 对接企业内部知识库
- [ ] 部署到阿里云服务器
