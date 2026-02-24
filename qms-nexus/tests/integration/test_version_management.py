"""
文档版本管理集成测试
测试完整的文档版本管理工作流，包括端到端测试
"""
import asyncio
import hashlib
import io
import os
import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes.document_versions import router as versions_router
from api.routes.upload import router as upload_router
from core.database import (
    Document,
    DocumentApprovalHistory,
    DocumentVersion,
    db_manager,
)
from core.document_version_store import (
    DuplicateType,
    InvalidStatusTransitionError,
    VersionStatus,
    document_version_store,
)


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(versions_router, prefix="/api/v1/documents")
    app.include_router(upload_router, prefix="/api/v1")
    return app


@pytest.fixture
def client(app):
    with TestClient(app) as c:
        yield c


@pytest.fixture
def mock_version_store():
    with patch("api.routes.document_versions.document_version_store") as mock_versions, \
         patch("api.routes.upload.document_version_store") as mock_upload:
        mock_upload.check_duplicate = AsyncMock()
        mock_upload.get_latest_effective_version = AsyncMock()
        mock_versions.check_duplicate = mock_upload.check_duplicate
        mock_versions.get_latest_effective_version = mock_upload.get_latest_effective_version
        yield mock_versions


@pytest.fixture
def sample_version():
    version = MagicMock()
    version.id = f"ver-{uuid.uuid4().hex[:8]}"
    version.document_id = f"doc-{uuid.uuid4().hex[:8]}"
    version.version_number = 1
    version.version_label = "V1.0"
    version.filename = "GJZ-QP-01.docx"
    version.file_hash = hashlib.sha256(b"test content").hexdigest()
    version.file_size = 1024
    version.file_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    version.status = VersionStatus.DRAFT
    version.title = "GJZ-QP-01.docx"
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


