"""
修正库服务
管理人工修正的答案，支持RAG优先检索
"""
import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

from core.logger import get_logger

logger = get_logger(__name__)

# 数据库文件路径
DB_PATH = Path("./data/corrections.db")


class CorrectionService:
    """修正库服务，使用SQLite存储人工修正记录"""

    def __init__(self):
        self.db_path = DB_PATH
        self._ensure_db()

    def _ensure_db(self):
        """确保数据库和表存在"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS corrections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question TEXT NOT NULL UNIQUE,
                    correct_answer TEXT NOT NULL,
                    original_answer TEXT,
                    source_doc TEXT,
                    page_number INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    metadata TEXT
                )
            """)
            # 创建索引加速查询
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_question ON corrections(question)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_active ON corrections(is_active)
            """)
            conn.commit()

    def add_correction(
        self,
        question: str,
        correct_answer: str,
        original_answer: Optional[str] = None,
        source_doc: Optional[str] = None,
        page_number: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        添加或更新修正记录
        
        Returns:
            修正记录ID
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO corrections 
                (question, correct_answer, original_answer, source_doc, page_number, metadata, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(question) DO UPDATE SET
                    correct_answer = excluded.correct_answer,
                    original_answer = excluded.original_answer,
                    source_doc = excluded.source_doc,
                    page_number = excluded.page_number,
                    metadata = excluded.metadata,
                    updated_at = excluded.updated_at,
                    is_active = 1
                """,
                (
                    question.strip(),
                    correct_answer,
                    original_answer,
                    source_doc,
                    page_number,
                    json.dumps(metadata) if metadata else None,
                    datetime.now().isoformat()
                )
            )
            conn.commit()
            logger.info(f"修正记录已保存: question={question[:50]}...")
            return cursor.lastrowid

    def find_correction(self, question: str) -> Optional[Dict[str, Any]]:
        """
        查找问题对应的修正答案
        
        Returns:
            修正记录字典，如果不存在返回None
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT * FROM corrections 
                WHERE question = ? AND is_active = 1
                """,
                (question.strip(),)
            )
            row = cursor.fetchone()
            if row:
                result = dict(row)
                if result.get("metadata"):
                    result["metadata"] = json.loads(result["metadata"])
                logger.info(f"修正库命中: question={question[:50]}...")
                return result
            return None

    def search_corrections(
        self,
        keyword: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        搜索修正记录
        
        Returns:
            {"items": [...], "total": int}
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # 构建查询条件
            conditions = []
            params = []
            if keyword:
                conditions.append("(question LIKE ? OR correct_answer LIKE ?)")
                params.extend([f"%{keyword}%", f"%{keyword}%"])
            if is_active is not None:
                conditions.append("is_active = ?")
                params.append(1 if is_active else 0)
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            
            # 查询总数
            count_sql = f"SELECT COUNT(*) FROM corrections {where_clause}"
            cursor = conn.execute(count_sql, params)
            total = cursor.fetchone()[0]
            
            # 查询数据
            sql = f"""
                SELECT id, question, correct_answer, original_answer, source_doc, 
                       page_number, created_at, updated_at, is_active
                FROM corrections {where_clause}
                ORDER BY updated_at DESC
                LIMIT ? OFFSET ?
            """
            cursor = conn.execute(sql, params + [limit, offset])
            
            items = []
            for row in cursor.fetchall():
                item = dict(row)
                items.append(item)
            
            return {"items": items, "total": total}

    def get_correction_by_id(self, correction_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取修正记录"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM corrections WHERE id = ?",
                (correction_id,)
            )
            row = cursor.fetchone()
            if row:
                result = dict(row)
                if result.get("metadata"):
                    result["metadata"] = json.loads(result["metadata"])
                return result
            return None

    def update_correction(
        self,
        correction_id: int,
        correct_answer: Optional[str] = None,
        is_active: Optional[bool] = None,
        source_doc: Optional[str] = None,
        page_number: Optional[int] = None
    ) -> bool:
        """更新修正记录"""
        updates = []
        params = []
        
        if correct_answer is not None:
            updates.append("correct_answer = ?")
            params.append(correct_answer)
        if is_active is not None:
            updates.append("is_active = ?")
            params.append(1 if is_active else 0)
        if source_doc is not None:
            updates.append("source_doc = ?")
            params.append(source_doc)
        if page_number is not None:
            updates.append("page_number = ?")
            params.append(page_number)
        
        if not updates:
            return False
        
        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(correction_id)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                f"UPDATE corrections SET {', '.join(updates)} WHERE id = ?",
                params
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_correction(self, correction_id: int) -> bool:
        """删除修正记录（软删除）"""
        return self.update_correction(correction_id, is_active=False)

    def hard_delete_correction(self, correction_id: int) -> bool:
        """硬删除修正记录"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM corrections WHERE id = ?",
                (correction_id,)
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_stats(self) -> Dict[str, int]:
        """获取修正库统计信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM corrections WHERE is_active = 1"
            )
            active_count = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM corrections")
            total_count = cursor.fetchone()[0]
            
            return {
                "active": active_count,
                "total": total_count,
                "inactive": total_count - active_count
            }


# 全局服务实例
correction_service = CorrectionService()
