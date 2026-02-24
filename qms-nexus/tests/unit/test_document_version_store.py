"""
DocumentVersionStore 单元测试
"""
import asyncio
import hashlib
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.database import Base, Document, DocumentVersion, DocumentApprovalHistory
from core.document_version_store import (
    DocumentVersionStore,
    VersionStatus,
    VersionAction,
    DuplicateType,
    VersionNotFoundError,
    InvalidStatusTransitionError,
    VersionAlreadyExistsError,
)


# 使用内存数据库进行测试
@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def version_store(db_session):
    """创建 DocumentVersionStore 实例"""
    store = DocumentVersionStore()
    # 使用测试数据库
    store._db = MagicMock()
    store._db.get_session = MagicMock(return_value=db_session)
    return store


@pytest.fixture
def sample_document_id():
    """示例文档ID"""
    return "doc-123456"


@pytest.fixture
def sample_file_hash():
    """示例文件哈希"""
    return hashlib.sha256(b"test content").hexdigest()


class TestCreateVersion:
    """测试创建版本功能"""

    @pytest.mark.asyncio
    async def test_create_first_version(self, version_store, sample_document_id, sample_file_hash):
        """测试创建第一个版本"""
        version = await version_store.create_version(
            document_id=sample_document_id,
            filename="test.pdf",
            file_hash=sample_file_hash,
            file_size=1024,
            file_type="pdf",
            change_summary="初始版本",
            prepared_by="user1",
        )

        assert version is not None
        assert version.document_id == sample_document_id
        assert version.version_number == 1
        assert version.version_label == "V1.0"
        assert version.status == VersionStatus.DRAFT
        assert version.file_hash == sample_file_hash

    @pytest.mark.asyncio
    async def test_create_subsequent_version(self, version_store, sample_document_id, sample_file_hash):
        """测试创建后续版本（自动递增版本号）"""
        # 创建第一个版本
        v1 = await version_store.create_version(
            document_id=sample_document_id,
            filename="test.pdf",
            file_hash=sample_file_hash,
            file_size=1024,
            file_type="pdf",
            change_summary="初始版本",
            prepared_by="user1",
        )

        # 创建第二个版本
        new_hash = hashlib.sha256(b"new content").hexdigest()
        v2 = await version_store.create_version(
            document_id=sample_document_id,
            filename="test.pdf",
            file_hash=new_hash,
            file_size=2048,
            file_type="pdf",
            change_summary="更新内容",
            prepared_by="user1",
        )

        assert v2.version_number == 2
        assert v2.version_label == "V2.0"
        assert v2.previous_version_id == v1.id

    @pytest.mark.asyncio
    async def test_create_version_with_custom_label(self, version_store, sample_document_id, sample_file_hash):
        """测试使用自定义版本标签"""
        version = await version_store.create_version(
            document_id=sample_document_id,
            filename="test.pdf",
            file_hash=sample_file_hash,
            file_size=1024,
            file_type="pdf",
            change_summary="初始版本",
            version_label="V1.0-beta",
            prepared_by="user1",
        )

        assert version.version_label == "V1.0-beta"


