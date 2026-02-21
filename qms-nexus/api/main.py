"""
FastAPI 异步问答接口
仅调用 Service 层，禁止直接写 DB/RAG 逻辑
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import sys

from api.routes.health import router as health_router
from api.routes.upload import router as upload_router
from api.routes.search import router as search_router
from api.routes.tags import router as tags_router
from api.routes.system import router as system_router
from api.routes.correction import router as correction_router
from api.routes.auth import router as auth_router
from api.routes.knowledge_base import router as kb_router
from core.rag_service import RAGService
from core.logger import get_logger
from core.cache import check_redis_connection
from core.auth import auth_middleware

logger = get_logger(__name__)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, description="问题内容")
    collection: str = Field(default="qms_docs", description="知识库名称")
    skip_correction: bool = Field(default=False, description="是否跳过修正库查询")


class AskResponse(BaseModel):
    answer: str
    sources: list[str]
    is_corrected: bool = Field(default=False, description="是否来自修正库")
    correction_id: Optional[int] = Field(default=None, description="修正记录ID")


class AskWithCorrectionRequest(BaseModel):
    question: str = Field(..., min_length=1, description="问题内容")
    correct_answer: Optional[str] = Field(default=None, description="如果提供，将保存到修正库")
    save_correction: bool = Field(default=False, description="是否保存到修正库")
    collection: str = Field(default="qms_docs", description="知识库名称")


app = FastAPI(title="QMS-Nexus API", version="1.0.0")


# 启动时检测 Redis 连接
@app.on_event("startup")
async def startup_event():
    print("\n" + "="*60)
    print("正在检查 Redis 连接...")
    print("="*60)
    
    success, message = check_redis_connection()
    print(message)
    
    if not success:
        print("\n警告：Redis 连接失败，部分功能将不可用！")
        print("="*60 + "\n")
    else:
        print("="*60 + "\n")


# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加认证中间件
# app.middleware("http")(auth_middleware)

# 注册路由
app.include_router(health_router, prefix="/api/v1")
app.include_router(system_router, prefix="/api/v1")
app.include_router(upload_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")
app.include_router(tags_router, prefix="/api/v1")
app.include_router(correction_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(kb_router, prefix="/api/v1")

rag = RAGService()


@app.get("/")
async def root():
    """API 根路径，返回服务信息"""
    return {
        "name": "QMS-Nexus API",
        "version": "1.0.0",
        "description": "医疗器械质量管理体系智能问答系统",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "endpoints": {
            "ask": "POST /ask",
            "search": "GET /api/v1/search",
            "upload": "POST /api/v1/upload",
            "knowledge_bases": "GET /api/v1/knowledge-bases",
            "corrections": "GET /api/v1/corrections",
            "auth": "GET /api/v1/auth/config"
        }
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "ok", "service": "qms-nexus"}


@app.post("/ask", response_model=AskResponse)
async def ask(req: AskRequest):
    """
    RAG 问答接口
    
    流程：
    1. 优先查询修正库，如有匹配直接返回
    2. 否则执行向量检索 + LLM 生成
    """
    try:
        answer, sources, metadata = await rag.answer(
            question=req.question,
            collection=req.collection,
            skip_correction=req.skip_correction
        )
        return AskResponse(
            answer=answer,
            sources=sources,
            is_corrected=metadata.get("is_corrected", False),
            correction_id=metadata.get("correction_id")
        )
    except Exception as e:
        logger.error(f"问答失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask-with-correction", response_model=AskResponse)
async def ask_with_correction(req: AskWithCorrectionRequest):
    """
    问答并保存修正
    
    如果提供了 correct_answer 且 save_correction=True，
    将直接返回正确答案并存入修正库
    """
    try:
        answer, sources, metadata = await rag.answer_with_feedback(
            question=req.question,
            correct_answer=req.correct_answer,
            collection=req.collection,
            save_correction=req.save_correction
        )
        return AskResponse(
            answer=answer,
            sources=sources,
            is_corrected=metadata.get("is_corrected", False),
            correction_id=metadata.get("correction_id")
        )
    except Exception as e:
        logger.error(f"问答失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
def metrics():
    """Prometheus 指标暴露"""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    return generate_latest()
