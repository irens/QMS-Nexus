"""
系统管理路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import time
from datetime import datetime

# psutil 是可选依赖
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

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
    
    if PSUTIL_AVAILABLE and psutil:
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
    else:
        # 返回模拟数据
        memory_usage = {
            "total": 17179869184,  # 16GB
            "used": 8589934592,    # 8GB
            "available": 8589934592,  # 8GB
            "percentage": 50.0
        }
        disk_usage = {
            "total": 536870912000,  # 500GB
            "used": 107374182400,   # 100GB
            "free": 429496729600,   # 400GB
            "percentage": 20.0
        }
        cpu_usage = 25.0
    
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

@router.get("/api-keys-mock", response_model=PaginatedResponse)
async def get_api_keys_mock(page: int = 1, page_size: int = 20):
    """获取API密钥列表（模拟数据）- 已废弃，请使用 /api/v1/api-keys"""
    # 返回空列表，引导用户使用新的认证接口
    return PaginatedResponse(
        items=[],
        total=0,
        page=page,
        page_size=page_size,
        total_pages=0
    )

@router.get("/api-keys-mock/{key_id}/logs", response_model=PaginatedResponse)
async def get_api_key_logs_mock(key_id: str, page: int = 1, page_size: int = 20):
    """获取API密钥使用日志（模拟）- 已废弃"""
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
    if PSUTIL_AVAILABLE and psutil:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        memory_usage = {
            "used": memory.used,
            "total": memory.total,
            "percentage": memory.percent
        }
        disk_usage = {
            "used": disk.used,
            "total": disk.total,
            "percentage": (disk.used / disk.total) * 100
        }
    else:
        memory_usage = {
            "used": 8589934592,
            "total": 17179869184,
            "percentage": 50.0
        }
        disk_usage = {
            "used": 107374182400,
            "total": 536870912000,
            "percentage": 20.0
        }
    
    return {
        "totalDocuments": 42,
        "totalUsers": 5,
        "totalApiKeys": 2,
        "systemUptime": f"{int((time.time() - start_time) // 3600)}小时",
        "memoryUsage": memory_usage,
        "diskUsage": disk_usage
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