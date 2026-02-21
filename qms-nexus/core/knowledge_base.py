"""
知识库管理服务
支持多知识库（多租户）数据隔离
"""
import sqlite3
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path

from core.logger import get_logger

logger = get_logger(__name__)

DB_PATH = Path("./data/knowledge_bases.db")


class KnowledgeBaseService:
    """知识库服务，管理多个独立的知识库"""
    
    DEFAULT_KB = "default"
    
    def __init__(self):
        self.db_path = DB_PATH
        self._ensure_db()
        # 确保默认知识库存在
        self._ensure_default_kb()
    
    def _ensure_db(self):
        """确保数据库和表存在"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_bases (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    collection_name TEXT NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    metadata TEXT,
                    document_count INTEGER DEFAULT 0
                )
            """)
            conn.commit()
    
    def _ensure_default_kb(self):
        """确保默认知识库存在"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT id FROM knowledge_bases WHERE id = ?",
                (self.DEFAULT_KB,)
            )
            if not cursor.fetchone():
                conn.execute(
                    """
                    INSERT INTO knowledge_bases (id, name, description, collection_name, is_active)
                    VALUES (?, ?, ?, ?, 1)
                    """,
                    (self.DEFAULT_KB, "默认知识库", "系统默认知识库", "qms_docs")
                )
                conn.commit()
    
    def create_kb(
        self,
        kb_id: str,
        name: str,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        创建新的知识库
        
        Args:
            kb_id: 知识库唯一标识（英文、数字、下划线）
            name: 显示名称
            description: 描述
            metadata: 元数据
        """
        import re
        
        # 验证 kb_id 格式
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", kb_id):
            raise ValueError("知识库ID必须以字母开头，只能包含字母、数字和下划线")
        
        if kb_id == self.DEFAULT_KB:
            raise ValueError("不能使用保留ID: default")
        
        collection_name = f"kb_{kb_id}"
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO knowledge_bases 
                    (id, name, description, collection_name, metadata, is_active)
                    VALUES (?, ?, ?, ?, ?, 1)
                    """,
                    (
                        kb_id,
                        name,
                        description,
                        collection_name,
                        sqlite3.dumps(metadata) if metadata else None
                    )
                )
                conn.commit()
            logger.info(f"Knowledge base created: {kb_id}")
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_kb(self, kb_id: str) -> Optional[Dict[str, Any]]:
        """获取知识库信息"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM knowledge_bases WHERE id = ? AND is_active = 1",
                (kb_id,)
            )
            row = cursor.fetchone()
            if row:
                result = dict(row)
                if result.get("metadata"):
                    result["metadata"] = sqlite3.loads(result["metadata"])
                return result
            return None
    
    def list_kbs(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """列出所有知识库"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if include_inactive:
                cursor = conn.execute(
                    "SELECT * FROM knowledge_bases ORDER BY created_at DESC"
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM knowledge_bases WHERE is_active = 1 ORDER BY created_at DESC"
                )
            results = []
            for row in cursor.fetchall():
                item = dict(row)
                if item.get("metadata"):
                    try:
                        import json
                        item["metadata"] = json.loads(item["metadata"])
                    except:
                        item["metadata"] = None
                results.append(item)
            return results
    
    def update_kb(
        self,
        kb_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """更新知识库信息"""
        if kb_id == self.DEFAULT_KB:
            raise ValueError("不能修改默认知识库")
        
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if metadata is not None:
            updates.append("metadata = ?")
            import json
            params.append(json.dumps(metadata))
        
        if not updates:
            return False
        
        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(kb_id)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                f"UPDATE knowledge_bases SET {', '.join(updates)} WHERE id = ?",
                params
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_kb(self, kb_id: str) -> bool:
        """删除知识库（软删除）"""
        if kb_id == self.DEFAULT_KB:
            raise ValueError("不能删除默认知识库")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "UPDATE knowledge_bases SET is_active = 0 WHERE id = ?",
                (kb_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def hard_delete_kb(self, kb_id: str) -> bool:
        """硬删除知识库（谨慎使用）"""
        if kb_id == self.DEFAULT_KB:
            raise ValueError("不能删除默认知识库")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM knowledge_bases WHERE id = ?",
                (kb_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def get_collection_name(self, kb_id: str) -> str:
        """获取知识库对应的 collection 名称"""
        if kb_id == self.DEFAULT_KB:
            return "qms_docs"
        
        kb = self.get_kb(kb_id)
        if kb:
            return kb["collection_name"]
        return "qms_docs"  # 默认 fallback


# 全局服务实例
kb_service = KnowledgeBaseService()
