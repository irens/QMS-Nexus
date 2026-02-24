"""
文档版本管理 API 单元测试
"""
import hashlib
import io
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from fastapi import FastAPI, UploadFile

from api.routes.document_versions import router as versions_router, _version_to_out, _approval_history_to_out
from api.routes.upload import router as upload_router
from core.document_version_store import (
    DocumentVersionStore,
    VersionStatus,
    DuplicateType,
    InvalidStatusTransitionError,
    VersionNotFoundError,
)


# 创建测试应用
@pytest.fixture
def app():
    """创建测试用的 FastAPI 应用"""
    app = FastAPI()
    app.include_router(versions_router, prefix="/api/v1/documents")
    app.include_router(upload_router, prefix="/api/v1")
    return app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
def mock_version_store():
    """创建模拟的 DocumentVersionStore"""
    with patch("api.routes.document_versions.document_version_store") as mock_versions, \
         patch("api.routes.upload.document_version_store") as mock_upload:
        # 为两个路由的 store 创建相同的 mock 方法
        mock_upload.check_duplicate = AsyncMock()
        mock_upload.get_latest_effective_version = AsyncMock()
        # 将 upload 的 mock 方法引用到 versions 的 mock 上，方便测试时统一设置
        mock_versions.check_duplicate = mock_upload.check_duplicate
        mock_versions.get_latest_effective_version = mock_upload.get_latest_effective_version
        yield mock_versions


@pytest.fixture
def sample_version():
    """示例版本数据"""
    version = MagicMock()
    version.id = "ver-123456"
    version.document_id = "doc-123456"
    version.version_number = 1
    version.version_label = "V1.0"
    version.filename = "test.pdf"
    version.file_hash = hashlib.sha256(b"test").hexdigest()
    version.file_size = 1024
    version.file_type = "application/pdf"
    version.status = VersionStatus.DRAFT
    version.title = "test.pdf"
    version.description = None
    version.change_summary = "初始版本"
    version.change_details = None
    version.previous_version_id = None
    version.effective_date = None
    version.review_date = None
    version.is_latest = False
    version.prepared_by = "user1"
    version.reviewed_by = None
    version.approved_by = None
    version.approved_date = None
    version.kb_id = "default"
    version.created_by = "user1"
    version.created_at = datetime.utcnow()
    version.updated_at = datetime.utcnow()
    return version


@pytest.fixture
def sample_approval_history():
    """示例审批历史数据"""
    history = MagicMock()
    history.id = 1
    history.action = "create"
    history.action_by = "user1"
    history.action_at = datetime.utcnow()
    history.comment = "创建版本"
    history.from_status = None
    history.to_status = VersionStatus.DRAFT
    return history


class TestCreateVersion:
    """测试创建版本 API"""

    def test_create_version_success(self, client, mock_version_store, sample_version):
        """测试成功创建版本"""
        mock_version_store.create_version = AsyncMock(return_value=sample_version)

        # 创建测试文件
        file_content = b"test file content"
        file = io.BytesIO(file_content)

        response = client.post(
            "/api/v1/documents/doc-123456/versions",
            data={
                "change_summary": "初始版本",
                "change_details": "详细变更说明",
                "current_user": "user1",
            },
            files={"file": ("test.pdf", file, "application/pdf")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "版本创建成功" in data["message"]
        assert data["data"]["version_number"] == 1
        assert data["data"]["version_label"] == "V1.0"
        assert data["data"]["status"] == VersionStatus.DRAFT

    def test_create_version_missing_file(self, client):
        """测试缺少文件时创建版本"""
        response = client.post(
            "/api/v1/documents/doc-123456/versions",
            data={"change_summary": "初始版本"},
        )

        assert response.status_code == 422  # FastAPI 验证错误

    def test_create_version_missing_change_summary(self, client):
        """测试缺少变更摘要时创建版本"""
        file_content = b"test file content"
        file = io.BytesIO(file_content)

        response = client.post(
            "/api/v1/documents/doc-123456/versions",
            data={},
            files={"file": ("test.pdf", file, "application/pdf")},
        )

        assert response.status_code == 422  # FastAPI 验证错误


class TestListVersions:
    """测试获取版本列表 API"""

    def test_list_versions_success(self, client, mock_version_store, sample_version):
        """测试成功获取版本列表"""
        # 模拟数据库查询
        with patch("api.routes.document_versions.db_manager") as mock_db:
            mock_session = MagicMock()
            mock_db.get_session.return_value.__enter__.return_value = mock_session

            # 模拟查询结果
            mock_query = MagicMock()
            mock_session.query.return_value.filter.return_value = mock_query
            mock_query.count.return_value = 2
            mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
                sample_version,
                sample_version,
            ]

            response = client.get("/api/v1/documents/doc-123456/versions")

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["data"]["total"] == 2
            assert len(data["data"]["items"]) == 2

    def test_list_versions_with_status_filter(self, client, mock_version_store, sample_version):
        """测试按状态筛选版本列表"""
        with patch("api.routes.document_versions.db_manager") as mock_db:
            mock_session = MagicMock()
            mock_db.get_session.return_value.__enter__.return_value = mock_session

            mock_query = MagicMock()
            mock_session.query.return_value.filter.return_value.filter.return_value = mock_query
            mock_query.count.return_value = 1
            mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
                sample_version
            ]

            response = client.get("/api/v1/documents/doc-123456/versions?status=draft")

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["data"]["total"] == 1

    def test_list_versions_with_pagination(self, client, mock_version_store, sample_version):
        """测试版本列表分页"""
        with patch("api.routes.document_versions.db_manager") as mock_db:
            mock_session = MagicMock()
            mock_db.get_session.return_value.__enter__.return_value = mock_session

            mock_query = MagicMock()
            mock_session.query.return_value.filter.return_value = mock_query
            mock_query.count.return_value = 25
            mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
                sample_version
            ]

            response = client.get("/api/v1/documents/doc-123456/versions?page=2&page_size=10")

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 200
            assert data["data"]["page"] == 2
            assert data["data"]["page_size"] == 10
            assert data["data"]["total_pages"] == 3


