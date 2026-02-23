"""
反馈存储服务
管理用户对问答的反馈（赞/踩）
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import uuid4

from sqlalchemy.exc import IntegrityError

from core.database import db_manager, Feedback, ChatLog
from core.logger import get_logger

logger = get_logger(__name__)


class FeedbackStore:
    """反馈存储服务，管理用户反馈记录"""

    def create(
        self,
        chat_log_id: str,
        rating: str,
        comment: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Optional[Feedback]:
        """
        创建反馈记录

        Args:
            chat_log_id: 问答日志ID
            rating: 评分，'thumbs_up' 或 'thumbs_down'
            comment: 可选的评论
            user_id: 可选的用户ID

        Returns:
            创建的Feedback对象，如果已存在则返回None

        Raises:
            ValueError: 当rating不是有效值时
        """
        if rating not in ('thumbs_up', 'thumbs_down'):
            raise ValueError("rating必须是 'thumbs_up' 或 'thumbs_down'")

        with db_manager.get_session() as session:
            # 检查是否已存在反馈
            existing = session.query(Feedback).filter_by(
                chat_log_id=chat_log_id,
                user_id=user_id
            ).first()

            if existing:
                logger.info(f"反馈已存在: chat_log_id={chat_log_id}, user_id={user_id}")
                return None

            # 检查chat_log是否存在
            chat_log = session.query(ChatLog).filter_by(id=chat_log_id).first()
            if not chat_log:
                raise ValueError(f"问答日志不存在: {chat_log_id}")

            feedback = Feedback(
                id=str(uuid4()),
                chat_log_id=chat_log_id,
                rating=rating,
                comment=comment,
                user_id=user_id,
                created_at=datetime.utcnow()
            )

            try:
                session.add(feedback)
                session.commit()
                # 刷新对象以便在session关闭后仍能访问属性
                session.refresh(feedback)
                logger.info(f"反馈已创建: id={feedback.id}, rating={rating}")
                return feedback
            except IntegrityError:
                session.rollback()
                logger.warning(f"反馈创建失败（唯一约束冲突）: chat_log_id={chat_log_id}")
                return None

    def get_by_chat_log(self, chat_log_id: str) -> List[Feedback]:
        """
        获取某问答的所有反馈

        Args:
            chat_log_id: 问答日志ID

        Returns:
            反馈列表
        """
        with db_manager.get_session() as session:
            feedbacks = session.query(Feedback).filter_by(
                chat_log_id=chat_log_id
            ).order_by(Feedback.created_at.desc()).all()

            # 将对象从session中分离，避免session关闭后无法访问
            result = []
            for fb in feedbacks:
                result.append({
                    'id': fb.id,
                    'chat_log_id': fb.chat_log_id,
                    'rating': fb.rating,
                    'comment': fb.comment,
                    'user_id': fb.user_id,
                    'created_at': fb.created_at.isoformat() if fb.created_at else None
                })
            return result

    def get_stats(self, chat_log_id: str) -> Dict[str, int]:
        """
        获取某问答的反馈统计

        Args:
            chat_log_id: 问答日志ID

        Returns:
            {"thumbsUp": int, "thumbsDown": int, "total": int}
        """
        with db_manager.get_session() as session:
            feedbacks = session.query(Feedback).filter_by(chat_log_id=chat_log_id).all()

            thumbs_up = sum(1 for f in feedbacks if f.rating == 'thumbs_up')
            thumbs_down = sum(1 for f in feedbacks if f.rating == 'thumbs_down')

            return {
                "thumbsUp": thumbs_up,
                "thumbsDown": thumbs_down,
                "total": len(feedbacks)
            }

    def has_feedback(self, chat_log_id: str, user_id: Optional[str] = None) -> bool:
        """
        检查用户是否已对某问答提交反馈

        Args:
            chat_log_id: 问答日志ID
            user_id: 用户ID，None表示检查是否有任何反馈

        Returns:
            是否已存在反馈
        """
        with db_manager.get_session() as session:
            query = session.query(Feedback).filter_by(chat_log_id=chat_log_id)
            if user_id is not None:
                query = query.filter_by(user_id=user_id)
            return query.first() is not None

    def get_by_id(self, feedback_id: str) -> Optional[Dict[str, Any]]:
        """
        根据ID获取反馈

        Args:
            feedback_id: 反馈ID

        Returns:
            反馈字典，不存在返回None
        """
        with db_manager.get_session() as session:
            feedback = session.query(Feedback).filter_by(id=feedback_id).first()
            if feedback:
                return {
                    'id': feedback.id,
                    'chat_log_id': feedback.chat_log_id,
                    'rating': feedback.rating,
                    'comment': feedback.comment,
                    'user_id': feedback.user_id,
                    'created_at': feedback.created_at.isoformat() if feedback.created_at else None
                }
            return None

    def delete(self, feedback_id: str) -> bool:
        """
        删除反馈

        Args:
            feedback_id: 反馈ID

        Returns:
            是否删除成功
        """
        with db_manager.get_session() as session:
            feedback = session.query(Feedback).filter_by(id=feedback_id).first()
            if not feedback:
                return False

            session.delete(feedback)
            session.commit()
            logger.info(f"反馈已删除: id={feedback_id}")
            return True

    def get_all_stats(self) -> Dict[str, Any]:
        """
        获取全局反馈统计

        Returns:
            {"thumbsUp": int, "thumbsDown": int, "total": int}
        """
        with db_manager.get_session() as session:
            feedbacks = session.query(Feedback).all()

            thumbs_up = sum(1 for f in feedbacks if f.rating == 'thumbs_up')
            thumbs_down = sum(1 for f in feedbacks if f.rating == 'thumbs_down')

            return {
                "thumbsUp": thumbs_up,
                "thumbsDown": thumbs_down,
                "total": len(feedbacks)
            }


# 全局服务实例
feedback_store = FeedbackStore()
