import os
import shutil
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QRadioButton, QComboBox, QLineEdit, QLabel,
                             QProgressBar, QPushButton, QMessageBox, QButtonGroup)
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import Qt


class CenteredProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextVisible(False)  # 隐藏默认的百分比显示

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setPen(Qt.black)
        painter.drawText(self.rect(), Qt.AlignCenter, f"{self.value()}%")


class CopyUIThread(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    # Fixed class translation to match bot_gina_proxy.ini abbreviations
    class_translation = {
        "Magician": "mag",
        "Wizard": "wiz",
        "Necromancer": "nec",
        "Enchanter": "enc",
        "Cleric": "clr",
        "Druid": "dru",
        "Shaman": "shm",
        "Rogue": "rog",
        "Warrior": "war",
        "Paladin": "pal",
        "Ranger": "rng",
        "Monk": "mnk",
        "Bard": "brd"
    }

    def __init__(self, eq_dir, from_char, to_target, is_class_based, class_name, to_server):
        super().__init__()
        self.eq_dir = eq_dir
        self.from_char = from_char
        self.to_target = to_target
        self.is_class_based = is_class_based
        # Use the class_translation dictionary to get the abbreviation
        if is_class_based and class_name:
            self.class_name = self.class_translation.get(class_name, class_name.lower())
        else:
            self.class_name = ""
        self.to_server = to_server
        self.bot_list = self.load_bot_list()

    def load_bot_list(self):
        bot_list = {}
        if os.path.exists('bot_gina_proxy.ini'):
            with open('bot_gina_proxy.ini', 'r') as f:
                for line in f:
                    parts = line.strip().split(',')
                    if len(parts) >= 2:
                        name, cls = parts[0], parts[1]
                        bot_list[name] = cls
            return bot_list
        else:
            return None

    def run(self):
        try:
            # Extract character name and server from from_char (format: "CharName-Server")
            if '-' in self.from_char:
                from_char_name, from_server = self.from_char.split('-', 1)
            else:
                from_char_name = self.from_char
                from_server = "P1999Green"  # Default if no server specified

            # Validate source character
            source_ui = f"UI_{from_char_name}_{from_server}.ini"
            source_settings = f"{from_char_name}_{from_server}.ini"
            source_ui_path = os.path.join(self.eq_dir, source_ui)
            source_settings_path = os.path.join(self.eq_dir, source_settings)

            if not os.path.exists(source_ui_path) or not os.path.exists(source_settings_path):
                self.finished.emit(False, f"Source files for {self.from_char} not found!")
                return

            # Get target characters
            if self.is_class_based:
                # Handle "All Class" selection
                if self.class_name.lower() == "all class":
                    target_chars = list(self.bot_list.keys())
                else:
                    target_chars = [name for name, cls in self.bot_list.items()
                                    if cls.lower() == self.class_name.lower()]
                if not target_chars:
                    self.finished.emit(False, f"No bots found for class {self.class_name}!")
                    return
            else:
                target_chars = [self.to_target]

            total = len(target_chars)
            success_count = 0

            for i, char in enumerate(target_chars):
                self.status.emit(f"Copying to {char}...")

                # Target file paths with selected server
                target_ui = f"UI_{char}_{self.to_server}.ini"
                target_settings = f"{char}_{self.to_server}.ini"
                target_ui_path = os.path.join(self.eq_dir, target_ui)
                target_settings_path = os.path.join(self.eq_dir, target_settings)

                try:
                    # Copy UI file
                    shutil.copy2(source_ui_path, target_ui_path)
                    # Copy settings file
                    shutil.copy2(source_settings_path, target_settings_path)
                    success_count += 1
                except Exception as e:
                    self.status.emit(f"Error copying to {char}: {str(e)}")

                progress_value = int((i + 1) / total * 100)
                self.progress.emit(progress_value)

            self.finished.emit(True, f"Successfully copied UI to {success_count}/{total} characters!")

        except Exception as e:
            self.finished.emit(False, f"Error during copy process: {str(e)}")


class CopyUIDialog(QDialog):
    def __init__(self, parent, eq_dir):
        super().__init__(parent)
        self.eq_dir = eq_dir
        self.setWindowTitle("Copy EQ UI Configuration")
        self.setModal(True)
        self.setFixedSize(500, 450)  # Increased height to accommodate server selection

        self.setup_ui()
        self.load_character_list()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Description
        desc = QLabel("This function allows you to copy EQ UI settings from one character to others. "
                      "You can copy to specific character or all bots of a certain class.")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Progress bar - always visible
        self.progress_bar = CenteredProgressBar()
        self.progress_bar.setValue(0)  # Initialize with 0%
        layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("Ready to copy UI settings.")
        layout.addWidget(self.status_label)

        # FROM section
        from_group = QGroupBox("Copy FROM:")
        from_layout = QVBoxLayout()

        self.from_radio_list = QRadioButton("Select a character from list:")
        self.from_radio_list.setChecked(True)
        self.from_combo = QComboBox()

        self.from_radio_manual = QRadioButton("Enter character name (format: CharName-Server):")
        self.from_manual_edit = QLineEdit()
        self.from_manual_edit.setEnabled(False)
        self.from_manual_edit.setPlaceholderText("e.g., Aabudzenki-P1999Green")

        from_layout.addWidget(self.from_radio_list)
        from_layout.addWidget(self.from_combo)
        from_layout.addWidget(self.from_radio_manual)
        from_layout.addWidget(self.from_manual_edit)
        from_group.setLayout(from_layout)
        layout.addWidget(from_group)

        # TO section
        to_group = QGroupBox("Copy TO:")
        to_layout = QVBoxLayout()

        # Server selection for target
        server_layout = QHBoxLayout()
        server_label = QLabel("Target Server:")
        self.server_combo = QComboBox()
        server_layout.addWidget(server_label)
        server_layout.addWidget(self.server_combo)
        server_layout.addStretch()
        to_layout.addLayout(server_layout)

        self.to_radio_class = QRadioButton("All bots of class:")
        self.to_radio_class.setChecked(True)
        self.class_combo = QComboBox()
        self.class_combo.addItems(["Magician", "Wizard", "Necromancer", "Enchanter", "Cleric", "Druid",
                                   "Shaman", "Rogue", "Warrior", "Paladin", "Ranger", "Monk", "Bard", "All Class"])

        self.to_radio_manual = QRadioButton("Specific character:")
        self.to_manual_edit = QLineEdit()
        self.to_manual_edit.setEnabled(False)

        to_layout.addWidget(self.to_radio_class)
        to_layout.addWidget(self.class_combo)
        to_layout.addWidget(self.to_radio_manual)
        to_layout.addWidget(self.to_manual_edit)
        to_group.setLayout(to_layout)
        layout.addWidget(to_group)

        # Button group for radio buttons
        self.from_group = QButtonGroup()
        self.from_group.addButton(self.from_radio_list)
        self.from_group.addButton(self.from_radio_manual)

        self.to_group = QButtonGroup()
        self.to_group.addButton(self.to_radio_class)
        self.to_group.addButton(self.to_radio_manual)

        # Connect signals
        self.from_radio_list.toggled.connect(self.from_combo.setEnabled)
        self.from_radio_manual.toggled.connect(self.from_manual_edit.setEnabled)
        self.to_radio_class.toggled.connect(self.class_combo.setEnabled)
        self.to_radio_manual.toggled.connect(self.to_manual_edit.setEnabled)

        # Buttons
        button_layout = QHBoxLayout()
        self.copy_btn = QPushButton("Copy UI")
        self.copy_btn.clicked.connect(self.start_copy)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(self.copy_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_character_list(self):
        """Load character list from EQ directory with server names"""
        characters = set()
        servers = set()

        if os.path.exists(self.eq_dir):
            for filename in os.listdir(self.eq_dir):
                if filename.startswith("UI_") and filename.endswith(".ini"):
                    # Extract character name and server from "UI_CharName_Server.ini"
                    parts = filename.split('_')
                    if len(parts) >= 3:
                        char_name = parts[1]
                        server_name = parts[2].replace('.ini', '')
                        characters.add(f"{char_name}-{server_name}")
                        servers.add(server_name)

        # Populate FROM combo
        self.from_combo.clear()
        for char in sorted(characters):
            self.from_combo.addItem(char)

        # Populate server combo
        self.server_combo.clear()
        for server in sorted(servers):
            self.server_combo.addItem(server)

        # Set default server if available
        if "P1999Green" in servers:
            self.server_combo.setCurrentText("P1999Green")
        elif servers:
            self.server_combo.setCurrentIndex(0)

    def get_from_char(self):
        if self.from_radio_list.isChecked():
            return self.from_combo.currentText()
        else:
            return self.from_manual_edit.text().strip()

    def get_to_target(self):
        if self.to_radio_class.isChecked():
            return self.class_combo.currentText(), True
        else:
            return self.to_manual_edit.text().strip(), False

    def start_copy(self):
        from_char = self.get_from_char()
        to_target, is_class_based = self.get_to_target()
        to_server = self.server_combo.currentText()

        if not from_char:
            QMessageBox.warning(self, "Error", "Please select or enter a source character!")
            return

        if not to_target:
            QMessageBox.warning(self, "Error", "Please select or enter a target!")
            return

        if not to_server:
            QMessageBox.warning(self, "Error", "Please select a target server!")
            return

        # Disable UI during copy
        self.set_ui_enabled(False)
        self.status_label.setText("Starting copy process...")

        # Create and start copy thread
        self.copy_thread = CopyUIThread(
            self.eq_dir, from_char, to_target, is_class_based,
            to_target if is_class_based else None, to_server
        )
        self.copy_thread.progress.connect(self.progress_bar.setValue)
        self.copy_thread.status.connect(self.status_label.setText)
        self.copy_thread.finished.connect(self.copy_finished)
        self.copy_thread.start()

    def set_ui_enabled(self, enabled):
        self.from_combo.setEnabled(enabled and self.from_radio_list.isChecked())
        self.from_manual_edit.setEnabled(enabled and self.from_radio_manual.isChecked())
        self.class_combo.setEnabled(enabled and self.to_radio_class.isChecked())
        self.to_manual_edit.setEnabled(enabled and self.to_radio_manual.isChecked())
        self.server_combo.setEnabled(enabled)
        self.copy_btn.setEnabled(enabled)
        self.cancel_btn.setEnabled(enabled)

    def copy_finished(self, success, message):
        self.set_ui_enabled(True)

        if success:
            self.status_label.setText("Copy completed successfully!")
            QMessageBox.information(self, "Success", message)
        else:
            self.status_label.setText("Copy failed!")
            QMessageBox.critical(self, "Error", message)