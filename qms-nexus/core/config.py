"""
统一配置管理
支持环境变量覆盖
"""
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # ============== 基础配置 ==============
    APP_NAME: str = "QMS-Nexus"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # ============== 服务器配置 ==============
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # ============== 数据库配置 ==============
    DATABASE_URL: str = "sqlite:///./data/qms_nexus.db"
    
    # ============== 向量库配置 ==============
    CHROMA_PERSIST_DIR: str = "./chroma_data"
    
    # ============== Redis 配置 ==============
    REDIS_URL: str = "redis://localhost:6379/0"
    ARQ_QUEUE_NAME: str = "qms_nexus_queue"
    
    # ============== LLM 配置 ==============
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_MODEL: str = "gpt-3.5-turbo"
    LLM_TIMEOUT: int = 60
    # 备选模型配置（JSON格式）
    LLM_FALLBACK_MODELS: str = '["gpt-3.5-turbo"]'
    
    # ============== 日志配置 ==============
    LOG_LEVEL: str = "INFO"
    LOG_RETENTION_DAYS: int = 30
    LOG_MAX_SIZE_MB: int = 10
    LOG_DIR: str = "./logs"
    
    # ============== 安全配置 ==============
    JWT_SECRET: str = "your-secret-key-change-in-production"
    JWT_EXPIRE_HOURS: int = 24
    
    # ============== 备份配置 ==============
    BACKUP_DIR: str = "./backups"
    BACKUP_RETENTION_DAYS: int = 30
    AUTO_BACKUP_ENABLED: bool = False
    AUTO_BACKUP_CRON: str = "0 2 * * *"  # 每天凌晨2点
    
    # ============== RAG 配置 ==============
    RAG_TOP_K: int = 5
    RAG_SIMILARITY_THRESHOLD: float = 0.7
    CORRECTION_MATCH_THRESHOLD: float = 0.9
    
    # ============== 限流配置 ==============
    RATE_LIMIT_DEFAULT: int = 1000  # 每小时请求数
    RATE_LIMIT_WINDOW: int = 3600   # 窗口大小（秒）

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 全局配置实例
settings = Settings()


def validate_critical_config() -> list[str]:
    """
    验证关键配置是否完整
    
    Returns:
        缺失的关键配置列表
    """
    missing = []
    
    # 检查 LLM 配置
    if not settings.LLM_API_KEY:
        missing.append("LLM_API_KEY: 未配置 LLM API 密钥，问答功能将不可用")
    
    # 检查 JWT 密钥（生产环境）
    if not settings.DEBUG and settings.JWT_SECRET == "your-secret-key-change-in-production":
        missing.append("JWT_SECRET: 请修改默认的 JWT 密钥")
    
    return missing


def print_config_status():
    """打印配置状态"""
    print(f"\n{'='*50}")
    print(f"应用名称: {settings.APP_NAME}")
    print(f"应用版本: {settings.APP_VERSION}")
    print(f"调试模式: {settings.DEBUG}")
    print(f"数据库: {settings.DATABASE_URL}")
    print(f"向量库: {settings.CHROMA_PERSIST_DIR}")
    print(f"Redis: {settings.REDIS_URL}")
    print(f"LLM 模型: {settings.LLM_MODEL}")
    print(f"日志级别: {settings.LOG_LEVEL}")
    print(f"{'='*50}\n")
    
    # 检查关键配置
    missing = validate_critical_config()
    if missing:
        print("⚠️  配置警告:")
        for msg in missing:
            print(f"   - {msg}")
        print()


if __name__ == "__main__":
    print_config_status()
