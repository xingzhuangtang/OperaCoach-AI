"""
AI 作曲历史记录模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.core.database import Base


class MusicGeneration(Base):
    """AI 作曲历史记录"""
    __tablename__ = "music_generations"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), default="", comment="曲目名称")
    lyrics = Column(Text, nullable=False, comment="歌词内容")
    style = Column(String(50), default="流行", comment="音乐风格")
    duration = Column(Integer, default=30, comment="时长（秒）")
    voice_gender = Column(String(10), default="", comment="声音性别: 男/女")
    audio_url = Column(String(500), nullable=False, comment="生成的音频URL")
    cover_url = Column(String(500), default="", comment="封面图片URL")
    album_id = Column(Integer, nullable=True, comment="所属专辑ID")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
