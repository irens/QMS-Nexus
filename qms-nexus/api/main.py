"""
FastAPI 异步问答接口
仅调用 Service 层，禁止直接写 DB/RAG 逻辑
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from core.rag_service import RAGService


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str
    sources: list[str]


app = FastAPI(title="QMS-Nexus API", version="0.1.0")
rag = RAGService()


@app.post("/ask", response_model=AskResponse)
async def ask(req: AskRequest):
    """RAG 问答，无结果时返回固定文案"""
    try:
        answer, sources = await rag.answer(req.question)
        return AskResponse(answer=answer, sources=sources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))