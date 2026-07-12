"""
数字简谱转衬字语气词映射器
"""
import re
import numpy as np
from typing import List, Dict, Optional

# 十二平均律频率（C4=261.63 Hz 基准）
NOTE_FREQS = {
    "C": 261.63, "C#": 277.18, "D": 293.66, "D#": 311.13,
    "E": 329.63, "F": 349.23, "F#": 369.99, "G": 392.00,
    "G#": 415.30, "A": 440.00, "A#": 466.16, "B": 493.88,
}

# 简谱数字对应音名（C 大调）
SOLFEGE_TO_NOTE = {
    1: "C", 2: "D", 3: "E", 4: "F", 5: "G", 6: "A", 7: "B",
}


def freq_to_note(freq: float) -> Optional[str]:
    """将频率映射到最近的十二平均律音符"""
    if freq <= 0:
        return None
    # 找到最接近的八度
    best_note = None
    best_dist = float('inf')
    for note_name, base_freq in NOTE_FREQS.items():
        # 在不同八度中搜索
        for octave in range(-1, 3):
            f = base_freq * (2 ** octave)
            # 使用对数距离
            dist = abs(np.log2(freq / f))
            if dist < best_dist:
                best_dist = dist
                best_note = note_name
    return best_note


def freq_to_solfege(freq: float, key: str = "C") -> int:
    """将频率映射到简谱数字 (1-7)，默认 C 大调"""
    if freq <= 0:
        return 0
    # 找到最近的音符
    note = freq_to_note(freq)
    if not note:
        return 0
    # 计算音级（相对于调性）
    note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    key_offset = note_names.index(key)
    note_offset = note_names.index(note)
    # 大调音阶：1-2-3-4-5-6-7 对应全全半全全全半
    major_scale = [0, 2, 4, 5, 7, 9, 11]  # 音级偏移
    semitone = (note_offset - key_offset) % 12
    # 找到最接近的大调音级
    best = 0
    best_dist = 13
    for i, s in enumerate(major_scale):
        dist = abs(semitone - s)
        if dist < best_dist:
            best_dist = dist
            best = i + 1
    return best


class ChenziMapper:
    """数字简谱到衬字语气词的映射器

    映射规则（5 个最顺口的单字）：
    1=啊, 2=哎, 3=咦, 4=呦, 5=呜
    """

    DEFAULT_MAPPING = {
        "1": "啊",
        "2": "哎",
        "3": "咦",
        "4": "呦",
        "5": "呜",
        "6": "啦",
        "7": "嘻",
    }

    def __init__(self, custom_mapping: Dict[str, str] = None):
        self.mapping = custom_mapping or self.DEFAULT_MAPPING

    def parse_notation(self, notation_str: str) -> List[Dict[str, str]]:
        """解析数字简谱字符串，返回结构化数据

        支持格式：
        - 空格分隔："3 5 6 1 2"
        - 连续数字："35612"
        - 带八度标记："3' 5 6"（高音）
        - 带附点："3. 5 6"（附点音符）

        返回：[{"digit": "3", "chenzi": "咦", "is_high": False, "is_dotted": False}, ...]
        """
        notation_str = notation_str.strip()

        # 移除连字符和多余空格
        notation_str = re.sub(r'[-\s]+', ' ', notation_str).strip()

        # 分割成单个音符
        tokens = notation_str.split()

        result = []
        for token in tokens:
            # 处理连续数字：将 "35612" 拆分为单个数字
            if re.match(r'^\d+$', token):
                for digit in token:
                    chenzi = self.mapping.get(digit, "?")
                    result.append({
                        "digit": digit,
                        "chenzi": chenzi,
                        "is_high": False,
                        "is_dotted": False,
                    })
            else:
                # 提取数字部分（带修饰符）
                match = re.match(r"^(\d)(['.]*)$", token)
                if match:
                    digit = match.group(1)
                    modifiers = match.group(2)
                    is_high = "'" in modifiers
                    is_dotted = "." in modifiers

                    chenzi = self.mapping.get(digit, "?")

                    result.append({
                        "digit": digit,
                        "chenzi": chenzi,
                        "is_high": is_high,
                        "is_dotted": is_dotted,
                    })
                else:
                    # 无法解析的字符，保留原样
                    result.append({
                        "digit": token,
                        "chenzi": token,
                        "is_high": False,
                        "is_dotted": False,
                    })

        return result

    def to_chenzi_string(self, notation_str: str, separator: str = "-") -> str:
        """将数字简谱转换为衬字语气词字符串

        输入："3 5 6 1 2" 或 "35612" 或 "3-5-6-1-2"
        输出："咦-呜-呀-啊-哎"
        """
        parsed = self.parse_notation(notation_str)
        chenzis = [item["chenzi"] for item in parsed]
        return separator.join(chenzis)

    def batch_convert(self, notations: List[str], separator: str = "-") -> List[str]:
        """批量转换数字简谱为衬字字符串"""
        return [self.to_chenzi_string(n, separator) for n in notations]

    def get_mapping_table(self) -> Dict[str, str]:
        """获取当前映射表"""
        return self.mapping.copy()

    def auto_generate_chenzi(self, lyrics: str, separator: str = "-") -> Dict[str, str]:
        """根据歌词字数，自动循环 1-5 生成衬字谱（降级方案，无音高数据时使用）"""
        char_count = len(lyrics.replace(" ", "").replace("\n", "").strip())
        if char_count == 0:
            return {"chenzi": "", "notation": ""}
        cycle = ["1", "2", "3", "4", "5"]
        digits = [cycle[i % 5] for i in range(char_count)]
        notation = " ".join(digits)
        chenzi = self.to_chenzi_string(notation, separator)
        return {"chenzi": chenzi, "notation": notation}

    def generate_chenzi_from_pitch(
        self,
        lyrics: str,
        pitches: List[Optional[float]],
        separator: str = "-",
    ) -> Dict[str, str]:
        """
        根据真实音高数据生成精确的简谱和衬字谱
        将音高序列分段（按歌词字数），每段取中位数频率映射到简谱
        """
        # 计算有效字数
        char_count = len(lyrics.replace(" ", "").replace("\n", "").strip())
        if char_count == 0:
            return {"chenzi": "", "notation": ""}

        # 过滤有效音高
        valid_pitches = [p for p in pitches if p is not None and p > 0]
        if not valid_pitches:
            # 无音高数据，降级到循环映射
            return self.auto_generate_chenzi(lyrics, separator)

        # 将音高序列均匀分段
        total_frames = len(pitches)
        segment_len = total_frames // char_count
        if segment_len < 1:
            segment_len = 1

        digits = []
        for i in range(char_count):
            start = i * segment_len
            end = start + segment_len if i < char_count - 1 else total_frames
            segment = pitches[start:end]
            valid_segment = [p for p in segment if p is not None and p > 0]

            if not valid_segment:
                digits.append("5")  # 默认
                continue

            # 取中位数频率（抗干扰）
            median_freq = float(np.median(valid_segment))
            solfege = freq_to_solfege(median_freq)
            # 简谱只显示 1-7
            digit = str(solfege) if 1 <= solfege <= 7 else "5"
            digits.append(digit)

        notation = " ".join(digits)
        chenzi = self.to_chenzi_string(notation, separator)

        return {"chenzi": chenzi, "notation": notation}
