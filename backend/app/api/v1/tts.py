"""
TTS (Text-to-Speech) API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.processors.audio import AudioProcessor

router = APIRouter()


class TTSRequest(BaseModel):
    text: str
    voice: str = "longxiaochun"


class TTSResponse(BaseModel):
    audio_url: str
    cached: bool = False


@router.post("/synthesize", response_model=TTSResponse)
async def synthesize_speech(request: TTSRequest):
    """
    文字转语音
    参数:
        text: 要合成的文本
        voice: 音色（zhiyan_emo/zhibei_emo/zhichu_emo）
    返回:
        audio_url: 生成的音频 URL
        cached: 是否使用缓存
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="文本不能为空")

    processor = AudioProcessor()
    result = processor.text_to_speech(request.text, request.voice)

    if result["status"] == "failed":
        raise HTTPException(status_code=500, detail=result["error"])

    return TTSResponse(
        audio_url=result["audio_url"],
        cached=result.get("cached", False)
    )


@router.get("/voices")
async def list_voices():
    """
    获取可用音色列表
    """
    return {
        "voices": [
            {"id": "longxiaochun", "name": "小淳（女声）", "desc": "温柔女声"},
            {"id": "longyue", "name": "小悦（女声）", "desc": "清脆女声"},
            {"id": "longshuo", "name": "小硕（男声）", "desc": "沉稳男声"},
        ]
    }