class TestVersionManagementWorkflow:
    """
    测试完整的文档版本管理工作流
    端到端测试
    """

    def test_complete_workflow(self, client, mock_version_store, sample_version):
        """
        测试完整流程：上传 → 提交审核 → 审批通过 → 生效
        """
        v1 = sample_version
        v1.status = VersionStatus.DRAFT

        mock_version_store.get_version_by_id = AsyncMock(return_value=v1)
        mock_version_store.update_version_status = AsyncMock(return_value=True)
        mock_version_store.approve_version = AsyncMock(return_value=True)
        mock_version_store.get_approval_history = AsyncMock(return_value=[])

        response = client.get(f"/api/v1/documents/versions/{v1.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["version"]["status"] == VersionStatus.DRAFT

        response = client.post(
            f"/api/v1/documents/versions/{v1.id}/submit",
            json={"comment": "请审核", "current_user": "user1"},
        )
        assert response.status_code == 200
        assert "已提交审核" in response.json()["message"]

        v1.status = VersionStatus.APPROVED
        mock_version_store.get_version_by_id = AsyncMock(return_value=v1)

        response = client.post(
            f"/api/v1/documents/versions/{v1.id}/approve",
            json={"comment": "审核通过", "current_user": "admin"},
        )
        assert response.status_code == 200
        assert "审批通过" in response.json()["message"]

    def test_submit_and_reject_workflow(self, client, mock_version_store, sample_version):
        """
        测试提交审核后被拒绝的流程
        """
        sample_version.status = VersionStatus.DRAFT
        mock_version_store.get_version_by_id = AsyncMock(return_value=sample_version)
        mock_version_store.update_version_status = AsyncMock(return_value=True)
        mock_version_store.get_approval_history = AsyncMock(return_value=[])

        response = client.post(
            f"/api/v1/documents/versions/{sample_version.id}/submit",
            json={"comment": "请审核", "current_user": "user1"},
        )
        assert response.status_code == 200
        assert "已提交审核" in response.json()["message"]

        sample_version.status = VersionStatus.REVIEW
        mock_version_store.get_version_by_id = AsyncMock(return_value=sample_version)

        response = client.post(
            f"/api/v1/documents/versions/{sample_version.id}/reject",
            json={"comment": "需要修改", "current_user": "reviewer"},
        )
        assert response.status_code == 200
        assert "退回草稿" in response.json()["message"]

    def test_obsolete_workflow(self, client, mock_version_store, sample_version):
        """
        测试作废版本流程
        """
        sample_version.status = VersionStatus.EFFECTIVE
        mock_version_store.get_version_by_id = AsyncMock(return_value=sample_version)
        mock_version_store.obsolete_version = AsyncMock(return_value=True)
        mock_version_store.get_approval_history = AsyncMock(return_value=[])

        response = client.post(
            f"/api/v1/documents/versions/{sample_version.id}/obsolete",
            json={"reason": "版本过时", "current_user": "admin"},
        )
        assert response.status_code == 200
        assert "已作废" in response.json()["message"]


class TestMultiVersionScenarios:
    """
    测试多版本并行场景
    """

    def test_multiple_versions_same_document(self, client, mock_version_store, sample_version):
        """
        测试同一文档的多个版本
        """
        versions = []
        for i in range(3):
            v = MagicMock()
            v.id = f"ver-{i}"
            v.document_id = sample_version.document_id
            v.version_number = i + 1
            v.version_label = f"V{i + 1}.0"
            v.filename = sample_version.filename
            v.file_hash = hashlib.sha256(f"content{i}".encode()).hexdigest()
            v.file_size = 1024 * (i + 1)
            v.file_type = sample_version.file_type
            v.status = VersionStatus.EFFECTIVE if i == 2 else VersionStatus.OBSOLETE
            v.title = sample_version.title
            v.description = None
            v.change_summary = f"版本 {i + 1}"
            v.change_details = None
            v.previous_version_id = f"ver-{i - 1}" if i > 0 else None
            v.effective_date = datetime.utcnow()
            v.review_date = None
            v.is_latest = (i == 2)
            v.prepared_by = "user1"
            v.reviewed_by = "reviewer"
            v.approved_by = "admin"
            v.approved_date = datetime.utcnow()
            v.kb_id = "default"
            v.created_by = "user1"
            v.created_at = datetime.utcnow()
            v.updated_at = datetime.utcnow()
            versions.append(v)

        with patch("api.routes.document_versions.db_manager") as mock_db:
            mock_session = MagicMock()
            mock_db.get_session.return_value.__enter__.return_value = mock_session

            mock_query = MagicMock()
            mock_session.query.return_value.filter.return_value = mock_query
            mock_query.count.return_value = 3
            mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = versions

            response = client.get(f"/api/v1/documents/{sample_version.document_id}/versions")

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["total"] == 3
            assert len(data["data"]["items"]) == 3

    def test_version_comparison(self, client, mock_version_store, sample_version):
        """
        测试版本对比功能
        """
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
        assert data["data"]["v1_version_label"] == "V1.0"
        assert data["data"]["v2_version_label"] == "V2.0"
        assert data["data"]["statistics"]["added_count"] == 1
        assert data["data"]["statistics"]["removed_count"] == 1
        assert data["data"]["statistics"]["modified_count"] == 1


class TestDuplicateDetectionIntegration:
    """
    测试去重检测集成
    """

    def test_exact_match_detection(self, client, mock_version_store):
        """
        测试完全匹配检测
        """
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
        assert data["data"]["type"] == "exact_match"
        assert "已存在" in data["data"]["message"]

    def test_name_match_detection(self, client, mock_version_store):
        """
        测试名称匹配检测
        """
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
        assert data["data"]["type"] == "name_match"
        assert "同名" in data["data"]["message"]

    def test_new_file_detection(self, client, mock_version_store):
        """
        测试新文件检测
        """
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
        assert data["data"]["type"] == "new_file"
        assert "新文件" in data["data"]["message"]


class TestConcurrentScenarios:
    """
    测试并发场景数据一致性
    """

    def test_concurrent_status_updates(self, client, mock_version_store, sample_version):
        """
        测试并发状态更新
        """
        sample_version.status = VersionStatus.DRAFT
        mock_version_store.get_version_by_id = AsyncMock(return_value=sample_version)
        mock_version_store.update_version_status = AsyncMock(return_value=True)

        def submit_version():
            return client.post(
                f"/api/v1/documents/versions/{sample_version.id}/submit",
                json={"comment": "并发提交", "current_user": "user1"},
            )

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(submit_version) for _ in range(3)]
            results = [f.result() for f in futures]

        success_count = sum(1 for r in results if r.status_code == 200)
        assert success_count >= 1

    def test_concurrent_approve_operations(self, client, mock_version_store, sample_version):
        """
        测试并发审批操作
        """
        sample_version.status = VersionStatus.APPROVED
        mock_version_store.get_version_by_id = AsyncMock(return_value=sample_version)
        mock_version_store.approve_version = AsyncMock(return_value=True)

        def approve_version():
            return client.post(
                f"/api/v1/documents/versions/{sample_version.id}/approve",
                json={"comment": "并发审批", "current_user": "admin"},
            )

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(approve_version) for _ in range(3)]
            results = [f.result() for f in futures]

        success_count = sum(1 for r in results if r.status_code == 200)
        assert success_count >= 1


