import re
from collections import defaultdict


class ClericIDManager:
    def __init__(self):
        self.observed_ids = []
        self.pattern_counts = defaultdict(int)
        self.dominant_pattern = None

    def _detect_pattern(self, cleric_id):
        """检测单个ID所属模式"""
        if re.fullmatch(r'(\d)\1{2}', cleric_id): # 111 model
            return 'pattern_1', int(cleric_id[0])
        elif re.fullmatch(r'([A-Z])\1{2}', cleric_id):  # AAA model
            return 'pattern_2', ord(cleric_id[0]) - ord('A') + 1
        elif re.fullmatch(r'\d{1,2}', cleric_id): # 1-99 model
            return 'pattern_3', int(cleric_id)
        elif re.fullmatch(r'0\d{2}', cleric_id):  # 001 model
            return 'pattern_4', int(cleric_id)
        else:
            return  'unknown_parttern',-1                           # default mode is AAA model

    def add_id(self, cleric_id):
        """添加新ID并更新模式统计"""
        pattern, _ = self._detect_pattern(cleric_id)
        if pattern == 'unknown_parttern':
            return

        if cleric_id not in self.observed_ids:
            self.observed_ids.append(cleric_id)
        self.pattern_counts[pattern] += 1

        # 更新主导模式（出现次数最多的）
        self.dominant_pattern = max(self.pattern_counts,
                                    key=self.pattern_counts.get)

    def get_sorted_ids(self):
        """按实际序号排序所有观察到的ID"""

        def get_numeric_value(cleric_id):
            _, num = self._detect_pattern(cleric_id)
            return num

        return sorted(self.observed_ids, key=get_numeric_value)

    def predict_next_id(self, current_clericid: str):
        """预测下一个应该出现的ID，考虑当前ID和系统主导模式

        Args:
            current_clericid: 当前输入的cleric ID

        Returns:
            下一个预测的cleric ID，根据主导模式自动转换格式
        """
        if not current_clericid:
            # 如果没有当前ID，使用默认值
            return "   "

        # 解析当前ID的模式和数值
        current_pattern, current_num = self._detect_pattern(current_clericid)
        if current_pattern == "unknown_parttern":
            return "   "

        # 计算下一个数值
        if self.dominant_pattern == 'pattern_2':  # AAA-ZZZ模式
            max_alpha_num = 26
            next_num = current_num + 1 if current_num < max_alpha_num else 1
            return chr(ord('A') + next_num - 1) * 3
        elif self.dominant_pattern == 'pattern_1':  # 111-999模式
            max_repeat_num = 9
            next_num = current_num + 1 if current_num < max_repeat_num else 1
            return str(next_num) * 3
        elif self.dominant_pattern == 'pattern_3':  # 1-99模式
            max_num = 99
            next_num = current_num + 1 if current_num < max_num else 1
            return str(next_num)
        elif self.dominant_pattern == 'pattern_4':  # 001-099模式
            max_num = 99
            next_num = current_num + 1 if current_num < max_num else 1
            return f"{next_num:03d}"
        else:
            # 默认回退
            return "AAA"

    def get_pattern_description(self):
        """获取当前主导模式的描述"""
        desc = {
            'pattern_1': '111-999重复数字模式',
            'pattern_2': 'AAA-ZZZ重复字母模式',
            'pattern_3': '1-99数字模式',
            'pattern_4': '001-099三位数字模式'
        }
        return desc.get(self.dominant_pattern, "未知模式")


# 使用示例
if __name__ == "__main__":
    manager = ClericIDManager()

    # 模拟输入的混合ID
    test_ids = ["111", "3", "002", "BBB", "5", "004", "AAA", "222","6"]

    print("添加ID过程:")
    for id in test_ids:
        manager.add_id(id)
        print(f"添加: {id:<5} | 当前模式: {manager.get_pattern_description():<15} | 排序结果: {manager.get_sorted_ids()}")

    print("\n最终状态:")
    print(f"主导模式: {manager.get_pattern_description()}")
    print(f"所有ID排序: {manager.get_sorted_ids()}")
    print(f"下一个推荐ID: {manager.predict_next_id()}")