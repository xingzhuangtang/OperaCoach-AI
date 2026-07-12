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


@router.delete("/works/{work_id}")
async def delete_work(work_id: int, db: Session = Depends(get_db)):
    """删除作品（级联删除关联唱段和切片）"""

    work = db.query(OperaWork).filter(OperaWork.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")

    # 删除该作品的所有唱段及其切片
    segments = db.query(OperaSegment).filter(OperaSegment.work_id == work_id).all()
    for segment in segments:
        db.query(SegmentSlice).filter(SegmentSlice.segment_id == segment.id).delete()
        db.delete(segment)

    db.delete(work)
    db.commit()
    return {"message": "删除成功"}


@router.get("/works/{work_id}", response_model=OperaWorkResponse)
async def get_work(work_id: int, db: Session = Depends(get_db)):
    """获取单个作品详情"""
    work = db.query(OperaWork).filter(OperaWork.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")
    return work


@router.get("/by-work/{work_id}", response_model=OperaSegmentDetailResponse)
async def get_segment_by_work(work_id: int, db: Session = Depends(get_db)):
    """根据作品 ID 获取第一个唱段详情（包含切片）"""
    segment = db.query(OperaSegment).filter(OperaSegment.work_id == work_id).first()
    if not segment:
        raise HTTPException(status_code=404, detail="该作品还没有唱段，请先上传内容")
    return segment


@router.get("/works/{work_id}/segments", response_model=list[OperaSegmentResponse])
async def list_segments_by_work(work_id: int, db: Session = Depends(get_db)):
    """获取指定作品的唱段列表"""
    work = db.query(OperaWork).filter(OperaWork.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")
    return db.query(OperaSegment).filter(OperaSegment.work_id == work_id).all()


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


@router.delete("/{segment_id}")
async def delete_segment(segment_id: int, db: Session = Depends(get_db)):
    """删除唱段（级联删除关联切片）"""
    segment = db.query(OperaSegment).filter(OperaSegment.id == segment_id).first()
    if not segment:
        raise HTTPException(status_code=404, detail="唱段不存在")

    # 删除该唱段的所有切片
    db.query(SegmentSlice).filter(SegmentSlice.segment_id == segment_id).delete()
    db.delete(segment)
    db.commit()
    return {"message": "删除成功"}


@router.post("/{segment_id}/slice")
async def slice_audio(
    segment_id: int,
    db: Session = Depends(get_db),
):
    """音频智能切片 + 歌词提取"""
    from app.processors.audio import AudioSlicer, AudioProcessor
    
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
        # 1. 提取完整歌词
        processor = AudioProcessor()
        full_lyrics = processor.extract_lyrics(str(audio_path))
        
        # 2. 提取带时间戳的歌词片段
        lyrics_segments = processor.extract_lyrics_with_timestamps(str(audio_path))
        
        # 3. 创建切片输出目录
        UPLOAD_DIR = Path(settings.UPLOAD_DIR)
        slices_dir = UPLOAD_DIR / "slices"
        slices_dir.mkdir(parents=True, exist_ok=True)
        
        # 4. 执行切片（生成实际音频文件）
        slicer = AudioSlicer()
        slices = slicer.slice_by_phrases(str(audio_path), output_dir=str(slices_dir))
        
        # 5. 保存切片到数据库，并匹配歌词
        from app.models.segment_slice import SegmentSlice
        # 删除旧切片
        db.query(SegmentSlice).filter(SegmentSlice.segment_id == segment_id).delete()
        
        for i, slice_data in enumerate(slices):
            # 匹配该时间段内的歌词
            slice_lyrics = []
            for lyric in lyrics_segments:
                # 如果歌词时间段与切片时间段有重叠
                if lyric["start"] < slice_data["end_time"] and lyric["end"] > slice_data["start_time"]:
                    slice_lyrics.append(lyric["text"])
            
            segment_slice = SegmentSlice(
                segment_id=segment_id,
                slice_index=i + 1,
                start_time=slice_data["start_time"],
                end_time=slice_data["end_time"],
                audio_url=slice_data.get("audio_url"),
                lyrics="\n".join(slice_lyrics) if slice_lyrics else "",
            )
            db.add(segment_slice)
        
        db.commit()
        
        # 返回完整歌词和切片列表
        return {
            "full_lyrics": full_lyrics,
            "slices": db.query(SegmentSlice).filter(SegmentSlice.segment_id == segment_id).all()
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{segment_id}/extract-lyrics")
async def extract_lyrics(
    segment_id: int,
    db: Session = Depends(get_db),
):
    """提取音频歌词"""
    from app.processors.audio import AudioProcessor
    
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
        # 提取完整歌词
        processor = AudioProcessor()
        full_lyrics = processor.extract_lyrics(str(audio_path))
        
        # 更新数据库
        segment.lyrics = full_lyrics
        db.commit()
        
        return {
            "full_lyrics": full_lyrics,
            "message": "歌词提取成功"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{segment_id}/lyrics")
async def update_lyrics(
    segment_id: int,
    lyrics_data: dict,
    db: Session = Depends(get_db),
):
    """编辑保存完整歌词"""
    segment = db.query(OperaSegment).filter(OperaSegment.id == segment_id).first()
    if not segment:
        raise HTTPException(status_code=404, detail="唱段不存在")

    segment.lyrics = lyrics_data.get("lyrics", "")
    db.commit()
    return {"message": "歌词保存成功", "lyrics": segment.lyrics}


@router.put("/{segment_id}/slices/{slice_id}")
async def update_slice_lyrics(
    segment_id: int,
    slice_id: int,
    lyrics_data: dict,
    db: Session = Depends(get_db),
):
    """编辑保存切片歌词"""
    segment = db.query(OperaSegment).filter(OperaSegment.id == segment_id).first()
    if not segment:
        raise HTTPException(status_code=404, detail="唱段不存在")

    segment_slice = db.query(SegmentSlice).filter(
        SegmentSlice.id == slice_id,
        SegmentSlice.segment_id == segment_id,
    ).first()
    if not segment_slice:
        raise HTTPException(status_code=404, detail="切片不存在")

    segment_slice.lyrics = lyrics_data.get("lyrics", "")
    db.commit()
    return {"message": "切片歌词保存成功", "lyrics": segment_slice.lyrics}


@router.get("/{segment_id}/pitches")
async def get_pitches(
    segment_id: int,
    db: Session = Depends(get_db),
):
    """
    提取所有切片的音高数据（逐片提取，速度快）
    结果缓存到数据库，下次直接返回
    """
    from app.processors.audio import AudioProcessor
    from app.core.config import settings
    from pathlib import Path

    segment = db.query(OperaSegment).filter(OperaSegment.id == segment_id).first()
    if not segment:
        raise HTTPException(status_code=404, detail="唱段不存在")

    slices = db.query(SegmentSlice).filter(
        SegmentSlice.segment_id == segment_id
    ).order_by(SegmentSlice.slice_index).all()

    if not slices:
        raise HTTPException(status_code=400, detail="没有切片")

    processor = AudioProcessor()
    results = []
    
    for slice in slices:
        # 如果已缓存，直接返回
        if slice.pitches:
            results.append({
                "slice_id": slice.id,
                "slice_index": slice.slice_index,
                "pitches": slice.pitches
            })
            continue
        
        # 提取切片音高
        if not slice.audio_url:
            results.append({
                "slice_id": slice.id,
                "slice_index": slice.slice_index,
                "pitches": None
            })
            continue
        
        audio_path = Path(settings.UPLOAD_DIR) / slice.audio_url.removeprefix("/uploads/")
        if not audio_path.exists():
            results.append({
                "slice_id": slice.id,
                "slice_index": slice.slice_index,
                "pitches": None
            })
            continue
        
        try:
            pitches = processor.extract_pitch(str(audio_path))
            slice.pitches = pitches
            db.commit()
            results.append({
                "slice_id": slice.id,
                "slice_index": slice.slice_index,
                "pitches": pitches
            })
        except Exception as e:
            results.append({
                "slice_id": slice.id,
                "slice_index": slice.slice_index,
                "pitches": None,
                "error": str(e)
            })
    
    return {"slices": results}


@router.post("/{segment_id}/regenerate-chenzi")
async def regenerate_chenzi(
    segment_id: int,
    db: Session = Depends(get_db),
):
    """
    根据已缓存的音高数据重新生成衬字谱
    """
    from app.processors.chenzi import ChenziMapper, freq_to_solfege
    import numpy as np

    segment = db.query(OperaSegment).filter(OperaSegment.id == segment_id).first()
    if not segment:
        raise HTTPException(status_code=404, detail="唱段不存在")

    slices = db.query(SegmentSlice).filter(
        SegmentSlice.segment_id == segment_id
    ).order_by(SegmentSlice.slice_index).all()

    if not slices:
        raise HTTPException(status_code=400, detail="没有切片")

    mapper = ChenziMapper()
    updated_count = 0

    for slice in slices:
        if not slice.pitches or not slice.lyrics:
            continue

        char_count = len(slice.lyrics.replace(" ", "").replace("\n", "").strip())
        if char_count == 0:
            continue

        valid_pitches = [p for p in slice.pitches if p is not None and p > 0]
        if not valid_pitches:
            continue

        total_frames = len(slice.pitches)
        segment_len = total_frames // char_count
        if segment_len < 1:
            segment_len = 1

        digits = []
        for i in range(char_count):
            start = i * segment_len
            end = start + segment_len if i < char_count - 1 else total_frames
            segment_pitches = slice.pitches[start:end]
            valid_segment = [p for p in segment_pitches if p is not None and p > 0]

            if not valid_segment:
                digits.append("5")
                continue

            median_freq = float(np.median(valid_segment))
            solfege = freq_to_solfege(median_freq)
            digit = str(solfege) if 1 <= solfege <= 7 else "5"
            digits.append(digit)

        notation = " ".join(digits)
        chenzi = mapper.to_chenzi_string(notation)

        slice.numbered_notation = notation
        slice.chenzi_lyrics = chenzi
        updated_count += 1

    db.commit()

    return {
        "message": f"已更新 {updated_count} 个切片的衬字谱",
        "updated_count": updated_count
    }


@router.post("/{segment_id}/separate")
async def separate_audio(
    segment_id: int,
    db: Session = Depends(get_db),
):
    """
    音频分离：使用 Demucs 分离人声和伴奏
    返回: {vocal_url, accompaniment_url}
    """
    from app.processors.audio import AudioProcessor
    from app.core.config import settings
    from pathlib import Path

    segment = db.query(OperaSegment).filter(OperaSegment.id == segment_id).first()
    if not segment:
        raise HTTPException(status_code=404, detail="唱段不存在")

    if not segment.audio_url:
        raise HTTPException(status_code=400, detail="唱段没有音频文件")

    # 构建音频文件路径
    audio_path = Path(settings.UPLOAD_DIR) / segment.audio_url.removeprefix("/uploads/")

    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="音频文件不存在")

    try:
        processor = AudioProcessor()
        result = processor.separate_vocals(str(audio_path))

        # 更新数据库
        segment.vocal_url = "/uploads" + result["vocal_path"].split("/uploads", 1)[1] if "/uploads" in result["vocal_path"] else result["vocal_path"]
        segment.accompaniment_url = "/uploads" + result["accompaniment_path"].split("/uploads", 1)[1] if "/uploads" in result["accompaniment_path"] else result["accompaniment_path"]
        segment.is_separated = True

        db.commit()

        return {
            "vocal_url": segment.vocal_url,
            "accompaniment_url": segment.accompaniment_url,
            "message": "音频分离成功",
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{segment_id}/smart-slice")
async def smart_slice(
    segment_id: int,
    db: Session = Depends(get_db),
):
    """
    智能切片 + 衬字谱生成（核心端点）
    1. 如果未分离，先分离人声
    2. 对人声进行 Fun-ASR 句子级切片
    3. 对每个切片生成衬字谱
    4. 保存到数据库
    返回: {full_lyrics, chenzi_full, slices}
    """
    from app.processors.audio import AudioProcessor
    from app.processors.chenzi import ChenziMapper
    from app.core.config import settings
    from pathlib import Path

    segment = db.query(OperaSegment).filter(OperaSegment.id == segment_id).first()
    if not segment:
        raise HTTPException(status_code=404, detail="唱段不存在")

    if not segment.audio_url:
        raise HTTPException(status_code=400, detail="唱段没有音频文件")

    try:
        processor = AudioProcessor()
        mapper = ChenziMapper()
        audio_path = Path(settings.UPLOAD_DIR) / segment.audio_url.removeprefix("/uploads/")
        if not audio_path.exists():
            raise HTTPException(status_code=404, detail="音频文件不存在")

        # 1. 尝试分离人声（Demucs 可选）
        vocal_path = None
        if segment.is_separated and segment.vocal_url:
            vocal_path = Path(settings.UPLOAD_DIR) / segment.vocal_url.removeprefix("/uploads/")
            if not vocal_path.exists():
                vocal_path = None

        if not vocal_path:
            try:
                result = processor.separate_vocals(str(audio_path))
                segment.vocal_url = "/uploads" + result["vocal_path"].split("/uploads", 1)[1] if "/uploads" in result["vocal_path"] else result["vocal_path"]
                segment.accompaniment_url = "/uploads" + result["accompaniment_path"].split("/uploads", 1)[1] if "/uploads" in result["accompaniment_path"] else result["accompaniment_path"]
                segment.is_separated = True
                db.commit()
                vocal_path = Path(settings.UPLOAD_DIR) / segment.vocal_url.removeprefix("/uploads/")
            except Exception as e:
                # Demucs 不可用，降级使用原始音频
                print(f"音频分离失败，使用原始音频: {e}")
                vocal_path = audio_path

        # 2. 对音频进行 Fun-ASR 句子级切片
        if not vocal_path.exists():
            raise HTTPException(status_code=404, detail="音频文件不存在")

        # 创建切片输出目录
        UPLOAD_DIR = Path(settings.UPLOAD_DIR)
        slices_dir = UPLOAD_DIR / "funasr_slices"
        slices_dir.mkdir(parents=True, exist_ok=True)

        slices = processor.slice_by_fun_asr_sentences(str(vocal_path), output_dir=str(slices_dir), segment_id=segment_id)

        if not slices:
            raise HTTPException(status_code=500, detail="Fun-ASR 识别失败，未能提取句子")

        # 3. 保存切片到数据库

        # 删除旧切片
        db.query(SegmentSlice).filter(SegmentSlice.segment_id == segment_id).delete()

        for i, slice_data in enumerate(slices):
            lyrics = slice_data.get("lyrics", "")

            # 先提取该切片的音高数据
            slice_audio_path = Path(settings.UPLOAD_DIR) / slice_data.get("audio_url", "").removeprefix("/uploads/")
            pitches = []
            if slice_audio_path.exists():
                try:
                    pitches = processor.extract_pitch(str(slice_audio_path))
                except Exception:
                    pass

            # 用真实音高生成精确衬字谱
            if pitches:
                chenzi_result = mapper.generate_chenzi_from_pitch(lyrics, pitches)
            else:
                chenzi_result = mapper.auto_generate_chenzi(lyrics)

            segment_slice = SegmentSlice(
                segment_id=segment_id,
                slice_index=i + 1,
                start_time=slice_data["start_time"],
                end_time=slice_data["end_time"],
                lyrics=lyrics,
                chenzi_lyrics=chenzi_result["chenzi"],
                numbered_notation=chenzi_result["notation"],
                audio_url=slice_data.get("audio_url"),
                pitches=pitches,
            )
            db.add(segment_slice)

        db.commit()

        full_lyrics = processor.extract_lyrics(str(vocal_path))
        # 生成完整衬字谱
        full_chenzi_result = mapper.auto_generate_chenzi(full_lyrics)

        return {
            "full_lyrics": full_lyrics,
            "chenzi_full": full_chenzi_result["chenzi"],
            "slices": db.query(SegmentSlice).filter(SegmentSlice.segment_id == segment_id).all(),
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{segment_id}/generate-chenzi")
async def generate_chenzi(
    segment_id: int,
    notation_data: dict,
    db: Session = Depends(get_db),
):
    """
    为已有切片手动输入数字简谱，生成衬字谱
    输入: {"notations": {1: "3 5 6 1 2", 2: "1 2 3", ...}}
    返回: 更新后的切片列表
    """
    from app.processors.chenzi import ChenziMapper

    segment = db.query(OperaSegment).filter(OperaSegment.id == segment_id).first()
    if not segment:
        raise HTTPException(status_code=404, detail="唱段不存在")

    try:
        mapper = ChenziMapper()
        notations = notation_data.get("notations", {})

        for slice_index_str, notation in notations.items():
            slice_index = int(slice_index_str)
            chenzi_string = mapper.to_chenzi_string(notation)

            slice_obj = db.query(SegmentSlice).filter(
                SegmentSlice.segment_id == segment_id,
                SegmentSlice.slice_index == slice_index,
            ).first()

            if slice_obj:
                slice_obj.chenzi_lyrics = chenzi_string
                slice_obj.numbered_notation = notation

        db.commit()

        return {
            "message": "衬字谱生成成功",
            "slices": db.query(SegmentSlice).filter(SegmentSlice.segment_id == segment_id).all(),
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{segment_id}/generate-music")
async def generate_music(
    segment_id: int,
    data: dict,
    db: Session = Depends(get_db),
):
    """
    AI 生成音乐
    输入: {"lyrics": "...", "style": "流行", "duration": 30}
    返回: {"audio_url": "..."}
    """
    from app.processors.audio import AudioProcessor

    segment = db.query(OperaSegment).filter(OperaSegment.id == segment_id).first()
    if not segment:
        raise HTTPException(status_code=404, detail="唱段不存在")

    lyrics = data.get("lyrics", "")
    if not lyrics:
        raise HTTPException(status_code=400, detail="歌词不能为空")

    style = data.get("style", "流行")
    duration = data.get("duration", 30)

    print(f"[generate-music] 收到请求: lyrics={lyrics[:50]}..., style={style}, duration={duration}")

    try:
        processor = AudioProcessor()
        result = processor.generate_music(lyrics=lyrics, style=style, duration=duration)

        if result["status"] == "success":
            return {"audio_url": result["audio_url"]}
        else:
            print(f"[generate-music] API 返回失败: {result['error']}")
            raise HTTPException(status_code=500, detail=result["error"])
    except Exception as e:
        print(f"[generate-music] 异常: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")