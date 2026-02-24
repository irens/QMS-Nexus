"""
数据库迁移脚本：从 v1.0.0 迁移到 v1.1.0
将现有 documents 表数据迁移到 document_versions 表
"""
import asyncio
import hashlib
import uuid
from datetime import datetime
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from core.database import db_manager, Document, DocumentVersion, DocumentApprovalHistory
from core.logger import get_logger

logger = get_logger(__name__)


def generate_uuid() -> str:
    """生成 UUID"""
    return str(uuid.uuid4())


def calculate_file_hash(file_path: str) -> str:
    """计算文件 SHA256 哈希"""
    try:
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception as e:
        logger.warning(f"无法计算文件哈希: {file_path}, 错误: {e}")
        return ""


async def migrate_documents_to_versions():
    """将现有文档数据迁移到 document_versions 表"""
    logger.info("开始数据迁移...")
    
    with db_manager.get_session() as session:
        # 1. 获取所有现有文档
        documents = session.query(Document).all()
        logger.info(f"找到 {len(documents)} 个文档需要迁移")
        
        migrated_count = 0
        error_count = 0
        
        for doc in documents:
            try:
                # 检查是否已存在对应的版本记录
                existing_version = session.query(DocumentVersion).filter(
                    DocumentVersion.document_id == doc.id
                ).first()
                
                if existing_version:
                    logger.info(f"文档 {doc.id} 已存在版本记录，跳过")
                    continue
                
                # 生成版本 ID
                version_id = generate_uuid()
                
                # 尝试计算文件哈希（如果文件存在）
                file_hash = ""
                if doc.metadata_json:
                    import json
                    try:
                        metadata = json.loads(doc.metadata_json)
                        file_path = metadata.get('file_path', '')
                        if file_path and Path(file_path).exists():
                            file_hash = calculate_file_hash(file_path)
                    except:
                        pass
                
                # 如果没有计算出哈希，使用占位符
                if not file_hash:
                    file_hash = hashlib.sha256(f"{doc.id}_{doc.filename}".encode()).hexdigest()
                
                # 创建版本记录
                version = DocumentVersion(
                    id=version_id,
                    document_id=doc.id,
                    version_number=1,
                    version_label="V1.0",
                    filename=doc.filename,
                    file_hash=file_hash,
                    file_size=doc.file_size,
                    file_type=doc.file_type,
                    status="effective",  # 现有文档标记为生效中
                    title=doc.filename,
                    description=None,
                    doc_type=None,
                    doc_code=None,
                    change_summary="初始版本（系统迁移生成）",
                    change_details="从 v1.0.0 迁移的初始版本",
                    previous_version_id=None,
                    effective_date=doc.upload_time or datetime.utcnow(),
                    review_date=None,
                    is_latest=True,
                    prepared_by="system",
                    reviewed_by=None,
                    approved_by="system",
                    approved_date=datetime.utcnow(),
                    kb_id=doc.kb_id or 'default',
                    created_by="system",
                    created_at=doc.upload_time or datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                session.add(version)
                
                # 创建审批历史记录
                approval_history = DocumentApprovalHistory(
                    document_version_id=version_id,
                    action="publish",
                    action_by="system",
                    action_at=datetime.utcnow(),
                    comment="系统迁移：初始版本自动生效",
                    from_status=None,
                    to_status="effective"
                )
                session.add(approval_history)
                
                # 更新 documents 表的 current_version_id
                doc.current_version_id = version_id
                
                migrated_count += 1
                logger.info(f"已迁移文档: {doc.filename} (ID: {doc.id}) -> 版本: {version_id}")
                
            except Exception as e:
                error_count += 1
                logger.error(f"迁移文档 {doc.id} 失败: {e}")
                continue
        
        session.commit()
        logger.info(f"数据迁移完成: 成功 {migrated_count} 个, 失败 {error_count} 个")
        
        return migrated_count, error_count


async def verify_migration():
    """验证迁移结果"""
    logger.info("开始验证迁移结果...")
    
    with db_manager.get_session() as session:
        # 统计文档数量
        doc_count = session.query(Document).count()
        version_count = session.query(DocumentVersion).count()
        history_count = session.query(DocumentApprovalHistory).count()
        
        # 检查未关联版本的文档
        orphaned_docs = session.query(Document).filter(
            Document.current_version_id.is_(None)
        ).count()
        
        logger.info(f"验证结果:")
        logger.info(f"  - Documents 表记录数: {doc_count}")
        logger.info(f"  - DocumentVersions 表记录数: {version_count}")
        logger.info(f"  - DocumentApprovalHistory 表记录数: {history_count}")
        logger.info(f"  - 未关联版本的文档数: {orphaned_docs}")
        
        if orphaned_docs > 0:
            logger.warning(f"警告: 有 {orphaned_docs} 个文档未关联版本")
        
        if doc_count == version_count and orphaned_docs == 0:
            logger.info("✅ 迁移验证通过")
            return True
        else:
            logger.warning("⚠️ 迁移验证发现问题")
            return False


async def rollback_migration():
    """回滚迁移（删除所有版本数据）"""
    logger.warning("开始回滚迁移...")
    
    with db_manager.get_session() as session:
        # 删除审批历史
        session.query(DocumentApprovalHistory).delete()
        
        # 删除版本记录
        session.query(DocumentVersion).delete()
        
        # 重置 documents 表的 current_version_id
        session.execute(
            text("UPDATE documents SET current_version_id = NULL")
        )
        
        session.commit()
        logger.info("回滚完成")


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='数据库迁移工具 v1.0.0 -> v1.1.0')
    parser.add_argument('--migrate', action='store_true', help='执行迁移')
    parser.add_argument('--verify', action='store_true', help='验证迁移结果')
    parser.add_argument('--rollback', action='store_true', help='回滚迁移')
    parser.add_argument('--all', action='store_true', help='执行迁移并验证')
    
    args = parser.parse_args()
    
    if args.all or (not args.migrate and not args.verify and not args.rollback):
        # 执行完整流程
        migrated, errors = await migrate_documents_to_versions()
        await verify_migration()
        print(f"\n{'='*50}")
        print(f"迁移完成: 成功 {migrated} 个, 失败 {errors} 个")
        print(f"{'='*50}")
    elif args.migrate:
        await migrate_documents_to_versions()
    elif args.verify:
        await verify_migration()
    elif args.rollback:
        await rollback_migration()


if __name__ == "__main__":
    asyncio.run(main())
