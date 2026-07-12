"""
音频处理器
"""
import numpy as np
import librosa
import torch
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
        调用阿里 Fun-ASR 2026年4月更新的大模型版本
        全面支持汉语传统七大方言体系，对戏曲识别效果更好
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

            # 5. 调用 Transcription API - 使用 2026年4月更新的 Fun-ASR 大模型
            response = Transcription.async_call(
                model='fun-asr',
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
        使用阿里 Fun-ASR 2026年4月更新的大模型提取音频歌词
        全面支持汉语传统七大方言体系，对戏曲识别效果更好
        """
        result = self._call_fun_asr_v2(audio_path)

        if result.get('status') == 'success':
            return ' '.join([s['text'] for s in result['sentences']])

        raise RuntimeError(f"Fun-ASR 识别失败: {result.get('error')}")

    def extract_lyrics_with_timestamps(self, audio_path: str, model_size: str = "small") -> List[Dict[str, Any]]:
        """
        使用阿里 Fun-ASR 2026年4月更新的大模型提取歌词及时间戳
        全面支持汉语传统七大方言体系，对戏曲识别效果更好
        """
        result = self._call_fun_asr_v2(audio_path)

        if result.get('status') == 'success':
            return result['sentences']

        raise RuntimeError(f"Fun-ASR 识别失败: {result.get('error')}")

    def separate_vocals(self, audio_path: str, output_dir: str = None) -> Dict[str, str]:
        """
        使用 Demucs 分离人声和伴奏
        返回: {"vocal_path": "...", "accompaniment_path": "..."}
        """
        import subprocess
        from pathlib import Path
        from app.core.config import settings

        if output_dir is None:
            output_dir = str(Path(audio_path).parent / "separated")

        Path(output_dir).mkdir(parents=True, exist_ok=True)

        try:
            # 调用 demucs CLI
            result = subprocess.run(
                [
                    "demucs",
                    "--two-stems=vocals",
                    "-n", settings.UVR_MODEL,
                    "--device", settings.UVR_DEVICE,
                    "-o", output_dir,
                    audio_path,
                ],
                capture_output=True,
                text=True,
                timeout=600,  # 10 分钟超时
            )

            if result.returncode != 0:
                raise RuntimeError(f"Demucs 分离失败: {result.stderr}")

            # Demucs 输出路径：output_dir/htdemucs/<filename>/vocals.wav 和 no_vocals.wav
            audio_name = Path(audio_path).stem
            separated_dir = Path(output_dir) / settings.UVR_MODEL / audio_name

            vocal_path = separated_dir / "vocals.wav"
            accompaniment_path = separated_dir / "no_vocals.wav"

            if not vocal_path.exists():
                raise RuntimeError(f"分离完成但未找到人声文件: {vocal_path}")

            return {
                "vocal_path": str(vocal_path),
                "accompaniment_path": str(accompaniment_path),
            }

        except subprocess.TimeoutExpired:
            raise RuntimeError("Demucs 分离超时（>10 分钟）")
        except FileNotFoundError:
            raise RuntimeError("未找到 demucs 命令，请安装: pip install demucs")

    def extract_pitch(self, audio_path: str) -> List[float]:
        """
        从音频中提取音高序列（Hz）
        使用 librosa.pyin（速度快，适合实时场景）
        返回: [f0_1, f0_2, ...] 浮点数组，无音高帧为 null
        """
        y, sr = self.load_audio(audio_path)
        # 确保单声道
        if y.ndim > 1:
            y = y.mean(axis=1)

        # 使用 pyin 提取音高
        f0, voiced_flag, voiced_probs = librosa.pyin(
            y,
            sr=sr,
            fmin=librosa.note_to_hz('C2'),
            fmax=librosa.note_to_hz('C7'),
            frame_length=2048,
        )
        return [float(f) if not np.isnan(f) else None for f in f0]

    def generate_music(self, lyrics: str, style: str = "流行", duration: int = 30, reference_audio_url: str = "") -> Dict[str, Any]:
        """
        调用阿里 Fun-Music API 生成音乐（同步模式）
        参数:
            lyrics: 歌词文本
            style: 风格描述（如"流行"、"古风"、"戏曲"）
            duration: 生成时长（秒）
            reference_audio_url: 参考音频URL（可选，用于参考旋律）
        返回:
            {"status": "success", "audio_url": "..."} 或 {"status": "failed", "error": "..."}
        """
        import requests
        import time
        from pathlib import Path
        from app.core.config import settings

        api_key = settings.DASHSCOPE_API_KEY
        if not api_key:
            return {"status": "failed", "error": "DASHSCOPE_API_KEY 未配置"}

        # 创建输出目录
        output_dir = Path(settings.UPLOAD_DIR) / "audios" / "fun_music"
        output_dir.mkdir(parents=True, exist_ok=True)

        # 调用 Fun-Music API（同步模式）
        url = "https://dashscope.aliyuncs.com/api/v1/services/audio/music/generation"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "fun-music-v1",
            "input": {
                "lyrics": lyrics,
                "style": style
            },
            "parameters": {
                "duration": duration
            }
        }

        # 如果有参考音频，添加到 payload
        if reference_audio_url:
            # 将相对路径转换为完整的 URL
            if reference_audio_url.startswith("/uploads/"):
                from app.core.config import settings
                ref_audio_full_url = f"http://localhost:8000{reference_audio_url}"
            else:
                ref_audio_full_url = reference_audio_url
            payload["input"]["ref_audio"] = ref_audio_full_url
            print(f"[Fun-Music] 使用参考音频: {ref_audio_full_url}")

        try:
            print(f"[Fun-Music] 开始生成音乐，时长: {duration}秒...")
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            
            if response.status_code != 200:
                return {"status": "failed", "error": f"API 调用失败: {response.text}"}

            result = response.json()
            
            # 解析返回的音频 URL
            audio_url = result.get("output", {}).get("audio", {}).get("url")
            if not audio_url:
                return {"status": "failed", "error": f"未获取到音频 URL: {result}"}

            print(f"[Fun-Music] 获取到音频 URL，开始下载...")

            # 下载音频文件
            audio_response = requests.get(audio_url, timeout=60)
            if audio_response.status_code != 200:
                return {"status": "failed", "error": "下载音频失败"}

            # 保存文件（MP3 格式）
            import random
            filename = f"fun_music_{int(time.time())}_{random.randint(1000, 9999)}.mp3"
            file_path = output_dir / filename
            with open(file_path, "wb") as f:
                f.write(audio_response.content)

            # 裁剪音频到指定时长
            try:
                import librosa
                import soundfile as sf
                import numpy as np
                y, sr = librosa.load(file_path, sr=None)
                target_samples = int(duration * sr)
                if len(y) > target_samples:
                    y = y[:target_samples]
                    sf.write(file_path, y, sr, format='mp3')
                    print(f"[Fun-Music] 音频已裁剪到 {duration} 秒")
            except Exception as e:
                print(f"[Fun-Music] 音频裁剪失败: {e}")

            # 返回相对 URL
            relative_url = f"/uploads/audios/fun_music/{filename}"
            print(f"[Fun-Music] 音乐生成成功: {relative_url}")
            return {"status": "success", "audio_url": relative_url}

        except requests.exceptions.RequestException as e:
            return {"status": "failed", "error": f"网络请求失败: {str(e)}"}
        except Exception as e:
            return {"status": "failed", "error": f"生成失败: {str(e)}"}

    def slice_by_fun_asr_sentences(self, audio_path: str, output_dir: str = None, segment_id: int = None) -> List[Dict[str, Any]]:
        """
        基于 Fun-ASR 识别结果的句子级切片
        1. 调用 _call_fun_asr_v2() 获取带时间戳的句子
        2. 按句子时间戳切分音频
        3. 生成独立音频文件
        返回: [{start_time, end_time, lyrics, audio_url}, ...]
        """
        import soundfile as sf
        from pathlib import Path
        from app.core.config import settings

        if output_dir is None:
            output_dir = str(Path(audio_path).parent / "funasr_slices")

        # 使用 segment_id 隔离子目录，避免不同唱段切片互相覆盖
        if segment_id is not None:
            output_dir = str(Path(output_dir) / str(segment_id))

        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # 1. 获取句子级时间戳
        sentences = self.extract_lyrics_with_timestamps(audio_path)

        if not sentences:
            return []

        # 打印识别结果用于调试
        print(f"[FunASR] 识别到 {len(sentences)} 个句子:")
        for idx, s in enumerate(sentences):
            print(f"  [{idx+1}] {s['start']:.1f}s-{s['end']:.1f}s: {s['text']}")

        # 2. 加载完整音频
        y, sr = self.load_audio(audio_path)

        # 计算 output_dir 相对于 UPLOAD_DIR 的路径，用于生成正确的 URL
        upload_root = Path(settings.UPLOAD_DIR).resolve()
        output_path_resolved = Path(output_dir).resolve()
        try:
            rel_dir = output_path_resolved.relative_to(upload_root)
        except ValueError:
            rel_dir = Path("funasr_slices") / (str(segment_id) if segment_id else "")

        # 3. 按句子时间戳切片
        slices = []
        for i, sentence in enumerate(sentences):
            start_time = sentence["start"]
            end_time = sentence["end"]
            lyrics = sentence["text"]

            # 计算采样点范围
            start_sample = int(start_time * sr)
            end_sample = int(end_time * sr)

            # 确保范围有效
            if start_sample >= end_sample or start_sample >= len(y):
                continue

            end_sample = min(end_sample, len(y))

            # 提取切片音频
            slice_audio = y[start_sample:end_sample]

            # 保存切片音频
            filename = f"sentence_{i+1}.wav"
            output_file = Path(output_dir) / filename
            sf.write(str(output_file), slice_audio, sr)

            slices.append({
                "start_time": start_time,
                "end_time": end_time,
                "lyrics": lyrics,
                "audio_url": f"/uploads/{rel_dir}/{filename}",
            })

        return slices


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
