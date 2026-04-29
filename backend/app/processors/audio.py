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

    def _call_fun_asr_v2(self, audio_path: str) -> dict:
        """
        调用阿里 Fun-ASR paraformer-v1 (经验证对戏曲识别效果更好)
        注意：paraformer-v2 对戏曲识别极差（只识别出1句），v1 能识别出更多内容
        """
        import dashscope
        from dashscope import Files
        from dashscope.audio.asr import Transcription
        from app.core.config import settings
        import requests
        import time
        import soundfile as sf
        import librosa
        from pathlib import Path
        
        dashscope.api_key = settings.DASHSCOPE_API_KEY
        
        # 1. 加载音频为 16kHz 单声道
        y, sr = librosa.load(audio_path, sr=16000, mono=True)
        
        # 2. 保存到临时文件
        temp_path = Path(audio_path).parent / f"temp_funasr_{Path(audio_path).stem}.wav"
        sf.write(str(temp_path), y, 16000)
        
        try:
            # 3. 上传文件
            upload_result = Files.upload(
                file_path=str(temp_path),
                purpose='transcription'
            )
            
            if upload_result.get('status_code') != 200:
                return {"status": "failed", "error": f"Upload failed: {upload_result}"}
                
            file_id = upload_result['output']['uploaded_files'][0]['file_id']
            
            # 4. 获取文件 URL
            file_info = Files.get(file_id=file_id)
            if file_info.get('status_code') != 200:
                return {"status": "failed", "error": "Get file info failed"}
                
            file_url = file_info['output']['url']
            
            # 5. 调用 Transcription API - 使用 paraformer-v1（对戏曲识别更好）
            response = Transcription.async_call(
                model='paraformer-v1',
                file_urls=[file_url],
                language_hints=['zh'],
                channel_id=[0],
                diarization_enabled=False,
                sample_rate=16000
            )
            
            if response.get('status_code') != 200:
                return {"status": "failed", "error": f"Transcription call failed: {response}"}
                
            task_id = response['output']['task_id']
            
            # 6. 轮询结果
            for _ in range(60):
                task_response = Transcription.fetch(task=task_id)
                status = task_response['output']['task_status']
                
                if status == 'SUCCEEDED':
                    result_url = task_response['output']['results'][0].get('transcription_url')
                    if not result_url:
                        return {"status": "failed", "error": "No transcription URL"}
                        
                    result_resp = requests.get(result_url)
                    if result_resp.status_code != 200:
                        return {"status": "failed", "error": "Failed to download result"}
                        
                    result_data = result_resp.json()
                    transcripts = result_data.get('transcripts', [])
                    
                    if not transcripts:
                        return {"status": "success", "sentences": []}
                        
                    sentences = transcripts[0].get('sentences', [])
                    formatted_sentences = []
                    for s in sentences:
                        formatted_sentences.append({
                            "text": s['text'].strip(),
                            "start": s['begin_time'] / 1000.0,
                            "end": s['end_time'] / 1000.0,
                        })
                    
                    return {"status": "success", "sentences": formatted_sentences}
                
                elif status == 'FAILED':
                    error_msg = task_response['output'].get('message', 'Unknown error')
                    return {"status": "failed", "error": error_msg}
                
                time.sleep(2)
                
            return {"status": "failed", "error": "Timeout"}
            
        except Exception as e:
            return {"status": "failed", "error": str(e)}
        finally:
            temp_path.unlink(missing_ok=True)

    def extract_lyrics(self, audio_path: str, model_size: str = "small") -> str:
        """
        使用阿里 Fun-ASR paraformer-v1 提取音频歌词
        注意：paraformer-v1 对戏曲/唱歌识别效果优于 v2
        """
        result = self._call_fun_asr_v2(audio_path)
        
        if result.get('status') == 'success':
            return ' '.join([s['text'] for s in result['sentences']])
        
        # Fallback
        print(f"Fun-ASR failed: {result.get('error')}, using realtime fallback")
        return self._extract_lyrics_realtime(audio_path)

    def extract_lyrics_with_timestamps(self, audio_path: str, model_size: str = "small") -> List[Dict[str, Any]]:
        """
        使用阿里 Fun-ASR paraformer-v1 提取歌词及时间戳
        注意：paraformer-v1 对戏曲/唱歌识别效果优于 v2
        """
        result = self._call_fun_asr_v2(audio_path)
        
        if result.get('status') == 'success':
            return result['sentences']
        
        # Fallback
        print(f"Fun-ASR failed: {result.get('error')}, using realtime fallback")
        return self._extract_lyrics_realtime_with_timestamps(audio_path)

    def _extract_lyrics_realtime(self, audio_path: str) -> str:
        """备用：实时版模型 (paraformer-realtime-v2)"""
        import dashscope
        from dashscope.audio.asr import Recognition
        from app.core.config import settings
        import soundfile as sf
        import librosa
        from pathlib import Path
        
        dashscope.api_key = settings.DASHSCOPE_API_KEY
        
        y, sr = librosa.load(audio_path, sr=16000, mono=True)
        temp_path = Path(audio_path).parent / f"temp_realtime_{Path(audio_path).stem}.wav"
        sf.write(str(temp_path), y, 16000)
        
        try:
            recognition = Recognition(
                model='paraformer-realtime-v2',
                format='wav',
                sample_rate=16000,
                language_hints=['zh'],
                callback=lambda x: None
            )
            
            result = recognition.call(str(temp_path))
            
            if result.get('status_code') == 200 and result.get('output'):
                sentences = result['output'].get('sentence', [])
                return ' '.join([s['text'] for s in sentences])
            return ""
        finally:
            temp_path.unlink(missing_ok=True)

    def _extract_lyrics_realtime_with_timestamps(self, audio_path: str) -> List[Dict[str, Any]]:
        """备用：实时版模型 (带时间戳)"""
        import dashscope
        from dashscope.audio.asr import Recognition
        from app.core.config import settings
        import soundfile as sf
        import librosa
        from pathlib import Path
        
        dashscope.api_key = settings.DASHSCOPE_API_KEY
        
        y, sr = librosa.load(audio_path, sr=16000, mono=True)
        temp_path = Path(audio_path).parent / f"temp_realtime_{Path(audio_path).stem}.wav"
        sf.write(str(temp_path), y, 16000)
        
        try:
            recognition = Recognition(
                model='paraformer-realtime-v2',
                format='wav',
                sample_rate=16000,
                language_hints=['zh'],
                callback=lambda x: None
            )
            
            result = recognition.call(str(temp_path))
            
            if result.get('status_code') == 200 and result.get('output'):
                sentences = result['output'].get('sentence', [])
                segments = []
                for s in sentences:
                    segments.append({
                        "text": s['text'].strip(),
                        "start": s['begin_time'] / 1000.0,
                        "end": s['end_time'] / 1000.0,
                    })
                return segments
            return []
        finally:
            temp_path.unlink(missing_ok=True)


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
