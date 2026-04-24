"""
后端配置文件
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "OperaCoach-AI"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = True

    # 数据库
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/opera_coach"

    # 服务器
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    # 文件存储
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 500 * 1024 * 1024  # 500MB

    # Whisper 模型
    WHISPER_MODEL_SIZE: str = "small"

    class Config:
        env_file = ".env"


settings = Settings()
