"""
认证服务单元测试
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock

from core.auth import AuthService


@pytest.fixture
def temp_auth_service():
    """创建临时的认证服务"""
    temp_dir = tempfile.mkdtemp()
    
    # 临时修改数据库路径
    import core.auth as auth_module
    original_path = auth_module.DB_PATH
    auth_module.DB_PATH = Path(temp_dir) / "auth.db"
    
    service = AuthService()
    
    yield service
    
    # 清理
    auth_module.DB_PATH = original_path
    shutil.rmtree(temp_dir)


class TestAuthService:
    """认证服务测试类"""
    
    def test_create_api_key(self, temp_auth_service):
        """测试创建 API Key"""
        key_id, api_key = temp_auth_service.create_api_key("测试密钥")
        
        assert key_id.startswith("key_")
        assert api_key.startswith("sk-")
        assert len(api_key) > 10
    
    def test_validate_api_key(self, temp_auth_service):
        """测试验证 API Key"""
        # 创建密钥
        key_id, api_key = temp_auth_service.create_api_key("验证测试")
        
        # 验证密钥
        is_valid = temp_auth_service.validate_api_key(api_key)
        assert is_valid is True
    
    def test_validate_invalid_api_key(self, temp_auth_service):
        """测试验证无效的 API Key"""
        is_valid = temp_auth_service.validate_api_key("sk-invalid-key")
        assert is_valid is False
    
    def test_list_api_keys(self, temp_auth_service):
        """测试列出 API Keys"""
        # 创建密钥
        temp_auth_service.create_api_key("密钥1")
        temp_auth_service.create_api_key("密钥2")
        
        # 列出密钥
        keys = temp_auth_service.list_api_keys()
        
        assert len(keys) >= 2
    
    def test_revoke_api_key(self, temp_auth_service):
        """测试吊销 API Key"""
        # 创建密钥
        key_id, api_key = temp_auth_service.create_api_key("要吊销的密钥")
        
        # 吊销密钥
        success = temp_auth_service.revoke_api_key(key_id)
        assert success is True
        
        # 验证密钥已失效
        is_valid = temp_auth_service.validate_api_key(api_key)
        assert is_valid is False
    
    def test_add_ip_to_whitelist(self, temp_auth_service):
        """测试添加 IP 到白名单"""
        success = temp_auth_service.add_ip_to_whitelist(
            "192.168.1.0/24",
            "内网网段"
        )
        assert success is True
    
    def test_add_invalid_ip(self, temp_auth_service):
        """测试添加无效 IP"""
        success = temp_auth_service.add_ip_to_whitelist("invalid-ip")
        assert success is False
    
    def test_is_ip_allowed(self, temp_auth_service):
        """测试 IP 白名单检查"""
        # 添加 IP 到白名单
        temp_auth_service.add_ip_to_whitelist("192.168.1.0/24")
        
        # 禁用白名单功能
        temp_auth_service.set_config("whitelist_enabled", "0")
        
        # 所有 IP 都应该被允许
        assert temp_auth_service.is_ip_allowed("192.168.1.100") is True
        assert temp_auth_service.is_ip_allowed("10.0.0.1") is True
    
    def test_ip_whitelist_enabled(self, temp_auth_service):
        """测试启用白名单后的 IP 检查"""
        # 添加 IP 到白名单
        temp_auth_service.add_ip_to_whitelist("192.168.1.0/24")
        
        # 启用白名单功能
        temp_auth_service.set_config("whitelist_enabled", "1")
        
        # 白名单内的 IP 应该被允许
        assert temp_auth_service.is_ip_allowed("192.168.1.100") is True
        
        # 白名单外的 IP 应该被拒绝
        assert temp_auth_service.is_ip_allowed("10.0.0.1") is False
    
    def test_auth_config(self, temp_auth_service):
        """测试认证配置"""
        # 默认认证应该是关闭的
        assert temp_auth_service.is_auth_enabled() is False
        
        # 启用认证
        temp_auth_service.set_config("auth_enabled", "1")
        assert temp_auth_service.is_auth_enabled() is True
        
        # 禁用认证
        temp_auth_service.set_config("auth_enabled", "0")
        assert temp_auth_service.is_auth_enabled() is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
