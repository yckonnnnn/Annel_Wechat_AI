from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.core_config import app_config
from backend.routers import auth, customers, proactive, callback, users, system

app = FastAPI(title="企业微信 AI 客服系统", version="1.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 企微回调（固定路径，不加 /api 前缀）
app.include_router(callback.router)

# API 路由
app.include_router(auth.router, prefix="/api")
app.include_router(system.router, prefix="/api")
app.include_router(customers.router, prefix="/api")
app.include_router(proactive.router, prefix="/api")
app.include_router(users.router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=app_config["host"], port=app_config["port"])
