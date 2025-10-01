import re
import os
from collections import defaultdict, Counter
import time
import argparse


class CombatLogAnalyzer:
    def __init__(self):
        # 定义所有已知的攻击类型
        self.known_attack_types = [
            'backstab', 'bash', 'bite', 'claw', 'crush',
            'gore', 'hit', 'kick', 'maul', 'pierce',
            'punch', 'slash', 'slice', 'sting', 'strike'
        ]

        # 构建正则表达式模式
        attack_patterns = []
        for attack_type in self.known_attack_types:
            # 匹配各种时态和形式
            attack_patterns.append(f"{attack_type}s")  # 第三人称单数
            attack_patterns.append(f"tries to {attack_type}")  # 尝试攻击
            attack_patterns.append(f"try to {attack_type}")  # 尝试攻击（原形）
            attack_patterns.append(attack_type)  # 原形

        pattern_str = '|'.join(attack_patterns)
        self.attack_pattern = re.compile(
            rf'^\[.*?\]\s+(.*?)\s+({pattern_str})\s+.*$',
            re.IGNORECASE
        )

        # 存储结果
        self.attack_types = Counter()
        self.monster_attacks = defaultdict(Counter)
        self.missed_attacks = Counter()  # 尝试但未命中的攻击
        self.successful_attacks = Counter()  # 成功命中的攻击
        self.total_attacks = 0

    def classify_attack(self, attack_verb: str) -> tuple:
        """对攻击动词进行分类，返回(基础攻击类型, 是否命中)"""
        attack_verb = attack_verb.lower()
        base_attack = None
        is_hit = True

        # 检查是否是尝试攻击（未命中）
        if attack_verb.startswith('tries to ') or attack_verb.startswith('try to '):
            base_attack = attack_verb.replace('tries to ', '').replace('try to ', '')
            is_hit = False
        # 检查第三人称单数形式
        elif attack_verb.endswith('s') and attack_verb[:-1] in self.known_attack_types:
            base_attack = attack_verb[:-1]
        # 直接匹配基础攻击类型
        elif attack_verb in self.known_attack_types:
            base_attack = attack_verb

        return base_attack, is_hit

    def process_line(self, line: str) -> bool:
        """处理单行日志"""
        match = self.attack_pattern.match(line.strip())
        if match:
            monster_name = match.group(1).strip()
            attack_verb = match.group(2).lower()

            base_attack, is_hit = self.classify_attack(attack_verb)

            if base_attack:  # 确保是已知的攻击类型
                # 统计攻击类型
                self.attack_types[base_attack] += 1
                self.monster_attacks[monster_name][base_attack] += 1
                self.total_attacks += 1

                # 统计命中和未命中
                if is_hit:
                    self.successful_attacks[base_attack] += 1
                else:
                    self.missed_attacks[base_attack] += 1

                return True
        return False

    def process_file(self, file_path: str):
        """处理单个文件"""
        attack_count = 0
        line_count = 0

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line_count += 1
                    if self.process_line(line):
                        attack_count += 1

                    # 进度显示
                    if line_count % 1000000 == 0:
                        print(f"Processed {line_count:,} lines in {os.path.basename(file_path)}")

        except Exception as e:
            print(f"Error processing {file_path}: {e}")

        return line_count, attack_count

    def process_directory(self, directory_path: str):
        """处理目录下的所有文件"""
        results = {'total_files': 0, 'total_lines': 0, 'total_attacks': 0}

        if not os.path.exists(directory_path):
            print(f"Directory {directory_path} does not exist!")
            return results

        # 查找所有日志文件
        log_files = []
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if any(file.endswith(ext) for ext in ['.txt', '.log', '.eqlog']):
                    log_files.append(os.path.join(root, file))

        print(f"Found {len(log_files)} log files")

        for i, file_path in enumerate(log_files, 1):
            print(f"[{i}/{len(log_files)}] Processing {os.path.basename(file_path)}")
            start_time = time.time()

            lines, attacks = self.process_file(file_path)
            results['total_lines'] += lines
            results['total_attacks'] += attacks
            results['total_files'] += 1

            elapsed = time.time() - start_time
            print(f"  -> {lines:,} lines, {attacks:,} attacks, {elapsed:.2f}s")

        return results

    def get_summary(self):
        """获取分析摘要"""
        total_hits = sum(self.successful_attacks.values())
        total_misses = sum(self.missed_attacks.values())
        hit_rate = (total_hits / self.total_attacks * 100) if self.total_attacks > 0 else 0

        # 计算每种攻击的命中率
        attack_stats = []
        for attack_type in self.known_attack_types:
            hits = self.successful_attacks[attack_type]
            misses = self.missed_attacks[attack_type]
            total = hits + misses
            if total > 0:
                rate = (hits / total * 100)
                attack_stats.append((attack_type, total, hits, misses, rate))

        # 按总数排序
        attack_stats.sort(key=lambda x: x[1], reverse=True)

        return {
            'total_attacks': self.total_attacks,
            'total_hits': total_hits,
            'total_misses': total_misses,
            'hit_rate': hit_rate,
            'attack_stats': attack_stats,
            'top_attack_types': self.attack_types.most_common(10),
            'top_monsters': [(m, sum(a.values())) for m, a in
                             sorted(self.monster_attacks.items(),
                                    key=lambda x: sum(x[1].values()),
                                    reverse=True)[:10]]
        }

    def save_detailed_report(self, output_file: str):
        """保存详细报告"""
        summary = self.get_summary()

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("DETAILED COMBAT ATTACK ANALYSIS\n")
            f.write("=" * 50 + "\n\n")

            f.write(f"Total attacks analyzed: {summary['total_attacks']:,}\n")
            f.write(f"Successful hits: {summary['total_hits']:,}\n")
            f.write(f"Missed attacks: {summary['total_misses']:,}\n")
            f.write(f"Overall hit rate: {summary['hit_rate']:.2f}%\n\n")

            f.write("ATTACK TYPE STATISTICS:\n")
            f.write("-" * 40 + "\n")
            f.write(f"{'Attack Type':<12} {'Total':<8} {'Hits':<8} {'Misses':<8} {'Hit Rate':<10}\n")
            f.write("-" * 40 + "\n")

            for attack_type, total, hits, misses, rate in summary['attack_stats']:
                if total > 0:
                    f.write(f"{attack_type:<12} {total:<8} {hits:<8} {misses:<8} {rate:<8.2f}%\n")

            f.write("\nTOP 10 ATTACK TYPES:\n")
            f.write("-" * 30 + "\n")
            for attack_type, count in summary['top_attack_types']:
                percentage = (count / summary['total_attacks']) * 100
                f.write(f"{attack_type:<12}: {count:>8,} ({percentage:6.2f}%)\n")

            f.write("\nTOP 10 MONSTERS BY ATTACK COUNT:\n")
            f.write("-" * 40 + "\n")
            for monster, count in summary['top_monsters']:
                f.write(f"{monster:<30}: {count:>8,}\n")

            f.write("\nDETAILED MONSTER ATTACK BREAKDOWN:\n")
            f.write("=" * 50 + "\n")
            for monster, attacks in sorted(self.monster_attacks.items(),
                                           key=lambda x: sum(x[1].values()),
                                           reverse=True):
                total = sum(attacks.values())
                if total >= 10:  # 只显示攻击次数较多的怪物
                    f.write(f"\n{monster} (Total: {total:,}):\n")
                    for attack_type, count in attacks.most_common():
                        percentage = (count / total) * 100
                        f.write(f"  {attack_type:<12}: {count:>6,} ({percentage:6.2f}%)\n")


