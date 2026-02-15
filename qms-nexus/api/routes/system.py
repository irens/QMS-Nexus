"""
系统管理路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import psutil
import time
from datetime import datetime

router = APIRouter(tags=["system"])

# 启动时间
start_time = time.time()

class SystemStatus(BaseModel):
    status: str
    uptime: str
    memory_usage: Dict[str, Any]
    disk_usage: Dict[str, Any]
    cpu_usage: float

class SystemConfig(BaseModel):
    app_name: str
    version: str
    debug: bool
    max_file_size: int
    supported_formats: list[str]

class ApiKey(BaseModel):
    id: str
    name: str
    key: str
    created_at: str
    last_used: Optional[str]
    is_active: bool

class ApiKeyForm(BaseModel):
    name: str
    expires_in_days: Optional[int] = 30

class PaginatedResponse(BaseModel):
    items: list[Any]
    total: int
    page: int
    page_size: int
    total_pages: int

@router.get("/system/status", response_model=SystemStatus)
async def get_system_status():
    """获取系统状态信息"""
    # 计算运行时间
    uptime_seconds = time.time() - start_time
    uptime_str = f"{int(uptime_seconds // 3600)}小时 {int((uptime_seconds % 3600) // 60)}分钟"
    
    # 获取内存使用情况
    memory = psutil.virtual_memory()
    memory_usage = {
        "total": memory.total,
        "used": memory.used,
        "available": memory.available,
        "percentage": memory.percent
    }
    
    # 获取磁盘使用情况
    disk = psutil.disk_usage('/')
    disk_usage = {
        "total": disk.total,
        "used": disk.used,
        "free": disk.free,
        "percentage": (disk.used / disk.total) * 100
    }
    
    # 获取CPU使用率
    cpu_usage = psutil.cpu_percent(interval=1)
    
    return SystemStatus(
        status="running",
        uptime=uptime_str,
        memory_usage=memory_usage,
        disk_usage=disk_usage,
        cpu_usage=cpu_usage
    )

@router.get("/system/config", response_model=SystemConfig)
async def get_system_config():
    """获取系统配置信息"""
    return SystemConfig(
        app_name="QMS-Nexus",
        version="1.0.0",
        debug=True,
        max_file_size=50 * 1024 * 1024,  # 50MB
        supported_formats=["pdf", "docx", "xlsx", "pptx", "txt"]
    )

@router.put("/config", response_model=SystemConfig)
async def update_system_config(config: SystemConfig):
    """更新系统配置（模拟）"""
    # 这里应该实现实际的配置更新逻辑
    return config

@router.get("/api-keys", response_model=PaginatedResponse)
async def get_api_keys(page: int = 1, page_size: int = 20):
    """获取API密钥列表（模拟数据）"""
    # 模拟数据
    mock_keys = [
        ApiKey(
            id="key_001",
            name="开发环境密钥",
            key="sk-***1234",
            created_at="2026-02-15T10:00:00Z",
            last_used="2026-02-15T11:30:00Z",
            is_active=True
        ),
        ApiKey(
            id="key_002", 
            name="测试环境密钥",
            key="sk-***5678",
            created_at="2026-02-14T15:20:00Z",
            last_used=None,
            is_active=False
        )
    ]
    
    # 分页逻辑
    total = len(mock_keys)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    items = mock_keys[start_idx:end_idx]
    total_pages = (total + page_size - 1) // page_size
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.post("/api-keys", response_model=ApiKey)
async def create_api_key(form: ApiKeyForm):
    """创建新的API密钥（模拟）"""
    import uuid
    from datetime import datetime, timezone
    
    return ApiKey(
        id=f"key_{uuid.uuid4().hex[:8]}",
        name=form.name,
        key=f"sk-{uuid.uuid4().hex[:12]}",
        created_at=datetime.now(timezone.utc).isoformat(),
        last_used=None,
        is_active=True
    )

@router.put("/api-keys/{key_id}", response_model=ApiKey)
async def update_api_key(key_id: str, updates: Dict[str, Any]):
    """更新API密钥（模拟）"""
    # 这里应该实现实际的更新逻辑
    return ApiKey(
        id=key_id,
        name="更新后的密钥名称",
        key="sk-***updated",
        created_at="2026-02-15T10:00:00Z",
        last_used="2026-02-15T12:00:00Z",
        is_active=True
    )

@router.delete("/api-keys/{key_id}")
async def delete_api_key(key_id: str):
    """删除API密钥"""
    return {"message": f"API密钥 {key_id} 已删除"}

@router.get("/api-keys/{key_id}/logs", response_model=PaginatedResponse)
async def get_api_key_logs(key_id: str, page: int = 1, page_size: int = 20):
    """获取API密钥使用日志（模拟）"""
    return PaginatedResponse(
        items=[],
        total=0,
        page=page,
        page_size=page_size,
        total_pages=0
    )

@router.get("/logs", response_model=PaginatedResponse)
async def get_system_logs(
    page: int = 1,
    page_size: int = 20,
    level: Optional[str] = None,
    module: Optional[str] = None,
    startTime: Optional[str] = None,
    endTime: Optional[str] = None
):
    """获取系统日志（模拟）"""
    return PaginatedResponse(
        items=[
            {
                "id": "log_001",
                "timestamp": "2026-02-15T12:00:00Z",
                "level": "INFO",
                "module": "system",
                "message": "系统启动成功"
            },
            {
                "id": "log_002", 
                "timestamp": "2026-02-15T12:05:00Z",
                "level": "WARNING",
                "module": "upload",
                "message": "文件上传大小超过限制"
            }
        ],
        total=2,
        page=page,
        page_size=page_size,
        total_pages=1
    )

@router.get("/stats")
async def get_system_stats():
    """获取系统统计信息"""
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        "totalDocuments": 42,
        "totalUsers": 5,
        "totalApiKeys": 2,
        "systemUptime": f"{int((time.time() - start_time) // 3600)}小时",
        "memoryUsage": {
            "used": memory.used,
            "total": memory.total,
            "percentage": memory.percent
        },
        "diskUsage": {
            "used": disk.used,
            "total": disk.total,
            "percentage": (disk.used / disk.total) * 100
        }
    }

@router.post("/restart/{service}")
async def restart_service(service: str):
    """重启系统服务（模拟）"""
    return {"message": f"服务 {service} 重启成功"}

@router.post("/clear-cache")
async def clear_cache(type: Optional[str] = None):
    """清理系统缓存"""
    return {"message": f"缓存清理完成" + (f" (类型: {type})" if type else "")}

@router.post("/backup")
async def backup_data():
    """备份系统数据（模拟）"""
    import uuid
    from datetime import datetime, timezone
    
    return {
        "backupId": f"backup_{uuid.uuid4().hex[:8]}",
        "filename": f"qms_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
        "size": 1024 * 1024,  # 1MB
        "createdAt": datetime.now(timezone.utc).isoformat()
    }

@router.get("/backups", response_model=PaginatedResponse)
async def get_backups(page: int = 1, page_size: int = 20):
    """获取备份列表（模拟）"""
    return PaginatedResponse(
        items=[],
        total=0,
        page=page,
        page_size=page_size,
        total_pages=0
    )

@router.post("/restore/{backup_id}")
async def restore_data(backup_id: str):
    """恢复系统数据（模拟）"""
    return {"message": f"数据恢复完成: {backup_id}"}

@router.delete("/backups/{backup_id}")
async def delete_backup(backup_id: str):
    """删除备份"""
    return {"message": f"备份 {backup_id} 已删除"}