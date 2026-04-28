"""
音频处理器
"""
import numpy as np
import librosa
from typing import List, Dict, Any


class AudioProcessor:
    """音频处理基础类"""

    def __init__(self, sample_rate: int = 22050):
        self.sample_rate = sample_rate

    def load_audio(self, audio_path: str):
        """加载音频文件"""
        return librosa.load(audio_path, sr=self.sample_rate)

    def extract_audio_from_video(self, video_path: str, output_path: str):
        """从视频提取音频"""
        try:
            from moviepy import VideoFileClip
            clip = VideoFileClip(video_path)
            if clip.audio is None:
                raise ValueError("视频没有音轨")
            clip.audio.write_audiofile(output_path, logger=None)
            clip.close()
            return output_path
        except ImportError:
            raise RuntimeError("请安装 moviepy: pip install moviepy")

    def _prepare_audio_for_api(self, audio_path: str) -> str:
        """
        将音频转换为 Fun-ASR 要求的格式（16kHz 单声道 WAV）
        返回转换后的文件路径
        """
        import soundfile as sf
        import librosa
        from pathlib import Path
        
        # 加载音频并转换为 16kHz 单声道
        y, sr = librosa.load(audio_path, sr=16000, mono=True)
        
        # 保存到临时文件
        output_path = Path(audio_path).parent / f"temp_{Path(audio_path).stem}_16k.wav"
        sf.write(str(output_path), y, 16000)
        
        return str(output_path)

    def extract_lyrics(self, audio_path: str, model_size: str = "small") -> str:
        """
        使用本地 Whisper 模型提取音频歌词
        返回完整歌词文本
        """
        import whisper
        
        model = whisper.load_model(model_size)
        
        # Whisper 需要 16kHz 单声道音频
        audio = whisper.load_audio(audio_path)
        
        result = model.transcribe(audio, language='zh', fp16=False)
        text = result.get("text", "")
        
        # 如果识别结果为空，尝试不使用语言限制
        if not text.strip():
            result = model.transcribe(audio, fp16=False)
            text = result.get("text", "")
        
        return text

    def extract_lyrics_with_timestamps(self, audio_path: str, model_size: str = "small") -> List[Dict[str, Any]]:
        """
        使用本地 Whisper 模型提取歌词及时间戳
        返回: [{text, start, end}, ...]
        """
        import whisper
        
        model = whisper.load_model(model_size)
        
        # Whisper 需要 16kHz 单声道音频
        audio = whisper.load_audio(audio_path)
        
        result = model.transcribe(audio, language='zh', fp16=False, word_timestamps=False)
        
        segments = []
        for segment in result.get("segments", []):
            segments.append({
                "text": segment["text"].strip(),
                "start": segment["start"],
                "end": segment["end"],
            })
        
        # 如果识别结果为空，尝试不使用语言限制
        if not segments:
            result = model.transcribe(audio, fp16=False, word_timestamps=False)
            for segment in result.get("segments", []):
                segments.append({
                    "text": segment["text"].strip(),
                    "start": segment["start"],
                    "end": segment["end"],
                })
        
        return segments


class AudioSlicer(AudioProcessor):
    """音频切片器"""

    def slice_by_phrases(self, audio_path: str, output_dir: str = None) -> List[Dict[str, Any]]:
        """
        按乐句切片并生成实际音频文件
        返回: [{start_time, end_time, duration, audio_url}, ...]
        """
        y, sr = self.load_audio(audio_path)

        # 检测起始点
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        peaks = self._detect_peaks(onset_env, sr=sr)

        # 构建切片
        slices = []
        for i in range(len(peaks) + 1):
            start = peaks[i - 1] if i > 0 else 0.0
            end = peaks[i] if i < len(peaks) else len(y) / sr
            duration = end - start

            # 只保留合理的片段 (1-15 秒)
            if 1.0 <= duration <= 15.0:
                slice_data = {
                    "start_time": start,
                    "end_time": end,
                    "duration": duration,
                }
                
                # 如果指定了输出目录，生成实际音频文件
                if output_dir:
                    from pathlib import Path
                    import soundfile as sf
                    
                    output_path = Path(output_dir) / f"slice_{i+1}.wav"
                    try:
                        # 计算采样点范围
                        start_sample = int(start * sr)
                        end_sample = int(end * sr)
                        slice_audio = y[start_sample:end_sample]
                        sf.write(str(output_path), slice_audio, sr)
                        slice_data["audio_url"] = f"/uploads/slices/slice_{i+1}.wav"
                    except Exception as e:
                        print(f"切片 {i+1} 生成失败: {e}")
                
                slices.append(slice_data)

        return slices

    def _detect_peaks(self, onset_env: np.ndarray, sr: int) -> List[float]:
        """检测峰值"""
        from scipy.signal import find_peaks
        peaks, _ = find_peaks(onset_env, distance=int(2.0 * sr / 512))
        return (peaks * 512 / sr).tolist()
