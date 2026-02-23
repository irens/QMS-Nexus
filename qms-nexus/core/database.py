"""
数据库统一架构管理
使用 SQLAlchemy ORM 管理所有表
统一数据库文件: ./data/qms_nexus.db
"""
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Generator
from contextlib import contextmanager

from sqlalchemy import (
    create_engine, Column, String, Integer, Float, Boolean, 
    DateTime, Text, ForeignKey, UniqueConstraint, Index, event
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship
from sqlalchemy.pool import StaticPool

from core.config import settings
from core.logger import get_logger

logger = get_logger(__name__)

# 基础模型
Base = declarative_base()


class TimestampMixin:
    """时间戳混入类"""
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============== 数据表模型 ==============

class Tag(Base, TimestampMixin):
    """标签表"""
    __tablename__ = 'tags'
    
    id = Column(String(36), primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    color = Column(String(7), default='#409EFF')
    usage_count = Column(Integer, default=0)
    
    # 关系
    documents = relationship("Document", secondary='document_tags', back_populates="tags")


class Document(Base, TimestampMixin):
    """文档元数据表"""
    __tablename__ = 'documents'
    
    id = Column(String(36), primary_key=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50))
    file_size = Column(Integer)
    upload_time = Column(DateTime)
    status = Column(String(20), default='Pending')  # Pending/Processing/Completed/Failed
    metadata_json = Column(Text)  # JSON 字符串
    chunks_count = Column(Integer)
    parse_time = Column(Float)
    error_message = Column(Text)
    kb_id = Column(String(36), ForeignKey('knowledge_bases.id'), default='default')
    
    # 关系
    kb = relationship("KnowledgeBase", back_populates="documents")
    tags = relationship("Tag", secondary='document_tags', back_populates="documents")


class DocumentTag(Base):
    """文档-标签关联表"""
    __tablename__ = 'document_tags'
    
    document_id = Column(String(36), ForeignKey('documents.id'), primary_key=True)
    tag_id = Column(String(36), ForeignKey('tags.id'), primary_key=True)


class KnowledgeBase(Base, TimestampMixin):
    """知识库表"""
    __tablename__ = 'knowledge_bases'
    
    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    collection_name = Column(String(100), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    metadata_json = Column(Text)  # JSON 字符串
    document_count = Column(Integer, default=0)
    
    # 关系
    documents = relationship("Document", back_populates="kb")


class Correction(Base):
    """修正库表"""
    __tablename__ = 'corrections'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    question = Column(Text, unique=True, nullable=False)
    correct_answer = Column(Text, nullable=False)
    original_answer = Column(Text)
    source_doc = Column(String(255))
    page_number = Column(Integer)
    is_active = Column(Boolean, default=True)
    metadata_json = Column(Text)  # JSON 字符串
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ChatLog(Base):
    """问答日志表"""
    __tablename__ = 'chat_logs'
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36))
    kb_id = Column(String(36), ForeignKey('knowledge_bases.id'), default='default')
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    sources_json = Column(Text)  # JSON 字符串
    is_corrected = Column(Boolean, default=False)
    correction_id = Column(Integer, ForeignKey('corrections.id'))
    response_time_ms = Column(Integer)
    model_used = Column(String(50))
    tokens_used = Column(Integer)
    ip_address = Column(String(45))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    correction = relationship("Correction")
    feedbacks = relationship("Feedback", back_populates="chat_log")


class Feedback(Base):
    """反馈表"""
    __tablename__ = 'feedbacks'
    
    id = Column(String(36), primary_key=True)
    chat_log_id = Column(String(36), ForeignKey('chat_logs.id'), nullable=False)
    rating = Column(String(20), nullable=False)  # thumbs_up / thumbs_down
    comment = Column(Text)
    user_id = Column(String(36))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    chat_log = relationship("ChatLog", back_populates="feedbacks")
    
    __table_args__ = (
        UniqueConstraint('chat_log_id', 'user_id', name='uix_feedback_user'),
    )


class ApiKey(Base):
    """API Key 表"""
    __tablename__ = 'api_keys'
    
    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    key_hash = Column(String(64), unique=True, nullable=False)
    key_preview = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime)
    is_active = Column(Boolean, default=True)
    request_count = Column(Integer, default=0)
    rate_limit = Column(Integer, default=1000)


