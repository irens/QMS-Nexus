"""
认证中间件
支持 API Key 验证和 IP 白名单
"""
import sqlite3
import ipaddress
from typing import Optional, List, Set
from datetime import datetime
from pathlib import Path
from functools import wraps

from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from core.logger import get_logger

logger = get_logger(__name__)

DB_PATH = Path("./data/auth.db")
security = HTTPBearer(auto_error=False)


class AuthService:
    """认证服务，管理 API Key 和 IP 白名单"""
    
    def __init__(self):
        self.db_path = DB_PATH
        self._ensure_db()
        # 缓存配置
        self._api_keys_cache: Optional[Set[str]] = None
        self._whitelist_cache: Optional[List[str]] = None
        self._cache_enabled = True
    
    def _ensure_db(self):
        """确保数据库和表存在"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            # API Keys 表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    key_hash TEXT NOT NULL UNIQUE,
                    key_preview TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    request_count INTEGER DEFAULT 0
                )
            """)
            # IP 白名单表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ip_whitelist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip_address TEXT NOT NULL UNIQUE,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            # 配置表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS auth_config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)
            # 插入默认配置
            conn.execute("""
                INSERT OR IGNORE INTO auth_config (key, value) VALUES
                ('auth_enabled', '0'),
                ('whitelist_enabled', '0')
            """)
            conn.commit()
    
    def _invalidate_cache(self):
        """使缓存失效"""
        self._api_keys_cache = None
        self._whitelist_cache = None
    
    def get_config(self, key: str, default: str = "") -> str:
        """获取配置项"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT value FROM auth_config WHERE key = ?",
                (key,)
            )
            row = cursor.fetchone()
            return row[0] if row else default
    
    def set_config(self, key: str, value: str):
        """设置配置项"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO auth_config (key, value) VALUES (?, ?)",
                (key, value)
            )
            conn.commit()
        self._invalidate_cache()
    
    # ---------- API Key 管理 ----------
    
    def create_api_key(self, name: str) -> tuple[str, str]:
        """
        创建新的 API Key
        
        Returns:
            (key_id, api_key) - api_key 是明文，只返回一次
        """
        import uuid
        import hashlib
        
        key_id = f"key_{uuid.uuid4().hex[:8]}"
        # 生成 API Key: sk-前缀 + 随机字符串
        api_key = f"sk-{uuid.uuid4().hex[:24]}"
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        key_preview = api_key[:8] + "***" + api_key[-4:]
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO api_keys (id, name, key_hash, key_preview, is_active)
                VALUES (?, ?, ?, ?, 1)
                """,
                (key_id, name, key_hash, key_preview)
            )
            conn.commit()
        
        self._invalidate_cache()
        logger.info(f"API Key created: {key_id}, name={name}")
        return key_id, api_key
    
    def validate_api_key(self, api_key: str) -> bool:
        """验证 API Key 是否有效"""
        import hashlib
        
        if not api_key:
            return False
        
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT id FROM api_keys 
                WHERE key_hash = ? AND is_active = 1
                """,
                (key_hash,)
            )
            row = cursor.fetchone()
            
            if row:
                # 更新最后使用时间和计数
                conn.execute(
                    """
                    UPDATE api_keys 
                    SET last_used = ?, request_count = request_count + 1
                    WHERE id = ?
                    """,
                    (datetime.now().isoformat(), row[0])
                )
                conn.commit()
                return True
            return False
    
    def list_api_keys(self, include_inactive: bool = False):
        """列出所有 API Keys"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if include_inactive:
                cursor = conn.execute(
                    """
                    SELECT id, name, key_preview, created_at, last_used, is_active, request_count
                    FROM api_keys ORDER BY created_at DESC
                    """
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT id, name, key_preview, created_at, last_used, is_active, request_count
                    FROM api_keys WHERE is_active = 1 ORDER BY created_at DESC
                    """
                )
            return [dict(row) for row in cursor.fetchall()]
    
    def revoke_api_key(self, key_id: str) -> bool:
        """吊销 API Key"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "UPDATE api_keys SET is_active = 0 WHERE id = ?",
                (key_id,)
            )
            conn.commit()
            self._invalidate_cache()
            return cursor.rowcount > 0
    
    def delete_api_key(self, key_id: str) -> bool:
        """删除 API Key"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM api_keys WHERE id = ?",
                (key_id,)
            )
            conn.commit()
            self._invalidate_cache()
            return cursor.rowcount > 0
    
    # ---------- IP 白名单管理 ----------
    
    def add_ip_to_whitelist(self, ip_address: str, description: str = "") -> bool:
        """添加 IP 到白名单"""
        try:
            # 验证 IP 地址格式
            ipaddress.ip_network(ip_address, strict=False)
        except ValueError:
            return False
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO ip_whitelist (ip_address, description, is_active)
                    VALUES (?, ?, 1)
                    """,
                    (ip_address, description)
                )
                conn.commit()
            self._invalidate_cache()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def remove_ip_from_whitelist(self, ip_id: int) -> bool:
        """从白名单移除 IP"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM ip_whitelist WHERE id = ?",
                (ip_id,)
            )
            conn.commit()
            self._invalidate_cache()
            return cursor.rowcount > 0
    
    def list_whitelist(self):
        """列出所有白名单 IP"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT id, ip_address, description, created_at, is_active
                FROM ip_whitelist WHERE is_active = 1 ORDER BY created_at DESC
                """
            )
            return [dict(row) for row in cursor.fetchall()]
    
    def is_ip_allowed(self, client_ip: str) -> bool:
        """检查 IP 是否在白名单中"""
        # 如果白名单未启用，允许所有
        if self.get_config("whitelist_enabled") != "1":
            return True
        
        whitelist = self.list_whitelist()
        if not whitelist:
            return True  # 白名单为空时允许所有
        
        client_addr = ipaddress.ip_address(client_ip)
        
        for item in whitelist:
            try:
                network = ipaddress.ip_network(item["ip_address"], strict=False)
                if client_addr in network:
                    return True
            except ValueError:
                continue
        
        return False
    
    # ---------- 认证检查 ----------
    
    def is_auth_enabled(self) -> bool:
        """检查认证是否启用"""
        return self.get_config("auth_enabled") == "1"
    
    def check_request(self, request: Request, api_key: Optional[str] = None) -> bool:
        """
        检查请求是否通过认证
        
        Args:
            request: FastAPI Request 对象
            api_key: API Key（从 Header 中提取）
            
        Returns:
            bool: 是否通过认证
        """
        # 1. 检查 IP 白名单
        client_ip = request.client.host if request.client else "unknown"
        if not self.is_ip_allowed(client_ip):
            logger.warning(f"IP not allowed: {client_ip}")
            return False
        
        # 2. 如果认证未启用，跳过
        if not self.is_auth_enabled():
            return True
        
        # 3. 验证 API Key
        if not api_key:
            return False
        
        return self.validate_api_key(api_key)


# 全局认证服务实例
auth_service = AuthService()


async def auth_middleware(request: Request, call_next):
    """
    认证中间件
    
    对受保护的路径进行认证检查
    """
    # 公开路径（不需要认证）
    public_paths = [
        "/docs", "/openapi.json", "/redoc",  # API 文档
        "/api/v1/health",  # 健康检查
        "/",  # 根路径
    ]
    
    path = request.url.path
    
    # 检查是否是公开路径
    for public_path in public_paths:
        if path.startswith(public_path):
            return await call_next(request)
    
    # 提取 API Key
    api_key = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        api_key = auth_header[7:]
    elif auth_header and auth_header.startswith("sk-"):
        api_key = auth_header
    
    # 检查认证
    if not auth_service.check_request(request, api_key):
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": "Authentication failed. Invalid API Key or IP not allowed."}
        )
    
    return await call_next(request)
