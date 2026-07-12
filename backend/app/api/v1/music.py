"""
AI 作曲 API
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from pathlib import Path
import random
import time

from app.core.database import get_db
from app.core.config import settings
from app.models.music_generation import MusicGeneration
from app.models.music_album import MusicAlbum
from app.models.opera_work import OperaWork
from app.models.opera_segment import OperaSegment
from app.processors.audio import AudioProcessor
from pydantic import BaseModel


router = APIRouter()


class MusicGenerateRequest(BaseModel):
    lyrics: str
    title: str = ""
    style: str = "流行"
    duration: int = 30
    voice_gender: str = ""
    reference_audio_url: str = ""


class MusicUpdateRequest(BaseModel):
    title: Optional[str] = None
    album_id: Optional[int] = None


class ToSegmentRequest(BaseModel):
    work_id: Optional[int] = None
    work_name: Optional[str] = None


class MusicGenerationResponse(BaseModel):
    id: int
    title: str
    lyrics: str
    style: str
    duration: int
    voice_gender: str
    audio_url: str
    cover_url: str
    album_id: Optional[int]
    created_at: str

    class Config:
        from_attributes = True


class AlbumCreateRequest(BaseModel):
    name: str


class AlbumResponse(BaseModel):
    id: int
    name: str
    cover_url: str
    created_at: str

    class Config:
        from_attributes = True


def _music_to_response(r: MusicGeneration) -> dict:
    return {
        "id": r.id,
        "title": r.title or "",
        "lyrics": r.lyrics,
        "style": r.style,
        "duration": r.duration,
        "voice_gender": r.voice_gender or "",
        "audio_url": r.audio_url,
        "cover_url": r.cover_url or "",
        "album_id": r.album_id,
        "created_at": r.created_at.isoformat() if r.created_at else "",
    }


@router.post("/generate", response_model=MusicGenerationResponse)
async def generate_music(
    request: MusicGenerateRequest,
    db: Session = Depends(get_db),
):
    """AI 生成音乐"""
    if not request.lyrics.strip():
        raise HTTPException(status_code=400, detail="歌词不能为空")

    try:
        processor = AudioProcessor()
        result = processor.generate_music(
            lyrics=request.lyrics,
            style=request.style,
            duration=request.duration,
            reference_audio_url=request.reference_audio_url,
        )

        if result["status"] == "success":
            title = request.title or f"未命名_{int(time.time())}"
            music_gen = MusicGeneration(
                title=title,
                lyrics=request.lyrics,
                style=request.style,
                duration=request.duration,
                voice_gender=request.voice_gender,
                audio_url=result["audio_url"],
            )
            db.add(music_gen)
            db.commit()
            db.refresh(music_gen)
            return _music_to_response(music_gen)
        else:
            raise HTTPException(status_code=500, detail=result["error"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@router.get("/history", response_model=List[MusicGenerationResponse])
async def get_music_history(
    db: Session = Depends(get_db),
):
    """获取所有 AI 作曲记录"""
    records = db.query(MusicGeneration).order_by(MusicGeneration.created_at.desc()).all()
    return [_music_to_response(r) for r in records]


@router.put("/{music_id}", response_model=MusicGenerationResponse)
async def update_music(
    music_id: int,
    data: MusicUpdateRequest,
    db: Session = Depends(get_db),
):
    """更新曲目信息"""
    music = db.query(MusicGeneration).filter(MusicGeneration.id == music_id).first()
    if not music:
        raise HTTPException(status_code=404, detail="记录不存在")

    if data.title is not None:
        music.title = data.title
    if data.album_id is not None:
        music.album_id = data.album_id

    db.commit()
    db.refresh(music)
    return _music_to_response(music)


@router.delete("/{music_id}")
async def delete_music(
    music_id: int,
    db: Session = Depends(get_db),
):
    """删除 AI 作曲记录"""
    music = db.query(MusicGeneration).filter(MusicGeneration.id == music_id).first()
    if not music:
        raise HTTPException(status_code=404, detail="记录不存在")

    db.delete(music)
    db.commit()
    return {"message": "删除成功"}


@router.post("/albums", response_model=AlbumResponse)
async def create_album(
    data: AlbumCreateRequest,
    db: Session = Depends(get_db),
):
    """创建专辑"""
    album = MusicAlbum(name=data.name)
    db.add(album)
    db.commit()
    db.refresh(album)
    return {
        "id": album.id,
        "name": album.name,
        "cover_url": album.cover_url or "",
        "created_at": album.created_at.isoformat() if album.created_at else "",
    }


@router.get("/albums", response_model=List[AlbumResponse])
async def get_albums(
    db: Session = Depends(get_db),
):
    """获取专辑列表"""
    albums = db.query(MusicAlbum).order_by(MusicAlbum.created_at.desc()).all()
    return [
        {
            "id": a.id,
            "name": a.name,
            "cover_url": a.cover_url or "",
            "created_at": a.created_at.isoformat() if a.created_at else "",
        }
        for a in albums
    ]


@router.delete("/albums/{album_id}")
async def delete_album(
    album_id: int,
    db: Session = Depends(get_db),
):
    """删除专辑"""
    album = db.query(MusicAlbum).filter(MusicAlbum.id == album_id).first()
    if not album:
        raise HTTPException(status_code=404, detail="专辑不存在")

    db.query(MusicGeneration).filter(MusicGeneration.album_id == album_id).update(
        {"album_id": None}
    )
    db.delete(album)
    db.commit()
    return {"message": "删除成功"}


@router.get("/works")
async def get_works_for_music(db: Session = Depends(get_db)):
    """获取作品列表（用于选择关联作品）"""
    works = db.query(OperaWork).order_by(OperaWork.created_at.desc()).all()
    return [{"id": w.id, "name": w.name, "category": w.category or ""} for w in works]


@router.post("/{music_id}/to-segment")
async def send_to_segment(
    music_id: int,
    data: ToSegmentRequest,
    db: Session = Depends(get_db),
):
    """将 AI 生成的音乐发送到音乐拆解"""
    music = db.query(MusicGeneration).filter(MusicGeneration.id == music_id).first()
    if not music:
        raise HTTPException(status_code=404, detail="记录不存在")

    work_id = data.work_id
    if not work_id and data.work_name:
        work = OperaWork(name=data.work_name, category="AI生成")
        db.add(work)
        db.commit()
        db.refresh(work)
        work_id = work.id

    if not work_id:
        raise HTTPException(status_code=400, detail="请指定作品")

    segment = OperaSegment(
        work_id=work_id,
        name=music.title or f"AI生成_{music.id}",
        audio_url=music.audio_url,
        lyrics=music.lyrics,
    )
    db.add(segment)
    db.commit()
    db.refresh(segment)

    return {"segment_id": segment.id, "work_id": work_id}


@router.post("/upload-reference")
async def upload_reference_audio(
    file: UploadFile = File(...),
):
    """上传参考音频（配乐模式）"""
    allowed_types = {"audio/mpeg", "audio/wav", "audio/mp3", "audio/ogg", "audio/flac"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="不支持的音频格式")

    upload_dir = Path(settings.UPLOAD_DIR) / "audios" / "reference"
    upload_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename).suffix or ".mp3"
    filename = f"ref_{int(time.time())}_{random.randint(1000, 9999)}{ext}"
    file_path = upload_dir / filename

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    return {"url": f"/uploads/audios/reference/{filename}", "filename": filename}
