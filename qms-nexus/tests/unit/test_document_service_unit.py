"""
服务层单元测试示例：DocumentService
"""
import asyncio
from unittest.mock import Mock, patch, MagicMock
import pytest
from services.document_service import DocumentService
from core.parser_router import ParserRouter


class TestDocumentService:
    """DocumentService 单元测试"""

    def setup_method(self):
        """测试方法设置"""
        self.service = DocumentService()

    @pytest.mark.asyncio
    async def test_process_pdf_success(self):
        """测试PDF处理成功"""
        task_id = "test-task-id"
        file_path = "/tmp/test.pdf"
        content_type = "application/pdf"

        # Mock ParserRouter
        with patch.object(ParserRouter, 'parse', new_callable=MagicMock) as mock_parse:
            mock_parse.return_value = ["Page 1 content", "Page 2 content"]

            # Mock VectorDBClient
            with patch('services.document_service.VectorDBClient') as mock_vdb_class:
                mock_vdb_instance = Mock()
                mock_vdb_instance.insert_documents = Mock()
                mock_vdb_class.return_value = mock_vdb_instance

                # 执行测试
                await self.service.process(task_id, file_path, content_type)

                # 验证调用
                mock_parse.assert_called_once_with(file_path, content_type)
                mock_vdb_instance.insert_documents.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_unsupported_type(self):
        """测试不支持的文件类型"""
        task_id = "test-task-id"
        file_path = "/tmp/test.xyz"
        content_type = "application/unknown"

        # Mock tasks dictionary
        with patch.dict('services.document_service.tasks', {task_id: {"status": "Pending"}}):
            # 执行测试并验证是否会抛出异常或正确处理
            try:
                await self.service.process(task_id, file_path, content_type)
            except Exception:
                pass  # 预期可能会有异常

    @pytest.mark.asyncio
    async def test_process_file_not_found(self):
        """测试文件不存在的情况"""
        task_id = "test-task-id"
        file_path = "/nonexistent/test.pdf"
        content_type = "application/pdf"

        # Mock ParserRouter to raise FileNotFoundError
        with patch.object(ParserRouter, 'parse', side_effect=FileNotFoundError()):
            with patch.dict('services.document_service.tasks', {task_id: {"status": "Pending"}}):
                # 更新任务状态为失败
                with patch('services.document_service.tasks') as mock_tasks:
                    mock_tasks.__setitem__ = Mock()
                    
                    # 执行测试
                    await self.service.process(task_id, file_path, content_type)
                    
                    # 验证状态被设置为失败
                    mock_tasks.__setitem__.assert_called()