"""
Redis 和异步任务相关配置
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Redis 配置
    REDIS_URL: str = "redis://localhost:6379/0"
    ARQ_QUEUE_NAME: str = "qms_nexus_queue"

    class Config:
        env_file = ".env"


settings = Settings()