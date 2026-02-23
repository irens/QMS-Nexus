from __future__ import annotations

"""
标签存储封装。

基于统一的 `DatabaseManager` 使用 SQLAlchemy ORM 管理标签表，
为上层路由提供简单的 CRUD 接口。
"""

from typing import List, Optional, Tuple
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from core.database import Tag, db_manager


class TagAlreadyExistsError(Exception):
    """标签名称已存在时抛出。"""


class TagNotFoundError(Exception):
    """标签不存在时抛出。"""


class TagStore:
    """
    标签存储抽象，封装所有与标签相关的数据库操作。

    默认每次操作内部管理数据库会话。
    """

    def __init__(self) -> None:
        self._db = db_manager

    # ------- 公共方法 -------
    def create(
        self,
        *,
        name: str,
        description: str = "",
        color: str = "#409EFF",
    ) -> Tag:
        """
        创建标签。

        Args:
            name: 标签名称（唯一）
            description: 描述
            color: 颜色
            session: 可选外部会话

        Raises:
            TagAlreadyExistsError: 当名称重复时
        """

        with self._db.get_session() as session:
            try:
                # 先检查是否已存在，避免无意义的异常
                existing = session.execute(select(Tag).where(Tag.name == name)).scalar_one_or_none()
                if existing is not None:
                    raise TagAlreadyExistsError("标签已存在")

                tag = Tag(
                    id=str(uuid4()),
                    name=name,
                    description=description,
                    color=color,
                    usage_count=0,
                )
                session.add(tag)
                session.flush()
                return tag
            except IntegrityError as exc:
                # 唯一约束兜底
                raise TagAlreadyExistsError("标签已存在") from exc

    def get_by_id(self, tag_id: str) -> Optional[Tag]:
        """根据 ID 获取标签，不存在返回 None。"""

        with self._db.get_session() as session:
            return session.get(Tag, tag_id)

    def get_by_name(self, name: str) -> Optional[Tag]:
        """根据名称获取标签，不存在返回 None。"""

        with self._db.get_session() as session:
            return session.execute(select(Tag).where(Tag.name == name)).scalar_one_or_none()

    def list_all(
        self,
        *,
        search: Optional[str] = None,
        offset: int = 0,
        limit: Optional[int] = None,
    ) -> Tuple[List[Tag], int]:
        """
        列出标签，支持搜索和分页。

        Args:
            search: 按名称模糊搜索
            offset: 起始偏移量
            limit: 最大返回数量
        Returns:
            (tags, total) 元组
        """

        with self._db.get_session() as session:
            base_stmt = select(Tag)
            if search:
                like = f"%{search}%"
                base_stmt = base_stmt.where(Tag.name.ilike(like))

            # 先获取总数
            count_stmt = select(func.count(Tag.id)).select_from(base_stmt.subquery())
            total = session.execute(count_stmt).scalar_one() or 0

            stmt = base_stmt.order_by(Tag.created_at.desc())
            if offset:
                stmt = stmt.offset(offset)
            if limit is not None:
                stmt = stmt.limit(limit)

            items = list(session.execute(stmt).scalars())
            return items, int(total)

    def update(
        self,
        tag_id: str,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        color: Optional[str] = None,
    ) -> Tag:
        """
        更新标签。

        Raises:
            TagNotFoundError: 标签不存在
            TagAlreadyExistsError: 新名称与其他标签冲突
        """

        with self._db.get_session() as session:
            try:
                tag = session.get(Tag, tag_id)
                if tag is None:
                    raise TagNotFoundError("标签不存在")

                if name is not None and name != tag.name:
                    # 检查名称冲突
                    existing = (
                        session.execute(select(Tag).where(Tag.name == name, Tag.id != tag_id))
                        .scalar_one_or_none()
                    )
                    if existing is not None:
                        raise TagAlreadyExistsError("标签已存在")
                    tag.name = name

                if description is not None:
                    tag.description = description
                if color is not None:
                    tag.color = color

                session.flush()
                return tag
            except IntegrityError as exc:
                raise TagAlreadyExistsError("标签已存在") from exc

    def delete(self, tag_id: str) -> None:
        """
        删除标签。

        Raises:
            TagNotFoundError: 标签不存在
        """

        with self._db.get_session() as session:
            tag = session.get(Tag, tag_id)
            if tag is None:
                raise TagNotFoundError("标签不存在")
            session.delete(tag)
            session.flush()


# 默认全局实例，便于在路由中直接使用
tag_store = TagStore()

