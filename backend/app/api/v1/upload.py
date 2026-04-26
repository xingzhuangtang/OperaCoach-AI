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


@router.post("/extract-audio")
async def extract_audio(video_url: str):
    """从视频提取音频"""
    from app.processors.audio import AudioProcessor
    
    # 构建视频文件完整路径
    video_path = UPLOAD_DIR / video_url.removeprefix("/uploads/")
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="视频文件不存在")
    
    # 生成音频文件名
    audio_filename = f"{video_path.stem}.wav"
    audio_path = UPLOAD_DIR / "audios" / audio_filename
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        processor = AudioProcessor()
        processor.extract_audio_from_video(str(video_path), str(audio_path))
        return {"audio_url": f"/uploads/audios/{audio_filename}", "message": "提取成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_uploads():
    """列出已上传文件"""
    files = []
    
    # 视频文件
    videos_dir = UPLOAD_DIR / "videos"
    if videos_dir.exists():
        for f in videos_dir.iterdir():
            if f.is_file():
                files.append({
                    "name": f.name,
                    "url": f"/uploads/videos/{f.name}",
                    "type": "video"
                })
    
    # 音频文件
    audios_dir = UPLOAD_DIR / "audios"
    if audios_dir.exists():
        for f in audios_dir.iterdir():
            if f.is_file():
                files.append({
                    "name": f.name,
                    "url": f"/uploads/audios/{f.name}",
                    "type": "audio"
                })
    
    return files