class TestGetVersions:
    """测试查询版本功能"""

    @pytest.mark.asyncio
    async def test_get_version_by_id(self, version_store, sample_document_id, sample_file_hash):
        """测试根据ID获取版本"""
        created = await version_store.create_version(
            document_id=sample_document_id,
            filename="test.pdf",
            file_hash=sample_file_hash,
            file_size=1024,
            file_type="pdf",
            change_summary="初始版本",
            prepared_by="user1",
        )

        fetched = await version_store.get_version_by_id(created.id)
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.filename == "test.pdf"

    @pytest.mark.asyncio
    async def test_get_version_by_id_not_found(self, version_store):
        """测试获取不存在的版本"""
        result = await version_store.get_version_by_id("non-existent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_versions_by_document(self, version_store, sample_document_id, sample_file_hash):
        """测试获取文档的所有版本"""
        # 创建多个版本
        for i in range(3):
            new_hash = hashlib.sha256(f"content{i}".encode()).hexdigest()
            await version_store.create_version(
                document_id=sample_document_id,
                filename="test.pdf",
                file_hash=new_hash,
                file_size=1024,
                file_type="pdf",
                change_summary=f"版本 {i+1}",
                prepared_by="user1",
            )

        versions = await version_store.get_versions_by_document(sample_document_id)
        assert len(versions) == 3
        # 验证按版本号降序排列
        assert versions[0].version_number == 3
        assert versions[1].version_number == 2
        assert versions[2].version_number == 1

    @pytest.mark.asyncio
    async def test_get_versions_by_document_with_status_filter(self, version_store, sample_document_id, sample_file_hash):
        """测试按状态筛选版本"""
        # 创建版本并更改状态
        v1 = await version_store.create_version(
            document_id=sample_document_id,
            filename="test.pdf",
            file_hash=sample_file_hash,
            file_size=1024,
            file_type="pdf",
            change_summary="版本1",
            prepared_by="user1",
        )
        # 正确的状态流转: draft -> review -> approved -> effective
        await version_store.update_version_status(v1.id, VersionStatus.REVIEW, "user1")
        await version_store.update_version_status(v1.id, VersionStatus.APPROVED, "user1")
        await version_store.approve_version(v1.id, "admin")

        new_hash = hashlib.sha256(b"content2").hexdigest()
        v2 = await version_store.create_version(
            document_id=sample_document_id,
            filename="test.pdf",
            file_hash=new_hash,
            file_size=1024,
            file_type="pdf",
            change_summary="版本2",
            prepared_by="user1",
        )

        # 只查询草稿状态的版本
        draft_versions = await version_store.get_versions_by_document(
            sample_document_id, status=VersionStatus.DRAFT
        )
        assert len(draft_versions) == 1
        assert draft_versions[0].id == v2.id

    @pytest.mark.asyncio
    async def test_get_latest_version(self, version_store, sample_document_id, sample_file_hash):
        """测试获取最新版本"""
        # 创建多个版本
        for i in range(3):
            new_hash = hashlib.sha256(f"content{i}".encode()).hexdigest()
            await version_store.create_version(
                document_id=sample_document_id,
                filename="test.pdf",
                file_hash=new_hash,
                file_size=1024,
                file_type="pdf",
                change_summary=f"版本 {i+1}",
                prepared_by="user1",
            )

        latest = await version_store.get_latest_version(sample_document_id)
        assert latest is not None
        assert latest.version_number == 3

    @pytest.mark.asyncio
    async def test_get_effective_version_at_date(self, version_store, sample_document_id, sample_file_hash):
        """测试获取指定日期生效的版本"""
        # 创建并生效一个版本
        v1 = await version_store.create_version(
            document_id=sample_document_id,
            filename="test.pdf",
            file_hash=sample_file_hash,
            file_size=1024,
            file_type="pdf",
            change_summary="版本1",
            prepared_by="user1",
        )
        # 正确的状态流转: draft -> review -> approved -> effective
        await version_store.update_version_status(v1.id, VersionStatus.REVIEW, "user1")
        await version_store.update_version_status(v1.id, VersionStatus.APPROVED, "user1")
        await version_store.approve_version(v1.id, "admin")

        # 查询今天的生效版本
        today = datetime.utcnow()
        effective_version = await version_store.get_effective_version_at_date(
            sample_document_id, today
        )
        assert effective_version is not None
        assert effective_version.id == v1.id


class TestStatusTransition:
    """测试状态流转功能"""

    @pytest.mark.asyncio
    async def test_valid_status_transitions(self, version_store, sample_document_id, sample_file_hash):
        """测试合法的状态流转"""
        version = await version_store.create_version(
            document_id=sample_document_id,
            filename="test.pdf",
            file_hash=sample_file_hash,
            file_size=1024,
            file_type="pdf",
            change_summary="测试版本",
            prepared_by="user1",
        )

        # draft -> review
        result = await version_store.update_version_status(
            version.id, VersionStatus.REVIEW, "user1"
        )
        assert result is True

        # review -> approved
        result = await version_store.update_version_status(
            version.id, VersionStatus.APPROVED, "user1"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_invalid_status_transition(self, version_store, sample_document_id, sample_file_hash):
        """测试非法的状态流转"""
        version = await version_store.create_version(
            document_id=sample_document_id,
            filename="test.pdf",
            file_hash=sample_file_hash,
            file_size=1024,
            file_type="pdf",
            change_summary="测试版本",
            prepared_by="user1",
        )

        # draft 不能直接到 effective
        with pytest.raises(InvalidStatusTransitionError):
            await version_store.update_version_status(
                version.id, VersionStatus.EFFECTIVE, "user1"
            )

    @pytest.mark.asyncio
    async def test_approval_history_recorded(self, version_store, sample_document_id, sample_file_hash):
        """测试审批历史自动记录"""
        version = await version_store.create_version(
            document_id=sample_document_id,
            filename="test.pdf",
            file_hash=sample_file_hash,
            file_size=1024,
            file_type="pdf",
            change_summary="测试版本",
            prepared_by="user1",
        )

        await version_store.update_version_status(
            version.id, VersionStatus.REVIEW, "user1", "提交审核"
        )

        history = await version_store.get_approval_history(version.id)
        assert len(history) >= 2  # 创建 + 状态变更

        # 验证最新的历史记录
        latest = history[-1]
        assert latest.action == VersionAction.SUBMIT
        assert latest.from_status == VersionStatus.DRAFT
        assert latest.to_status == VersionStatus.REVIEW
        assert latest.comment == "提交审核"


class TestApproveVersion:
    """测试审批通过功能"""

    @pytest.mark.asyncio
    async def test_approve_version_success(self, version_store, sample_document_id, sample_file_hash):
        """测试成功审批版本"""
        version = await version_store.create_version(
            document_id=sample_document_id,
            filename="test.pdf",
            file_hash=sample_file_hash,
            file_size=1024,
            file_type="pdf",
            change_summary="测试版本",
            prepared_by="user1",
        )

        # 正确的状态流转: draft -> review -> approved -> effective
        await version_store.update_version_status(
            version.id, VersionStatus.REVIEW, "user1"
        )
        await version_store.update_version_status(
            version.id, VersionStatus.APPROVED, "reviewer"
        )

        # 审批通过
        result = await version_store.approve_version(version.id, "admin", "批准发布")
        assert result is True

        # 验证状态
        updated = await version_store.get_version_by_id(version.id)
        assert updated.status == VersionStatus.EFFECTIVE
        assert updated.approved_by == "admin"
        assert updated.is_latest is True

    @pytest.mark.asyncio
    async def test_approve_version_wrong_status(self, version_store, sample_document_id, sample_file_hash):
        """测试在非 approved 状态下审批"""
        version = await version_store.create_version(
            document_id=sample_document_id,
            filename="test.pdf",
            file_hash=sample_file_hash,
            file_size=1024,
            file_type="pdf",
            change_summary="测试版本",
            prepared_by="user1",
        )

        with pytest.raises(InvalidStatusTransitionError):
            await version_store.approve_version(version.id, "admin")

    @pytest.mark.asyncio
    async def test_previous_version_obsoleted(self, version_store, sample_document_id, sample_file_hash):
        """测试审批后上一版本被作废"""
        # 创建第一个版本并生效
        v1 = await version_store.create_version(
            document_id=sample_document_id,
            filename="test.pdf",
            file_hash=sample_file_hash,
            file_size=1024,
            file_type="pdf",
            change_summary="版本1",
            prepared_by="user1",
        )
        # 正确的状态流转: draft -> review -> approved -> effective
        await version_store.update_version_status(v1.id, VersionStatus.REVIEW, "reviewer")
        await version_store.update_version_status(v1.id, VersionStatus.APPROVED, "reviewer")
        await version_store.approve_version(v1.id, "admin")

        # 创建第二个版本并生效
        new_hash = hashlib.sha256(b"new content").hexdigest()
        v2 = await version_store.create_version(
            document_id=sample_document_id,
            filename="test.pdf",
            file_hash=new_hash,
            file_size=1024,
            file_type="pdf",
            change_summary="版本2",
            prepared_by="user1",
        )
        await version_store.update_version_status(v2.id, VersionStatus.REVIEW, "reviewer")
        await version_store.update_version_status(v2.id, VersionStatus.APPROVED, "reviewer")
        await version_store.approve_version(v2.id, "admin")

        # 验证第一个版本被作废
        old_version = await version_store.get_version_by_id(v1.id)
        assert old_version.status == VersionStatus.OBSOLETE
        assert old_version.is_latest is False


class TestObsoleteVersion:
    """测试作废版本功能"""

    @pytest.mark.asyncio
    async def test_obsolete_version(self, version_store, sample_document_id, sample_file_hash):
        """测试作废版本"""
        version = await version_store.create_version(
            document_id=sample_document_id,
            filename="test.pdf",
            file_hash=sample_file_hash,
            file_size=1024,
            file_type="pdf",
            change_summary="测试版本",
            prepared_by="user1",
        )
        # 正确的状态流转: draft -> review -> approved -> effective -> obsolete
        await version_store.update_version_status(version.id, VersionStatus.REVIEW, "user1")
        await version_store.update_version_status(version.id, VersionStatus.APPROVED, "user1")
        await version_store.approve_version(version.id, "admin")

        result = await version_store.obsolete_version(version.id, "admin", "版本作废")
        assert result is True

        updated = await version_store.get_version_by_id(version.id)
        assert updated.status == VersionStatus.OBSOLETE


class TestCompareVersions:
    """测试版本对比功能"""

    @pytest.mark.asyncio
    async def test_compare_versions(self, version_store, sample_document_id):
        """测试对比两个版本"""
        hash1 = hashlib.sha256(b"content1").hexdigest()
        v1 = await version_store.create_version(
            document_id=sample_document_id,
            filename="test.pdf",
            file_hash=hash1,
            file_size=1000,
            file_type="pdf",
            change_summary="版本1",
            prepared_by="user1",
        )

        hash2 = hashlib.sha256(b"content2").hexdigest()
        v2 = await version_store.create_version(
            document_id=sample_document_id,
            filename="test.pdf",
            file_hash=hash2,
            file_size=2000,
            file_type="pdf",
            change_summary="版本2",
            prepared_by="user1",
        )

        diff = await version_store.compare_versions(v1.id, v2.id)
        assert diff.v1_id == v1.id
        assert diff.v2_id == v2.id
        assert diff.v1_version_label == "V1.0"
        assert diff.v2_version_label == "V2.0"
        assert len(diff.modified_chunks) > 0  # 文件大小和哈希都不同

    @pytest.mark.asyncio
    async def test_compare_nonexistent_version(self, version_store, sample_document_id, sample_file_hash):
        """测试对比不存在的版本"""
        v1 = await version_store.create_version(
            document_id=sample_document_id,
            filename="test.pdf",
            file_hash=sample_file_hash,
            file_size=1024,
            file_type="pdf",
            change_summary="版本1",
            prepared_by="user1",
        )

        with pytest.raises(VersionNotFoundError):
            await version_store.compare_versions(v1.id, "non-existent-id")


class TestCheckDuplicate:
    """测试去重检测功能"""

    @pytest.mark.asyncio
    async def test_exact_match(self, version_store, sample_document_id, sample_file_hash):
        """测试完全相同的文件"""
        await version_store.create_version(
            document_id=sample_document_id,
            filename="test.pdf",
            file_hash=sample_file_hash,
            file_size=1024,
            file_type="pdf",
            change_summary="初始版本",
            prepared_by="user1",
        )

        result = await version_store.check_duplicate(sample_file_hash, "other.pdf")
        assert result.type == DuplicateType.EXACT_MATCH
        assert "该文件已存在" in result.message

    @pytest.mark.asyncio
    async def test_name_match(self, version_store, sample_document_id):
        """测试同名不同内容的文件"""
        hash1 = hashlib.sha256(b"content1").hexdigest()
        await version_store.create_version(
            document_id=sample_document_id,
            filename="test.pdf",
            file_hash=hash1,
            file_size=1024,
            file_type="pdf",
            change_summary="初始版本",
            prepared_by="user1",
        )

        hash2 = hashlib.sha256(b"content2").hexdigest()
        result = await version_store.check_duplicate(hash2, "test.pdf")
        assert result.type == DuplicateType.NAME_MATCH
        assert "检测到同名文档" in result.message

    @pytest.mark.asyncio
    async def test_new_file(self, version_store):
        """测试新文件"""
        new_hash = hashlib.sha256(b"new content").hexdigest()
        result = await version_store.check_duplicate(new_hash, "new_file.pdf")
        assert result.type == DuplicateType.NEW_FILE
        assert result.message == "新文件"


class TestVersionStats:
    """测试版本统计功能"""

    @pytest.mark.asyncio
    async def test_get_version_stats(self, version_store, sample_document_id, sample_file_hash):
        """测试获取版本统计信息"""
        # 创建多个版本
        for i in range(3):
            new_hash = hashlib.sha256(f"content{i}".encode()).hexdigest()
            await version_store.create_version(
                document_id=sample_document_id,
                filename="test.pdf",
                file_hash=new_hash,
                file_size=1024,
                file_type="pdf",
                change_summary=f"版本 {i+1}",
                prepared_by="user1",
            )

        stats = await version_store.get_version_stats(sample_document_id)
        assert stats["total_versions"] == 3
        assert stats["by_status"][VersionStatus.DRAFT] == 3
        assert stats["latest_version"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
