"""
上传 API
"""
import os
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.core.config import settings

router = APIRouter()

UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def save_upload_file(file: UploadFile, sub_dir: str = "") -> str:
    """保存上传文件并返回路径"""
    ext = Path(file.filename).suffix if file.filename else ".bin"
    filename = f"{uuid.uuid4().hex}{ext}"

    upload_path = UPLOAD_DIR / sub_dir if sub_dir else UPLOAD_DIR
    upload_path.mkdir(parents=True, exist_ok=True)

    file_path = upload_path / filename
    with open(file_path, "wb") as f:
        content = file.file.read()
        f.write(content)

    return f"/uploads/{sub_dir}/{filename}" if sub_dir else f"/uploads/{filename}"


@router.post("/video")
async def upload_video(video: UploadFile = File(...)):
    """上传视频文件"""
    if not video.filename.lower().endswith(('.mp4', '.mov', '.avi')):
        raise HTTPException(status_code=400, detail="仅支持 MP4/MOV/AVI 格式")

    path = save_upload_file(video, "videos")
    return {"video_url": path, "filename": video.filename}


@router.post("/audio")
async def upload_audio(audio: UploadFile = File(...)):
    """上传音频文件"""
    if not audio.filename.lower().endswith(('.mp3', '.wav', '.flac')):
        raise HTTPException(status_code=400, detail="仅支持 MP3/WAV/FLAC 格式")

    path = save_upload_file(audio, "audios")
    return {"audio_url": path, "filename": audio.filename}
