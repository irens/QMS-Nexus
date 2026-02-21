"""
知识库服务单元测试
"""
import pytest
import tempfile
import shutil
from pathlib import Path

from core.knowledge_base import KnowledgeBaseService


@pytest.fixture
def temp_kb_service():
    """创建临时的知识库服务"""
    temp_dir = tempfile.mkdtemp()
    
    # 临时修改数据库路径
    import core.knowledge_base as kb_module
    original_path = kb_module.DB_PATH
    kb_module.DB_PATH = Path(temp_dir) / "knowledge_bases.db"
    
    service = KnowledgeBaseService()
    
    yield service
    
    # 清理
    kb_module.DB_PATH = original_path
    shutil.rmtree(temp_dir)


class TestKnowledgeBaseService:
    """知识库服务测试类"""
    
    def test_create_kb(self, temp_kb_service):
        """测试创建知识库"""
        success = temp_kb_service.create_kb(
            kb_id="hr_docs",
            name="人力资源文档",
            description="公司人力资源相关文档"
        )
        
        assert success is True
    
    def test_create_kb_invalid_id(self, temp_kb_service):
        """测试创建知识库（无效ID）"""
        with pytest.raises(ValueError):
            temp_kb_service.create_kb(
                kb_id="123_invalid",  # 以数字开头
                name="测试"
            )
    
    def test_create_duplicate_kb(self, temp_kb_service):
        """测试创建重复的知识库"""
        temp_kb_service.create_kb(kb_id="test_kb", name="测试")
        
        # 再次创建相同的 ID
        success = temp_kb_service.create_kb(kb_id="test_kb", name="测试2")
        assert success is False
    
    def test_get_kb(self, temp_kb_service):
        """测试获取知识库"""
        # 创建知识库
        temp_kb_service.create_kb(
            kb_id="legal_docs",
            name="法律文档",
            description="法律相关文档"
        )
        
        # 获取知识库
        kb = temp_kb_service.get_kb("legal_docs")
        
        assert kb is not None
        assert kb["name"] == "法律文档"
        assert kb["collection_name"] == "kb_legal_docs"
    
    def test_get_nonexistent_kb(self, temp_kb_service):
        """测试获取不存在的知识库"""
        kb = temp_kb_service.get_kb("nonexistent")
        assert kb is None
    
    def test_list_kbs(self, temp_kb_service):
        """测试列出知识库"""
        # 创建多个知识库
        temp_kb_service.create_kb(kb_id="kb1", name="知识库1")
        temp_kb_service.create_kb(kb_id="kb2", name="知识库2")
        
        # 列出知识库
        kbs = temp_kb_service.list_kbs()
        
        # 包含默认知识库 + 新建的2个
        assert len(kbs) >= 3
    
    def test_update_kb(self, temp_kb_service):
        """测试更新知识库"""
        # 创建知识库
        temp_kb_service.create_kb(kb_id="update_test", name="原名称")
        
        # 更新知识库
        success = temp_kb_service.update_kb(
            kb_id="update_test",
            name="新名称",
            description="新描述"
        )
        
        assert success is True
        
        # 验证更新
        kb = temp_kb_service.get_kb("update_test")
        assert kb["name"] == "新名称"
        assert kb["description"] == "新描述"
    
    def test_delete_kb(self, temp_kb_service):
        """测试删除知识库（软删除）"""
        # 创建知识库
        temp_kb_service.create_kb(kb_id="delete_test", name="待删除")
        
        # 删除知识库
        success = temp_kb_service.delete_kb("delete_test")
        assert success is True
        
        # 验证已删除（在活跃列表中找不到）
        kb = temp_kb_service.get_kb("delete_test")
        assert kb is None
        
        # 但在包含非活跃的列表中应该能找到
        kbs = temp_kb_service.list_kbs(include_inactive=True)
        found = any(k["id"] == "delete_test" for k in kbs)
        assert found is True
    
    def test_cannot_delete_default_kb(self, temp_kb_service):
        """测试不能删除默认知识库"""
        with pytest.raises(ValueError):
            temp_kb_service.delete_kb("default")
    
    def test_get_collection_name(self, temp_kb_service):
        """测试获取 collection 名称"""
        # 默认知识库
        assert temp_kb_service.get_collection_name("default") == "qms_docs"
        
        # 创建并获取自定义知识库
        temp_kb_service.create_kb(kb_id="test_collection", name="测试")
        assert temp_kb_service.get_collection_name("test_collection") == "kb_test_collection"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
