"""
唱段模型
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class OperaSegment(Base):
    __tablename__ = "opera_segments"

    id = Column(Integer, primary_key=True, index=True)
    work_id = Column(Integer, ForeignKey("opera_works.id"), nullable=False)
    name = Column(String(200), nullable=False)
    video_url = Column(String(500))
    audio_url = Column(String(500))
    lyrics = Column(String(5000))  # 完整歌词
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关联
    work = relationship("OperaWork")
    slices = relationship("SegmentSlice", back_populates="segment", cascade="all, delete-orphan")
