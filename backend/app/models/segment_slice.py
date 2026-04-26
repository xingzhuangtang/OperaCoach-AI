"""
唱段切片模型
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class SegmentSlice(Base):
    __tablename__ = "segment_slices"

    id = Column(Integer, primary_key=True, index=True)
    segment_id = Column(Integer, ForeignKey("opera_segments.id"), nullable=False)
    slice_index = Column(Integer, nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    lyrics = Column(String(1000))
    commands = Column(String(2000))
    pitches = Column(JSON)  # 音高序列 JSON 数组
    audio_url = Column(String(500))  # 切片音频文件 URL
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关联
    segment = relationship("OperaSegment", back_populates="slices")
