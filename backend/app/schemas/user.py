"""
Pydantic 验证模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# 用户
class UserCreate(BaseModel):
    phone: str
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    phone: Optional[str]
    username: str
    role: str

    class Config:
        from_attributes = True


# 登录
class LoginRequest(BaseModel):
    phone: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


# 戏曲作品
class OperaWorkCreate(BaseModel):
    name: str
    category: Optional[str] = None
    description: Optional[str] = None


class OperaWorkResponse(BaseModel):
    id: int
    name: str
    category: Optional[str]

    class Config:
        from_attributes = True


# 唱段
class OperaSegmentCreate(BaseModel):
    work_id: int
    name: str


class OperaSegmentResponse(BaseModel):
    id: int
    work_id: int
    name: str
    video_url: Optional[str]
    audio_url: Optional[str]

    class Config:
        from_attributes = True


# 切片
class SegmentSliceResponse(BaseModel):
    id: int
    slice_index: int
    start_time: float
    end_time: float
    lyrics: Optional[str]
    commands: Optional[str]
    pitches: Optional[list]

    class Config:
        from_attributes = True


# 唱段详情（包含切片）
class OperaSegmentDetailResponse(BaseModel):
    id: int
    work_id: int
    name: str
    video_url: Optional[str]
    audio_url: Optional[str]
    slices: List[SegmentSliceResponse] = []

    class Config:
        from_attributes = True
