"""
修正库服务单元测试
"""
import pytest
import tempfile
import shutil
from pathlib import Path

from core.correction_service import CorrectionService


@pytest.fixture
def temp_correction_service():
    """创建临时的修正库服务"""
    temp_dir = tempfile.mkdtemp()
    original_db_path = CorrectionService.__init__.__code__.co_consts
    
    # 临时修改数据库路径
    import core.correction_service as cs
    original_path = cs.DB_PATH
    cs.DB_PATH = Path(temp_dir) / "corrections.db"
    
    service = CorrectionService()
    
    yield service
    
    # 清理
    cs.DB_PATH = original_path
    shutil.rmtree(temp_dir)


class TestCorrectionService:
    """修正库服务测试类"""
    
    def test_add_correction(self, temp_correction_service):
        """测试添加修正记录"""
        correction_id = temp_correction_service.add_correction(
            question="什么是ISO13485？",
            correct_answer="ISO13485是医疗器械质量管理体系标准。",
            source_doc="ISO13485.pdf",
            page_number=10
        )
        
        assert correction_id > 0
    
    def test_find_correction(self, temp_correction_service):
        """测试查找修正记录"""
        # 先添加记录
        temp_correction_service.add_correction(
            question="什么是GMP？",
            correct_answer="GMP是良好生产规范。"
        )
        
        # 查找记录
        correction = temp_correction_service.find_correction("什么是GMP？")
        
        assert correction is not None
        assert correction["correct_answer"] == "GMP是良好生产规范。"
        assert correction["is_active"] == 1
    
    def test_find_nonexistent_correction(self, temp_correction_service):
        """测试查找不存在的修正记录"""
        correction = temp_correction_service.find_correction("不存在的问题")
        assert correction is None
    
    def test_update_correction(self, temp_correction_service):
        """测试更新修正记录"""
        # 添加记录
        correction_id = temp_correction_service.add_correction(
            question="测试问题",
            correct_answer="原答案"
        )
        
        # 更新记录
        success = temp_correction_service.update_correction(
            correction_id,
            correct_answer="更新后的答案"
        )
        
        assert success is True
        
        # 验证更新
        correction = temp_correction_service.get_correction_by_id(correction_id)
        assert correction["correct_answer"] == "更新后的答案"
    
    def test_delete_correction(self, temp_correction_service):
        """测试删除修正记录（软删除）"""
        # 添加记录
        correction_id = temp_correction_service.add_correction(
            question="要删除的问题",
            correct_answer="答案"
        )
        
        # 删除记录
        success = temp_correction_service.delete_correction(correction_id)
        assert success is True
        
        # 验证已删除（找不到）
        correction = temp_correction_service.find_correction("要删除的问题")
        assert correction is None
    
    def test_search_corrections(self, temp_correction_service):
        """测试搜索修正记录"""
        # 添加多条记录
        temp_correction_service.add_correction(
            question="ISO13485的要求",
            correct_answer="答案是A"
        )
        temp_correction_service.add_correction(
            question="GMP的要求",
            correct_answer="答案是B"
        )
        
        # 搜索
        result = temp_correction_service.search_corrections(keyword="ISO")
        
        assert result["total"] >= 1
        assert len(result["items"]) >= 1
    
    def test_get_stats(self, temp_correction_service):
        """测试获取统计信息"""
        # 添加记录
        temp_correction_service.add_correction(
            question="统计测试",
            correct_answer="测试答案"
        )
        
        stats = temp_correction_service.get_stats()
        
        assert "active" in stats
        assert "total" in stats
        assert stats["active"] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
