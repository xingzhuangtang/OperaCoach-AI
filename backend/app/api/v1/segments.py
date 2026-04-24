"""
唱段 API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.opera_segment import OperaSegment
from app.models.segment_slice import SegmentSlice
from app.schemas.user import UserResponse
from app.schemas.user import OperaSegmentResponse, OperaSegmentDetailResponse

router = APIRouter()


@router.get("/", response_model=list[OperaSegmentResponse])
async def list_segments(db: Session = Depends(get_db)):
    """获取所有唱段列表"""
    return db.query(OperaSegment).all()


@router.get("/{segment_id}", response_model=OperaSegmentDetailResponse)
async def get_segment(segment_id: int, db: Session = Depends(get_db)):
    """获取唱段详情（包含切片）"""
    segment = db.query(OperaSegment).filter(OperaSegment.id == segment_id).first()
    if not segment:
        raise HTTPException(status_code=404, detail="唱段不存在")
    return segment


@router.post("/{segment_id}/slice")
async def slice_audio(
    segment_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user),
):
    """音频智能切片"""
    segment = db.query(OperaSegment).filter(OperaSegment.id == segment_id).first()
    if not segment:
        raise HTTPException(status_code=404, detail="唱段不存在")

    if not segment.audio_url:
        raise HTTPException(status_code=400, detail="唱段没有音频文件")

    # TODO: 调用 AI 服务进行切片
    # 这里先返回模拟数据
    return {
        "code": 0,
        "message": "切片功能开发中",
        "data": {
            "segment_id": segment_id,
            "num_slices": 0,
        },
    }
