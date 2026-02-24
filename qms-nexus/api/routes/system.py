"""
系统管理路由
"""
from datetime import datetime
import time
import platform
import subprocess
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from core.log_store import log_store
from core.logger import get_logger
from core.backup_manager import backup_manager

logger = get_logger(__name__)

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
    endTime: Optional[str] = None,
    search: Optional[str] = None,
):
    """获取系统日志（真实数据，支持筛选和分页）。"""

    def _parse_dt(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    start_dt = _parse_dt(startTime)
    end_dt = _parse_dt(endTime)

    items, total = log_store.query_logs(
        page=page,
        page_size=page_size,
        level=level,
        module=module,
        start_time=start_dt,
        end_time=end_dt,
        search=search,
    )

    total_pages = (total + page_size - 1) // page_size if page_size else 1

    def _row_to_dict(row) -> Dict[str, Any]:
        return {
            "id": row.id,
            "timestamp": row.created_at.isoformat() if row.created_at else None,
            "level": row.level,
            "module": row.module,
            "message": row.message,
            "userId": row.user_id,
            "requestId": row.request_id,
            "ipAddress": row.ip_address,
        }

    return PaginatedResponse(
        items=[_row_to_dict(r) for r in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )

@router.get("/stats")
async def get_system_stats():
    """获取系统统计信息"""
    from core.database import Document, ChatLog, db_manager
    from sqlalchemy import func
    
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
    
    # 从数据库获取真实统计数据
    try:
        with db_manager.get_session() as session:
            # 总文档数
            total_documents = session.query(func.count(Document.id)).scalar() or 0
            
            # 已解析文档数（状态为 Completed）
            parsed_documents = session.query(func.count(Document.id)).filter(
                Document.status == 'Completed'
            ).scalar() or 0
            
            # 问答次数
            total_chats = session.query(func.count(ChatLog.id)).scalar() or 0
            
            # 活跃用户数（不同的 user_id）
            active_users = session.query(func.count(func.distinct(ChatLog.user_id))).filter(
                ChatLog.user_id.isnot(None)
            ).scalar() or 0
            
            # 上月数据（用于计算增长率）
            from datetime import timedelta
            last_month = datetime.utcnow() - timedelta(days=30)
            
            # 上月文档数
            last_month_docs = session.query(func.count(Document.id)).filter(
                Document.created_at >= last_month
            ).scalar() or 0
            
            # 上月问答次数
            last_month_chats = session.query(func.count(ChatLog.id)).filter(
                ChatLog.created_at >= last_month
            ).scalar() or 0
            
            # 计算增长率
            if total_documents > 0:
                doc_growth = round((last_month_docs / total_documents) * 100, 1) if last_month_docs > 0 else 0
            else:
                doc_growth = 0
                
            if total_chats > 0:
                chat_growth = round((last_month_chats / total_chats) * 100, 1) if last_month_chats > 0 else 0
            else:
                chat_growth = 0
            
    except Exception as e:
        logger.error(f"获取统计数据失败: {e}")
        total_documents = 0
        parsed_documents = 0
        total_chats = 0
        active_users = 0
        doc_growth = 0
        chat_growth = 0
    
    return {
        "totalDocuments": total_documents,
        "parsedDocuments": parsed_documents,
        "totalChats": total_chats,
        "activeUsers": active_users,
        "totalUsers": active_users,
        "totalApiKeys": 0,
        "systemUptime": f"{int((time.time() - start_time) // 3600)}小时",
        "memoryUsage": memory_usage,
        "diskUsage": disk_usage,
        "growthRate": {
            "documents": doc_growth,
            "chats": chat_growth
        }
    }

# 允许重启的服务列表
ALLOWED_SERVICES = ["backend", "worker", "redis"]

# PowerShell脚本 - 重启backend
RESTART_BACKEND_PS = """
$ErrorActionPreference = "Stop"
Write-Host "正在停止backend服务..."
Get-Process -Name "python" -ErrorAction SilentlyContinue | 
    Where-Object {$_.CommandLine -like "*uvicorn*" -or $_.CommandLine -like "*api.main*"} | 
    Stop-Process -Force
Start-Sleep -Seconds 2
Write-Host "正在启动backend服务..."
Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000" -WindowStyle Hidden
Write-Host "Backend服务已重启"
"""

# PowerShell脚本 - 重启worker
RESTART_WORKER_PS = """
$ErrorActionPreference = "Stop"
Write-Host "正在停止worker服务..."
Get-Process -Name "python" -ErrorAction SilentlyContinue | 
    Where-Object {$_.CommandLine -like "*worker*"} | 
    Stop-Process -Force
Start-Sleep -Seconds 2
Write-Host "正在启动worker服务..."
Start-Process -FilePath "python" -ArgumentList "scripts/worker.py" -WindowStyle Hidden
Write-Host "Worker服务已重启"
"""

# PowerShell脚本 - 重启redis
RESTART_REDIS_PS = """
$ErrorActionPreference = "Stop"
Write-Host "正在重启Redis服务..."
Restart-Service -Name "Redis" -Force -ErrorAction SilentlyContinue
if ($?) {
    Write-Host "Redis服务已重启"
} else {
    # 尝试使用redis-server
    Get-Process -Name "redis-server" -ErrorAction SilentlyContinue | Stop-Process -Force
    Start-Sleep -Seconds 1
    Start-Process -FilePath "redis-server" -WindowStyle Hidden
    Write-Host "Redis服务已重启（使用redis-server）"
}
"""


@router.post("/system/restart/{service}")
async def restart_system(service: str):
    """
    重启系统服务
    
    支持的服务：
    - backend: 重启后端API服务
    - worker: 重启后台任务worker
    - redis: 重启Redis服务
    
    注意：重启是异步操作，API立即返回"重启中"，实际重启在后台执行
    """
    # 验证服务名称
    if service not in ALLOWED_SERVICES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的服务: {service}。支持的服务: {', '.join(ALLOWED_SERVICES)}"
        )
    
    # 记录重启请求到系统日志
    log_store.log(
        level="INFO",
        module="system",
        message=f"请求重启服务: {service}",
        metadata={"service": service, "action": "restart"}
    )
    
    system = platform.system()
    logger.info(f"执行重启: service={service}, platform={system}")
    
    try:
        if system == "Windows":
            await _restart_windows(service)
        elif system == "Linux":
            await _restart_linux(service)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的操作系统: {system}"
            )
        
        # 记录重启成功
        log_store.log(
            level="INFO",
            module="system",
            message=f"服务重启命令已执行: {service}",
            metadata={"service": service, "platform": system}
        )
        
        return {
            "message": "重启中",
            "service": service,
            "status": "restarting",
            "platform": system
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重启服务失败: {e}")
        log_store.log(
            level="ERROR",
            module="system",
            message=f"重启服务失败: {service}, 错误: {str(e)}",
            metadata={"service": service, "error": str(e)}
        )
        raise HTTPException(status_code=500, detail=f"重启失败: {str(e)}")


async def _restart_windows(service: str):
    """Windows平台重启服务"""
    if service == "backend":
        script = RESTART_BACKEND_PS
    elif service == "worker":
        script = RESTART_WORKER_PS
    elif service == "redis":
        script = RESTART_REDIS_PS
    else:
        raise ValueError(f"未知服务: {service}")
    
    # 使用subprocess.Popen非阻塞执行PowerShell脚本
    # 将脚本写入临时文件执行，避免命令行长度限制
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ps1', delete=False) as f:
        f.write(script)
        script_path = f.name
    
    try:
        # 使用PowerShell执行脚本
        subprocess.Popen(
            ["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP  # 创建新进程组，避免被父进程终止
        )
        logger.info(f"Windows重启命令已提交: {service}")
    except Exception as e:
        # 清理临时文件
        try:
            os.unlink(script_path)
        except:
            pass
        raise e


async def _restart_linux(service: str):
    """Linux平台重启服务"""
    commands = {
        "backend": ["sudo", "systemctl", "restart", "qms-nexus"],
        "worker": ["sudo", "systemctl", "restart", "qms-nexus-worker"],
        "redis": ["sudo", "systemctl", "restart", "redis"],
    }
    
    if service not in commands:
        raise ValueError(f"未知服务: {service}")
    
    cmd = commands[service]
    
    # 使用subprocess.Popen非阻塞执行
    subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True  # 创建新会话，避免被父进程终止
    )
    logger.info(f"Linux重启命令已提交: {service}")


# 保持旧接口兼容（可选）
@router.post("/restart/{service}")
async def restart_service_legacy(service: str):
    """重启系统服务（兼容旧接口）"""
    return await restart_system(service)

@router.post("/clear-cache")
async def clear_cache(type: Optional[str] = None):
    """清理系统缓存"""
    return {"message": f"缓存清理完成" + (f" (类型: {type})" if type else "")}

class BackupCreateRequest(BaseModel):
    """创建备份请求"""
    includeLogs: bool = False


class BackupItem(BaseModel):
    """备份项"""
    backupId: str
    createdAt: str
    size: int
    sizeBytes: int
    components: Dict[str, bool]
    version: str
    filename: str


class BackupListResponse(BaseModel):
    """备份列表响应"""
    items: List[BackupItem]
    total: int


class BackupCreateResponse(BaseModel):
    """创建备份响应"""
    backupId: str
    message: str
    createdAt: str


class RestoreResponse(BaseModel):
    """恢复备份响应"""
    message: str
    autoBackupId: Optional[str]
    needRestart: bool
    restoredComponents: List[str]


@router.post("/system/backup", response_model=BackupCreateResponse)
async def create_backup_endpoint(body: BackupCreateRequest):
    """
    创建系统备份
    
    Args:
        includeLogs: 是否包含系统日志（默认false）
        
    Returns:
        备份信息
    """
    try:
        logger.info(f"开始创建备份: includeLogs={body.includeLogs}")
        
        backup_id = backup_manager.create_backup(include_logs=body.includeLogs)
        
        # 记录到系统日志
        log_store.log(
            level="INFO",
            module="system",
            message=f"备份创建成功: {backup_id}",
            metadata={"backup_id": backup_id, "include_logs": body.includeLogs}
        )
        
        return BackupCreateResponse(
            backupId=backup_id,
            message="备份创建成功",
            createdAt=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"创建备份失败: {e}")
        log_store.log(
            level="ERROR",
            module="system",
            message=f"创建备份失败: {str(e)}",
            metadata={"error": str(e)}
        )
        raise HTTPException(status_code=500, detail=f"创建备份失败: {str(e)}")


@router.get("/system/backups", response_model=BackupListResponse)
async def list_backups_endpoint():
    """
    获取备份列表
    
    Returns:
        备份列表
    """
    try:
        backups = backup_manager.list_backups()
        
        # 转换为响应格式
        items = [
            BackupItem(
                backupId=b.get("backup_id", ""),
                createdAt=b.get("created_at", ""),
                size=b.get("size_bytes", 0),
                sizeBytes=b.get("size_bytes", 0),
                components=b.get("components", {}),
                version=b.get("version", "unknown"),
                filename=b.get("filename", "")
            )
            for b in backups
        ]
        
        return BackupListResponse(
            items=items,
            total=len(items)
        )
        
    except Exception as e:
        logger.error(f"获取备份列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取备份列表失败: {str(e)}")


@router.post("/system/restore/{backup_id}", response_model=RestoreResponse)
async def restore_backup_endpoint(backup_id: str):
    """
    恢复系统备份
    
    恢复前会自动创建当前状态的备份
    
    Args:
        backup_id: 备份ID
        
    Returns:
        恢复结果
    """
    try:
        logger.info(f"开始恢复备份: {backup_id}")
        
        result = backup_manager.restore_backup(backup_id)
        
        # 记录到系统日志
        log_store.log(
            level="INFO",
            module="system",
            message=f"备份恢复成功: {backup_id}",
            metadata={
                "backup_id": backup_id,
                "auto_backup_id": result.get("auto_backup_id"),
                "restored_components": result.get("restored_components", [])
            }
        )
        
        return RestoreResponse(
            message=result.get("message", "恢复成功"),
            autoBackupId=result.get("auto_backup_id"),
            needRestart=result.get("need_restart", True),
            restoredComponents=result.get("restored_components", [])
        )
        
    except FileNotFoundError as e:
        logger.error(f"备份文件不存在: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"恢复备份失败: {e}")
        log_store.log(
            level="ERROR",
            module="system",
            message=f"恢复备份失败: {backup_id}, 错误: {str(e)}",
            metadata={"backup_id": backup_id, "error": str(e)}
        )
        raise HTTPException(status_code=500, detail=f"恢复备份失败: {str(e)}")


@router.delete("/system/backups/{backup_id}")
async def delete_backup_endpoint(backup_id: str):
    """
    删除指定备份
    
    Args:
        backup_id: 备份ID
        
    Returns:
        删除结果
    """
    try:
        success = backup_manager.delete_backup(backup_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"备份不存在: {backup_id}")
        
        # 记录到系统日志
        log_store.log(
            level="INFO",
            module="system",
            message=f"备份已删除: {backup_id}",
            metadata={"backup_id": backup_id}
        )
        
        return {"message": f"备份 {backup_id} 已删除"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除备份失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除备份失败: {str(e)}")


# 保持旧接口兼容
@router.post("/backup")
async def backup_data_legacy():
    """备份系统数据（兼容旧接口）"""
    return await create_backup_endpoint(BackupCreateRequest(includeLogs=False))


@router.get("/backups", response_model=PaginatedResponse)
async def get_backups_legacy(page: int = 1, page_size: int = 20):
    """获取备份列表（兼容旧接口）"""
    result = await list_backups_endpoint()
    
    # 转换为PaginatedResponse格式
    items = [
        {
            "id": item.backupId,
            "filename": item.filename,
            "size": item.size,
            "createdAt": item.createdAt,
            "components": item.components
        }
        for item in result.items
    ]
    
    total_pages = (result.total + page_size - 1) // page_size if page_size else 1
    offset = (page - 1) * page_size
    paginated_items = items[offset:offset + page_size]
    
    return PaginatedResponse(
        items=paginated_items,
        total=result.total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.post("/restore/{backup_id}")
async def restore_data_legacy(backup_id: str):
    """恢复系统数据（兼容旧接口）"""
    return await restore_backup_endpoint(backup_id)


@router.delete("/backups/{backup_id}")
async def delete_backup_legacy(backup_id: str):
    """删除备份（兼容旧接口）"""
    return await delete_backup_endpoint(backup_id)