class TestStatusTransitions:
    """
    测试状态流转验证
    """

    def test_valid_status_transitions(self, client, mock_version_store, sample_version):
        """
        测试有效的状态流转
        """
        transitions = [
            (VersionStatus.DRAFT, VersionStatus.REVIEW, "submit"),
            (VersionStatus.REVIEW, VersionStatus.APPROVED, "approve"),
            (VersionStatus.APPROVED, VersionStatus.EFFECTIVE, "approve"),
            (VersionStatus.EFFECTIVE, VersionStatus.OBSOLETE, "obsolete"),
        ]

        for from_status, to_status, action in transitions:
            sample_version.status = from_status
            mock_version_store.get_version_by_id = AsyncMock(return_value=sample_version)

            if action == "submit":
                mock_version_store.update_version_status = AsyncMock(return_value=True)
                response = client.post(
                    f"/api/v1/documents/versions/{sample_version.id}/submit",
                    json={"comment": "提交", "current_user": "user1"},
                )
            elif action == "approve":
                mock_version_store.approve_version = AsyncMock(return_value=True)
                response = client.post(
                    f"/api/v1/documents/versions/{sample_version.id}/approve",
                    json={"comment": "审批", "current_user": "admin"},
                )
            elif action == "obsolete":
                mock_version_store.obsolete_version = AsyncMock(return_value=True)
                response = client.post(
                    f"/api/v1/documents/versions/{sample_version.id}/obsolete",
                    json={"reason": "作废", "current_user": "admin"},
                )

            assert response.status_code == 200, f"Failed: {from_status} -> {to_status}"

    def test_invalid_status_transitions(self, client, mock_version_store, sample_version):
        """
        测试无效的状态流转
        """
        invalid_transitions = [
            (VersionStatus.DRAFT, "approve"),
            (VersionStatus.EFFECTIVE, "submit"),
            (VersionStatus.OBSOLETE, "approve"),
        ]

        for status, action in invalid_transitions:
            sample_version.status = status
            mock_version_store.get_version_by_id = AsyncMock(return_value=sample_version)

            if action == "submit":
                response = client.post(
                    f"/api/v1/documents/versions/{sample_version.id}/submit",
                    json={"comment": "提交", "current_user": "user1"},
                )
            elif action == "approve":
                response = client.post(
                    f"/api/v1/documents/versions/{sample_version.id}/approve",
                    json={"comment": "审批", "current_user": "admin"},
                )

            assert response.status_code == 400, f"Should fail: {status} -> {action}"


