"""
数字简谱转衬字语气词映射器
"""
import re
from typing import List, Dict


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
        """根据歌词字数，自动循环 1-5 生成衬字谱

        规则：按字数循环映射 1=啊 2=哎 3=咦 4=呦 5=呜
        例如："海岛冰轮初转腾"（7 字）→ 1-2-3-4-5-1-2 → 啊-哎-咦-呦-呜-啊-哎

        返回：{"chenzi": "啊-哎-咦-呦-呜-啊-哎", "notation": "1 2 3 4 5 1 2"}
        """
        # 去除空格和换行，计算有效字数
        char_count = len(lyrics.replace(" ", "").replace("\n", "").strip())
        if char_count == 0:
            return {"chenzi": "", "notation": ""}

        # 循环 1-5 生成衬字
        cycle = ["1", "2", "3", "4", "5"]
        digits = [cycle[i % 5] for i in range(char_count)]
        notation = " ".join(digits)
        chenzi = self.to_chenzi_string(notation, separator)

        return {"chenzi": chenzi, "notation": notation}
