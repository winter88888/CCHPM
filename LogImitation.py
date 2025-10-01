import os
import time
import threading
import datetime
import re
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import (QFileDialog, QMessageBox, QPushButton, QVBoxLayout,
                             QDialog, QLabel, QProgressBar, QHBoxLayout)


class LogImitationDialog(QDialog):
    def __init__(self, parent, eq_log_dir):
        super().__init__(parent)
        self.parent = parent
        self.eq_log_dir = eq_log_dir
        self.engage_log_path = ""
        self.is_running = False
        self.is_paused = False
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.thread = None

        self.setWindowTitle("Log Replay Tool")
        self.setModal(False)
        self.resize(500, 250)

        # Main layout
        main_layout = QVBoxLayout()

        # Info label
        self.info_label = QLabel("This function is to replay a fragment of EQ combat log. So you can test your UIs settings of log parsers, such as GINA,CCHPM,EQNag etc.First load an engage log file, then hit the Play button. Lines from the selected log file will be copied to eqlog_Kingdombot_P1999Green.txt line by line in a timely manner. You could setup other tools to point to this file ahead to test UI.")
        self.info_label.setWordWrap(True)  # 启用自动换行
        self.info_label.setFixedWidth(480)  # 固定宽度
        main_layout.addWidget(self.info_label)

        self.file_label = QLabel(f"Log Selected: ")
        self.file_label.setWordWrap(True)  # 启用自动换行
        self.file_label.setFixedWidth(480)  # 固定宽度
        main_layout.addWidget(self.file_label)

        # Progress bar (always visible)
        self.progress_bar = QProgressBar()
        self.progress_bar.setFormat("%p%")  # Show percentage in the middle
        main_layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("Status: Ready")
        main_layout.addWidget(self.status_label)

        # Button layout (horizontal)
        button_layout = QHBoxLayout()

        # Load button
        self.load_button = QPushButton("Load Log File...")
        self.load_button.clicked.connect(self.select_log_file)
        button_layout.addWidget(self.load_button)

        # Play/Pause button
        self.play_pause_button = QPushButton("Play")
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        self.play_pause_button.setEnabled(False)
        button_layout.addWidget(self.play_pause_button)

        # Stop button
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_imitation)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)

        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def select_log_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Engage Log File",
            "",
            "Text Files (*.txt);;All Files (*)"
        )

        if file_path:
            self.engage_log_path = file_path
            self.file_label.setText(f"Log Selected: {file_path}")
            self.play_pause_button.setEnabled(True)
            self.stop_button.setEnabled(True)

            # Preview file information
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    line_count = sum(1 for _ in f)
                self.status_label.setText(f"Status: Ready - {line_count} lines found")
                self.progress_bar.setValue(0)  # 重置进度条
            except:
                self.status_label.setText("Status: Ready - Unable to count lines")

    def toggle_play_pause(self):
        if not self.engage_log_path:
            QMessageBox.warning(self, "Warning", "Please select a log file first")
            return

        if not os.path.exists(self.eq_log_dir):
            QMessageBox.critical(self, "Error", f"EQ log directory does not exist: {self.eq_log_dir}")
            return

        if not self.is_running:
            # Start imitation
            self.start_imitation()
        else:
            # Toggle pause/resume
            if self.is_paused:
                self.resume_imitation()
            else:
                self.pause_imitation()

    def start_imitation(self):
        self.is_running = True
        self.is_paused = False
        self.stop_event.clear()
        self.pause_event.clear()
        self.play_pause_button.setText("Pause")
        self.status_label.setText("Status: Running...")
        self.load_button.setEnabled(False)
        self.progress_bar.setValue(0)  # 开始前重置进度条

        # Start imitation in a separate thread
        self.thread = threading.Thread(target=self.run_imitation)
        self.thread.daemon = True
        self.thread.start()

    def pause_imitation(self):
        self.is_paused = True
        self.pause_event.set()
        self.play_pause_button.setText("Play")
        self.status_label.setText("Status: Paused")

    def resume_imitation(self):
        self.is_paused = False
        self.pause_event.clear()
        self.play_pause_button.setText("Pause")
        self.status_label.setText("Status: Running...")

    def stop_imitation(self):
        self.stop_event.set()
        self.pause_event.set()  # Also clear any pause state
        self.is_running = False
        self.is_paused = False
        self.play_pause_button.setText("Play")
        self.play_pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.load_button.setEnabled(True)
        self.status_label.setText("Status: Stopped")
        self.progress_bar.setValue(0)  # 按下STOP后重置进度条

    def run_imitation(self):
        try:
            target_log_path = os.path.join(self.eq_log_dir, "eqlog_Kingdombot_P1999Green.txt")
            anchor_time = None
            processed_lines = 0
            total_lines = 0

            # First count total lines
            with open(self.engage_log_path, 'r', encoding='utf-8') as f:
                total_lines = sum(1 for _ in f)

            with open(self.engage_log_path, 'r', encoding='utf-8') as engage_file:
                lines = engage_file.readlines()

                for i, line in enumerate(lines):
                    if self.stop_event.is_set():
                        break

                    # Check for pause
                    if self.pause_event.is_set():
                        while self.pause_event.is_set() and not self.stop_event.is_set():
                            time.sleep(0.1)
                        if self.stop_event.is_set():
                            break

                    line = line.strip()
                    if not line:
                        continue

                    # Parse EQ log timestamp (format: [Tue Aug 12 09:14:43 2025])
                    try:
                        # Use regex to extract timestamp part
                        timestamp_match = re.match(r'^\[([A-Za-z]{3} [A-Za-z]{3} \d{2} \d{2}:\d{2}:\d{2} \d{4})\]',
                                                   line)
                        if not timestamp_match:
                            continue

                        timestamp_str = timestamp_match.group(1)
                        # Parse timestamp - EQ uses English month abbreviations
                        log_time = datetime.datetime.strptime(timestamp_str, "%a %b %d %H:%M:%S %Y")
                    except (ValueError, IndexError, AttributeError) as e:
                        # Skip invalid timestamp lines
                        continue

                    current_real_time = datetime.datetime.now()

                    if anchor_time is None:
                        # First valid timestamp - set anchor point
                        anchor_time = log_time
                        real_anchor_time = current_real_time
                        time_difference = 0
                    else:
                        # Calculate time difference relative to anchor
                        time_difference = (log_time - anchor_time).total_seconds()
                        real_target_time = real_anchor_time + datetime.timedelta(seconds=time_difference)

                        # Calculate wait time
                        wait_time = (real_target_time - current_real_time).total_seconds()

                        if wait_time > 0:
                            # Wait until it's time to process this line
                            # Check for stop or pause during wait
                            wait_interval = 0.1  # Check every 100ms
                            while wait_time > 0 and not self.stop_event.is_set() and not self.pause_event.is_set():
                                if wait_time > wait_interval:
                                    time.sleep(wait_interval)
                                    wait_time -= wait_interval
                                else:
                                    time.sleep(wait_time)
                                    wait_time = 0

                            # If paused during wait, handle it
                            if self.pause_event.is_set():
                                while self.pause_event.is_set() and not self.stop_event.is_set():
                                    time.sleep(0.1)
                                if self.stop_event.is_set():
                                    break
                                # Recalculate wait time after pause
                                current_real_time = datetime.datetime.now()
                                wait_time = (real_target_time - current_real_time).total_seconds()
                                if wait_time > 0:
                                    time.sleep(wait_time)

                    # Write to target log file
                    with open(target_log_path, 'a', encoding='utf-8') as target_file:
                        target_file.write(line + '\n')
                        target_file.flush()

                    processed_lines += 1

                    # Update progress
                    progress = int((i + 1) / total_lines * 100)
                    QtCore.QMetaObject.invokeMethod(self, "update_progress",
                                                    QtCore.Qt.QueuedConnection,
                                                    QtCore.Q_ARG(int, progress),
                                                    QtCore.Q_ARG(str, f"Processing: {timestamp_str}"))

            # Imitation completed
            if not self.stop_event.is_set():
                QtCore.QMetaObject.invokeMethod(self, "imitation_completed",
                                                QtCore.Qt.QueuedConnection)

        except Exception as e:
            QtCore.QMetaObject.invokeMethod(self, "imitation_error",
                                            QtCore.Qt.QueuedConnection,
                                            QtCore.Q_ARG(str, str(e)))

    @QtCore.pyqtSlot(int, str)
    def update_progress(self, progress, status):
        self.progress_bar.setValue(progress)
        self.status_label.setText(f"Status: {status} - {progress}%")

    @QtCore.pyqtSlot()
    def imitation_completed(self):
        self.is_running = False
        self.is_paused = False
        self.play_pause_button.setText("Play")
        self.play_pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.load_button.setEnabled(True)
        self.status_label.setText("Status: Completed")
        QMessageBox.information(self, "Completed", "Log imitation completed successfully")

    @QtCore.pyqtSlot(str)
    def imitation_error(self, error_msg):
        self.is_running = False
        self.is_paused = False
        self.play_pause_button.setText("Play")
        self.play_pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.load_button.setEnabled(True)
        self.status_label.setText("Status: Error")
        self.progress_bar.setValue(0)  # 出错时也重置进度条
        QMessageBox.critical(self, "Error", f"Imitation failed: {error_msg}")

    def closeEvent(self, event):
        if self.is_running:
            self.stop_imitation()
            # Wait for thread to stop
            if self.thread and self.thread.is_alive():
                self.thread.join(1.0)
        event.accept()