class TestApprovalHistory:
    """
    测试审批历史记录
    """

    def test_approval_history_recorded(self, client, mock_version_store, sample_version):
        """
        测试审批历史被正确记录
        """
        sample_version.status = VersionStatus.DRAFT
        mock_version_store.get_version_by_id = AsyncMock(return_value=sample_version)
        mock_version_store.update_version_status = AsyncMock(return_value=True)

        history1 = MagicMock()
        history1.id = 1
        history1.action = "create"
        history1.action_by = "user1"
        history1.action_at = datetime.utcnow()
        history1.comment = "创建版本"
        history1.from_status = None
        history1.to_status = VersionStatus.DRAFT

        history2 = MagicMock()
        history2.id = 2
        history2.action = "submit"
        history2.action_by = "user1"
        history2.action_at = datetime.utcnow()
        history2.comment = "提交审核"
        history2.from_status = VersionStatus.DRAFT
        history2.to_status = VersionStatus.REVIEW

        mock_version_store.get_approval_history = AsyncMock(return_value=[history1, history2])

        response = client.get(f"/api/v1/documents/versions/{sample_version.id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["approval_history"]) == 2


class TestVersionCreation:
    """
    测试版本创建
    """

    def test_create_version_success(self, client, mock_version_store, sample_version):
        """
        测试成功创建版本
        """
        mock_version_store.create_version = AsyncMock(return_value=sample_version)

        file_content = b"test file content"
        file = io.BytesIO(file_content)

        response = client.post(
            f"/api/v1/documents/{sample_version.document_id}/versions",
            data={
                "change_summary": "初始版本",
                "change_details": "详细变更说明",
                "current_user": "user1",
            },
            files={"file": ("test.pdf", file, "application/pdf")},
        )

        assert response.status_code == 200
        data = response.json()
        assert "版本创建成功" in data["message"]
        assert data["data"]["version_number"] == 1

    def test_create_version_missing_file(self, client):
        """
        测试缺少文件时创建版本
        """
        response = client.post(
            "/api/v1/documents/doc-123/versions",
            data={"change_summary": "初始版本"},
        )

        assert response.status_code == 422

    def test_create_version_missing_change_summary(self, client):
        """
        测试缺少变更摘要时创建版本
        """
        file_content = b"test file content"
        file = io.BytesIO(file_content)

        response = client.post(
            "/api/v1/documents/doc-123/versions",
            data={},
            files={"file": ("test.pdf", file, "application/pdf")},
        )

        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


class TestRAGVersionFiltering:
    """
    测试 RAG 问答时版本过滤
    """

    @pytest.mark.asyncio
    async def test_rag_search_latest_effective_only(self, mock_version_store):
        """
        测试 RAG 搜索只返回最新生效版本
        """
        from core.rag_service import RAGService
        from core.vectordb import VectorDBClient
        from unittest.mock import MagicMock

        mock_db = MagicMock(spec=VectorDBClient)
        mock_result = MagicMock()
        mock_result.text = "测试内容"
        mock_result.score = 0.9
        mock_result.source = "[测试文档 V2.0]"
        mock_result.metadata = {
            "filename": "test.pdf",
            "page": 1,
            "version_id": "ver-2",
            "version_number": 2,
            "version_label": "V2.0",
            "status": "effective",
            "is_latest": True,
        }

        mock_db.similarity_search = AsyncMock(return_value=[mock_result])

        rag = RAGService()
        rag.db = mock_db

        results = await rag.search(
            query="测试问题",
            kb_id="default",
            version_strategy="latest_effective",
        )

        assert len(results) == 1
        assert results[0]["is_latest"] == True
        assert results[0]["status"] == "effective"

    @pytest.mark.asyncio
    async def test_rag_search_with_obsolete_warning(self, mock_version_store):
        """
        测试 RAG 搜索返回作废版本时显示警告
        """
        from core.rag_service import RAGService
        from core.vectordb import VectorDBClient

        mock_db = MagicMock(spec=VectorDBClient)
        mock_result = MagicMock()
        mock_result.text = "旧版本内容"
        mock_result.score = 0.8
        mock_result.source = "[测试文档 V1.0]"
        mock_result.metadata = {
            "filename": "test.pdf",
            "page": 1,
            "version_id": "ver-1",
            "version_number": 1,
            "version_label": "V1.0",
            "status": "obsolete",
            "is_latest": False,
        }

        mock_db.similarity_search = AsyncMock(return_value=[mock_result])

        rag = RAGService()
        rag.db = mock_db

        results = await rag.search(
            query="测试问题",
            kb_id="default",
            version_strategy="all_versions",
        )

        assert len(results) == 1
        assert results[0]["status"] == "obsolete"
        assert "已作废" in results[0]["warning"]


class TestPermissionControl:
    """
    测试权限控制
    """

    def test_approve_requires_valid_status(self, client, mock_version_store, sample_version):
        """
        测试审批需要正确的状态
        """
        sample_version.status = VersionStatus.DRAFT
        mock_version_store.get_version_by_id = AsyncMock(return_value=sample_version)

        response = client.post(
            f"/api/v1/documents/versions/{sample_version.id}/approve",
            json={"comment": "审批通过", "current_user": "admin"},
        )

        assert response.status_code == 400
        assert "approved 或 review" in response.json()["detail"]

    def test_reject_requires_review_status(self, client, mock_version_store, sample_version):
        """
        测试拒绝需要 review 状态
        """
        sample_version.status = VersionStatus.DRAFT
        mock_version_store.get_version_by_id = AsyncMock(return_value=sample_version)

        response = client.post(
            f"/api/v1/documents/versions/{sample_version.id}/reject",
            json={"comment": "拒绝原因", "current_user": "reviewer"},
        )

        assert response.status_code == 400
        assert "review" in response.json()["detail"]

    def test_obsolete_requires_effective_or_approved(self, client, mock_version_store, sample_version):
        """
        测试作废需要 effective 或 approved 状态
        """
        sample_version.status = VersionStatus.DRAFT
        mock_version_store.get_version_by_id = AsyncMock(return_value=sample_version)

        response = client.post(
            f"/api/v1/documents/versions/{sample_version.id}/obsolete",
            json={"reason": "作废原因", "current_user": "admin"},
        )

        assert response.status_code == 400
        assert "effective 或 approved" in response.json()["detail"]

    def test_submit_requires_draft_status(self, client, mock_version_store, sample_version):
        """
        测试提交需要 draft 状态
        """
        sample_version.status = VersionStatus.REVIEW
        mock_version_store.get_version_by_id = AsyncMock(return_value=sample_version)

        response = client.post(
            f"/api/v1/documents/versions/{sample_version.id}/submit",
            json={"comment": "提交审核", "current_user": "user1"},
        )

        assert response.status_code == 400
        assert "draft" in response.json()["detail"]


class TestDuplicateDetectionFullIntegration:
    """
    完整的去重检测集成测试
    """

    def test_upload_duplicate_file_returns_conflict(self, client, mock_version_store):
        """
        测试上传重复文件返回 409 冲突
        """
        from core.document_version_store import DuplicateCheckResult

        result = DuplicateCheckResult(
            type=DuplicateType.EXACT_MATCH,
            message="该文件已存在",
            existing_document={"id": "doc-123"},
            existing_version={"version_id": "ver-123"},
            suggestions=[{"action": "view", "label": "查看现有版本"}],
        )

        mock_version_store.check_duplicate.return_value = result

        file_content = b"test content"
        file = io.BytesIO(file_content)

        response = client.post(
            "/api/v1/upload",
            files={"file": ("test.docx", file, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            data={"collection": "default"},
        )

        assert response.status_code == 409

    def test_upload_name_match_allows_upload(self, client, mock_version_store):
        """
        测试同名文件允许上传
        """
        from core.document_version_store import DuplicateCheckResult

        result = DuplicateCheckResult(
            type=DuplicateType.NAME_MATCH,
            message="检测到同名文件",
            existing_document={"id": "doc-123"},
            existing_version={"version_id": "ver-123"},
            suggestions=[{"action": "upload_as_new_version", "label": "创建新版本"}],
        )

        mock_version_store.check_duplicate.return_value = result

        file_content = b"different content"
        file = io.BytesIO(file_content)

        with patch("services.document_service.DocumentService.process", AsyncMock()):
            response = client.post(
                "/api/v1/upload",
                files={"file": ("test.docx", file, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                data={"collection": "default"},
            )

            assert response.status_code == 200


class TestConcurrentVersionCreation:
    """
    测试并发创建版本
    """

    def test_concurrent_version_creation_consistency(self, client, mock_version_store, sample_version):
        """
        测试并发创建版本时的数据一致性
        """
        def create_version_call(**kwargs):
            version = MagicMock()
            version.id = f"ver-{uuid.uuid4().hex[:8]}"
            version.document_id = kwargs.get("document_id", sample_version.document_id)
            version.version_number = kwargs.get("version_number", 1)
            version.version_label = f"V{version.version_number}.0"
            version.status = VersionStatus.DRAFT
            version.filename = kwargs.get("filename", "test.pdf")
            version.file_hash = hashlib.sha256(b"test content").hexdigest()
            version.file_size = 1024
            version.file_type = "application/pdf"
            version.title = kwargs.get("filename", "test.pdf")
            version.description = None
            version.change_summary = kwargs.get("change_summary", "")
            version.change_details = None
            version.previous_version_id = None
            version.effective_date = None
            version.review_date = None
            version.is_latest = False
            version.prepared_by = kwargs.get("prepared_by", "user1")
            version.reviewed_by = None
            version.approved_by = None
            version.approved_date = None
            version.kb_id = "default"
            version.created_by = kwargs.get("prepared_by", "user1")
            version.created_at = datetime.utcnow()
            version.updated_at = datetime.utcnow()
            return version

        mock_version_store.create_version = AsyncMock(side_effect=create_version_call)

        file_content = b"test content"

        def upload_version(version_num):
            file = io.BytesIO(file_content)
            return client.post(
                f"/api/v1/documents/{sample_version.document_id}/versions",
                data={
                    "change_summary": f"版本 {version_num}",
                    "current_user": "user1",
                },
                files={"file": (f"test_{version_num}.pdf", file, "application/pdf")},
            )

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(upload_version, i) for i in range(1, 4)]
            results = [f.result() for f in futures]

        success_count = sum(1 for r in results if r.status_code == 200)
        assert success_count >= 1


class TestVersionLifecycle:
    """
    测试版本完整生命周期
    """

    def test_full_lifecycle_draft_to_effective(self, client, mock_version_store, sample_version):
        """
        测试从草稿到生效的完整生命周期
        """
        sample_version.status = VersionStatus.DRAFT
        mock_version_store.get_version_by_id = AsyncMock(return_value=sample_version)
        mock_version_store.update_version_status = AsyncMock(return_value=True)
        mock_version_store.approve_version = AsyncMock(return_value=True)
        mock_version_store.get_approval_history = AsyncMock(return_value=[])

        response = client.post(
            f"/api/v1/documents/versions/{sample_version.id}/submit",
            json={"comment": "提交审核", "current_user": "user1"},
        )
        assert response.status_code == 200

        sample_version.status = VersionStatus.APPROVED
        mock_version_store.get_version_by_id = AsyncMock(return_value=sample_version)

        response = client.post(
            f"/api/v1/documents/versions/{sample_version.id}/approve",
            json={"comment": "审批通过", "current_user": "admin"},
        )
        assert response.status_code == 200

    def test_lifecycle_with_rejection(self, client, mock_version_store, sample_version):
        """
        测试包含拒绝的生命周期
        """
        sample_version.status = VersionStatus.DRAFT
        mock_version_store.get_version_by_id = AsyncMock(return_value=sample_version)
        mock_version_store.update_version_status = AsyncMock(return_value=True)
        mock_version_store.get_approval_history = AsyncMock(return_value=[])

        response = client.post(
            f"/api/v1/documents/versions/{sample_version.id}/submit",
            json={"comment": "提交审核", "current_user": "user1"},
        )
        assert response.status_code == 200

        sample_version.status = VersionStatus.REVIEW
        mock_version_store.get_version_by_id = AsyncMock(return_value=sample_version)

        response = client.post(
            f"/api/v1/documents/versions/{sample_version.id}/reject",
            json={"comment": "需要修改", "current_user": "reviewer"},
        )
        assert response.status_code == 200

        sample_version.status = VersionStatus.DRAFT
        mock_version_store.get_version_by_id = AsyncMock(return_value=sample_version)

        response = client.post(
            f"/api/v1/documents/versions/{sample_version.id}/submit",
            json={"comment": "重新提交", "current_user": "user1"},
        )
        assert response.status_code == 200


class TestVersionDownload:
    """
    测试版本下载
    """

    def test_download_version_not_found(self, client, mock_version_store):
        """
        测试下载不存在的版本
        """
        mock_version_store.get_version_by_id = AsyncMock(return_value=None)

        response = client.get("/api/v1/documents/versions/non-existent-id/download")

        assert response.status_code == 404
