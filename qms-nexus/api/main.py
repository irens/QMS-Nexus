"""
FastAPI 异步问答接口
仅调用 Service 层，禁止直接写 DB/RAG 逻辑
"""
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from api.routes.health import router as health_router
from api.routes.upload import router as upload_router
from api.routes.search import router as search_router
from api.routes.tags import router as tags_router
from api.routes.system import router as system_router
from api.routes.correction import router as correction_router
from api.routes.feedback import router as feedback_router
from api.routes.auth import router as auth_router
from api.routes.knowledge_base import router as kb_router
from api.routes.documents import router as documents_router
from api.routes.chat import router as chat_router
from api.routes.document_versions import router as document_versions_router
from core.rag_service import RAGService
from core.logger import get_logger
from core.cache import check_redis_connection
from core.database import init_database
from core.auth import auth_middleware
from core.chat_logger import chat_logger
from core.backup_manager import backup_manager

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


@app.on_event("startup")
async def startup_event():
    """启动时检查依赖并初始化数据库。"""

    print("\n" + "=" * 60)
    print("正在检查 Redis 连接...")
    print("=" * 60)

    success, message = check_redis_connection()
    print(message)

    if not success:
        print("\n警告：Redis 连接失败，部分功能将不可用！")
        print("=" * 60 + "\n")
    else:
        print("=" * 60 + "\n")

    # 初始化数据库（幂等操作）
    init_database()

    # 设置定时自动备份
    print("正在初始化自动备份...")
    backup_manager.schedule_auto_backup()
    print("自动备份初始化完成\n")


# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加认证中间件（后续启用）
# app.middleware("http")(auth_middleware)

# 注册路由
app.include_router(health_router, prefix="/api/v1")
app.include_router(system_router, prefix="/api/v1")
app.include_router(upload_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")
app.include_router(tags_router, prefix="/api/v1")
app.include_router(correction_router, prefix="/api/v1")
app.include_router(feedback_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(kb_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(document_versions_router, prefix="/api/v1/documents")

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
            "auth": "GET /api/v1/auth/config",
        },
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "ok", "service": "qms-nexus"}


@app.post("/ask", response_model=AskResponse)
async def ask(req: AskRequest, request: Request):
    """
    RAG 问答接口

    流程：
    1. 优先查询修正库，如有匹配直接返回
    2. 否则执行向量检索 + LLM 生成
    """
    import time as _time

    start_ts = _time.time()
    try:
        answer, sources, metadata = await rag.answer(
            question=req.question,
            collection=req.collection,
            skip_correction=req.skip_correction,
        )
        elapsed_ms = int((_time.time() - start_ts) * 1000)

        # 记录问答日志（失败不影响主流程）
        try:
            client_host = request.client.host if request.client else None
            chat_logger.log_chat(
                user_id=None,
                kb_id=req.collection,
                question=req.question,
                answer=answer,
                sources=sources,
                is_corrected=metadata.get("is_corrected", False),
                correction_id=metadata.get("correction_id"),
                response_time_ms=elapsed_ms,
                model_used=metadata.get("model_used") or getattr(rag.llm, "model", None),
                tokens_used=metadata.get("tokens_used"),
                ip_address=client_host,
            )
        except Exception as log_exc:
            logger.error(f"记录问答日志失败: {log_exc}")

        return AskResponse(
            answer=answer,
            sources=sources,
            is_corrected=metadata.get("is_corrected", False),
            correction_id=metadata.get("correction_id"),
        )
    except Exception as e:
        logger.error(f"问答失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask-with-correction", response_model=AskResponse)
async def ask_with_correction(req: AskWithCorrectionRequest, request: Request):
    """
    问答并保存修正

    如果提供了 correct_answer 且 save_correction=True，
    将直接返回正确答案并存入修正库
    """
    import time as _time

    start_ts = _time.time()
    try:
        answer, sources, metadata = await rag.answer_with_feedback(
            question=req.question,
            correct_answer=req.correct_answer,
            collection=req.collection,
            save_correction=req.save_correction,
        )
        elapsed_ms = int((_time.time() - start_ts) * 1000)

        try:
            client_host = request.client.host if request.client else None
            chat_logger.log_chat(
                user_id=None,
                kb_id=req.collection,
                question=req.question,
                answer=answer,
                sources=sources,
                is_corrected=metadata.get("is_corrected", False),
                correction_id=metadata.get("correction_id"),
                response_time_ms=elapsed_ms,
                model_used=metadata.get("model_used") or getattr(rag.llm, "model", None),
                tokens_used=metadata.get("tokens_used"),
                ip_address=client_host,
            )
        except Exception as log_exc:
            logger.error(f"记录问答日志失败: {log_exc}")

        return AskResponse(
            answer=answer,
            sources=sources,
            is_corrected=metadata.get("is_corrected", False),
            correction_id=metadata.get("correction_id"),
        )
    except Exception as e:
        logger.error(f"问答失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
def metrics():
    """Prometheus 指标暴露"""
    from prometheus_client import generate_latest

    return generate_latest()
