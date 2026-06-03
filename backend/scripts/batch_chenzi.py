#!/usr/bin/env python3
"""
批量数字简谱转衬字谱 CLI 工具

用法:
    python -m scripts.batch_chenzi input.txt output_dir/
    python -m scripts.batch_chenzi input.txt --format json
    python -m scripts.batch_chenzi input.txt --separator "/"

输入文件格式（每行一个简谱序列，支持注释）：
    # 贵妃醉酒 - 海岛冰轮
    3 5 6 1 2
    1 2 3 5 6
    ---
    # 霸王别姬 - 看大王
    5 3 2 1
    6 5 3 2
"""
import argparse
import json
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.processors.chenzi import ChenziMapper


def parse_input_file(input_path: str) -> list[dict]:
    """
    解析输入文件，返回作品列表
    格式：
    # 作品名 - 唱段名
    3 5 6 1 2
    1 2 3
    ---
    """
    works = []
    current_work = None

    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()

            # 跳过空行
            if not line:
                continue

            # 分隔符：结束当前作品
            if line == '---':
                current_work = None
                continue

            # 注释行：作品名 - 唱段名
            if line.startswith('#'):
                title = line[1:].strip()
                parts = title.split(' - ', 1)
                current_work = {
                    "work_name": parts[0].strip() if len(parts) > 0 else "未知作品",
                    "segment_name": parts[1].strip() if len(parts) > 1 else "",
                    "notations": [],
                }
                works.append(current_work)
                continue

            # 简谱行
            if current_work is not None:
                current_work["notations"].append(line)
            else:
                # 没有作品头，创建默认作品
                current_work = {
                    "work_name": "未分类",
                    "segment_name": "",
                    "notations": [line],
                }
                works.append(current_work)

    return works


def generate_chenzi_files(
    works: list[dict],
    output_dir: str,
    separator: str = "-",
    output_format: str = "txt",
):
    """
    为每个作品生成衬字谱文件
    """
    mapper = ChenziMapper()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    total_count = 0

    for work in works:
        work_name = work["work_name"]
        segment_name = work["segment_name"]
        notations = work["notations"]

        # 生成文件名
        if segment_name:
            filename = f"{work_name}_{segment_name}"
        else:
            filename = work_name
        filename = filename.replace(' ', '_').replace('/', '_')

        if output_format == "json":
            # JSON 格式输出
            results = []
            for notation in notations:
                chenzi_string = mapper.to_chenzi_string(notation, separator)
                parsed = mapper.parse_notation(notation)
                results.append({
                    "notation": notation,
                    "chenzi": chenzi_string,
                    "parsed": parsed,
                })

            output_file = output_path / f"{filename}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "work_name": work_name,
                    "segment_name": segment_name,
                    "results": results,
                }, f, ensure_ascii=False, indent=2)

        else:
            # TXT 格式输出（默认）
            lines = []
            lines.append(f"# {work_name}" + (f" - {segment_name}" if segment_name else ""))
            lines.append("")

            for notation in notations:
                chenzi_string = mapper.to_chenzi_string(notation, separator)
                lines.append(f"简谱: {notation}")
                lines.append(f"衬字: {chenzi_string}")
                lines.append("")

            output_file = output_path / f"{filename}.txt"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))

        total_count += len(notations)
        print(f"✓ 已生成: {output_file} ({len(notations)} 条简谱)")

    print(f"\n总计: 处理 {len(works)} 个作品，{total_count} 条简谱")
    return total_count


def main():
    parser = argparse.ArgumentParser(
        description="批量数字简谱转衬字语气词谱",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python -m scripts.batch_chenzi notations.txt output/
    python -m scripts.batch_chenzi notations.txt --format json
    python -m scripts.batch_chenzi notations.txt --separator "/"
        """,
    )
    parser.add_argument("input_file", help="输入文件路径（TXT 格式）")
    parser.add_argument("output_dir", nargs="?", default="chenzi_output", help="输出目录（默认: chenzi_output）")
    parser.add_argument("--format", choices=["txt", "json"], default="txt", help="输出格式（默认: txt）")
    parser.add_argument("--separator", default="-", help="衬字分隔符（默认: -）")

    args = parser.parse_args()

    # 检查输入文件
    if not os.path.exists(args.input_file):
        print(f"错误: 输入文件不存在: {args.input_file}")
        sys.exit(1)

    print(f"读取输入文件: {args.input_file}")
    works = parse_input_file(args.input_file)

    if not works:
        print("错误: 未找到有效的简谱数据")
        sys.exit(1)

    print(f"找到 {len(works)} 个作品")
    print(f"输出目录: {args.output_dir}")
    print(f"输出格式: {args.format}")
    print(f"分隔符: {args.separator}")
    print("-" * 50)

    generate_chenzi_files(works, args.output_dir, args.separator, args.format)


if __name__ == "__main__":
    main()
