import os
import zipfile
import shutil
import datetime
from PyQt5 import QtCore
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QProgressBar,
                             QLabel, QPushButton, QFileDialog, QMessageBox,
                             QListWidget, QCheckBox, QGroupBox, QFrame, QMenu, QInputDialog,
                             QApplication)
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QMimeData

if os.name == 'nt':
    import win32clipboard
    import win32con
    import struct


class BackupRestoreDialog(QDialog):
    def __init__(self, parent=None, eq_log_dir=None):
        super().__init__(parent)
        self.parent = parent
        self.eq_log_dir = eq_log_dir
        self.eq_ini_dir = os.path.dirname(eq_log_dir) if eq_log_dir else ""
        self.backup_dir = os.path.join(os.getcwd(), "eq backup")
        self.temp_dir = os.path.join(self.backup_dir, "temp")

        self.setup_ui()
        self.refresh_backup_list()

    def setup_ui(self):
        self.setWindowTitle("EQ Configuration Backup & Restore")
        self.setFixedSize(500, 400)

        layout = QVBoxLayout()

        # Description
        desc_label = QLabel("This function is to help backup your EQ configurations or restore them.")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        # Create a frame with light gray border for progress section
        progress_frame = QFrame()
        progress_frame.setFrameStyle(QFrame.Box | QFrame.Plain)
        progress_frame.setLineWidth(1)
        # 设置浅灰色边框
        progress_frame.setStyleSheet("QFrame { border: 1px solid #CCCCCC; }")
        progress_layout = QVBoxLayout(progress_frame)

        # Progress bar (always visible) with centered text
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        # 设置进度条文本居中
        self.progress_bar.setAlignment(QtCore.Qt.AlignCenter)
        # 设置样式表，让文本在进度条中间显示
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid grey;
                border-radius: 2px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #05B8CC;
                width: 1px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("Ready")
        progress_layout.addWidget(self.status_label)

        layout.addWidget(progress_frame)

        # Backup button
        self.backup_btn = QPushButton("Backup now...")
        self.backup_btn.clicked.connect(self.start_backup)
        layout.addWidget(self.backup_btn)

        # Restore section
        restore_group = QGroupBox("Restore from Backup")
        restore_layout = QVBoxLayout()

        # Backup list
        self.backup_list = QListWidget()
        self.backup_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.backup_list.customContextMenuRequested.connect(self.show_context_menu)
        restore_layout.addWidget(QLabel("Available backups:"))
        restore_layout.addWidget(self.backup_list)

        # Restore options
        options_layout = QHBoxLayout()
        self.restore_eq_cb = QCheckBox("EQ INI Files")
        self.restore_eq_cb.setChecked(True)
        self.restore_gina_cb = QCheckBox("GINA Config")
        self.restore_gina_cb.setChecked(True)
        options_layout.addWidget(self.restore_eq_cb)
        options_layout.addWidget(self.restore_gina_cb)
        restore_layout.addLayout(options_layout)

        # Restore button
        self.restore_btn = QPushButton("Restore Selected")
        self.restore_btn.clicked.connect(self.start_restore)
        restore_layout.addWidget(self.restore_btn)

        restore_group.setLayout(restore_layout)
        layout.addWidget(restore_group)

        self.setLayout(layout)

    def show_context_menu(self, position):
        """显示右键上下文菜单"""
        item = self.backup_list.itemAt(position)
        if not item:
            return

        menu = QMenu()

        open_action = menu.addAction("Open")
        delete_action = menu.addAction("Delete")
        rename_action = menu.addAction("Rename")
        copy_to_clipboard_action = menu.addAction("Copy")
        copy_action = menu.addAction("Save as")
        menu.addSeparator()
        show_in_explorer_action = menu.addAction("Show in Explorer")

        action = menu.exec_(self.backup_list.mapToGlobal(position))

        if action == open_action:
            self.open_backup_file(item)
        elif action == delete_action:
            self.delete_backup_file(item)
        elif action == rename_action:
            self.rename_backup_file(item)
        elif action == copy_action:
            self.copy_backup_file(item)
        elif action == copy_to_clipboard_action:
            self.copy_to_clipboard(item)
        elif action == show_in_explorer_action:
            self.show_in_explorer(item)

    def copy_to_clipboard(self, item):
        """将备份文件复制到剪贴板，兼容Windows资源管理器"""
        backup_file = item.text()
        backup_path = os.path.join(self.backup_dir, backup_file)

        if not os.path.exists(backup_path):
            QMessageBox.warning(self, "Error", f"File not found: {backup_file}")
            return

        try:
            if os.name == 'nt':  # Windows系统
                self._copy_file_to_clipboard_windows(backup_path)
            else:  # 其他系统使用Qt的剪贴板功能
                self._copy_file_to_clipboard_qt(backup_path)

            QMessageBox.information(self, "Success", f"'{backup_file}' copied to clipboard")

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to copy to clipboard: {str(e)}")

    def _copy_file_to_clipboard_windows(self, file_path):
        """Windows系统专用的文件复制到剪贴板方法 - 修复版本"""
        file_path = os.path.abspath(file_path)

        # 确保文件存在
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            # 使用Qt的剪贴板功能，这在Windows上通常更可靠
            clipboard = QApplication.clipboard()
            mime_data = QMimeData()

            # 创建文件URL
            file_url = QtCore.QUrl.fromLocalFile(file_path)

            # 设置MIME数据
            mime_data.setUrls([file_url])
            mime_data.setText(file_path)

            # 设置到剪贴板
            clipboard.setMimeData(mime_data)

        except Exception as e:
            # 如果Qt方法失败，回退到Windows API方法
            try:
                self._copy_file_to_clipboard_windows_api(file_path)
            except Exception as api_error:
                raise Exception(f"Both Qt and Windows API methods failed: {str(api_error)}")

    def _copy_file_to_clipboard_windows_api(self, file_path):
        """使用Windows API的备选方法"""
        file_path = os.path.abspath(file_path).replace('/', '\\')

        # 准备DROPFILES结构
        # DROPFILES结构: pFiles(4), pt(8), fNC(4), fWide(4)
        dropfiles = struct.pack('IIII', 20, 0, 0, 1)  # 最后一个参数为1表示使用Unicode

        # Unicode字符串，以双空字符结束
        files = file_path + '\0\0'
        files_unicode = files.encode('utf-16le')

        # 组合数据
        data = dropfiles + files_unicode

        # 打开剪贴板
        win32clipboard.OpenClipboard()
        try:
            # 清空剪贴板
            win32clipboard.EmptyClipboard()

            # 设置CF_HDROP格式
            win32clipboard.SetClipboardData(win32con.CF_HDROP, data)

        finally:
            # 关闭剪贴板
            win32clipboard.CloseClipboard()

    def _copy_file_to_clipboard_qt(self, file_path):
        """Qt通用的文件复制到剪贴板方法"""
        clipboard = QApplication.clipboard()
        mime_data = QMimeData()

        # 创建文件URL
        file_url = QtCore.QUrl.fromLocalFile(file_path)

        # 设置MIME数据
        mime_data.setUrls([file_url])
        mime_data.setText(file_path)

        # 设置到剪贴板
        clipboard.setMimeData(mime_data)

    def open_backup_file(self, item):
        """打开备份文件（使用系统默认程序）"""
        backup_file = item.text()
        backup_path = os.path.join(self.backup_dir, backup_file)

        if os.path.exists(backup_path):
            try:
                os.startfile(backup_path)  # Windows
            except:
                # 对于其他操作系统或Windows失败的情况
                try:
                    import subprocess
                    if os.name == 'nt':  # Windows
                        os.startfile(backup_path)
                    elif os.name == 'posix':  # macOS, Linux
                        if os.uname().sysname == 'Darwin':  # macOS
                            subprocess.call(('open', backup_path))
                        else:  # Linux
                            subprocess.call(('xdg-open', backup_path))
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Cannot open file: {str(e)}")

    def delete_backup_file(self, item):
        """删除备份文件"""
        backup_file = item.text()
        backup_path = os.path.join(self.backup_dir, backup_file)

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete '{backup_file}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                os.remove(backup_path)
                self.refresh_backup_list()
                QMessageBox.information(self, "Success", f"Deleted: {backup_file}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to delete: {str(e)}")

    def rename_backup_file(self, item):
        """重命名备份文件"""
        backup_file = item.text()
        backup_path = os.path.join(self.backup_dir, backup_file)

        new_name, ok = QInputDialog.getText(
            self,
            "Rename Backup",
            "Enter new name:",
            text=backup_file
        )

        if ok and new_name:
            if not new_name.endswith('.zip'):
                new_name += '.zip'

            new_path = os.path.join(self.backup_dir, new_name)

            if os.path.exists(new_path):
                QMessageBox.warning(self, "Error", "A file with that name already exists.")
                return

            try:
                os.rename(backup_path, new_path)
                self.refresh_backup_list()
                QMessageBox.information(self, "Success", f"Renamed to: {new_name}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to rename: {str(e)}")

    def copy_backup_file(self, item):
        """复制备份文件"""
        backup_file = item.text()
        backup_path = os.path.join(self.backup_dir, backup_file)

        # 获取目标路径
        target_path, _ = QFileDialog.getSaveFileName(
            self,
            "Copy Backup File",
            backup_file,
            "ZIP Files (*.zip)"
        )

        if target_path:
            try:
                shutil.copy2(backup_path, target_path)
                QMessageBox.information(self, "Success", f"File copied to: {target_path}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to copy: {str(e)}")

    def show_in_explorer(self, item):
        """在文件资源管理器中显示文件"""
        backup_file = item.text()
        backup_path = os.path.join(self.backup_dir, backup_file)

        if os.path.exists(backup_path):
            try:
                # Windows
                os.startfile(os.path.dirname(backup_path))
            except:
                try:
                    import subprocess
                    if os.name == 'nt':  # Windows
                        subprocess.Popen(f'explorer /select,"{backup_path}"')
                    elif os.name == 'posix':  # macOS, Linux
                        if os.uname().sysname == 'Darwin':  # macOS
                            subprocess.Popen(['open', '-R', backup_path])
                        else:  # Linux
                            subprocess.Popen(['xdg-open', os.path.dirname(backup_path)])
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Cannot show in explorer: {str(e)}")

    def refresh_backup_list(self):
        """Refresh the list of available backups"""
        self.backup_list.clear()
        if not os.path.exists(self.backup_dir):
            return

        for item in os.listdir(self.backup_dir):
            if item.endswith(".zip"):
                self.backup_list.addItem(item)

    def start_backup(self):
        """Start backup process"""
        self.backup_worker = BackupWorker(self.eq_ini_dir, self.backup_dir, self.temp_dir)
        self.backup_worker.progress_signal.connect(self.update_progress)
        self.backup_worker.finished_signal.connect(self.backup_finished)
        self.backup_worker.start()

        self.backup_btn.setEnabled(False)
        self.restore_btn.setEnabled(False)

    def start_restore(self):
        """Start restore process"""
        selected_items = self.backup_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select a backup to restore")
            return

        if not self.restore_eq_cb.isChecked() and not self.restore_gina_cb.isChecked():
            QMessageBox.warning(self, "Warning", "Please select at least one option to restore")
            return

        backup_file = selected_items[0].text()
        backup_path = os.path.join(self.backup_dir, backup_file)

        self.restore_worker = RestoreWorker(
            backup_path,
            self.eq_ini_dir,
            self.restore_eq_cb.isChecked(),
            self.restore_gina_cb.isChecked()
        )
        self.restore_worker.progress_signal.connect(self.update_progress)
        self.restore_worker.finished_signal.connect(self.restore_finished)
        self.restore_worker.start()

        self.backup_btn.setEnabled(False)
        self.restore_btn.setEnabled(False)

    def update_progress(self, value, message):
        """Update progress bar and status"""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)

    def backup_finished(self, success, message):
        """Handle backup completion"""
        self.backup_btn.setEnabled(True)
        self.restore_btn.setEnabled(True)
        self.refresh_backup_list()

        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.warning(self, "Error", message)

    def restore_finished(self, success, message):
        """Handle restore completion"""
        self.backup_btn.setEnabled(True)
        self.restore_btn.setEnabled(True)

        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.warning(self, "Error", message)


