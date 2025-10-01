import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QFileDialog, QMessageBox, QSpinBox, QProgressBar)
from PyQt5.QtCore import Qt


class FileSplitterApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('文本文件分割工具')
        self.setGeometry(300, 300, 500, 250)

        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 布局
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # 文件选择部分
        file_layout = QHBoxLayout()
        self.file_label = QLabel('选择文件:')
        self.file_path = QLineEdit()
        self.file_path.setReadOnly(True)
        self.browse_btn = QPushButton('浏览...')
        self.browse_btn.clicked.connect(self.browse_file)

        file_layout.addWidget(self.file_label)
        file_layout.addWidget(self.file_path)
        file_layout.addWidget(self.browse_btn)

        # 文件大小设置部分
        size_layout = QHBoxLayout()
        self.size_label = QLabel('每个分割文件大小 (KB):')
        self.size_spin = QSpinBox()
        self.size_spin.setRange(1, 102400)  # 1KB 到 100MB
        self.size_spin.setValue(1024)  # 默认1MB

        size_layout.addWidget(self.size_label)
        size_layout.addWidget(self.size_spin)
        size_layout.addStretch()

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)

        # 按钮部分
        btn_layout = QHBoxLayout()
        self.split_btn = QPushButton('开始分割')
        self.split_btn.clicked.connect(self.split_file)
        self.split_btn.setEnabled(False)

        self.cancel_btn = QPushButton('取消')
        self.cancel_btn.clicked.connect(self.close)

        btn_layout.addWidget(self.split_btn)
        btn_layout.addWidget(self.cancel_btn)

        # 添加到主布局
        layout.addLayout(file_layout)
        layout.addLayout(size_layout)
        layout.addWidget(self.progress_bar)
        layout.addLayout(btn_layout)
        layout.addStretch()

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, '选择要分割的文本文件', '', '文本文件 (*.txt);;所有文件 (*)')

        if file_path:
            self.file_path.setText(file_path)
            self.split_btn.setEnabled(True)

    def split_file(self):
        input_file = self.file_path.text()
        if not os.path.isfile(input_file):
            QMessageBox.warning(self, '错误', '请选择有效的文件!')
            return

        chunk_size = self.size_spin.value() * 1024  # 转换为字节

        # 获取输出目录
        output_dir = QFileDialog.getExistingDirectory(
            self, '选择保存分割文件的目录')

        if not output_dir:
            return

        try:
            self.progress_bar.setVisible(True)
            self.split_btn.setEnabled(False)
            self.browse_btn.setEnabled(False)

            # 读取并分割文件
            with open(input_file, 'r', encoding='utf-8') as f:
                file_count = 1
                base_name = os.path.splitext(os.path.basename(input_file))[0]

                # 获取文件总大小以设置进度条
                total_size = os.path.getsize(input_file)
                self.progress_bar.setMaximum(total_size)
                processed_size = 0

                while True:
                    # 读取指定大小的内容
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break

                    # 写入新文件
                    output_file = os.path.join(
                        output_dir, f"{base_name}_part{file_count}.txt")

                    with open(output_file, 'w', encoding='utf-8') as out_f:
                        out_f.write(chunk)

                    file_count += 1
                    processed_size += len(chunk.encode('utf-8'))
                    self.progress_bar.setValue(processed_size)
                    QApplication.processEvents()  # 更新UI

            QMessageBox.information(
                self, '完成', f'文件已成功分割为 {file_count - 1} 个部分!')

        except Exception as e:
            QMessageBox.critical(self, '错误', f'分割文件时出错: {str(e)}')

        finally:
            self.progress_bar.setVisible(False)
            self.split_btn.setEnabled(True)
            self.browse_btn.setEnabled(True)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FileSplitterApp()
    window.show()
    sys.exit(app.exec_())