"""
后端配置文件
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "OperaCoach-AI"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = True

    # 数据库 (MVP 阶段使用 SQLite，后期可切换到 PostgreSQL)
    DATABASE_URL: str = "sqlite:///./opera_coach.db"

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
    
    # 阿里 DashScope API（用于歌词识别）
    DASHSCOPE_API_KEY: str = ""

    # Demucs 音频分离（UVR5 替代方案）
    UVR_MODEL: str = "htdemucs"
    UVR_DEVICE: str = "cpu"

    # 衬字映射表（数字简谱 -> 衬字语气词）
    # 5 个最顺口的单字：1=啊, 2=哎, 3=咦, 4=呦, 5=呜
    CHENZI_MAPPING: dict = {
        "1": "啊",
        "2": "哎",
        "3": "咦",
        "4": "呦",
        "5": "呜",
    }

    class Config:
        env_file = ".env"


settings = Settings()