class TestGetVersionDetail:
    """测试获取版本详情 API"""

    def test_get_version_detail_success(self, client, mock_version_store, sample_version, sample_approval_history):
        """测试成功获取版本详情"""
        mock_version_store.get_version_by_id = AsyncMock(return_value=sample_version)
        mock_version_store.get_approval_history = AsyncMock(return_value=[sample_approval_history])

        response = client.get("/api/v1/documents/versions/ver-123456")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["version"]["id"] == "ver-123456"
        assert data["data"]["version"]["version_number"] == 1
        assert len(data["data"]["approval_history"]) == 1

    def test_get_version_detail_not_found(self, client, mock_version_store):
        """测试获取不存在的版本详情"""
        mock_version_store.get_version_by_id = AsyncMock(return_value=None)

        response = client.get("/api/v1/documents/versions/non-existent-id")

        assert response.status_code == 404
        data = response.json()
        assert "版本不存在" in data["detail"]


class TestApproveVersion:
    """测试审批通过版本 API"""

    def test_approve_version_success(self, client, mock_version_store, sample_version):
        """测试成功审批版本"""
        sample_version.status = VersionStatus.APPROVED

        mock_version_store.get_version_by_id = AsyncMock(return_value=sample_version)
        mock_version_store.approve_version = AsyncMock(return_value=True)

        response = client.post(
            "/api/v1/documents/versions/ver-123456/approve",
            json={"comment": "批准发布", "current_user": "admin"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "审批通过" in data["message"]
        assert data["data"]["status"] == "effective"

    def test_approve_version_wrong_status(self, client, mock_version_store, sample_version):
        """测试在错误状态下审批版本"""
        sample_version.status = VersionStatus.DRAFT

        mock_version_store.get_version_by_id = AsyncMock(return_value=sample_version)

        response = client.post(
            "/api/v1/documents/versions/ver-123456/approve",
            json={"comment": "批准发布", "current_user": "admin"},
        )

        assert response.status_code == 400
        data = response.json()
        assert "approved 或 review" in data["detail"]

    def test_approve_version_not_found(self, client, mock_version_store):
        """测试审批不存在的版本"""
        mock_version_store.get_version_by_id = AsyncMock(return_value=None)

        response = client.post(
            "/api/v1/documents/versions/non-existent-id/approve",
            json={"comment": "批准发布", "current_user": "admin"},
        )

        assert response.status_code == 404
        data = response.json()
        assert "版本不存在" in data["detail"]


class TestRejectVersion:
    """测试审批拒绝版本 API"""

    def test_reject_version_success(self, client, mock_version_store, sample_version):
        """测试成功拒绝版本"""
        sample_version.status = VersionStatus.REVIEW

        mock_version_store.get_version_by_id = AsyncMock(return_value=sample_version)
        mock_version_store.update_version_status = AsyncMock(return_value=True)

        response = client.post(
            "/api/v1/documents/versions/ver-123456/reject",
            json={"comment": "需要修改", "current_user": "reviewer"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "退回草稿" in data["message"]
        assert data["data"]["status"] == "draft"

    def test_reject_version_missing_comment(self, client, mock_version_store, sample_version):
        """测试拒绝时缺少原因"""
        sample_version.status = VersionStatus.REVIEW
        mock_version_store.get_version_by_id = AsyncMock(return_value=sample_version)

        response = client.post(
            "/api/v1/documents/versions/ver-123456/reject",
            json={"current_user": "reviewer"},
        )

        assert response.status_code == 422

    def test_reject_version_wrong_status(self, client, mock_version_store, sample_version):
        """测试在错误状态下拒绝版本"""
        sample_version.status = VersionStatus.DRAFT

        mock_version_store.get_version_by_id = AsyncMock(return_value=sample_version)

        response = client.post(
            "/api/v1/documents/versions/ver-123456/reject",
            json={"comment": "需要修改", "current_user": "reviewer"},
        )

        assert response.status_code == 400
        data = response.json()
        assert "review" in data["detail"]


class TestObsoleteVersion:
    """测试作废版本 API"""

    def test_obsolete_version_success(self, client, mock_version_store, sample_version):
        """测试成功作废版本"""
        sample_version.status = VersionStatus.EFFECTIVE

        mock_version_store.get_version_by_id = AsyncMock(return_value=sample_version)
        mock_version_store.obsolete_version = AsyncMock(return_value=True)

        response = client.post(
            "/api/v1/documents/versions/ver-123456/obsolete",
            json={"reason": "版本过时", "current_user": "admin"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "已作废" in data["message"]
        assert data["data"]["status"] == "obsolete"

    def test_obsolete_version_wrong_status(self, client, mock_version_store, sample_version):
        """测试在错误状态下作废版本"""
        sample_version.status = VersionStatus.DRAFT

        mock_version_store.get_version_by_id = AsyncMock(return_value=sample_version)

        response = client.post(
            "/api/v1/documents/versions/ver-123456/obsolete",
            json={"reason": "版本过时", "current_user": "admin"},
        )

        assert response.status_code == 400
        data = response.json()
        assert "effective 或 approved" in data["detail"]


class TestCompareVersions:
    """测试版本对比 API"""

    def test_compare_versions_success(self, client, mock_version_store):
        """测试成功对比版本"""
        from core.document_version_store import VersionDiff

        diff_result = VersionDiff(
            v1_id="ver-1",
            v2_id="ver-2",
            v1_version_label="V1.0",
            v2_version_label="V2.0",
            added_chunks=[{"type": "text", "content": "新增内容"}],
            removed_chunks=[{"type": "text", "content": "删除内容"}],
            modified_chunks=[{"type": "text", "v1": "旧内容", "v2": "新内容"}],
            change_summary="从 V1.0 升级到 V2.0",
        )

        mock_version_store.compare_versions = AsyncMock(return_value=diff_result)

        response = client.get("/api/v1/documents/versions/ver-1/compare/ver-2")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["v1_version_label"] == "V1.0"
        assert data["data"]["v2_version_label"] == "V2.0"
        assert data["data"]["statistics"]["added_count"] == 1
        assert data["data"]["statistics"]["removed_count"] == 1
        assert data["data"]["statistics"]["modified_count"] == 1

    def test_compare_versions_not_found(self, client, mock_version_store):
        """测试对比不存在的版本"""
        mock_version_store.compare_versions = AsyncMock(
            side_effect=VersionNotFoundError("版本不存在")
        )

        response = client.get("/api/v1/documents/versions/ver-1/compare/ver-2")

        assert response.status_code == 404


class TestSubmitVersion:
    """测试提交审核 API"""

    def test_submit_version_success(self, client, mock_version_store, sample_version):
        """测试成功提交版本审核"""
        mock_version_store.get_version_by_id = AsyncMock(return_value=sample_version)
        mock_version_store.update_version_status = AsyncMock(return_value=True)

        response = client.post(
            "/api/v1/documents/versions/ver-123456/submit",
            json={"comment": "请审核", "current_user": "user1"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "已提交审核" in data["message"]
        assert data["data"]["status"] == "review"

    def test_submit_version_wrong_status(self, client, mock_version_store, sample_version):
        """测试在错误状态下提交审核"""
        sample_version.status = VersionStatus.REVIEW

        mock_version_store.get_version_by_id = AsyncMock(return_value=sample_version)

        response = client.post(
            "/api/v1/documents/versions/ver-123456/submit",
            json={"comment": "请审核", "current_user": "user1"},
        )

        assert response.status_code == 400
        data = response.json()
        assert "draft" in data["detail"]


class TestCheckDuplicateAPI:
    """测试去重检测 API"""

    def test_check_duplicate_exact_match(self, client, mock_version_store):
        """测试去重检测 - 完全匹配"""
        from core.document_version_store import DuplicateCheckResult

        result = DuplicateCheckResult(
            type=DuplicateType.EXACT_MATCH,
            message="该文件已存在，内容与现有版本完全相同",
            existing_document={
                "id": "doc-123",
                "title": "测试文档",
                "current_version": {
                    "version_id": "ver-123",
                    "version_number": 1,
                    "version_label": "V1.0",
                    "status": "effective"
                }
            },
            existing_version={
                "version_id": "ver-123",
                "version_number": 1,
                "version_label": "V1.0",
                "status": "effective",
                "file_hash": "abc123"
            },
            suggestions=[
                {"action": "view", "label": "查看现有版本"},
                {"action": "upload_as_new_version", "label": "作为新版本上传"},
            ]
        )

        mock_version_store.check_duplicate.return_value = result

        response = client.post(
            "/api/v1/upload/check-duplicate",
            json={
                "file_hash": "abc123",
                "filename": "test.docx",
                "kb_id": "default"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["type"] == "exact_match"
        assert "该文件已存在" in data["data"]["message"]
        assert "existing_document" in data["data"]
        assert "suggestions" in data["data"]
        assert len(data["data"]["suggestions"]) == 2

    def test_check_duplicate_name_match(self, client, mock_version_store):
        """测试去重检测 - 名称匹配"""
        from core.document_version_store import DuplicateCheckResult

        result = DuplicateCheckResult(
            type=DuplicateType.NAME_MATCH,
            message="检测到同名文件，内容不同",
            existing_document={
                "id": "doc-123",
                "title": "测试文档",
                "current_version": {
                    "version_id": "ver-123",
                    "version_number": 1,
                    "version_label": "V1.0",
                    "status": "effective"
                }
            },
            existing_version={
                "version_id": "ver-123",
                "version_number": 1,
                "version_label": "V1.0",
                "status": "effective"
            },
            suggestions=[
                {"action": "upload_as_new_version", "label": "创建为新版本 V2.0"},
                {"action": "rename", "label": "重命名后上传"},
            ]
        )

        mock_version_store.check_duplicate.return_value = result

        response = client.post(
            "/api/v1/upload/check-duplicate",
            json={
                "file_hash": "different_hash",
                "filename": "test.docx",
                "kb_id": "default"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["type"] == "name_match"
        assert "同名" in data["data"]["message"]

    def test_check_duplicate_new_file(self, client, mock_version_store):
        """测试去重检测 - 新文件"""
        from core.document_version_store import DuplicateCheckResult

        result = DuplicateCheckResult(
            type=DuplicateType.NEW_FILE,
            message="新文件，可以上传",
            existing_document=None,
            existing_version=None,
            suggestions=[
                {"action": "upload", "label": "继续上传"},
            ]
        )

        mock_version_store.check_duplicate.return_value = result

        response = client.post(
            "/api/v1/upload/check-duplicate",
            json={
                "file_hash": "new_hash",
                "filename": "new_file.docx",
                "kb_id": "default"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["type"] == "new_file"
        assert "新文件" in data["data"]["message"]

    def test_check_duplicate_missing_params(self, client):
        """测试去重检测缺少参数"""
        response = client.post(
            "/api/v1/upload/check-duplicate",
            json={}
        )

        assert response.status_code == 422  # FastAPI 验证错误


class TestHelperFunctions:
    """测试辅助函数"""

    def test_version_to_out(self, sample_version):
        """测试版本对象转换"""
        result = _version_to_out(sample_version)

        assert result.id == sample_version.id
        assert result.version_number == sample_version.version_number
        assert result.version_label == sample_version.version_label
        assert result.status == sample_version.status
        assert result.filename == sample_version.filename

    def test_approval_history_to_out(self, sample_approval_history):
        """测试审批历史对象转换"""
        result = _approval_history_to_out(sample_approval_history)

        assert result["id"] == sample_approval_history.id
        assert result["action"] == sample_approval_history.action
        assert result["action_by"] == sample_approval_history.action_by
        assert result["from_status"] == sample_approval_history.from_status
        assert result["to_status"] == sample_approval_history.to_status


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
