"""
认证管理接口
提供 API Key 和 IP 白名单管理
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from core.auth import auth_service

router = APIRouter(tags=["auth"])


class ApiKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="API Key 名称")


class ApiKeyOut(BaseModel):
    id: str
    name: str
    key_preview: str
    created_at: str
    last_used: Optional[str]
    is_active: bool
    request_count: int


class IpWhitelistCreate(BaseModel):
    ip_address: str = Field(..., description="IP 地址或网段，如 192.168.1.1 或 10.0.0.0/24")
    description: str = Field(default="", max_length=200)


class IpWhitelistOut(BaseModel):
    id: int
    ip_address: str
    description: str
    created_at: str
    is_active: bool


class AuthConfigOut(BaseModel):
    auth_enabled: bool
    whitelist_enabled: bool


class AuthConfigUpdate(BaseModel):
    auth_enabled: Optional[bool] = None
    whitelist_enabled: Optional[bool] = None


# ---------- API Key 管理 ----------

@router.post("/api-keys", response_model=dict)
async def create_api_key(body: ApiKeyCreate):
    """创建新的 API Key（只显示一次，请妥善保存）"""
    key_id, api_key = auth_service.create_api_key(body.name)
    return {
        "id": key_id,
        "name": body.name,
        "api_key": api_key,
        "message": "API Key 已创建，请妥善保存，此密钥只显示一次"
    }


@router.get("/api-keys", response_model=List[ApiKeyOut])
async def list_api_keys(include_inactive: bool = Query(False)):
    """获取 API Key 列表（不包含完整密钥）"""
    return auth_service.list_api_keys(include_inactive=include_inactive)


@router.post("/api-keys/{key_id}/revoke", response_model=dict)
async def revoke_api_key(key_id: str):
    """吊销 API Key"""
    success = auth_service.revoke_api_key(key_id)
    if not success:
        raise HTTPException(status_code=404, detail="API Key 不存在")
    return {"message": "API Key 已吊销"}


@router.delete("/api-keys/{key_id}", response_model=dict)
async def delete_api_key(key_id: str):
    """删除 API Key"""
    success = auth_service.delete_api_key(key_id)
    if not success:
        raise HTTPException(status_code=404, detail="API Key 不存在")
    return {"message": "API Key 已删除"}


# ---------- IP 白名单管理 ----------

@router.post("/ip-whitelist", response_model=dict)
async def add_ip_whitelist(body: IpWhitelistCreate):
    """添加 IP 到白名单"""
    success = auth_service.add_ip_to_whitelist(body.ip_address, body.description)
    if not success:
        raise HTTPException(status_code=400, detail="IP 地址格式错误或已存在")
    return {"message": "IP 已添加到白名单"}


@router.get("/ip-whitelist", response_model=List[IpWhitelistOut])
async def list_ip_whitelist():
    """获取 IP 白名单列表"""
    return auth_service.list_whitelist()


@router.delete("/ip-whitelist/{ip_id}", response_model=dict)
async def remove_ip_whitelist(ip_id: int):
    """从白名单移除 IP"""
    success = auth_service.remove_ip_from_whitelist(ip_id)
    if not success:
        raise HTTPException(status_code=404, detail="IP 记录不存在")
    return {"message": "IP 已从白名单移除"}


# ---------- 认证配置 ----------

@router.get("/auth/config", response_model=AuthConfigOut)
async def get_auth_config():
    """获取认证配置"""
    return {
        "auth_enabled": auth_service.is_auth_enabled(),
        "whitelist_enabled": auth_service.get_config("whitelist_enabled") == "1"
    }


@router.put("/auth/config", response_model=AuthConfigOut)
async def update_auth_config(body: AuthConfigUpdate):
    """更新认证配置"""
    if body.auth_enabled is not None:
        auth_service.set_config("auth_enabled", "1" if body.auth_enabled else "0")
    if body.whitelist_enabled is not None:
        auth_service.set_config("whitelist_enabled", "1" if body.whitelist_enabled else "0")
    
    return {
        "auth_enabled": auth_service.is_auth_enabled(),
        "whitelist_enabled": auth_service.get_config("whitelist_enabled") == "1"
    }


@router.get("/auth/check", response_model=dict)
async def check_auth(request: Request):
    """检查当前请求的认证状态"""
    # 提取 API Key
    api_key = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        api_key = auth_header[7:]
    elif auth_header and auth_header.startswith("sk-"):
        api_key = auth_header
    
    client_ip = request.client.host if request.client else "unknown"
    
    is_allowed = auth_service.check_request(request, api_key)
    
    return {
        "client_ip": client_ip,
        "ip_allowed": auth_service.is_ip_allowed(client_ip),
        "auth_enabled": auth_service.is_auth_enabled(),
        "has_api_key": api_key is not None,
        "api_key_valid": auth_service.validate_api_key(api_key) if api_key else False,
        "is_authenticated": is_allowed
    }
