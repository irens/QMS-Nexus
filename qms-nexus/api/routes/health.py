"""
健康检查路由，返回 200 OK
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health():
    """FastAPI 健康检查接口。"""
    return {"status": "ok"}