def main():
    parser = argparse.ArgumentParser(description='Analyze combat attack types in EQ logs')
    parser.add_argument('path', help='Path to log file or directory')
    parser.add_argument('-o', '--output', default='attack_analysis.txt',
                        help='Output file name')
    parser.add_argument('--min-lines', type=int, default=1000,
                        help='Minimum lines to process (skip small files)')

    args = parser.parse_args()

    analyzer = CombatLogAnalyzer()
    start_time = time.time()

    print("Known attack types:", ', '.join(analyzer.known_attack_types))
    print()

    if os.path.isfile(args.path):
        print(f"Processing file: {args.path}")
        lines, attacks = analyzer.process_file(args.path)
        print(f"Results: {lines:,} lines, {attacks:,} attacks")

    elif os.path.isdir(args.path):
        print(f"Processing directory: {args.path}")
        results = analyzer.process_directory(args.path)
        print(f"Final results: {results['total_files']} files, "
              f"{results['total_lines']:,} lines, "
              f"{results['total_attacks']:,} attacks")

    else:
        print(f"Path {args.path} does not exist!")
        return

    # 保存结果
    analyzer.save_detailed_report(args.output)

    elapsed = time.time() - start_time
    print(f"\nAnalysis completed in {elapsed:.2f} seconds")
    print(f"Detailed report saved to {args.output}")

    # 显示简要结果
    summary = analyzer.get_summary()
    print(f"\nSUMMARY:")
    print(f"Total attacks: {summary['total_attacks']:,}")
    print(f"Hit rate: {summary['hit_rate']:.2f}%")
    print(f"Attack types:")
    for i, (attack_type, count) in enumerate(summary['top_attack_types'][:], 1):
        print(f"  {i}. {attack_type}: {count:,}")


if __name__ == "__main__":
    main()
