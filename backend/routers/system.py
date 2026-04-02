import time
from fastapi import APIRouter

router = APIRouter(prefix="/system", tags=["system"])

@router.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": time.time()}