class BackupWorker(QThread):
    progress_signal = pyqtSignal(int, str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, eq_ini_dir, backup_dir, temp_dir):
        super().__init__()
        self.eq_ini_dir = eq_ini_dir
        self.backup_dir = backup_dir
        self.temp_dir = temp_dir

    def run(self):
        try:
            # Create backup directory if it doesn't exist
            if not os.path.exists(self.backup_dir):
                os.makedirs(self.backup_dir)

            # Create temp directory
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
            os.makedirs(self.temp_dir)

            self.progress_signal.emit(10, "Starting backup...")

            # Backup EQ INI files
            eq_backup_path = os.path.join(self.temp_dir, "EQ")
            os.makedirs(eq_backup_path)

            if os.path.exists(self.eq_ini_dir):
                for file in os.listdir(self.eq_ini_dir):
                    if file.endswith(".ini"):
                        src = os.path.join(self.eq_ini_dir, file)
                        dst = os.path.join(eq_backup_path, file)
                        shutil.copy2(src, dst)

            self.progress_signal.emit(40, "EQ INI files backed up")

            # Backup GINA config
            gina_backup_path = os.path.join(self.temp_dir, "GINA")
            os.makedirs(gina_backup_path)

            gina_src = os.path.join(os.environ['USERPROFILE'], "AppData", "Local", "GimaSoft", "GINA")
            if os.path.exists(gina_src):
                for file in os.listdir(gina_src):
                    src = os.path.join(gina_src, file)
                    dst = os.path.join(gina_backup_path, file)
                    if os.path.isfile(src):
                        shutil.copy2(src, dst)

            self.progress_signal.emit(70, "GINA config backed up")

            # Create zip file
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            zip_filename = f"backup{timestamp}.zip"
            zip_path = os.path.join(self.backup_dir, zip_filename)

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(self.temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, self.temp_dir)
                        zipf.write(file_path, arcname)

            self.progress_signal.emit(90, "Creating compressed backup...")

            # Clean up temp directory
            shutil.rmtree(self.temp_dir)

            self.progress_signal.emit(100, "Backup completed successfully")
            self.finished_signal.emit(True, f"Backup completed: {zip_filename}")

        except Exception as e:
            self.finished_signal.emit(False, f"Backup failed: {str(e)}")


