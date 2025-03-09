import json
import re
from collections import OrderedDict
from typing import Tuple
import argparse


def load_names(name_file: str) -> list:
    """加载潜在玩家名单并优化匹配顺序"""
    with open(name_file, 'r') as f:
        names = [line.strip() for line in f if line.strip()]

    # 优化策略：按长度降序排列，优先匹配长姓名
    names_sorted = sorted(names, key=lambda x: (-len(x), x.lower()))

    # 生成不重复的姓名列表（不区分大小写）
    seen = set()
    unique_names = []
    for name in names_sorted:
        lower_name = name.lower()
        if lower_name not in seen:
            seen.add(lower_name)
            unique_names.append(name)
    return unique_names


def create_name_pattern(names: list) -> re.Pattern:
    """创建优化后的正则匹配模式"""
    # 按长度降序排列确保优先匹配长字符串
    sorted_names = sorted(names, key=lambda x: -len(x))

    # 构建正则表达式，支持单词边界和大小写不敏感
    pattern = r'\b(' + '|'.join(
        re.escape(name) for name in sorted_names
    ) + r')\b'

    return re.compile(pattern, flags=re.IGNORECASE)


def normalize_text(text: str, pattern: re.Pattern) -> Tuple[str, dict]:
    """执行文本归一化替换"""
    matches = []

    # 第一次遍历：记录所有匹配项（保留原始大小写）
    for match in pattern.finditer(text):
        original = match.group(0)
        start, end = match.start(), match.end()
        matches.append((start, end, original))

    # 去重处理：保留每个名称的首次出现
    seen = OrderedDict()  # 保持插入顺序
    for start, end, original in matches:
        lower_name = original.lower()
        if lower_name not in seen:
            seen[lower_name] = original

    # 生成替换映射
    mapping = OrderedDict()
    placeholder_count = 0
    placeholder_map = {}
    for lower_name, original in seen.items():
        placeholder = f"Player{chr(65 + placeholder_count)}"
        placeholder_map[lower_name] = placeholder
        placeholder_count += 1
        if placeholder_count >= 26:  # 仅支持A-Z
            break

    # 执行替换（从后往前避免位置偏移）
    normalized = list(text)
    for start, end, original in reversed(matches):
        lower_name = original.lower()
        if lower_name in placeholder_map:
            normalized[start:end] = list(placeholder_map[lower_name])

    return ''.join(normalized), {v: k for k, v in placeholder_map.items()}


def process_file(input_path: str, output_path: str, mapping_path: str, name_file: str):
    """处理整个文件"""
    # 加载姓名列表
    names = load_names(name_file)
    if not names:
        raise ValueError("No valid names found in the name file")

    # 创建匹配模式
    pattern = create_name_pattern(names)

    # 处理文本
    with open(input_path, 'r') as f_in, \
            open(output_path, 'w') as f_out, \
            open(mapping_path, 'w') as f_map:

        for line in f_in:
            original_line = line.strip()
            if not original_line:
                continue

            # 执行归一化
            normalized, mapping = normalize_text(original_line, pattern)

            # 写入结果
            f_out.write(normalized + '\n')

            # 保存映射关系（每行独立）
            if mapping:
                f_map.write(f"{original_line} ||| {normalized} ||| {json.dumps(mapping)}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="文本归一化处理器")
    parser.add_argument("-i", "--input", required=True, help="原始语料文件路径")
    parser.add_argument("-o", "--output", required=True, help="归一化后文件路径")
    parser.add_argument("-m", "--mapping", required=True, help="映射关系保存路径")
    parser.add_argument("-n", "--names", required=True, help="玩家名单文件路径")

    args = parser.parse_args()

    process_file(
        input_path=args.input,
        output_path=args.output,
        mapping_path=args.mapping,
        name_file=args.names
    )