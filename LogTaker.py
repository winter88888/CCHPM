import os
import sys
import re
from PyQt5.QtWidgets import (
    QMainWindow, QSplitter, QTreeWidget, QTreeWidgetItem,
    QPlainTextEdit, QApplication, QPushButton, QHBoxLayout,
    QWidget, QVBoxLayout, QSizePolicy, QProgressBar, QLabel,
    QFrame, QScrollArea, QDialog
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QTime, QSettings, QRect
from PyQt5.QtGui import QTextCursor, QTextCharFormat, QColor, QFont
import joblib
from fuzzywuzzy import process
from typing import Optional
from LogImporterDialog import *
from datetime import datetime, timedelta


class TypoCorrector:
    def __init__(self, name_file: str):
        # 加载潜在出勤人员名单并预处理
        with open(name_file, 'r') as f:
            self.raiders = [line.strip().lower() for line in f if line.strip()]

        # 构建单词分割正则（支持英文标点）
        self.word_pattern = re.compile(r"\b[\w']+\b")

    def find_typo_candidate(self, text: str, word_pos: int) -> Optional[str]:
        """查找可能正确的名字"""
        # 分割单词（保留原始大小写）
        words = self.word_pattern.findall(text)
        if word_pos < 1 or word_pos > len(words):
            return None

        # 提取目标单词并转为小写
        target_word = words[word_pos - 1].lower()

        # 模糊匹配最佳候选（阈值设为75）
        candidates = process.extractBests(
            target_word,
            self.raiders,
            score_cutoff=75,
            limit=1
        )
        return candidates[0][0].title() if candidates else None


class LogTaker(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("EQ Raid Attendance Log Taker")
        self.initialized = False
        self.settings = QSettings("Kingdom", "LogTaker")  # 初始化QSettings
        self.setGeometry(100, 100, 1200, 800)
        self.autoPopupRALogTaker=False
        self.tellWaitingTime = 10                         # 10 minutes
        self.is_stopped = True                            # stop flag for processing tells or /who lines
        self.who_status = "unseen"
        self.yourName = ""
        self.tell_pattern= ""
        self.model = None
        self.corrector =None
        self.current_timeout = 0
        self.events = []
        self.current_event = None
        self.is_doing_offline_processing = False
        self.last_KLOG_time = None
        self.who_pattern=re.compile(r'^\[.*?\] +(?: \<LINKDEAD\>| AFK |\* GM \* ){0,3}\[.*\] (\S+)')
        self.pet_tell_pattern = r'^\[.*?\] \w+ tells you, \'Attacking .* Master\.\''

        self.init_ui()
        self.load_layout()  # 初始化时加载布局
        self.init_connections()

        self.max_loaded_events = 10  # 新增配置变量
        #self.load_events()          # 初始化时加载事件
        self.save_dir = os.path.join(os.getcwd(), "KLOGS")
        os.makedirs(self.save_dir, exist_ok=True)


        self.logEditor=LogImporterDialog(self)


    def init_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)  # 可选：设置边距

        # Top section: Tree + Logs
        self.top_splitter = QSplitter(Qt.Horizontal)
        self.top_splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Left panel - Event tree
        self.event_tree = QTreeWidget()
        self.event_tree.setHeaderLabels(["Time", "Event Name","Zone"])
        # 设置标题居中
        header = self.event_tree.headerItem()
        for col in range(header.columnCount()):
            header.setTextAlignment(col, Qt.AlignCenter)
        self.event_tree.setColumnWidth(0, 150)
        self.top_splitter.addWidget(self.event_tree)

        # Right panels
        self.right_splitter = QSplitter(Qt.Vertical)

        # Raw log section with header
        raw_widget = QWidget()
        raw_layout = QVBoxLayout(raw_widget)
        raw_header = QHBoxLayout()
        raw_header.addWidget(QLabel("Raw Logs"))
        raw_header.addStretch()
        self.offline_btn = QPushButton("Offline mode")  # 新增离线按钮
        raw_header.addWidget(self.offline_btn)
        self.reset_layout_btn=QPushButton("Reset layout")
        raw_header.addWidget(self.reset_layout_btn)
        raw_layout.addLayout(raw_header)
        self.raw_text = QPlainTextEdit()
        self.raw_text.setReadOnly(True)
        raw_layout.addWidget(self.raw_text)
        self.right_splitter.addWidget(raw_widget)

        # Format button with separator
        format_widget = QWidget()
        format_layout = QVBoxLayout(format_widget)
        self.format_btn = QPushButton("▼ Format above logs while keep receiving tells▼")
        self.format_btn.setStyleSheet("QPushButton { font-weight: bold; }")
        format_layout.addWidget(self.format_btn)
        self.right_splitter.addWidget(format_widget)

        # Converted log section with header
        converted_widget = QWidget()
        converted_layout = QVBoxLayout(converted_widget)
        converted_header = QHBoxLayout()
        converted_header.addWidget(QLabel("Converted Logs"))
        converted_header.addStretch()
        converted_layout.addLayout(converted_header)
        self.conv_text = QPlainTextEdit()
        self.conv_text.setReadOnly(True)
        converted_layout.addWidget(self.conv_text)
        self.right_splitter.addWidget(converted_widget)

        self.top_splitter.addWidget(self.right_splitter)
        self.top_splitter.setSizes([300, 900])
        self.top_splitter.setHandleWidth(5)  # 可选：调整分隔条宽度
        self.top_splitter.setStretchFactor(0, 1)  # 左侧事件树占1份
        self.top_splitter.setStretchFactor(1, 3)  # 右侧日志区域占3份
        self.right_splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.right_splitter.setStretchFactor(0, 1)  # 原始日志区域占1份
        self.right_splitter.setStretchFactor(1, 1)  # 格式按钮占0份（固定高度）
        self.right_splitter.setStretchFactor(2, 1)  # 转换日志区域占1份
        # 设置各部分的默认比例（例如：原始日志40%，按钮20%，转换日志40%）
        self.right_splitter.setSizes([400, 50, 400])

        # Copy buttons
        self.copy_raw_btn  = QPushButton("Copy Original Log", self.raw_text)
        self.copy_conv_btn = QPushButton("Copy Formatted Log", self.conv_text)





        # Bottom section
        self.bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(self.bottom_widget)
        self.bottom_widget.setMaximumHeight(150)  # 固定底部区域最大高度
        self.bottom_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Progress bar with label
        progress_container = QHBoxLayout()
        self.progress_label = QLabel("Tells waiting time remaining [00:00]")
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(self.tellWaitingTime*60)
        self.progress_bar.setTextVisible(False)
        self.stop_btn = QPushButton("Stop receiving tell")
        self.stop_btn.setStyleSheet("QPushButton { padding: 3px 8px; }")
        progress_container.addWidget(self.progress_label)
        progress_container.addWidget(self.progress_bar)
        progress_container.addWidget(self.stop_btn)

        bottom_layout.addLayout(progress_container)

        # Info panel with scroll
        info_scroll = QScrollArea()
        info_scroll.setWidgetResizable(True)
        self.info_panel = QPlainTextEdit()
        self.info_panel.setReadOnly(True)
        self.info_panel.setMaximumHeight(100)
        info_scroll.setWidget(self.info_panel)
        bottom_layout.addWidget(QLabel("System Messages:"))
        bottom_layout.addWidget(info_scroll)

        # Assemble main layout
        main_layout.addWidget(self.top_splitter, 1)  # 关键修改：拉伸因子为1
        main_layout.addWidget(self.bottom_widget)
        self.setCentralWidget(main_widget)

        # Text formats
        self.highlight_format = QTextCharFormat()
        self.highlight_format.setBackground(QColor(255, 255, 150))

    def reset_layout(self):
        self.settings.clear()
        self.setGeometry(QRect(358, 319, 1167, 587))

        # Top section: Tree + Logs
        self.top_splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Left panel - Event tree
        self.event_tree.setColumnWidth(0, 150)

        # Converted log section with header
        self.top_splitter.setSizes([300, 900])
        self.top_splitter.setHandleWidth(5)  # 可选：调整分隔条宽度
        self.top_splitter.setStretchFactor(0, 1)  # 左侧事件树占1份
        self.top_splitter.setStretchFactor(1, 3)  # 右侧日志区域占3份
        self.right_splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.right_splitter.setStretchFactor(0, 1)  # 原始日志区域占1份
        self.right_splitter.setStretchFactor(1, 1)  # 格式按钮占0份（固定高度）
        self.right_splitter.setStretchFactor(2, 1)  # 转换日志区域占1份
        # 设置各部分的默认比例（例如：原始日志40%，按钮20%，转换日志40%）
        self.right_splitter.setSizes([400, 50, 400])

        self.bottom_widget.setMaximumHeight(150)  # 固定底部区域最大高度
        self.bottom_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)


        # Info panel with scroll
        self.info_panel.setMaximumHeight(100)

        self.adjustCopyButtons()
        self.log_message("The layout of window has been seset to its default.")



    def save_layout(self):
        """保存窗口布局状态"""
        self.settings.setValue("Version", "1.1")

        # 保存主窗口几何状态
        self.settings.setValue("MainWindow/Geometry", self.saveGeometry())
        # 保存顶部横向分隔条位置
        self.settings.setValue("TopSplitter/State", self.top_splitter.saveState())
        # 保存右侧纵向分隔条位置
        self.settings.setValue("RightSplitter/State", self.right_splitter.saveState())
        # 保存事件树的列宽
        self.settings.setValue("EventTree/ColumnWidth", self.event_tree.columnWidth(0))

    def load_layout(self):
        """加载窗口布局状态"""
        version = self.settings.value("Version", "1.1")
        if version == "1.1":
            # 恢复主窗口几何状态
            if self.settings.contains("MainWindow/Geometry"):
                self.restoreGeometry(self.settings.value("MainWindow/Geometry"))
            # 恢复顶部横向分隔条位置
            if self.settings.contains("TopSplitter/State"):
                self.top_splitter.restoreState(self.settings.value("TopSplitter/State"))
            # 恢复右侧纵向分隔条位置
            if self.settings.contains("RightSplitter/State"):
                self.right_splitter.restoreState(self.settings.value("RightSplitter/State"))
            # 恢复事件树的列宽
            if self.settings.contains("EventTree/ColumnWidth"):
                self.event_tree.setColumnWidth(0, self.settings.value("EventTree/ColumnWidth", type=int))
        else:
            self.reset_layout()

    def init_connections(self):
        self.event_tree.itemSelectionChanged.connect(self.on_event_selected)
        self.copy_raw_btn.clicked.connect(self.copy_raw)
        self.copy_conv_btn.clicked.connect(self.copy_conv)
        #self.raw_text.cursorPositionChanged.connect(self.highlight_conv_line)
        self.format_btn.clicked.connect(self.format_logs)
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_progress)
        self.top_splitter.splitterMoved.connect(self.adjustCopyButtons)
        self.right_splitter.splitterMoved.connect(self.adjustCopyButtons)
        self.reset_layout_btn.clicked.connect(self.reset_layout)
        self.stop_btn.clicked.connect(self.on_stop_clicked)  # 连接点击事件
        self.offline_btn.clicked.connect(self.showEditor)

    def initialize_filters(self,yourName:str):

        self.yourName=yourName
        # 动态生成匹配模式，使用 re.escape 避免特殊字符干扰
        your_name_pattern = re.escape(self.yourName)
        self.tell_pattern = (
            r'^\[(.*?)\]\s+'  # 时间戳
            r'(\w+)\s+'  # 发送者
            r'(?:'  # 匹配以下两种形式之一
            r'->\s+{0}: '  # 形式1: -> [考勤员ID]
            r'|'  # 或
            r'tells\s+you,\s*\''  # 形式2: tells you
            r')'  # 结束分组
            r'(.*)'  # 消息内容
        ).format(your_name_pattern)  # 动态插入考勤员ID

        if self.initialized:
            return

        self.initialized = True


        self.model = joblib.load("classifier.joblib")

        # 初始化纠错器（假设raiders.txt已加载）
        self.corrector = TypoCorrector("raiders.txt")  # 需提前初始化

        # 加载潜在出勤人员名单
        self.raider_names = self.load_raiders("raiders.txt")


    def load_raiders(self, filename: str) -> list:
        with open(filename, 'r') as f:
            names = [line.strip() for line in f if line.strip()]
        # 按长度降序排序，优先匹配长姓名
        return sorted(names, key=lambda x: -len(x))

    def normalize_message(self,message: str, raider_names: list) -> tuple:
        # 生成正则匹配模式（不区分大小写）
        pattern = re.compile(
            r'\b(' + '|'.join(re.escape(name) for name in raider_names) + r')\b',
            flags=re.IGNORECASE
        )

        # 查找所有匹配的姓名（按原始大小写）
        matches = []
        for match in pattern.finditer(message):
            original_name = message[match.start():match.end()]
            matches.append(original_name)

        # 去重并保留前两个不同姓名
        unique_matches = []
        seen = set()
        for name in matches:
            lower_name = name.lower()
            if lower_name not in seen:
                seen.add(lower_name)
                unique_matches.append(name)
                if len(unique_matches) >= 2:
                    break

        # 构建替换映射（PlayerA, PlayerB）
        mapping = {}
        normalized = message
        for i, name in enumerate(unique_matches, 1):
            placeholder = f"Player{chr(64 + i)}"  # PlayerA, PlayerB
            mapping[placeholder] = name
            normalized = re.sub(rf'\b{re.escape(name)}\b', placeholder, normalized, flags=re.IGNORECASE)

        return normalized, mapping

    def denormalize_result(self,result: str, mapping: dict) -> str:
        # 匹配占位符（PlayerA/B/C）
        placeholders = re.findall(r'\bPlayer[A-C]\b', result)
        for ph in placeholders:
            if ph in mapping:
                result = result.replace(ph, mapping[ph])
        return result


    def predict(self, text):
        try:
            return self.model.predict([text])[0]
        except Exception as e:
            self.log_message(f"Prediction error: {str(e)}")
            return f"error:{str(e)}"


    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        super().keyPressEvent(event)

    def closeEvent(self,event):

        self.save_layout()  # 关闭窗口时保存布局
        event.ignore()
        self.hide()

    def resizeEvent(self,event):
        event.accept()
        self.adjustCopyButtons()

    def on_stop_clicked(self):
        """停止计时、格式化日志并重置状态"""
        if not self.is_stopped:
            self.is_stopped = True
            self.who_status = "unseen"
            # 停止计时器
            self.progress_timer.stop()
            # 立即格式化日志
            self.format_logs()
            # 设置停止标志以阻止处理新tells或/who消息，只能处理!klog
            self.event_tree.setEnabled(True)


            # 重置进度显示
            self.current_timeout = 0
            self.progress_bar.setValue(0)
            self.progress_label.setText("Tells waiting time remaining: 00:00")
            self.log_message("Manual stop - Log formatting completed")

    def adjustCopyButtons(self):

        raw_width=self.raw_text.geometry().getRect()[2]
        self.copy_raw_btn.move(raw_width-self.copy_raw_btn.geometry().getRect()[2]-20, 10)
        conv_width=self.conv_text.geometry().getRect()[2]
        self.copy_conv_btn.move(conv_width-self.copy_conv_btn.geometry().getRect()[2]-20, 10)



    def log_message(self, message):
        """Log system messages to info panel"""
        timestamp = QTime.currentTime().toString("hh:mm:ss")
        self.info_panel.appendPlainText(f"[{timestamp}] {message}")
        self.info_panel.ensureCursorVisible()

    def offline_process_start(self):

        self.is_doing_offline_processing = True
        self.last_KLOG_time = None

    def offline_process(self,line:str):

        self.process_log_line(line)


    def offline_process_stop(self):

        self.on_stop_clicked()
        self.is_doing_offline_processing = False
        self.last_KLOG_time = None

    def online_process(self,line:str):

        if self.is_doing_offline_processing:          #program won't handle online msg if doing offline processing
            return                                    #since offline is quicker

        self.process_log_line(line)


    # 补全的核心方法
    def process_log_line(self, line:str):
        """Main log processing entry point"""
        try:

            if line[26:].lower() == " log is not online at this time.\n":
                self.show()
                self.raise_()
                width = self.geometry().getRect()[2]
                height = self.geometry().getRect()[3]
                self.resize(width + 1, height)
                self.resize(width, height)

                return


            if line[26:49]==" You say to your guild,":
                index = line[49:].upper().find('!KLOG')
                if index != -1:
                    raw_time = re.search(r'\[(.*?)\]', line).group(1)
                    current_time = datetime.strptime(raw_time, "%a %b %d %H:%M:%S %Y")
                    if self.last_KLOG_time == None or current_time-self.last_KLOG_time > timedelta(seconds=10):   #prevent dampening of KLOG
                        self.last_KLOG_time=current_time
                        self.start_new_event(line,49+index)
                return

            if self.is_stopped:  # 如果已停止，不再处理新tells或/who消息
                return

            if not self.current_event:
                return


            if self.process_player_line(line) == True:
                return

            if self.who_status != "ended":         # 仅在/WHO结束后才开始处理tell
                return

            if self.process_tell_line(line) == True:
                return


        except Exception as e:
            self.log_message(f"Processing error: {str(e)}")

    @staticmethod
    def seconds_to_mmss(seconds: int) -> str:
        """将秒数转换为 mm:ss 格式"""
        mins, secs = divmod(seconds, 60)
        return f"{mins:02d}:{secs:02d}"  # 格式化为两位数

    def start_new_event(self, line:str,index:int):
        """Initialize new logging event"""
        try:

            # 如果存在进行中的未停止事件，先终止旧事件
            if not self.is_stopped:
                self.is_stopped = True
                self.who_status = "unseen"
                # 停止计时器
                self.progress_timer.stop()
                # 强制格式化旧日志
                self.format_logs()
                # 重置进度状态
                self.current_timeout = 0
                self.progress_bar.setValue(0)
                self.progress_label.setText("Tells waiting time remaining [00:00]")
                self.log_message("Previous event terminated for new log start")


            # 清空显示内容
            self.raw_text.clear()
            self.conv_text.clear()
            # 清理可能残留的选中状态
            self.event_tree.clearSelection()
            self.is_stopped = False  # 核心状态控制
            self.event_tree.setEnabled(False)



            # 初始化新事件（无论是否有旧事件）
            line=line.rstrip()
            original_time = re.search(r'\[(.*?)\]', line).group(1)
            dt = datetime.strptime(original_time, "%a %b %d %H:%M:%S %Y")
            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")

            event_name = re.search(r'(?:[ -]+)(.*?)\'', line[index:]).group(1)
            if event_name == "":
                event_name = "*Unknown Event*"

            tree_item = QTreeWidgetItem([formatted_time, event_name, "TBD"])
            self.event_tree.addTopLevelItem(tree_item)

            for col in range(tree_item.columnCount()):
                tree_item.setForeground(col, QColor("#0000FF"))  # 蓝色

            # 重置事件状态
            self.current_event = {
                'time': formatted_time,
                'name': event_name,
                'zone': "TBD",
                'players': [],
                'tells': [],
                'raw_logs': [],
                'raw_tells':[],
                'commands': [],
                'converted': False,
                'tree_item':tree_item,
                'tell_pattern':self.tell_pattern

            }

            self.events.append(self.current_event)

            # stop existing timer
            self.progress_timer.stop()


            # Initialize progress tracking

            self.current_timeout = self.tellWaitingTime*60
            self.progress_bar.setMaximum(self.current_timeout)
            self.progress_bar.setValue(self.current_timeout)

            # 初始化标签显示
            time_str = self.seconds_to_mmss(self.current_timeout)
            self.progress_label.setText(f"Tells waiting time remaining [{time_str}]")

            self.progress_timer.start(1000)


            self.current_event['raw_logs'].append(line)
            self.raw_text.appendPlainText(line)

            self.log_message(f"New event started: {event_name}")

        except Exception as e:
            self.log_message(f"Event creation failed: {str(e)}")

    def process_player_line(self, line:str):
        """Process /who list entries"""
        try:
            line = line.rstrip()

            if line[26:] ==  " Players on EverQuest:":
                if self.who_status == "unseen":        #仅在KLOG生成新战斗记录后处理第一次的/WHO结果
                    self.who_status = "started"
                    self.current_event['raw_logs'].append(line)
                    self.current_event['raw_logs'].append(line.replace(" Players on EverQuest:"," ---------------------------"))
                    self.raw_text.appendPlainText(line)
                    self.raw_text.appendPlainText(line.replace(" Players on EverQuest:"," ---------------------------"))
                return True

            match = re.search(r" There are \d{1,3} players in (.+?)\.$", line[26:])
            if match:
                if self.who_status == "started":
                    self.who_status = "ended"
                    self.current_event['zone'] = match.group(1)
                    if 'tree_item' in self.current_event:  # 确保存在树项引用
                        self.current_event['tree_item'].setText(2, self.current_event['zone'])
                        # self.event_tree.resizeColumnToContents(2)  #自动调整列宽

                    self.current_event['raw_logs'].append(line)
                    self.raw_text.appendPlainText(line)
                    self.raw_text.appendPlainText("\n##########  Player Notifications  ##########\n")
                return True

            if self.who_status != "started":           #仅第一个/WHO产生的记录会被受理，其他时间段内产生的/WHO直接忽略
                return False

            if self.who_pattern.search(line):
                self.current_event['raw_logs'].append(line)
                self.raw_text.appendPlainText(line)
                return True

        except Exception as e:
            self.log_message(f"Player entry error: {str(e)}")

        return False

    def update_tell_pattern_for_offline(self,pattern:str):

        if self.current_event:
            self.current_event['tell_pattern']=pattern

    def process_tell_line(self, line):
        """Process player tell messages"""
        try:

            match = re.search(self.current_event['tell_pattern'], line, re.IGNORECASE)
            if match:
                # 新增过滤逻辑：剔除宠物垃圾消息
                if re.match(self.pet_tell_pattern, line):
                    self.log_message(f"Filtered pet tell: {line}")
                    return False  # 跳过此消息

                timestamp, sender, message = match.groups()
                tell = {
                    'time': timestamp,
                    'sender': sender,
                    'message': message.strip("'").rstrip()
                }
                self.current_event['tells'].append(tell)
                self.current_event['raw_tells'].append(line.rstrip())
                self.raw_text.appendPlainText(line.rstrip())
                return True

        except Exception as e:
            self.log_message(f"Tell processing error: {str(e)}")

        return False

    def format_logs(self):
        """使用模型预测处理日志（去重版）"""
        if not self.current_event:
            return


        if not self.initialized:
            self.initialize_filters("Nobody")


        try:

            # ===== 初始化数据结构 =====
            existing_players = set()  # 当前出勤列表（小写存储）
            processed_senders = set()  # 已处理的发送者
            final_commands = []
            max_cmd_length = 0  # 用于对齐注释

            # 初始化existing_players（从/who结果提取）
            for log_line in self.current_event['raw_logs']:
                if match := self.who_pattern.search(log_line):
                    existing_players.add(match.group(1).lower())

            # ===== 处理每条tell消息 =====
            temp_commands = []
            for tell in self.current_event['tells']:
                sender = tell['sender'].lower().capitalize()  # 规范发送者格式
                sender_lower = sender.lower()
                message = tell['message'].strip()
                comment = f"{sender}: {message}"

                # (1) 检测重复tell
                if sender_lower in processed_senders:
                    cmd = f"#skip - no multiple tells in one log"
                    temp_commands.append((cmd, comment))
                    max_cmd_length = max(max_cmd_length, len(cmd))
                    continue

                processed_senders.add(sender_lower)  # 标记为已处理

                # 姓名替换归一化
                normalized_msg, mapping = self.normalize_message(message, self.raider_names)

                # (2) 调用模型预测
                try:
                    result = self.predict(normalized_msg)
                except Exception as e:
                    cmd = f"#skip - met an error: {str(e)}"
                    temp_commands.append((cmd, comment))
                    max_cmd_length = max(max_cmd_length, len(cmd))
                    continue

                # 反向解析占位符
                result = self.denormalize_result(result, mapping)

                # (3-6) 处理预测结果
                if result == "DEFAULT_SENDER":
                    cmd = f"add {sender}"
                    temp_commands.append((cmd, comment))
                    max_cmd_length = max(max_cmd_length, len(cmd))
                    continue
                if result == "NORMAL_CHAT":
                    cmd = "#skip - normal chat"
                    temp_commands.append((cmd, comment))
                    max_cmd_length = max(max_cmd_length, len(cmd))
                    continue

                if result.startswith("error:"):
                    cmd = f"#skip - {result}"
                    temp_commands.append((cmd, comment))
                    max_cmd_length = max(max_cmd_length, len(cmd))
                    continue

                # 处理NAME_TYPO_AT_WORD_n返回值
                if result.startswith("NAME_TYPO_AT_WORD_"):
                    # 解析错误位置
                    try:
                        word_pos = int(result.split('_')[-1])
                    except:
                        cmd = "#skip - invalid typo format"
                        temp_commands.append((cmd, comment))
                        max_cmd_length = max(max_cmd_length, len(cmd))
                        continue
                    else:
                        # 执行纠错
                        corrected_name = self.corrector.find_typo_candidate(message, word_pos)
                        if corrected_name:
                            # 替换预测结果中的占位符
                            result = result.replace(
                                f"NAME_TYPO_AT_WORD_{word_pos}",
                                corrected_name
                            )
                        else:
                            cmd = "#skip - no candidate found"
                            temp_commands.append((cmd, comment))
                            max_cmd_length = max(max_cmd_length, len(cmd))
                            continue

                # 规范ID格式（首字母大写）
                result_id = result[0].upper() + result[1:].lower()

                # (5) 判断sender是否存在
                if sender_lower in existing_players:
                    cmd = f"swap {sender} {result_id}"
                else:
                    cmd = f"add {result_id}"

                temp_commands.append((cmd, comment))
                max_cmd_length = max(max_cmd_length, len(cmd))

            # ===== 生成对齐的命令行 =====
            for cmd, cmt in temp_commands:
                padding = ' ' * (max_cmd_length - len(cmd)) if max_cmd_length > len(cmd) else ''
                final_commands.append(f"{cmd}{padding}  # {cmt}")

            # ===== 构建最终输出 =====
            converted = [
                *self.current_event['raw_logs'],
                "\n##########  Players to Add/Swap  ##########\n",
                *final_commands
            ]

            self.conv_text.setPlainText("\n".join(converted))
            self.current_event['commands'] = final_commands
            self.current_event['converted'] = True
            # ===== 新增：保存到文件 =====
            self.save_current_event()

        except Exception as e:
            self.log_message(f"Formating log met an error: {str(e)}")


    def update_progress(self):
        """Update progress bar and handle timeout"""

        if self.current_timeout > 0:
            self.current_timeout -= 1
            self.progress_bar.setValue(self.current_timeout)
            # 更新标签显示
            time_str = self.seconds_to_mmss(self.current_timeout)
            self.progress_label.setText(f"Tells waiting time remaining [{time_str}]")

        else:
            self.progress_timer.stop()
            self.is_stopped = True
            self.who_status = "unseen"
            self.format_logs()
            self.event_tree.setEnabled(True)
            self.log_message("Timeout reached - auto-formatting logs")
            # 可选：超时后显示 00:00
            self.progress_label.setText("Tells waiting time remaining [00:00]")
            if self.autoPopupRALogTaker == True:
                self.show()
                self.raise_()

    def on_event_selected(self):
        """Handle event selection from tree"""
        selected = self.event_tree.selectedItems()
        if selected:
            index = self.event_tree.indexOfTopLevelItem(selected[0])
            self.show_event_details(self.events[index])

    def show_event_details(self, event):
        """Display selected event details"""
        if not event['converted']:
            return
        if not self.is_stopped:
            return
        self.current_event=event
        self.raw_text.clear()
        self.conv_text.clear()
        self.raw_text.setPlainText("\n".join([*event['raw_logs'],"\n##########  Player Notifications  ##########\n",*event.get('raw_tells', [])]))
        self.conv_text.setPlainText("\n".join([*event['raw_logs'],"\n##########  Players to Add/Swap  ##########\n",*event.get('commands', [])]))
        # 新增代码：滚动到converted logs底部
        cursor = self.conv_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.conv_text.setTextCursor(cursor)
        self.conv_text.ensureCursorVisible()


    def copy_raw(self):
        """Copy raw log contents"""
        QApplication.clipboard().setText(self.raw_text.toPlainText())
        self.log_message("Raw logs copied to clipboard")

    def copy_conv(self):
        """Copy converted log contents"""
        QApplication.clipboard().setText(self.conv_text.toPlainText())
        self.log_message("Converted logs copied to clipboard")

    def save_current_event(self):
        """保存当前事件到文件"""
        try:
            # 准备保存目录
            save_dir = os.path.join(os.getcwd(), "KLOGS")
            os.makedirs(save_dir, exist_ok=True)

            # 生成文件名
            time_str =self.current_event['time'].replace(':', '').replace(' ', '').replace('-', '')
            zone = self.current_event['zone'].replace(' ', '_')
            filename = f"KLOG{time_str}_{zone}.txt"

            # 构建文件内容
            content = [
                f"Time: {self.current_event['time']}",
                f"Event: {self.current_event['name']}",
                f"Zone: {self.current_event['zone']}",
                f"Tell_Pattern: {self.current_event['tell_pattern']}",
                "\n===== Raw Logs =====",
                *self.current_event['raw_logs'],
                "\n===== Raw Tells =====",
                *self.current_event['raw_tells'],
                "\n===== Converted Commands =====",
                *self.current_event['commands']
            ]

            # 写入文件
            with open(os.path.join(save_dir, filename), 'w') as f:
                f.write('\n'.join(content))

            self.log_message(f"Event saved: {filename}")

        except Exception as e:
            self.log_message(f"Saving event met a failure: {str(e)}")

    def max_loaded_event_handler(self,event_count:int):

        self.max_loaded_events=event_count
        self.event_tree.clear()
        self.events = []
        self.current_event = None
        # 清空日志显示
        self.raw_text.clear()
        self.conv_text.clear()

        self.load_events()

    def load_events(self):

        """加载最近的事件"""
        try:
            save_dir = os.path.join(os.getcwd(), "KLOGS")
            if not os.path.exists(save_dir):
                return

            # 获取所有符合格式的文件
            pattern = re.compile(r'KLOG(\d{14})_(.+)\.txt')
            valid_files = []
            for fname in os.listdir(save_dir):
                match = pattern.match(fname)
                if match:
                    try:
                        dt =datetime.strptime(match.group(1), '%Y%m%d%H%M%S')
                        valid_files.append((dt, fname))
                    except:
                        continue

            # 按时间降序排序
            valid_files.sort(reverse=False, key=lambda x: x[0])
            if self.max_loaded_events <= len(valid_files):
                valid_files = valid_files[-self.max_loaded_events:]
                loaded_count = self.max_loaded_events
            else:
                loaded_count= len(valid_files)


            # 加载最近的N个事件

            for dt, fname in valid_files:
                with open(os.path.join(save_dir, fname)) as f:
                    content = f.read().split('\n')

                    # 解析元数据
                    metadata = {
                        'time': content[0][6:],
                        'name': content[1][7:],
                        'zone': content[2][6:],
                        'tell_pattern': content[3][14:],
                        'raw_logs': content[6:content.index('===== Raw Tells =====')-1],
                        'tells':[],
                        'raw_tells': content[content.index('===== Raw Tells =====')+1:content.index('===== Converted Commands =====')-1],
                        'commands': content[content.index('===== Converted Commands =====') + 1:],
                        'converted': True
                    }

                    # 重建树项
                    tree_item = QTreeWidgetItem([
                        metadata['time'],
                        metadata['name'],
                        metadata['zone']
                    ])
                    self.event_tree.addTopLevelItem(tree_item)


                    for line in metadata['raw_tells']:

                        try:

                            match = re.search(metadata['tell_pattern'], line, re.IGNORECASE)
                            if match:
                                timestamp, sender, message = match.groups()
                                tell = {
                                    'time': timestamp,
                                    'sender': sender,
                                    'message': message.strip("'").rstrip()
                                }
                                metadata['tells'].append(tell)

                        except Exception as e:
                            self.log_message(f"Raw_tells processing error: {str(e)}")

                    # 添加到事件列表
                    self.events.append({
                        **metadata,
                        'tree_item': tree_item,
                        'players': []
                    })

                    for col in range(tree_item.columnCount()):
                        tree_item.setForeground(col, QColor("#8B4513"))  # 褐色


            self.log_message(f"Successfully loaded {loaded_count} latest events")

        except Exception as e:
            self.log_message(f"Failed to load latest events: {str(e)}")

    def showEditor(self):

        self.logEditor.show()
        self.logEditor.raise_()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LogTaker()

    # 测试数据
    test_logs = [
        "[Mon Apr 24 20:09:19 2023] You say to your guild, '!KLOG KDT 4/24'",
        "[Thu Jul 04 15:33:49 2024] [60 Assassin] Boucc (Dwarf) <Kingdom>",
        "[Thu Jul 04 15:33:49 2024] Bolea -> Oghaels: this is bucke",
        "[Thu Jul 04 15:33:50 2024] Player1 -> Oghaels: replace OldID with NewID",
        "[Thu Jul 04 15:33:51 2024] Player2 -> Oghaels: add MyCharacter"
    ]

    for log in test_logs:
        window.process_log_line(log)

    window.show()
    sys.exit(app.exec_())