class RestoreWorker(QThread):
    progress_signal = pyqtSignal(int, str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, backup_path, eq_ini_dir, restore_eq, restore_gina):
        super().__init__()
        self.backup_path = backup_path
        self.eq_ini_dir = eq_ini_dir
        self.restore_eq = restore_eq
        self.restore_gina = restore_gina
        self.temp_dir = os.path.join(os.path.dirname(backup_path), "temp_restore")

    def run(self):
        try:
            # Create temp directory
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
            os.makedirs(self.temp_dir)

            self.progress_signal.emit(10, "Extracting backup...")

            # Extract backup
            with zipfile.ZipFile(self.backup_path, 'r') as zipf:
                zipf.extractall(self.temp_dir)

            self.progress_signal.emit(40, "Backup extracted")

            # Restore files
            if self.restore_eq:
                eq_src = os.path.join(self.temp_dir, "EQ")
                if os.path.exists(eq_src):
                    for file in os.listdir(eq_src):
                        src = os.path.join(eq_src, file)
                        dst = os.path.join(self.eq_ini_dir, file)
                        shutil.copy2(src, dst)

            self.progress_signal.emit(60, "EQ INI files restored")

            if self.restore_gina:
                gina_src = os.path.join(self.temp_dir, "GINA")
                gina_dst = os.path.join(os.environ['USERPROFILE'], "AppData", "Local", "GimaSoft", "GINA")

                if os.path.exists(gina_src):
                    if not os.path.exists(gina_dst):
                        os.makedirs(gina_dst)

                    for file in os.listdir(gina_src):
                        src = os.path.join(gina_src, file)
                        dst = os.path.join(gina_dst, file)
                        shutil.copy2(src, dst)

            self.progress_signal.emit(90, "GINA config restored")

            # Clean up
            shutil.rmtree(self.temp_dir)

            self.progress_signal.emit(100, "Restore completed successfully")
            self.finished_signal.emit(True, "Restore completed successfully")

        except Exception as e:
            self.finished_signal.emit(False, f"Restore failed: {str(e)}")