class IpWhitelist(Base):
    """IP 白名单表"""
    __tablename__ = 'ip_whitelist'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ip_address = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SystemLog(Base):
    """系统日志表"""
    __tablename__ = 'system_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    level = Column(String(20), nullable=False)  # DEBUG/INFO/WARNING/ERROR/CRITICAL
    module = Column(String(100))
    message = Column(Text, nullable=False)
    user_id = Column(String(36))
    request_id = Column(String(36))
    ip_address = Column(String(45))
    metadata_json = Column(Text)  # JSON 字符串
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_system_logs_created', 'created_at'),
        Index('idx_system_logs_level', 'level'),
        Index('idx_system_logs_module', 'module'),
    )


class ApiCallStat(Base):
    """API 调用统计表"""
    __tablename__ = 'api_call_stats'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    api_key_id = Column(String(36), ForeignKey('api_keys.id'))
    endpoint = Column(String(255))
    method = Column(String(10))
    status_code = Column(Integer)
    response_time_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_api_stats_created', 'created_at'),
        Index('idx_api_stats_key', 'api_key_id'),
    )


class User(Base):
    """用户表"""
    __tablename__ = 'users'
    
    id = Column(String(36), primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100))
    role = Column(String(20), default='user')  # admin/user/guest
    status = Column(String(20), default='active')
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login_at = Column(DateTime)


class AuthConfig(Base):
    """认证配置表"""
    __tablename__ = 'auth_config'
    
    key = Column(String(50), primary_key=True)
    value = Column(Text, nullable=False)


# ============== 数据库管理器 ==============

class DatabaseManager:
    """
    数据库管理器（单例模式）
    统一管理数据库连接和会话
    """
    
    _instance: Optional['DatabaseManager'] = None
    _engine = None
    _session_factory = None
    
    def __new__(cls) -> 'DatabaseManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._engine is not None:
            return
        
        # 确保数据目录存在
        db_path = Path(settings.DATABASE_URL.replace('sqlite:///', ''))
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 创建引擎
        self._engine = create_engine(
            settings.DATABASE_URL,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=settings.DEBUG
        )
        
        # 创建会话工厂
        self._session_factory = sessionmaker(
            bind=self._engine,
            autocommit=False,
            autoflush=False
        )
        
        # 监听连接事件，启用外键约束
        @event.listens_for(self._engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
        
        logger.info(f"数据库管理器初始化完成: {settings.DATABASE_URL}")
    
    def create_tables(self):
        """创建所有表"""
        Base.metadata.create_all(self._engine)
        logger.info("数据库表创建完成")
        
        # 初始化默认数据
        self._init_default_data()
    
    def _init_default_data(self):
        """初始化默认数据"""
        with self.get_session() as session:
            # 初始化认证配置
            default_configs = [
                ('auth_enabled', '0'),
                ('whitelist_enabled', '0'),
            ]
            for key, value in default_configs:
                existing = session.query(AuthConfig).filter_by(key=key).first()
                if not existing:
                    session.add(AuthConfig(key=key, value=value))
            
            # 初始化默认知识库
            default_kb = session.query(KnowledgeBase).filter_by(id='default').first()
            if not default_kb:
                session.add(KnowledgeBase(
                    id='default',
                    name='默认知识库',
                    description='系统默认知识库',
                    collection_name='qms_docs'
                ))
            
            session.commit()
            logger.info("默认数据初始化完成")
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        获取数据库会话（上下文管理器）
        
        使用示例:
            with db_manager.get_session() as session:
                user = session.query(User).first()
        """
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_engine(self):
        """获取数据库引擎"""
        return self._engine
    
    def check_connection(self) -> bool:
        """检查数据库连接是否正常"""
        try:
            with self._engine.connect() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"数据库连接检查失败: {e}")
            return False
    
    def drop_all_tables(self):
        """删除所有表（危险操作，仅用于测试）"""
        Base.metadata.drop_all(self._engine)
        logger.warning("所有数据库表已删除")


# 全局数据库管理器实例
db_manager = DatabaseManager()


# ============== 便捷函数 ==============

def init_database():
    """初始化数据库（创建表和默认数据）"""
    db_manager.create_tables()
    logger.info("数据库初始化完成")


def get_db_session() -> Generator[Session, None, None]:
    """
    FastAPI 依赖注入使用的会话生成器
    
    使用示例:
        @router.get("/users")
        def get_users(session: Session = Depends(get_db_session)):
            return session.query(User).all()
    """
    session = db_manager._session_factory()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
