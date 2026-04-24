"""
数据库初始化脚本
"""
from app.core.database import engine, Base
from app.models.user import User
from app.models.opera_work import OperaWork
from app.models.opera_segment import OperaSegment
from app.models.segment_slice import SegmentSlice

print("创建数据库表...")
Base.metadata.create_all(bind=engine)
print("✅ 数据库表创建完成")
