"""
数据库模型
"""
from app.models.user import User
from app.models.opera_work import OperaWork
from app.models.opera_segment import OperaSegment
from app.models.segment_slice import SegmentSlice
from app.models.music_generation import MusicGeneration
from app.models.music_album import MusicAlbum

__all__ = ["User", "OperaWork", "OperaSegment", "SegmentSlice", "MusicGeneration", "MusicAlbum"]
