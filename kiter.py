import re


def analyze_hate(log_file):
    # 初始化变量
    current_target = None
    hate_counts = {}

    # 定义匹配模式
    target_pattern = re.compile(r'\[.*\] (\w+) is not online at this time\.')
    hate_patterns = [
        re.compile(r'\[.*\] Your target resisted the .* spell\.'),
        re.compile(r'\[.*\] Your spell did not take hold\.'),
        re.compile(r'\[.*\] .* looks uncomfortable\.')
    ]

    # 读取日志文件
    with open(log_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # 检查是否是目标切换行
            target_match = target_pattern.match(line)
            if target_match:
                current_target = target_match.group(1)
                if current_target not in hate_counts:
                    hate_counts[current_target] = 0
                continue

            # 如果不是目标切换行且有当前目标，检查是否是仇恨行为
            if current_target:
                for pattern in hate_patterns:
                    if pattern.match(line):
                        hate_counts[current_target] += 1
                        break

    return hate_counts


if __name__ == '__main__':
    import sys

    if len(sys.argv) != 2:
        print("Usage: python kiter.py <log_file>")
        sys.exit(1)

    result = analyze_hate(sys.argv[1])
    for target, count in result.items():
        print(f"{target}: {count}")
