"""
备份管理器
负责系统数据的备份、恢复、自动备份调度
"""
import os
import json
import shutil
import zipfile
import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from threading import Lock

from core.config import settings
from core.logger import get_logger

logger = get_logger(__name__)


class BackupManager:
    """备份管理器（单例模式）
    
    功能：
    - 创建完整系统备份（SQLite、ChromaDB、Redis、配置）
    - 恢复系统数据
    - 自动清理旧备份
    - 定时自动备份（APScheduler）
    """
    
    _instance: Optional['BackupManager'] = None
    _lock = Lock()
    
    def __new__(cls) -> 'BackupManager':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        self.backup_dir = Path(settings.BACKUP_DIR)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 数据路径
        self.db_path = Path("./data/qms_nexus.db")
        self.chroma_dir = Path(settings.CHROMA_PERSIST_DIR)
        self.logs_dir = Path(settings.LOG_DIR)
        self.config_dir = Path("./config")
        self.env_file = Path("./.env")
        
        # Redis配置
        self.redis_url = settings.REDIS_URL
        
        logger.info(f"BackupManager初始化: backup_dir={self.backup_dir}")
    
    def create_backup(self, include_logs: bool = False) -> str:
        """创建系统备份
        
        Args:
            include_logs: 是否包含系统日志
            
        Returns:
            backup_id: 备份ID
        """
        # 生成备份ID和时间戳
        timestamp = datetime.now()
        backup_id = timestamp.strftime("%Y%m%d_%H%M%S")
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            backup_temp = temp_path / backup_id
            backup_temp.mkdir()
            
            components = {
                "database": False,
                "chroma": False,
                "redis": False,
                "config": False,
                "logs": False
            }
            
            try:
                # 1. 备份SQLite数据库
                if self.db_path.exists():
                    db_backup_dir = backup_temp / "data"
                    db_backup_dir.mkdir()
                    shutil.copy2(self.db_path, db_backup_dir / "qms_nexus.db")
                    components["database"] = True
                    logger.info(f"备份数据库: {self.db_path}")
                
                # 2. 备份ChromaDB数据
                if self.chroma_dir.exists():
                    chroma_backup_dir = backup_temp / "chroma"
                    chroma_backup_dir.mkdir()
                    self._copy_directory(self.chroma_dir, chroma_backup_dir)
                    components["chroma"] = True
                    logger.info(f"备份ChromaDB: {self.chroma_dir}")
                
                # 3. 备份Redis数据
                try:
                    redis_backup_dir = backup_temp / "redis"
                    redis_backup_dir.mkdir()
                    if self._backup_redis(redis_backup_dir):
                        components["redis"] = True
                        logger.info("备份Redis数据成功")
                except Exception as e:
                    logger.warning(f"备份Redis数据失败: {e}")
                
                # 4. 备份配置文件
                config_backup_dir = backup_temp / "config"
                config_backup_dir.mkdir()
                
                if self.env_file.exists():
                    shutil.copy2(self.env_file, config_backup_dir / ".env")
                
                if self.config_dir.exists():
                    self._copy_directory(self.config_dir, config_backup_dir / "config")
                
                components["config"] = True
                logger.info("备份配置文件")
                
                # 5. 备份系统日志（可选）
                if include_logs and self.logs_dir.exists():
                    logs_backup_dir = backup_temp / "logs"
                    logs_backup_dir.mkdir()
                    self._copy_directory(self.logs_dir, logs_backup_dir)
                    components["logs"] = True
                    logger.info(f"备份系统日志: {self.logs_dir}")
                
                # 6. 创建metadata.json
                metadata = {
                    "backup_id": backup_id,
                    "created_at": timestamp.isoformat(),
                    "version": settings.APP_VERSION,
                    "components": components,
                    "size_bytes": self._get_directory_size(backup_temp)
                }
                
                metadata_path = backup_temp / "metadata.json"
                with open(metadata_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)
                
                # 7. 打包为zip
                zip_filename = f"qms_backup_{backup_id}.zip"
                zip_path = self.backup_dir / zip_filename
                
                self._create_zip(backup_temp, zip_path)
                
                logger.info(f"备份创建成功: {zip_filename}")
                return backup_id
                
            except Exception as e:
                logger.error(f"创建备份失败: {e}")
                raise
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """获取所有备份列表
        
        Returns:
            备份信息列表
        """
        backups = []
        
        if not self.backup_dir.exists():
            return backups
        
        for zip_file in self.backup_dir.glob("qms_backup_*.zip"):
            try:
                backup_info = self._read_backup_info(zip_file)
                if backup_info:
                    backups.append(backup_info)
            except Exception as e:
                logger.warning(f"读取备份信息失败 {zip_file}: {e}")
        
        # 按创建时间倒序排列
        backups.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return backups
    
    def restore_backup(self, backup_id: str) -> Dict[str, Any]:
        """恢复系统备份
        
        流程：
        1. 验证备份文件存在
        2. 创建当前状态自动备份
        3. 解压备份文件
        4. 恢复各组件数据
        
        Args:
            backup_id: 备份ID
            
        Returns:
            恢复结果信息
        """
        zip_filename = f"qms_backup_{backup_id}.zip"
        zip_path = self.backup_dir / zip_filename
        
        if not zip_path.exists():
            raise FileNotFoundError(f"备份文件不存在: {zip_filename}")
        
        # 1. 创建当前状态自动备份
        auto_backup_id = None
        try:
            logger.info("创建自动备份（当前状态）...")
            auto_backup_id = self.create_backup(include_logs=False)
            logger.info(f"自动备份创建成功: {auto_backup_id}")
        except Exception as e:
            logger.warning(f"自动备份创建失败: {e}")
        
        # 2. 解压备份文件
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            extract_dir = temp_path / "restore"
            extract_dir.mkdir()
            
            try:
                self._extract_zip(zip_path, extract_dir)
                
                backup_root = extract_dir / backup_id
                if not backup_root.exists():
                    # 尝试直接查找子目录
                    subdirs = [d for d in extract_dir.iterdir() if d.is_dir()]
                    if subdirs:
                        backup_root = subdirs[0]
                
                # 3. 读取metadata
                metadata_path = backup_root / "metadata.json"
                if metadata_path.exists():
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                else:
                    metadata = {"components": {}}
                
                restored_components = []
                
                # 4. 恢复数据库
                if metadata.get("components", {}).get("database"):
                    db_source = backup_root / "data" / "qms_nexus.db"
                    if db_source.exists():
                        # 确保目标目录存在
                        self.db_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(db_source, self.db_path)
                        restored_components.append("database")
                        logger.info("恢复数据库成功")
                
                # 5. 恢复ChromaDB
                if metadata.get("components", {}).get("chroma"):
                    chroma_source = backup_root / "chroma"
                    if chroma_source.exists():
                        if self.chroma_dir.exists():
                            shutil.rmtree(self.chroma_dir)
                        self._copy_directory(chroma_source, self.chroma_dir)
                        restored_components.append("chroma")
                        logger.info("恢复ChromaDB成功")
                
                # 6. 恢复Redis
                if metadata.get("components", {}).get("redis"):
                    redis_source = backup_root / "redis" / "dump.rdb"
                    if redis_source.exists():
                        try:
                            self._restore_redis(redis_source)
                            restored_components.append("redis")
                            logger.info("恢复Redis成功")
                        except Exception as e:
                            logger.warning(f"恢复Redis失败: {e}")
                
                # 7. 恢复配置文件
                if metadata.get("components", {}).get("config"):
                    config_source = backup_root / "config"
                    if config_source.exists():
                        # 恢复.env
                        env_source = config_source / ".env"
                        if env_source.exists():
                            shutil.copy2(env_source, self.env_file)
                        
                        # 恢复config目录
                        config_dir_source = config_source / "config"
                        if config_dir_source.exists():
                            if self.config_dir.exists():
                                shutil.rmtree(self.config_dir)
                            self._copy_directory(config_dir_source, self.config_dir)
                        
                        restored_components.append("config")
                        logger.info("恢复配置文件成功")
                
                logger.info(f"备份恢复成功: {backup_id}, 恢复组件: {restored_components}")
                
                return {
                    "success": True,
                    "backup_id": backup_id,
                    "auto_backup_id": auto_backup_id,
                    "restored_components": restored_components,
                    "need_restart": True,
                    "message": "数据恢复成功，建议重启服务以确保所有更改生效"
                }
                
            except Exception as e:
                logger.error(f"恢复备份失败: {e}")
                raise
    
    def delete_backup(self, backup_id: str) -> bool:
        """删除指定备份
        
        Args:
            backup_id: 备份ID
            
        Returns:
            是否删除成功
        """
        zip_filename = f"qms_backup_{backup_id}.zip"
        zip_path = self.backup_dir / zip_filename
        
        if not zip_path.exists():
            return False
        
        try:
            zip_path.unlink()
            logger.info(f"备份已删除: {zip_filename}")
            return True
        except Exception as e:
            logger.error(f"删除备份失败: {e}")
            return False
    
    def cleanup_old_backups(self) -> int:
        """清理超过保留期限的旧备份
        
        Returns:
            删除的备份数量
        """
        retention_days = settings.BACKUP_RETENTION_DAYS
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        deleted_count = 0
        
        for backup_info in self.list_backups():
            try:
                created_at = datetime.fromisoformat(backup_info.get("created_at", ""))
                if created_at < cutoff_date:
                    backup_id = backup_info.get("backup_id")
                    if self.delete_backup(backup_id):
                        deleted_count += 1
                        logger.info(f"清理旧备份: {backup_id}")
            except Exception as e:
                logger.warning(f"清理备份时出错: {e}")
        
        if deleted_count > 0:
            logger.info(f"共清理 {deleted_count} 个旧备份")
        
        return deleted_count
    
    def schedule_auto_backup(self):
        """设置定时自动备份（使用APScheduler）"""
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from apscheduler.triggers.cron import CronTrigger
            
            if not settings.AUTO_BACKUP_ENABLED:
                logger.info("自动备份未启用")
                return
            
            scheduler = BackgroundScheduler()
            
            # 解析CRON表达式（简化处理，默认每天凌晨2点）
            cron_parts = settings.AUTO_BACKUP_CRON.split()
            if len(cron_parts) == 5:
                trigger = CronTrigger(
                    minute=cron_parts[0],
                    hour=cron_parts[1],
                    day=cron_parts[2],
                    month=cron_parts[3],
                    day_of_week=cron_parts[4]
                )
            else:
                # 默认每天凌晨2点
                trigger = CronTrigger(hour=2, minute=0)
            
            scheduler.add_job(
                self._auto_backup_job,
                trigger=trigger,
                id='auto_backup',
                replace_existing=True
            )
            
            scheduler.start()
            logger.info(f"自动备份已设置: {settings.AUTO_BACKUP_CRON}")
            
        except ImportError:
            logger.warning("APScheduler未安装，无法设置自动备份")
        except Exception as e:
            logger.error(f"设置自动备份失败: {e}")
    
    def _auto_backup_job(self):
        """自动备份任务"""
        try:
            logger.info("执行自动备份...")
            backup_id = self.create_backup(include_logs=False)
            logger.info(f"自动备份完成: {backup_id}")
            
            # 清理旧备份
            self.cleanup_old_backups()
            
        except Exception as e:
            logger.error(f"自动备份失败: {e}")
    
    def _backup_redis(self, backup_dir: Path) -> bool:
        """备份Redis数据
        
        Args:
            backup_dir: 备份目录
            
        Returns:
            是否成功
        """
        try:
            # 尝试执行bgsave
            result = subprocess.run(
                ['redis-cli', 'bgsave'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # 等待保存完成
            import time
            time.sleep(2)
            
            # 查找dump.rdb文件
            possible_paths = [
                Path("/var/lib/redis/dump.rdb"),
                Path("/var/redis/dump.rdb"),
                Path("./redis/dump.rdb"),
                Path("dump.rdb"),
            ]
            
            # Windows路径
            if os.name == 'nt':
                possible_paths.extend([
                    Path("C:/ProgramData/Redis/dump.rdb"),
                    Path("./dump.rdb"),
                ])
            
            for rdb_path in possible_paths:
                if rdb_path.exists():
                    shutil.copy2(rdb_path, backup_dir / "dump.rdb")
                    return True
            
            logger.warning("未找到Redis dump.rdb文件")
            return False
            
        except Exception as e:
            logger.warning(f"备份Redis失败: {e}")
            return False
    
    def _restore_redis(self, rdb_source: Path):
        """恢复Redis数据
        
        Args:
            rdb_source: dump.rdb源文件路径
        """
        # 查找Redis数据目录
        possible_paths = [
            Path("/var/lib/redis/dump.rdb"),
            Path("/var/redis/dump.rdb"),
            Path("./redis/dump.rdb"),
            Path("dump.rdb"),
        ]
        
        if os.name == 'nt':
            possible_paths.extend([
                Path("C:/ProgramData/Redis/dump.rdb"),
                Path("./dump.rdb"),
            ])
        
        for rdb_path in possible_paths:
            try:
                rdb_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(rdb_source, rdb_path)
                logger.info(f"Redis数据恢复到: {rdb_path}")
                return
            except Exception as e:
                continue
        
        raise RuntimeError("无法恢复Redis数据：无法找到或写入Redis数据目录")
    
    def _copy_directory(self, src: Path, dst: Path):
        """复制目录内容"""
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
    
    def _create_zip(self, source_dir: Path, zip_path: Path):
        """创建zip压缩包"""
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in source_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(source_dir)
                    zf.write(file_path, arcname)
    
    def _extract_zip(self, zip_path: Path, extract_dir: Path):
        """解压zip文件"""
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(extract_dir)
    
    def _get_directory_size(self, path: Path) -> int:
        """获取目录大小（字节）"""
        total = 0
        for file_path in path.rglob("*"):
            if file_path.is_file():
                total += file_path.stat().st_size
        return total
    
    def _read_backup_info(self, zip_path: Path) -> Optional[Dict[str, Any]]:
        """从zip文件读取备份信息"""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                # 查找metadata.json
                metadata_file = None
                for name in zf.namelist():
                    if name.endswith('metadata.json'):
                        metadata_file = name
                        break
                
                if metadata_file:
                    with zf.open(metadata_file) as f:
                        metadata = json.load(f)
                        # 添加文件大小信息
                        metadata['file_size'] = zip_path.stat().st_size
                        metadata['filename'] = zip_path.name
                        return metadata
                else:
                    # 没有metadata，从文件名解析
                    filename = zip_path.name
                    if filename.startswith("qms_backup_") and filename.endswith(".zip"):
                        backup_id = filename[11:-4]  # 提取时间戳部分
                        return {
                            "backup_id": backup_id,
                            "created_at": datetime.fromtimestamp(
                                zip_path.stat().st_mtime
                            ).isoformat(),
                            "version": "unknown",
                            "components": {},
                            "size_bytes": zip_path.stat().st_size,
                            "filename": filename
                        }
        except Exception as e:
            logger.warning(f"读取备份信息失败: {e}")
        
        return None


# 全局备份管理器实例
backup_manager = BackupManager()
