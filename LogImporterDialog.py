import datetime
import logging
import os
import re


from PyQt5.QtCore import Qt,QTimer, QSettings, QRect
from PyQt5.QtWidgets import (QLineEdit, QMessageBox, QComboBox, QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QPlainTextEdit, QProgressBar, QFileDialog, QWidget)


import sys
import traceback

def exception_hook(exctype, value, tb):
    error_msg = "".join(traceback.format_exception(exctype, value, tb))
    logging.critical(f"未捕获的全局异常:\n{error_msg}")
    QMessageBox.critical(None, "致命错误", f"程序崩溃:\n{error_msg}")
    sys.exit(1)

sys.excepthook = exception_hook



LOG_SENDNING_INTERVAL=10                #10 ms




class LogImporterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logTaker = parent
        self.setWindowTitle("EQ Raid Attendance Log Editor")
        self.setup_ui()
        self.is_processing = False
        self.paused = False
        self.tellWaitingTime = 5                          # 5 minutes
        self.is_stopped = True                            # stop flag for processing tells or /who lines
        self.who_status = "unseen"
        self.yourName = ""
        self.paused = False

        self.tell_pattern = r'^\[.*?\] \w+ (?:-> \w+: |tells you, \')'
        self.pop_tell_pattern = r'^\[.*?\] \w+ -> (\w+): '
        self.last_KLOG_time = None
        self.who_pattern=re.compile(r'^\[.*?\] +(?: \<LINKDEAD\>| AFK |\* GM \* ){0,3}\[.*\] (\S+)')

        self.timer = QTimer()
        self.timer.timeout.connect(self.process_next_line)

        self.last_dir = ""  # 新增变量保存上次打开的目录

        self.load_settings()



    def setup_ui(self):
        layout = QVBoxLayout()

        # 顶部控件：文件路径、打开按钮、时间范围、加载按钮
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("Log File:"))
        self.file_edit = QLineEdit()
        top_layout.addWidget(self.file_edit)

        open_btn = QPushButton("Open...")
        open_btn.clicked.connect(self.open_file_dialog)
        top_layout.addWidget(open_btn)

        # 添加空白占位区域
        top_layout.addSpacing(10)  # 固定10像素空白
        spacer = QWidget()
        spacer.setFixedWidth(20)  # 或使用 addStretch() 弹性空白
        top_layout.addWidget(spacer)

        self.time_combo = QComboBox()
        self.time_combo.addItems([
            "Load last hour log",
            "Load last 8 hours log",
            "Load last whole day log",
            "Load last 3 days log",
            "Load last whole week log",
            "Load entire log file"
        ])
        top_layout.addWidget(self.time_combo)

        load_btn = QPushButton("Load")
        load_btn.clicked.connect(self.load_logs)
        top_layout.addWidget(load_btn)

        # 将Clear按钮移动到Load按钮右侧
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_content)
        top_layout.addWidget(self.clear_btn)

        layout.addLayout(top_layout)

        # 文本框区域（移除原Clear按钮布局）
        text_container = QWidget()
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        self.text_edit = QPlainTextEdit()
        text_layout.addWidget(self.text_edit)
        layout.addWidget(text_container)

        # 进度条
        self.progress = QProgressBar()
        # 设置进度条文本居中样式
        self.progress.setStyleSheet("""
            QProgressBar {
                text-align: center;
                border: 1px solid grey;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: #05B8CC;
                width: 10px;
            }
        """)
        self.progress.setFormat("%v/%m")  # 显示 "当前值/最大值" (如 50/100)

        layout.addWidget(self.progress)

        # 按钮区
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("Send text to RA Log Taker")
        self.start_btn.setStyleSheet("color: green")
        self.start_btn.clicked.connect(self.toggle_processing)
        btn_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("Stop and Reset")
        self.stop_btn.setStyleSheet("color: red")
        self.stop_btn.clicked.connect(self.stop_processing)
        btn_layout.addWidget(self.stop_btn)

        view_btn = QPushButton("View result in RA Log Taker")
        view_btn.clicked.connect(self.show_main_window)
        btn_layout.addWidget(view_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def load_settings(self):
        settings = QSettings("Kingdom", "LogImporter")
        if settings.value("LogImporterDialog/geometry"):
            self.restoreGeometry(settings.value("LogImporterDialog/geometry"))
        else:
            self.setGeometry(QRect(406, 251, 1175, 651))
        self.last_dir = settings.value("LastDirectory", "")  # 新增

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        super().keyPressEvent(event)



    def closeEvent(self, event):
        settings = QSettings("Kingdom", "LogImporter")
        settings.setValue("LogImporterDialog/geometry", self.saveGeometry())
        self.stop_processing()
        super().closeEvent(event)

    def open_file_dialog(self):
        self.is_stopped = True
        self.last_KLOG_time = None
        self.who_status = "unseen"

        # 使用上次目录作为初始路径
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Log File",
            self.last_dir,  # 关键修改：传入上次目录
            "Log Files (*.txt)"
        )

        if file_path:
            self.file_edit.setText(file_path)
            # 更新并保存本次目录到 QSettings
            self.last_dir = os.path.dirname(file_path)  # 提取目录部分
            settings = QSettings("Kingdom", "LogImporter")
            settings.setValue("LastDirectory", self.last_dir)

    def clear_content(self):
        self.text_edit.clear()

    def load_logs(self):

        self.is_stopped = True
        self.who_status = "unseen"
        self.last_KLOG_time = None
        self.text_edit.clear()

        file_path = self.file_edit.text()
        if not file_path:
            QMessageBox.critical(self, "Error", "Please select a log file.")
            return

        index = self.time_combo.currentIndex()
        now = datetime.datetime.now()
        cutoff = {
            0: now - datetime.timedelta(hours=1),
            1: now - datetime.timedelta(hours=8),
            2: now - datetime.timedelta(days=1),
            3: now - datetime.timedelta(days=3),
            4: now - datetime.timedelta(weeks=1),
            5: "entire file"
        }.get(index, "entire file")

        try:
            chunk_size = 1024 * 100  # 100KB
            raw_buffer = bytearray()
            result_buffer = []
            found_start = False  # 新增标志位
            file_size= os.path.getsize(file_path)
            pointer = file_size

            with open(file_path, "rb") as f:
                if cutoff == "entire file":
                    found_start = True
                    f.seek(0)
                    raw_buffer = f.read(file_size)
                else:
                    f.seek(0, 2)

                while pointer > 0 and not found_start:
                    # 读取当前块
                    if pointer >= chunk_size:
                        read_size = chunk_size
                    else:
                        read_size = pointer
                        found_start = True


                    pointer -= read_size
                    f.seek(pointer)
                    chunk = f.read(read_size)

                    complete_1st_line=""
                    # 合并新旧数据并分割完整行
                    raw_buffer = chunk + raw_buffer  # 关键修改：正向累积
                    while True:
                        pos_n1 = raw_buffer.find(b'\n')
                        if pos_n1 == -1:
                            break
                        pos_n2 = raw_buffer[pos_n1+1:].find(b'\n')
                        if pos_n2 == -1:
                            break
                        complete_1st_line=raw_buffer[pos_n1+1:pos_n1+1+pos_n2]
                        break

                    # 正向检查块首行（时间最晚的行）
                    if complete_1st_line!="":
                        try:
                            converted_first_line = complete_1st_line.decode('utf-8', errors='replace').strip()
                            if converted_first_line.startswith('['):
                                time_str = converted_first_line[1:25]
                                log_time = datetime.datetime.strptime(time_str, '%a %b %d %H:%M:%S %Y')
                                if log_time < cutoff:
                                    found_start = True
                                    break
                        except (ValueError, IndexError):
                            pass

                if found_start:
                    pos=0
                    for i in range( len(raw_buffer)):
                        if raw_buffer[i] == 10:      #/n = 10
                            crlf = i
                            raw_line = raw_buffer[pos:crlf-1]   #/r/n = crlf in UTF-8
                            pos=crlf+1
                            if len(raw_line) < 25 :
                                continue
                            line = raw_line.decode('utf-8', errors='replace')
                            if self.isRALogLine(line):
                                result_buffer.append(line)

                    # 结果处理（保留原有顺序）
                    self.text_edit.setUpdatesEnabled(False)
                    self.text_edit.clear()
                    self.text_edit.setPlainText('\n'.join(result_buffer))
                    self.text_edit.setUpdatesEnabled(True)


                self.is_stopped = True
                self.last_KLOG_time = None
                self.who_status = "unseen"

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load logs: {str(e)}")
            print(e)

    def isRALogLine(self,line:str):

        """Main log processing entry point"""
        try:


            if line[26:49]==" You say to your guild,":
                index = line[49:].upper().find('!KLOG')
                if index != -1:
                    if self.last_KLOG_time == None:
                        self.last_KLOG_time= datetime.datetime.strptime(line[1:25], "%a %b %d %H:%M:%S %Y")
                        self.start_new_event(line,49+index)
                        return True

                    current_time = datetime.datetime.strptime(line[1:25], "%a %b %d %H:%M:%S %Y")
                    if current_time-self.last_KLOG_time > datetime.timedelta(seconds=10):   #prevent dampening of KLOG
                        self.last_KLOG_time=current_time
                        self.start_new_event(line,49+index)
                        return True

                return False


            if self.is_stopped:  # 如果已停止，不再处理新tells或/who消息
                return False

            current_time = datetime.datetime.strptime(line[1:25], "%a %b %d %H:%M:%S %Y")

            if current_time-self.last_KLOG_time > datetime.timedelta(minutes=self.logTaker.tellWaitingTime):  #use parent's tell waiting time
                self.is_stopped = True
                self.who_status = "unseen"
                self.last_KLOG_time = None
                return False

            if self.process_player_line(line) == True:
                return True

            if self.who_status != "ended":  # 仅在/WHO结束后才开始处理tell
                return False

            if self.process_tell_line(line) == True:
                return True

            return False

        except Exception as e:
            QMessageBox.critical(self, f"Processing error: {str(e)}")
            print(e)

        #return False

    def start_new_event(self, line:str,index:int):

        # 如果存在进行中的未停止事件，先终止旧事件
        if not self.is_stopped:
            self.is_stopped = True
            self.who_status = "unseen"

        self.is_stopped = False  # 核心状态控制


    def process_player_line(self, line:str):
        """Process /who list entries"""
        try:
            abcd=line[26:]
            if line[26:] ==  " Players on EverQuest:":
                if self.who_status == "unseen":        #仅在KLOG生成新战斗记录后处理第一次的/WHO结果
                    self.who_status = "started"
                    return True
                return False

            match = re.search(r" There are \d{1,3} players in (.+?)\.$", line[26:])
            if match:
                if self.who_status == "started":
                    self.who_status = "ended"
                    return True

                return False

            if self.who_status != "started":           #仅第一个/WHO产生的记录会被受理，其他时间段内产生的/WHO直接忽略
                return False

            if self.who_pattern.search(line):
                return True

        except Exception as e:
            QMessageBox.critical(self, f"Player entry error: {str(e)}")

        return False

    def process_tell_line(self, line):
        """Process player tell messages"""
        try:

            if re.search(self.tell_pattern,line, re.IGNORECASE):
                return True

        except Exception as e:
            QMessageBox.critical(self, f"Tell processing error: {str(e)}")

        return False



    def toggle_processing(self):

        try:
            if self.is_processing:
                self.paused = not self.paused
                self.start_btn.setText("Resume" if self.paused else "Pause")
                self.start_btn.setStyleSheet("color: orange" if self.paused else "color: green")
                if self. paused:
                    self.timer.stop()
                else:
                    self.timer.start(LOG_SENDNING_INTERVAL)
            else:
                self.lines = self.text_edit.toPlainText().split('\n')
                self.current_line = 0
                self.progress.setMaximum(len(self.lines))
                self.is_processing = True
                self.paused = False
                self.start_btn.setText("Pause")
                self.start_btn.setStyleSheet("color: orange")
                self.logTaker.initialize_filters("Nobody")
                self.logTaker.offline_process_start()


                self.timer.start(LOG_SENDNING_INTERVAL)

        except Exception as e:
            QMessageBox.critical(self, f"Send log error: {str(e)}")

    def process_next_line(self):
        if self.current_line < len(self.lines):
            line = self.lines[self.current_line]

            match = re.search(self.pop_tell_pattern,line, re.IGNORECASE)
            if match:
                tell_pattern = (
                    r'^\[(.*?)\]\s+'  # 时间戳
                    r'(\w+)\s+'  # 发送者
                    r'(?:'  # 匹配以下两种形式之一
                    r'->\s+{0}: '  # 形式1: -> [考勤员ID]
                    r'|'  # 或
                    r'tells\s+you,\s*\''  # 形式2: tells you
                    r')'  # 结束分组
                    r'(.*)'  # 消息内容
                ).format(match.group(1))  # 动态插入考勤员ID
                self.logTaker.update_tell_pattern_for_offline(tell_pattern)

            self.logTaker.offline_process(line)
            self.current_line += 1
            self.progress.setValue(self.current_line)
        else:
            self.stop_processing()

    def stop_processing(self):
        self.timer.stop()
        self.is_processing = False
        self.progress.reset()
        self.start_btn.setText("Send text to RA Log Taker")
        self.start_btn.setStyleSheet("color: green")
        self.logTaker.offline_process_stop()

    def show_main_window(self):
        self.stop_processing()
        self.logTaker.show()
        self.logTaker.raise_()
        width = self.logTaker.geometry().getRect()[2]
        height = self.logTaker.geometry().getRect()[3]
        self.logTaker.resize(width + 1, height)
        self.logTaker.resize(width, height)
        self.hide()
