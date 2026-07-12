"""
音乐专辑模型
"""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class MusicAlbum(Base):
    """音乐专辑"""
    __tablename__ = "music_albums"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, comment="专辑名称")
    cover_url = Column(String(500), default="", comment="封面图片URL")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
