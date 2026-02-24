"""
文档版本数据访问层

提供文档版本的完整生命周期管理，包括创建、查询、状态流转、审批等功能
满足医疗器械行业合规要求（ISO 13485、FDA 21 CFR Part 11）
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, func, select
from sqlalchemy.exc import IntegrityError

from core.database import (
    Document,
    DocumentApprovalHistory,
    DocumentDistribution,
    DocumentVersion,
    db_manager,
)
from core.logger import get_logger

logger = get_logger(__name__)


class VersionStatus(str, Enum):
    """版本状态枚举"""
    DRAFT = "draft"           # 草稿
    REVIEW = "review"         # 审核中
    APPROVED = "approved"     # 已批准
    EFFECTIVE = "effective"   # 生效中
    OBSOLETE = "obsolete"     # 已作废
    ARCHIVED = "archived"     # 已归档


class VersionAction(str, Enum):
    """版本操作枚举"""
    CREATE = "create"
    SUBMIT = "submit"
    REVIEW = "review"
    APPROVE = "approve"
    REJECT = "reject"
    PUBLISH = "publish"
    OBSOLETE = "obsolete"
    ARCHIVE = "archive"


class DuplicateType(str, Enum):
    """去重检测结果枚举"""
    EXACT_MATCH = "exact_match"    # 完全相同的文件（哈希相同）
    NAME_MATCH = "name_match"      # 同名不同内容
    NEW_FILE = "new_file"          # 新文件


@dataclass
class VersionDiff:
    """版本对比结果"""
    v1_id: str
    v2_id: str
    v1_version_label: str
    v2_version_label: str
    added_chunks: List[Dict[str, Any]]
    removed_chunks: List[Dict[str, Any]]
    modified_chunks: List[Dict[str, Any]]
    change_summary: str


@dataclass
class DuplicateCheckResult:
    """去重检测结果"""
    type: DuplicateType
    message: str
    existing_document: Optional[Dict[str, Any]] = None
    existing_version: Optional[Dict[str, Any]] = None
    suggestions: List[Dict[str, str]] = None


class VersionNotFoundError(Exception):
    """版本不存在时抛出"""
    pass


class InvalidStatusTransitionError(Exception):
    """非法状态流转时抛出"""
    pass


class VersionAlreadyExistsError(Exception):
    """版本已存在时抛出"""
    pass


class DocumentVersionStore:
    """文档版本存储抽象，封装所有与文档版本相关的数据库操作"""

    # 状态流转规则：key=当前状态, value=允许的目标状态列表
    STATUS_TRANSITIONS: Dict[str, List[str]] = {
        VersionStatus.DRAFT: [VersionStatus.REVIEW],
        VersionStatus.REVIEW: [VersionStatus.APPROVED, VersionStatus.DRAFT],
        VersionStatus.APPROVED: [VersionStatus.EFFECTIVE],
        VersionStatus.EFFECTIVE: [VersionStatus.OBSOLETE],
        VersionStatus.OBSOLETE: [],
        VersionStatus.ARCHIVED: [],
    }

    def __init__(self) -> None:
        self._db = db_manager

    def _generate_uuid(self) -> str:
        """生成 UUID"""
        return str(uuid.uuid4())

    def _validate_status_transition(self, from_status: str, to_status: str) -> bool:
        """验证状态流转是否合法"""
        # 处理枚举类型
        if isinstance(from_status, VersionStatus):
            from_status = from_status.value
        if isinstance(to_status, VersionStatus):
            to_status = to_status.value
        
        if from_status == to_status:
            return True
        allowed_transitions = self.STATUS_TRANSITIONS.get(from_status, [])
        return to_status in allowed_transitions

    def _record_approval_history(
        self,
        session,
        version_id: str,
        action: str,
        action_by: str,
        from_status: Optional[str],
        to_status: str,
        comment: Optional[str] = None,
    ) -> DocumentApprovalHistory:
        """记录审批历史"""
        history = DocumentApprovalHistory(
            document_version_id=version_id,
            action=action,
            action_by=action_by,
            action_at=datetime.utcnow(),
            comment=comment,
            from_status=from_status,
            to_status=to_status,
        )
        session.add(history)
        return history

    async def create_version(
        self,
        document_id: str,
        filename: str,
        file_hash: str,
        file_size: int,
        file_type: str,
        change_summary: str,
        change_details: Optional[str] = None,
        version_label: Optional[str] = None,
        prepared_by: Optional[str] = None,
        kb_id: str = "default",
    ) -> DocumentVersion:
        """
        创建新版本，自动递增版本号

        Args:
            document_id: 文档组ID
            filename: 文件名
            file_hash: 文件SHA256哈希
            file_size: 文件大小（字节）
            file_type: 文件类型
            change_summary: 变更摘要（必填）
            change_details: 变更详细说明
            version_label: 版本标签（如 V1.0），不传则自动生成
            prepared_by: 编制人
            kb_id: 知识库ID

        Returns:
            新创建的版本对象

        Raises:
            VersionAlreadyExistsError: 如果相同版本号已存在
        """
        with self._db.get_session() as session:
            # 获取当前最新版本号
            latest_version = (
                session.query(DocumentVersion)
                .filter(DocumentVersion.document_id == document_id)
                .order_by(desc(DocumentVersion.version_number))
                .first()
            )

            new_version_number = 1
            previous_version_id = None

            if latest_version:
                new_version_number = latest_version.version_number + 1
                previous_version_id = latest_version.id

            # 自动生成版本标签
            if not version_label:
                version_label = f"V{new_version_number}.0"

            # 创建新版本
            version = DocumentVersion(
                id=self._generate_uuid(),
                document_id=document_id,
                version_number=new_version_number,
                version_label=version_label,
                filename=filename,
                file_hash=file_hash,
                file_size=file_size,
                file_type=file_type,
                status=VersionStatus.DRAFT,
                title=filename,
                change_summary=change_summary,
                change_details=change_details,
                previous_version_id=previous_version_id,
                prepared_by=prepared_by,
                kb_id=kb_id,
                created_by=prepared_by,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            try:
                session.add(version)
                session.flush()

                # 记录创建历史
                self._record_approval_history(
                    session=session,
                    version_id=version.id,
                    action=VersionAction.CREATE,
                    action_by=prepared_by or "system",
                    from_status=None,
                    to_status=VersionStatus.DRAFT,
                    comment=f"创建版本 {version_label}",
                )

                session.commit()
                logger.info(
                    f"创建版本成功: document_id={document_id}, "
                    f"version_number={new_version_number}, version_id={version.id}"
                )
                return version

            except IntegrityError as e:
                session.rollback()
                logger.error(f"创建版本失败（唯一约束冲突）: {e}")
                raise VersionAlreadyExistsError(
                    f"版本号 {new_version_number} 已存在"
                ) from e
            except Exception as e:
                session.rollback()
                logger.error(f"创建版本失败: {e}")
                raise

    async def get_version_by_id(
        self, version_id: str
    ) -> Optional[DocumentVersion]:
        """
        根据ID获取版本详情

        Args:
            version_id: 版本ID

        Returns:
            版本对象，不存在则返回 None
        """
        with self._db.get_session() as session:
            return session.get(DocumentVersion, version_id)

    async def get_versions_by_document(
        self,
        document_id: str,
        status: Optional[str] = None,
    ) -> List[DocumentVersion]:
        """
        获取文档的所有版本

        Args:
            document_id: 文档组ID
            status: 可选，按状态筛选

        Returns:
            版本列表，按版本号降序排列
        """
        with self._db.get_session() as session:
            stmt = (
                select(DocumentVersion)
                .where(DocumentVersion.document_id == document_id)
                .order_by(desc(DocumentVersion.version_number))
            )

            if status:
                stmt = stmt.where(DocumentVersion.status == status)

            return list(session.execute(stmt).scalars())

    async def get_latest_version(
        self, document_id: str
    ) -> Optional[DocumentVersion]:
        """
        获取文档的最新版本

        Args:
            document_id: 文档组ID

        Returns:
            最新版本对象，不存在则返回 None
        """
        with self._db.get_session() as session:
            return (
                session.query(DocumentVersion)
                .filter(DocumentVersion.document_id == document_id)
                .order_by(desc(DocumentVersion.version_number))
                .first()
            )

    async def get_effective_version_at_date(
        self,
        document_id: str,
        date: datetime,
    ) -> Optional[DocumentVersion]:
        """
        获取指定日期生效的版本

        Args:
            document_id: 文档组ID
            date: 指定日期

        Returns:
            该日期生效的版本对象，不存在则返回 None
        """
        with self._db.get_session() as session:
            # 查找在指定日期之前生效的最新版本
            return (
                session.query(DocumentVersion)
                .filter(
                    and_(
                        DocumentVersion.document_id == document_id,
                        DocumentVersion.status == VersionStatus.EFFECTIVE,
                        DocumentVersion.effective_date <= date,
                    )
                )
                .order_by(desc(DocumentVersion.effective_date))
                .first()
            )

    async def update_version_status(
        self,
        version_id: str,
        new_status: str,
        user_id: str,
        comment: Optional[str] = None,
    ) -> bool:
        """
        更新版本状态，自动记录审批历史

        Args:
            version_id: 版本ID
            new_status: 新状态
            user_id: 操作用户ID
            comment: 审批意见

        Returns:
            是否更新成功

        Raises:
            VersionNotFoundError: 版本不存在
            InvalidStatusTransitionError: 非法状态流转
        """
        with self._db.get_session() as session:
            version = session.get(DocumentVersion, version_id)
            if not version:
                raise VersionNotFoundError(f"版本 {version_id} 不存在")

            old_status = version.status

            # 验证状态流转
            if not self._validate_status_transition(old_status, new_status):
                raise InvalidStatusTransitionError(
                    f"非法状态流转: {old_status} -> {new_status}"
                )

            try:
                # 更新状态
                version.status = new_status
                version.updated_at = datetime.utcnow()

                # 确定操作类型
                action_map = {
                    VersionStatus.REVIEW: VersionAction.SUBMIT,
                    VersionStatus.APPROVED: VersionAction.REVIEW,
                    VersionStatus.DRAFT: VersionAction.REJECT,
                    VersionStatus.EFFECTIVE: VersionAction.PUBLISH,
                    VersionStatus.OBSOLETE: VersionAction.OBSOLETE,
                    VersionStatus.ARCHIVED: VersionAction.ARCHIVE,
                }
                action = action_map.get(new_status, VersionAction.REVIEW)

                # 记录审批历史
                self._record_approval_history(
                    session=session,
                    version_id=version_id,
                    action=action,
                    action_by=user_id,
                    from_status=old_status,
                    to_status=new_status,
                    comment=comment,
                )

                session.commit()
                logger.info(
                    f"版本状态更新成功: version_id={version_id}, "
                    f"{old_status} -> {new_status}"
                )
                return True

            except Exception as e:
                session.rollback()
                logger.error(f"更新版本状态失败: {e}")
                raise

    async def approve_version(
        self,
        version_id: str,
        approved_by: str,
        comment: Optional[str] = None,
    ) -> bool:
        """
        审批通过版本

        流程：
        1. 状态: approved -> effective
        2. 将上一版本标记为 obsolete
        3. 更新 documents 表的 current_version_id
        4. 创建培训任务（后续实现）

        Args:
            version_id: 版本ID
            approved_by: 批准人
            comment: 审批意见

        Returns:
            是否审批成功
        """
        with self._db.get_session() as session:
            version = session.get(DocumentVersion, version_id)
            if not version:
                raise VersionNotFoundError(f"版本 {version_id} 不存在")

            if version.status != VersionStatus.APPROVED:
                raise InvalidStatusTransitionError(
                    f"版本状态必须是 approved，当前状态: {version.status}"
                )

            try:
                old_status = version.status

                # 更新版本状态为生效
                version.status = VersionStatus.EFFECTIVE
                version.approved_by = approved_by
                version.approved_date = datetime.utcnow()
                version.effective_date = datetime.utcnow()
                version.is_latest = True
                version.updated_at = datetime.utcnow()

                # 将上一版本标记为 obsolete
                if version.previous_version_id:
                    prev_version = session.get(
                        DocumentVersion, version.previous_version_id
                    )
                    if prev_version and prev_version.status == VersionStatus.EFFECTIVE:
                        prev_version.status = VersionStatus.OBSOLETE
                        prev_version.is_latest = False
                        prev_version.updated_at = datetime.utcnow()

                        # 记录上一版本的作废历史
                        self._record_approval_history(
                            session=session,
                            version_id=prev_version.id,
                            action=VersionAction.OBSOLETE,
                            action_by=approved_by,
                            from_status=VersionStatus.EFFECTIVE,
                            to_status=VersionStatus.OBSOLETE,
                            comment=f"被新版本 {version.version_label} 替代",
                        )

                # 更新文档的当前版本
                document = session.get(Document, version.document_id)
                if document:
                    document.current_version_id = version_id

                # 记录审批历史
                self._record_approval_history(
                    session=session,
                    version_id=version_id,
                    action=VersionAction.PUBLISH,
                    action_by=approved_by,
                    from_status=old_status,
                    to_status=VersionStatus.EFFECTIVE,
                    comment=comment,
                )

                session.commit()
                logger.info(
                    f"版本审批通过: version_id={version_id}, "
                    f"approved_by={approved_by}"
                )
                return True

            except Exception as e:
                session.rollback()
                logger.error(f"审批版本失败: {e}")
                raise

    async def obsolete_version(
        self,
        version_id: str,
        user_id: str,
        reason: Optional[str] = None,
    ) -> bool:
        """
        作废版本

        Args:
            version_id: 版本ID
            user_id: 操作用户ID
            reason: 作废原因

        Returns:
            是否作废成功
        """
        return await self.update_version_status(
            version_id=version_id,
            new_status=VersionStatus.OBSOLETE,
            user_id=user_id,
            comment=reason or "版本作废",
        )

    async def compare_versions(
        self,
        v1_id: str,
        v2_id: str,
    ) -> VersionDiff:
        """
        对比两个版本差异

        Args:
            v1_id: 版本1 ID
            v2_id: 版本2 ID

        Returns:
            版本对比结果

        Note:
            目前为基础实现，完整对比功能需要结合向量库内容对比
        """
        with self._db.get_session() as session:
            v1 = session.get(DocumentVersion, v1_id)
            v2 = session.get(DocumentVersion, v2_id)

            if not v1:
                raise VersionNotFoundError(f"版本 {v1_id} 不存在")
            if not v2:
                raise VersionNotFoundError(f"版本 {v2_id} 不存在")

            # 基础元数据对比
            added_chunks = []
            removed_chunks = []
            modified_chunks = []

            # 对比文件哈希
            if v1.file_hash != v2.file_hash:
                modified_chunks.append({
                    "type": "file_hash",
                    "v1": v1.file_hash[:16] + "...",
                    "v2": v2.file_hash[:16] + "...",
                })

            # 对比文件大小
            if v1.file_size != v2.file_size:
                size_diff = (v2.file_size or 0) - (v1.file_size or 0)
                modified_chunks.append({
                    "type": "file_size",
                    "v1": v1.file_size,
                    "v2": v2.file_size,
                    "diff": size_diff,
                })

            # 对比变更摘要
            if v1.change_summary != v2.change_summary:
                modified_chunks.append({
                    "type": "change_summary",
                    "v1": v1.change_summary,
                    "v2": v2.change_summary,
                })

            # 生成变更总结
            change_summary = f"从 {v1.version_label} 升级到 {v2.version_label}"
            if v2.change_summary:
                change_summary += f"：{v2.change_summary}"

            return VersionDiff(
                v1_id=v1_id,
                v2_id=v2_id,
                v1_version_label=v1.version_label,
                v2_version_label=v2.version_label,
                added_chunks=added_chunks,
                removed_chunks=removed_chunks,
                modified_chunks=modified_chunks,
                change_summary=change_summary,
            )

    async def check_duplicate(
        self,
        file_hash: str,
        filename: str,
        kb_id: str = "default",
    ) -> DuplicateCheckResult:
        """
        检查文件是否重复

        Args:
            file_hash: 文件SHA256哈希
            filename: 文件名
            kb_id: 知识库ID

        Returns:
            去重检测结果，包含处理建议
        """
        with self._db.get_session() as session:
            # 1. 检查完全相同的文件（哈希相同）
            exact_match = (
                session.query(DocumentVersion)
                .filter(
                    and_(
                        DocumentVersion.file_hash == file_hash,
                        DocumentVersion.kb_id == kb_id,
                    )
                )
                .first()
            )

            if exact_match:
                document = session.get(Document, exact_match.document_id)
                
                # 构建现有文档信息
                existing_document = {
                    "id": exact_match.document_id,
                    "title": document.filename if document else exact_match.filename,
                    "current_version": {
                        "version_id": exact_match.id,
                        "version_number": exact_match.version_number,
                        "version_label": exact_match.version_label or f"V{exact_match.version_number}.0",
                        "status": exact_match.status,
                    }
                }
                
                # 构建现有版本信息
                existing_version = {
                    "version_id": exact_match.id,
                    "version_number": exact_match.version_number,
                    "version_label": exact_match.version_label or f"V{exact_match.version_number}.0",
                    "status": exact_match.status,
                    "file_hash": exact_match.file_hash,
                    "created_at": exact_match.created_at.isoformat() if exact_match.created_at else None,
                }
                
                # 构建处理建议
                suggestions = [
                    {"action": "view", "label": "查看现有版本"},
                    {"action": "upload_as_new_version", "label": "作为新版本上传"},
                    {"action": "force_upload", "label": "强制重新上传"},
                    {"action": "cancel", "label": "取消"},
                ]
                
                return DuplicateCheckResult(
                    type=DuplicateType.EXACT_MATCH,
                    message="该文件已存在，内容与现有版本完全相同",
                    existing_document=existing_document,
                    existing_version=existing_version,
                    suggestions=suggestions,
                )

            # 2. 检查同名文件（文件名相同，哈希不同）- 查找该文档的最新版本
            name_match = (
                session.query(DocumentVersion)
                .filter(
                    and_(
                        DocumentVersion.filename == filename,
                        DocumentVersion.kb_id == kb_id,
                    )
                )
                .order_by(desc(DocumentVersion.version_number))
                .first()
            )

            if name_match:
                document = session.get(Document, name_match.document_id)
                
                # 计算下一版本号
                next_version_number = name_match.version_number + 1
                next_version_label = f"V{next_version_number}.0"
                
                # 构建现有文档信息
                existing_document = {
                    "id": name_match.document_id,
                    "title": document.filename if document else name_match.filename,
                    "current_version": {
                        "version_id": name_match.id,
                        "version_number": name_match.version_number,
                        "version_label": name_match.version_label or f"V{name_match.version_number}.0",
                        "status": name_match.status,
                    }
                }
                
                # 构建现有版本信息
                existing_version = {
                    "version_id": name_match.id,
                    "version_number": name_match.version_number,
                    "version_label": name_match.version_label or f"V{name_match.version_number}.0",
                    "status": name_match.status,
                    "file_hash": name_match.file_hash,
                    "created_at": name_match.created_at.isoformat() if name_match.created_at else None,
                }
                
                # 构建处理建议
                suggestions = [
                    {"action": "upload_as_new_version", "label": f"创建为新版本 {next_version_label}"},
                    {"action": "rename", "label": "重命名后上传"},
                    {"action": "cancel", "label": "取消上传"},
                ]
                
                return DuplicateCheckResult(
                    type=DuplicateType.NAME_MATCH,
                    message=f"检测到同名文件，内容不同",
                    existing_document=existing_document,
                    existing_version=existing_version,
                    suggestions=suggestions,
                )

            # 3. 新文件
            return DuplicateCheckResult(
                type=DuplicateType.NEW_FILE,
                message="新文件，可以上传",
                existing_document=None,
                existing_version=None,
                suggestions=[
                    {"action": "upload", "label": "继续上传"},
                ],
            )

    async def get_approval_history(
        self, version_id: str
    ) -> List[DocumentApprovalHistory]:
        """
        获取版本的审批历史

        Args:
            version_id: 版本ID

        Returns:
            审批历史列表，按时间升序排列
        """
        with self._db.get_session() as session:
            return (
                session.query(DocumentApprovalHistory)
                .filter(DocumentApprovalHistory.document_version_id == version_id)
                .order_by(DocumentApprovalHistory.action_at)
                .all()
            )

    async def get_version_stats(self, document_id: str) -> Dict[str, Any]:
        """
        获取文档版本统计信息

        Args:
            document_id: 文档组ID

        Returns:
            统计信息字典
        """
        with self._db.get_session() as session:
            versions = (
                session.query(DocumentVersion)
                .filter(DocumentVersion.document_id == document_id)
                .all()
            )

            total = len(versions)
            by_status: Dict[str, int] = {}
            for v in versions:
                by_status[v.status] = by_status.get(v.status, 0) + 1

            latest = await self.get_latest_version(document_id)
            effective = [v for v in versions if v.status == VersionStatus.EFFECTIVE]

            return {
                "total_versions": total,
                "by_status": by_status,
                "latest_version": {
                    "id": latest.id,
                    "label": latest.version_label,
                    "status": latest.status,
                } if latest else None,
                "effective_versions": len(effective),
            }


# 默认实例供路由层复用
document_version_store = DocumentVersionStore()
