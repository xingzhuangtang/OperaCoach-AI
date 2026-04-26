"""
唱段 API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.opera_segment import OperaSegment
from app.models.opera_work import OperaWork
from app.models.segment_slice import SegmentSlice
from app.schemas.user import UserResponse
from app.schemas.user import OperaSegmentResponse, OperaSegmentDetailResponse, OperaWorkResponse, OperaWorkCreate

router = APIRouter()


# ========== 戏曲作品管理 ==========

@router.post("/works", response_model=OperaWorkResponse)
async def create_work(
    work_data: OperaWorkCreate,
    db: Session = Depends(get_db)
):
    """创建戏曲作品"""
    work = OperaWork(
        name=work_data.name,
        category=work_data.category,
        description=work_data.description,
    )
    db.add(work)
    db.commit()
    db.refresh(work)
    return work


@router.get("/works", response_model=list[OperaWorkResponse])
async def list_works(db: Session = Depends(get_db)):
    """获取戏曲作品列表"""
    return db.query(OperaWork).all()


@router.post("", response_model=OperaSegmentResponse)
async def create_segment(
    segment_data: dict,
    db: Session = Depends(get_db)
):
    """创建唱段"""
    work = db.query(OperaWork).filter(OperaWork.id == segment_data.get("work_id")).first()
    if not work:
        raise HTTPException(status_code=404, detail="所属作品不存在")

    segment = OperaSegment(
        work_id=segment_data.get("work_id"),
        name=segment_data.get("name"),
        audio_url=segment_data.get("audio_url"),
        video_url=segment_data.get("video_url"),
    )
    db.add(segment)
    db.commit()
    db.refresh(segment)
    return segment


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
):
    """音频智能切片"""
    from app.processors.audio import AudioSlicer
    
    segment = db.query(OperaSegment).filter(OperaSegment.id == segment_id).first()
    if not segment:
        raise HTTPException(status_code=404, detail="唱段不存在")

    if not segment.audio_url:
        raise HTTPException(status_code=400, detail="唱段没有音频文件")

    # 构建音频文件路径
    from app.core.config import settings
    from pathlib import Path
    audio_path = Path(settings.UPLOAD_DIR) / segment.audio_url.removeprefix("/uploads/")
    
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="音频文件不存在")

    try:
        # 创建切片输出目录
        from pathlib import Path
        from app.core.config import settings
        UPLOAD_DIR = Path(settings.UPLOAD_DIR)
        slices_dir = UPLOAD_DIR / "slices"
        slices_dir.mkdir(parents=True, exist_ok=True)
        
        # 执行切片（生成实际音频文件）
        slicer = AudioSlicer()
        slices = slicer.slice_by_phrases(str(audio_path), output_dir=str(slices_dir))
        
        # 保存切片到数据库
        from app.models.segment_slice import SegmentSlice
        for i, slice_data in enumerate(slices):
            segment_slice = SegmentSlice(
                segment_id=segment_id,
                slice_index=i + 1,
                start_time=slice_data["start_time"],
                end_time=slice_data["end_time"],
                audio_url=slice_data.get("audio_url"),
            )
            db.add(segment_slice)
        
        db.commit()
        
        # 返回切片列表
        return db.query(SegmentSlice).filter(SegmentSlice.segment_id == segment_id).all()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
