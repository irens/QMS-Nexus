"""
为 documents 表添加 current_version_id 字段
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from core.database import db_manager
from core.logger import get_logger

logger = get_logger(__name__)


def add_current_version_id_column():
    """添加 current_version_id 字段到 documents 表"""
    logger.info("开始添加 current_version_id 字段...")
    
    with db_manager.get_engine().connect() as conn:
        # 检查字段是否已存在
        result = conn.execute(text(
            "SELECT name FROM pragma_table_info('documents') WHERE name = 'current_version_id'"
        ))
        
        if result.fetchone():
            logger.info("current_version_id 字段已存在，跳过")
            return True
        
        # 添加字段
        conn.execute(text(
            "ALTER TABLE documents ADD COLUMN current_version_id TEXT"
        ))
        conn.commit()
        logger.info("current_version_id 字段添加成功")
        return True


if __name__ == "__main__":
    add_current_version_id_column()
