"""
用户反馈接口
提供反馈提交和统计查询功能
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from core.feedback_store import feedback_store
from core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["feedback"])


class FeedbackCreate(BaseModel):
    """创建反馈请求体"""
    chatLogId: str = Field(..., description="问答日志ID")
    rating: str = Field(..., description="评分: 'thumbs_up' 或 'thumbs_down'")
    comment: Optional[str] = Field(None, description="可选的评论")


class FeedbackOut(BaseModel):
    """反馈响应模型"""
    id: str
    chatLogId: str
    rating: str
    comment: Optional[str]
    userId: Optional[str]
    createdAt: str


class FeedbackStats(BaseModel):
    """反馈统计响应"""
    thumbsUp: int = Field(..., description="赞的数量")
    thumbsDown: int = Field(..., description="踩的数量")
    total: int = Field(..., description="总数量")


class FeedbackList(BaseModel):
    """反馈列表响应"""
    items: List[FeedbackOut]
    total: int


def _get_client_user_id(request: Request) -> Optional[str]:
    """从请求中获取用户ID（当前简化实现，返回IP作为匿名标识）"""
    # 后续可以从JWT token或session中获取真实用户ID
    # 暂时使用IP地址作为匿名用户标识
    if request.client:
        return f"anon_{request.client.host}"
    return None


@router.post("/feedback", response_model=dict, status_code=201)
async def create_feedback(body: FeedbackCreate, request: Request):
    """
    提交反馈

    同一用户对同一问答只能反馈一次，重复反馈返回 409 Conflict
    """
    user_id = _get_client_user_id(request)

    # 验证rating值
    if body.rating not in ('thumbs_up', 'thumbs_down'):
        raise HTTPException(
            status_code=400,
            detail="rating必须是 'thumbs_up' 或 'thumbs_down'"
        )

    try:
        feedback = feedback_store.create(
            chat_log_id=body.chatLogId,
            rating=body.rating,
            comment=body.comment,
            user_id=user_id
        )

        if feedback is None:
            raise HTTPException(
                status_code=409,
                detail="您已经对该问答提交过反馈"
            )

        return {
            "id": feedback.id,
            "message": "反馈已提交",
            "chatLogId": feedback.chat_log_id,
            "rating": feedback.rating
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"创建反馈失败: {e}")
        raise HTTPException(status_code=500, detail=f"提交反馈失败: {str(e)}")


@router.get("/feedback/stats", response_model=FeedbackStats)
async def get_feedback_stats(chatLogId: str = Query(..., description="问答日志ID")):
    """
    获取某问答的反馈统计

    返回: {"thumbsUp": number, "thumbsDown": number, "total": number}
    """
    try:
        stats = feedback_store.get_stats(chat_log_id=chatLogId)
        return FeedbackStats(**stats)
    except Exception as e:
        logger.error(f"获取反馈统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


@router.get("/feedback", response_model=FeedbackList)
async def list_feedback(
    chatLogId: str = Query(..., description="问答日志ID"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    获取某问答的所有反馈列表
    """
    try:
        feedbacks = feedback_store.get_by_chat_log(chat_log_id=chatLogId)

        # 手动分页
        total = len(feedbacks)
        paginated = feedbacks[offset:offset + limit]

        # 转换为响应模型
        items = [
            FeedbackOut(
                id=fb['id'],
                chatLogId=fb['chat_log_id'],
                rating=fb['rating'],
                comment=fb['comment'],
                userId=fb['user_id'],
                createdAt=fb['created_at']
            )
            for fb in paginated
        ]

        return FeedbackList(items=items, total=total)

    except Exception as e:
        logger.error(f"获取反馈列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取列表失败: {str(e)}")


@router.get("/feedback/check", response_model=dict)
async def check_feedback(
    request: Request,
    chatLogId: str = Query(..., description="问答日志ID")
):
    """
    检查当前用户是否已对某问答提交反馈
    """
    user_id = _get_client_user_id(request)

    try:
        has_feedback = feedback_store.has_feedback(
            chat_log_id=chatLogId,
            user_id=user_id
        )
        return {
            "hasFeedback": has_feedback,
            "chatLogId": chatLogId
        }
    except Exception as e:
        logger.error(f"检查反馈状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"检查失败: {str(e)}")


@router.get("/feedback/global-stats", response_model=FeedbackStats)
async def get_global_feedback_stats():
    """
    获取全局反馈统计
    """
    try:
        stats = feedback_store.get_all_stats()
        return FeedbackStats(**stats)
    except Exception as e:
        logger.error(f"获取全局反馈统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")
