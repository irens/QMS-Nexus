"""
FastAPI 异步问答接口
仅调用 Service 层，禁止直接写 DB/RAG 逻辑
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from api.routes.health import router as health_router
from api.routes.upload import router as upload_router
from api.routes.search import router as search_router
from api.routes.tags import router as tags_router
from api.routes.system import router as system_router
from core.rag_service import RAGService
from core.logger import get_logger

logger = get_logger(__name__)


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str
    sources: list[str]


app = FastAPI(title="QMS-Nexus API", version="0.1.0")

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(health_router, prefix="/api/v1")
app.include_router(system_router, prefix="/api/v1")
app.include_router(upload_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")
app.include_router(tags_router, prefix="/api/v1")

rag = RAGService()


@app.post("/ask", response_model=AskResponse)
async def ask(req: AskRequest):
    """RAG 问答，无结果时返回固定文案"""
    try:
        answer, sources = await rag.answer(req.question)
        return AskResponse(answer=answer, sources=sources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
def metrics():
    """Prometheus 指标暴露"""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    return generate_latest()