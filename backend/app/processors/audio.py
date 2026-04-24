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
            from moviepy.editor import VideoFileClip
            clip = VideoFileClip(video_path)
            if clip.audio is None:
                raise ValueError("视频没有音轨")
            clip.audio.write_audiofile(output_path, logger=None)
            clip.close()
            return output_path
        except ImportError:
            raise RuntimeError("请安装 moviepy: pip install moviepy")


class AudioSlicer(AudioProcessor):
    """音频切片器"""

    def slice_by_phrases(self, audio_path: str) -> List[Dict[str, Any]]:
        """
        按乐句切片
        返回: [{start_time, end_time, duration}, ...]
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
                slices.append({
                    "start_time": start,
                    "end_time": end,
                    "duration": duration,
                })

        return slices

    def _detect_peaks(self, onset_env: np.ndarray, sr: int) -> List[float]:
        """检测峰值"""
        from scipy.signal import find_peaks
        peaks, _ = find_peaks(onset_env, distance=int(2.0 * sr / 512))
        return (peaks * 512 / sr).tolist()
