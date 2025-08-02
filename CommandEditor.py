import copy
import os

from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QTableWidget, QTableWidgetItem, QCheckBox, QPushButton,
                             QComboBox, QHeaderView, QMessageBox, QDialog, QLabel, QLineEdit, QDialogButtonBox)
from PyQt5.QtCore import Qt, pyqtSignal

class Command:
    def __init__(self, enabled=False, source="yourself", channel="guild chat",
                 command_str="", relay_command=True, relay_msg=True):
        self.command_enabled = enabled
        self.command_source = source  # "yourself", "others" or "anyone"
        self.command_channel = channel  # "guild chat", "ooc", "shout", "auction" or "all"
        self.command_str = command_str
        self.command_relay_command = relay_command  # Copy command to end
        self.command_relay_msg = relay_msg  # Copy full line

    def get_sort_key(self, column):
        """根据列索引返回排序键值"""
        if column == 0:  # Enabled
            return self.command_enabled
        elif column == 1:  # Command
            return self.command_str.lower()
        elif column == 2:  # Source
            return self.command_source.lower()
        elif column == 3:  # Channel
            return self.command_channel.lower()
        elif column == 4:  # Copy Command
            return self.command_relay_command
        elif column == 5:  # Copy Full Line
            return self.command_relay_msg
        return None

    def to_dict(self):
        return {
            "enabled": self.command_enabled,
            "source": self.command_source,
            "channel": self.command_channel,
            "command": self.command_str,
            "relay_command": self.command_relay_command,
            "relay_msg": self.command_relay_msg
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            enabled=data.get("enabled", False),
            source=data.get("source", "yourself"),
            channel=data.get("channel", "guild chat"),  # Default to "guild chat"
            command_str=data.get("command", ""),
            relay_command=data.get("relay_command", True),
            relay_msg=data.get("relay_msg", True)
        )

class CommandEditor(QWidget):
    data_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.commands = []
        self.history = []
        self.current_history_index = -1
        self.source_column_visible = False
        self.sort_column = 1
        self.sort_order = Qt.AscendingOrder

        self.window_geometry ={
            'width': 800,
            'height': 600,
            'x': 100,
            'y': 100
        }
        self.column_widths = [60, 200, 120, 120, 100, 100]


        self.load_commands_from_file()
        self.load_ui_settings()
        self.init_ui()
        self.load_commands()
        self.save_initial_state()


    def init_ui(self):
        self.setWindowTitle("In-Game Command Editor")

        # 设置初始大小和位置
        if self.window_geometry:
            self.resize(self.window_geometry['width'], self.window_geometry['height'])
            self.move(self.window_geometry['x'], self.window_geometry['y'])  # 设置窗口位置
        else:
            self.resize(800, 600)
            self.move(100, 100)  # 默认位置


        # 主布局
        main_layout = QVBoxLayout()

        # 顶部控制栏
        control_layout = QHBoxLayout()

        self.enable_all_checkbox = QCheckBox("Enable All")
        self.enable_all_checkbox.setTristate(True)
        self.enable_all_checkbox.stateChanged.connect(self.toggle_all_commands)

        # 排序控件
        control_layout.addWidget(self.enable_all_checkbox)
        control_layout.addStretch()

        # 命令表格
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["Enabled", "Command", "Source", "Channel", "Copy Command", "Copy Full Line"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.verticalHeader().setVisible(False)

        # 允许点击表头排序
        self.table.horizontalHeader().sectionClicked.connect(self.custom_header_clicked)

        # 设置列宽
        if self.column_widths and len(self.column_widths) == self.table.columnCount():
            for i, width in enumerate(self.column_widths):
                # 确保Source列至少有100宽度
                if i == 2 and width < 100:  # Source是第2列
                    width = 100
                self.table.setColumnWidth(i, width)
        else:
            # 修改默认列宽设置
            self.table.setColumnWidth(0, 60)  # Enabled
            self.table.setColumnWidth(1, 200)  # Command
            self.table.setColumnWidth(2, 120)  # Source
            self.table.setColumnWidth(3, 120)  # Channel
            self.table.setColumnWidth(4, 100)  # Copy Command
            self.table.setColumnWidth(5, 100)  # Copy Full Line

        # 居中显示内容
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)


        # Bottom buttons
        button_layout = QHBoxLayout()

        # Add button
        self.add_btn = QPushButton("Add")
        self.add_btn.clicked.connect(self.add_command)
        button_layout.addWidget(self.add_btn)

        # Delete button
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_command)
        button_layout.addWidget(self.delete_btn)

        # Undo button (moved here)
        self.undo_btn = QPushButton("Undo")
        self.undo_btn.clicked.connect(self.undo_action)
        button_layout.addWidget(self.undo_btn)

        button_layout.addStretch()

        # Cancel button
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.cancel_changes)
        button_layout.addWidget(self.cancel_btn)

        # Accept button
        self.accept_btn = QPushButton("Accept")
        self.accept_btn.clicked.connect(self.accept_changes)
        button_layout.addWidget(self.accept_btn)

        # 组装主布局
        main_layout.addLayout(control_layout)
        main_layout.addWidget(self.table)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)


    def save_initial_state(self):
        """Save the initial state when editor is opened"""
        self.history = [copy.deepcopy(self.commands)]
        self.current_history_index = 0
        self.update_undo_button()

    def custom_header_clicked(self, logical_index):
        """自定义表头点击排序处理"""
        if self.sort_column == logical_index:
            # 同一列点击，切换排序方向
            self.sort_order = Qt.DescendingOrder if self.sort_order == Qt.AscendingOrder else Qt.AscendingOrder
        else:
            # 不同列点击，重置为升序
            self.sort_column = logical_index
            self.sort_order = Qt.AscendingOrder

        # 执行排序并更新表格
        self.sort_commands()
        self.update_table()

        # 更新表头排序指示器
        self.update_header_sort_indicator()

    def update_header_sort_indicator(self):
        """更新表头排序指示器"""
        header = self.table.horizontalHeader()
        for i in range(header.count()):
            header.setSortIndicator(i, -1)  # 清除所有列指示器
        header.setSortIndicator(self.sort_column, self.sort_order)

    def sort_commands(self):
        """根据当前排序设置对命令进行排序"""
        if not self.commands:
            return

        # 使用带有多级比较的排序键
        def get_sort_key(cmd):
            primary = cmd.get_sort_key(self.sort_column)
            # 添加次要排序键确保稳定排序
            secondary = cmd.command_str.lower()  # 默认按command作为次要键
            return (primary, secondary)

        reverse = self.sort_order == Qt.DescendingOrder
        self.commands.sort(key=get_sort_key, reverse=reverse)

    # 添加新的方法来处理表格项变化
    def handle_item_changed(self, item):
        """处理表格项变化"""
        if item.column() == 1:  # 只有Command列需要处理
            row = item.row()
            if 0 <= row < len(self.commands):
                self.commands[row].command_str = item.text()
                self.save_state()

    def load_ui_settings(self):
        """Load UI settings from In-game cmd.ini [UI] section"""
        try:
            if os.path.exists('In-game cmd.ini'):
                with open('In-game cmd.ini', 'r') as f:
                    content = f.read()

                # Parse UI section
                ui_section = False
                ui_data = {}

                for line in content.split('\n'):
                    line = line.strip()
                    if line == "[UI]":
                        ui_section = True
                        continue
                    elif line.startswith("[") and line.endswith("]"):
                        ui_section = False
                        continue

                    if ui_section and '=' in line:
                        key, value = line.split('=', 1)
                        ui_data[key.strip()] = value.strip()

                # Apply settings if found
                if 'width' in ui_data and 'height' in ui_data:
                    self.window_geometry = {
                        'width': int(ui_data['width']),
                        'height': int(ui_data['height']),
                        'x': int(ui_data.get('x', 100)),  # 新增x坐标，默认100
                        'y': int(ui_data.get('y', 100))  # 新增y坐标，默认100
                    }

                if 'column_widths' in ui_data:
                    widths = ui_data['column_widths'].split(',')
                    # 确保Source列至少有100宽度
                    if len(widths) > 2 and widths[2] == '0':
                        widths[2] = '100'
                    self.column_widths = [int(w) for w in widths if w.isdigit()]

        except Exception as e:
            print(f"Error loading UI settings: {e}")


    def save_ui_settings(self):

        """Save UI settings to In-game cmd.ini [UI] section"""
        try:
            # Read existing content
            sections = {}
            current_section = None
            current_content = []

            if os.path.exists('In-game cmd.ini'):
                with open('In-game cmd.ini', 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("[") and line.endswith("]"):
                            if current_section:
                                sections[current_section] = current_content
                            current_section = line
                            current_content = []
                        else:
                            if line or (current_content and current_content[-1]):
                                current_content.append(line)

            # Add last section
            if current_section:
                sections[current_section] = current_content

            # Prepare UI settings
            ui_settings = []
            if self.window_geometry:
                ui_settings.append(f"width={self.window_geometry['width']}")
                ui_settings.append(f"height={self.window_geometry['height']}")
                ui_settings.append(f"x={self.window_geometry['x']}")  # 新增x坐标
                ui_settings.append(f"y={self.window_geometry['y']}")  # 新增y坐标

            column_widths = []
            for i in self.column_widths:
                column_widths.append(str(i))
            ui_settings.append(f"column_widths={','.join(column_widths)}")

            sections["[UI]"] = ui_settings

            # Write back to file
            with open('In-game cmd.ini', 'w') as f:
                # Write all sections except UI first
                for section, lines in sections.items():
                    if section != "[UI]":
                        f.write(f"{section}\n")
                        for line in lines:
                            f.write(f"{line}\n")
                        f.write("\n")

                # Write UI section last
                f.write("[UI]\n")
                for line in sections["[UI]"]:
                    f.write(f"{line}\n")
                f.write("\n")

        except Exception as e:
            print(f"Error saving UI settings: {e}")


    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()
        super().keyPressEvent(event)

    def closeEvent(self, event):

        event.ignore()
        self.hide()

    def hideEvent(self, event):
        """Override hide event to save window geometry"""
        try:
            self.window_geometry = {
                'width': self.width(),
                'height': self.height(),
                'x': self.x(),
                'y': self.y()
            }
            self.column_widths = [self.table.columnWidth(i) for i in range(self.table.columnCount())]


        except Exception as e:
            print(f"Error during close: {e}")
        finally:
            super().hideEvent(event)



    def set_source_column_visible(self, visible):
        """设置Source列的可见性"""
        self.source_column_visible = visible
        self.table.setColumnHidden(2, not visible)  # Source现在是第2列
        if visible:
            # 恢复列的交互式调整
            self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
            self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
            self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Interactive)
            if self.column_widths and len(self.column_widths) > 2:
                self.table.setColumnWidth(2, self.column_widths[2])
        else:
            # 当隐藏Source列时，让Command列可以拉伸
            self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
            self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

    def add_command(self):
        """Add a new empty command at the end of the list"""
        new_command = Command(False, "yourself", "guild chat", "", True, False)
        self.commands.append(new_command)
        self.update_table("no sort")
        self.save_state()

        # Scroll to the new row
        self.table.scrollToBottom()
        # Edit the command cell of the new row
        self.table.editItem(self.table.item(len(self.commands) - 1, 1))

    def delete_command(self):
        """Delete the currently selected command(s)"""
        selected_rows = sorted(set(index.row() for index in self.table.selectedIndexes()), reverse=True)
        if not selected_rows:
            QMessageBox.warning(self, "Warning", "Please select at least one command to delete")
            return

        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete {len(selected_rows)} command(s)?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            for row in selected_rows:
                if 0 <= row < len(self.commands):
                    del self.commands[row]
            self.sort_commands()  # 删除后重新排序
            self.update_table()
            self.save_state()

    def update_table(self, style="sort"):

        # 先判定是否要排序
        if style == "sort":
            self.sort_commands()

        # 然后更新表格内容
        self.table.setRowCount(len(self.commands))
        self.table.setColumnHidden(2, not self.source_column_visible)

        # 暂时断开itemChanged信号
        try:
            self.table.itemChanged.disconnect(self.handle_item_changed)
        except TypeError:
            pass

        for row, cmd in enumerate(self.commands):
            # Enabled checkbox
            enabled_check = QCheckBox()
            enabled_check.setChecked(cmd.command_enabled)
            enabled_check.stateChanged.connect(lambda state, r=row: self.update_command_enabled(r, state))
            # Center the checkbox
            enabled_widget = QWidget()
            enabled_layout = QHBoxLayout(enabled_widget)
            enabled_layout.addWidget(enabled_check)
            enabled_layout.setAlignment(Qt.AlignCenter)
            enabled_layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row, 0, enabled_widget)

            # Command text
            command_item = QTableWidgetItem(cmd.command_str)
            command_item.setTextAlignment(Qt.AlignCenter)
            if cmd.command_str == "!bp":
                command_item.setFlags(command_item.flags() & ~Qt.ItemIsEditable)
                command_item.setBackground(Qt.lightGray)
            else:
                command_item.setFlags(command_item.flags() | Qt.ItemIsEditable)  # 确保可编辑
            self.table.setItem(row, 1, command_item)

            # Source combo box
            source_combo = QComboBox()
            source_combo.addItems(["Anyone", "Yourself", "Others"])
            # 设置当前选中项
            if self.commands[row].command_source == "others":
                source_combo.setCurrentText("Others")
            elif self.commands[row].command_source == "yourself":
                source_combo.setCurrentText("Yourself")
            else:
                source_combo.setCurrentText("Anyone")  # 默认选中Anyone
            source_combo.currentTextChanged.connect(lambda text, r=row: self.update_command_source(r, text))

            # Center the combo box
            source_widget = QWidget()
            source_layout = QHBoxLayout(source_widget)
            source_layout.addWidget(source_combo)
            source_layout.setAlignment(Qt.AlignCenter)
            source_layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row, 2, source_widget)

            # Channel combo box
            channel_combo = QComboBox()
            channel_combo.addItems(["guild chat", "ooc", "shout", "auction", "all"])  # Updated channel options
            channel_combo.setCurrentText(cmd.command_channel)
            channel_combo.currentTextChanged.connect(lambda text, r=row: self.update_command_channel(r, text))
            # Center the combo box
            channel_widget = QWidget()
            channel_layout = QHBoxLayout(channel_widget)
            channel_layout.addWidget(channel_combo)
            channel_layout.setAlignment(Qt.AlignCenter)
            channel_layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row, 3, channel_widget)

            # Copy command checkbox
            relay_cmd_check = QCheckBox()
            relay_cmd_check.setChecked(cmd.command_relay_command)
            relay_cmd_check.stateChanged.connect(lambda state, r=row: self.update_relay_command(r, state))
            # Center the checkbox
            relay_cmd_widget = QWidget()
            relay_cmd_layout = QHBoxLayout(relay_cmd_widget)
            relay_cmd_layout.addWidget(relay_cmd_check)
            relay_cmd_layout.setAlignment(Qt.AlignCenter)
            relay_cmd_layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row, 4, relay_cmd_widget)

            # Copy full line checkbox
            relay_msg_check = QCheckBox()
            relay_msg_check.setChecked(cmd.command_relay_msg)
            relay_msg_check.stateChanged.connect(lambda state, r=row: self.update_relay_msg(r, state))
            # Center the checkbox
            relay_msg_widget = QWidget()
            relay_msg_layout = QHBoxLayout(relay_msg_widget)
            relay_msg_layout.addWidget(relay_msg_check)
            relay_msg_layout.setAlignment(Qt.AlignCenter)
            relay_msg_layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row, 5, relay_msg_widget)

        # 重新连接itemChanged信号
        self.table.itemChanged.connect(self.handle_item_changed)

        # 更新表头排序指示器
        self.update_header_sort_indicator()

        self.update_enable_all_checkbox()

    def update_command_text(self, row, text):
        """更新命令文本"""
        if 0 <= row < len(self.commands):
            self.commands[row].command_str = text
            self.save_state()

    def load_commands(self):
        """Load commands from class variable or defaults"""
        if not self.commands:
            self.load_default_commands()

        self.sort_commands()
        self.update_table()
        self.update_enable_all_checkbox()
        self.save_state()

    def load_default_commands(self):
        # Default command list
        default_commands = [
            Command(True, "anyone", "guild chat", "!tod", True, True),
            Command(True, "anyone", "all", "KCH", True, False),
            Command(True, "yourself", "all", "!bp", True, False),  # Changed from "all guildies"
            Command(False, "anyone", "guild chat", "!pop", True, False),
            Command(False, "yourself", "guild chat", "!park", True, False),
            Command(False, "yourself", "guild chat", "!KMT", True, False),
            Command(False, "yourself", "guild chat", "!KRT", True, False),
            Command(False, "yourself", "guild chat", "!KI", True, False),
            Command(False, "yourself", "guild chat", "TASH", True, False),
            Command(False, "yourself", "guild chat", "MALO", True, False),
            Command(False, "yourself", "guild chat", "MALOSINI", True, False),
            Command(False, "yourself", "guild chat", "OOS", True, False),
            Command(False, "yourself", "guild chat", "SLOW", True, False),
            Command(False, "yourself", "guild chat", "!addraid", True, False),
        ]

        self.commands = default_commands

    def load_commands_from_file(self):
        try:
            if os.path.exists('In-game cmd.ini'):
                with open('In-game cmd.ini', 'r') as f:
                    commands_section = False
                    commands = []

                    for line in f:
                        line = line.strip()
                        if line.startswith("[") and line.endswith("]"):
                            current_section = line
                            commands_section = (current_section == "[Commands]")
                            continue

                        if not commands_section:
                            continue

                        if line.startswith("#") or not line:
                            continue

                        parts = line.split('|')
                        if len(parts) == 6:
                            cmd = Command(
                                enabled=bool(int(parts[0])),
                                source=parts[1],
                                channel=parts[2],
                                command_str=parts[3],
                                relay_command=bool(int(parts[4])),
                                relay_msg=bool(int(parts[5]))
                            )
                            commands.append(cmd)

                    if commands:
                        self.commands = commands
                        return True
        except Exception as e:
            print(f"Error loading commands from file: {e}")

        return False

    def update_command_enabled(self, row, state):
        self.commands[row].command_enabled = state == Qt.Checked
        self.update_enable_all_checkbox()
        self.save_state()

    def update_enable_all_checkbox(self):
        """Update the Enable All checkbox based on current command states"""
        if not self.commands:  # Empty list
            self.enable_all_checkbox.setChecked(False)
            return

        all_enabled = all(cmd.command_enabled for cmd in self.commands)
        all_disabled = all(not cmd.command_enabled for cmd in self.commands)

        # Block signals temporarily to prevent recursive calls
        self.enable_all_checkbox.blockSignals(True)

        if all_enabled:
            self.enable_all_checkbox.setChecked(True)
            self.enable_all_checkbox.setTristate(False)
        elif all_disabled:
            self.enable_all_checkbox.setChecked(False)
            self.enable_all_checkbox.setTristate(False)
        else:  # Mixed state
            self.enable_all_checkbox.setCheckState(Qt.PartiallyChecked)

        self.enable_all_checkbox.blockSignals(False)

    def update_command_source(self, row, text):
        if text == "Others":
            self.commands[row].command_source = "others"
        elif text == "Yourself":
            self.commands[row].command_source = "yourself"
        else:  # "Anyone"
            self.commands[row].command_source = "anyone"
        self.save_state()

    def update_command_channel(self, row, text):
        self.commands[row].command_channel = text
        self.save_state()

    def update_relay_command(self, row, state):
        self.commands[row].command_relay_command = state == Qt.Checked
        self.save_state()

    def update_relay_msg(self, row, state):
        self.commands[row].command_relay_msg = state == Qt.Checked
        self.save_state()

    def toggle_all_commands(self, state):
        # Only take action when the checkbox is explicitly checked or unchecked
        if state == Qt.Checked:
            enabled = True
        elif state == Qt.Unchecked:
            enabled = False
        else:  # Partially checked - leave as is
            return

        for cmd in self.commands:
            cmd.command_enabled = enabled

        # Update the table to reflect changes
        self.update_table()
        self.save_state()

    def save_state(self):
        # Save current state to history
        if self.current_history_index < len(self.history) - 1:
            self.history = self.history[:self.current_history_index + 1]

        self.history.append(copy.deepcopy(self.commands))
        self.current_history_index = len(self.history) - 1
        self.update_undo_button()

    def update_undo_button(self):
        self.undo_btn.setEnabled(self.current_history_index > 0)

    def undo_action(self):
        if self.current_history_index > 0:
            self.current_history_index -= 1
            self.commands = copy.deepcopy(self.history[self.current_history_index])
            self.update_table()
            self.update_undo_button()
            self.update_enable_all_checkbox()

    def accept_changes(self):
        """接受所有更改（保存到类变量和文件）"""
        # 更新命令文本
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 1)
            if item and 0 <= row < len(self.commands):
                self.commands[row].command_str = item.text()

        self.history = []
        self.current_history_index = -1
        self.data_changed.emit()
        self.hide()

    def cancel_changes(self):
        """Cancel changes and close editor"""
        if self.history:
            self.commands = copy.deepcopy(self.history[0])
            self.update_table()

        self.hide()


    def save_command_to_file(self):
        try:
            # 确保在保存前获取最新的命令文本
            for row in range(self.table.rowCount()):
                item = self.table.item(row, 1)  # Command列
                if item and 0 <= row < len(self.commands):
                    self.commands[row].command_str = item.text()

            # Read existing file content and separate into sections
            sections = {}
            current_section = None
            current_content = []

            if os.path.exists('In-game cmd.ini'):
                with open('In-game cmd.ini', 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("[") and line.endswith("]"):
                            if current_section:
                                sections[current_section] = current_content
                            current_section = line
                            current_content = []
                        else:
                            if line or (current_content and current_content[-1]):  # Preserve meaningful empty lines
                                current_content.append(line)

                # Add the last section
                if current_section:
                    sections[current_section] = current_content

            # Write all content back to file
            with open('In-game cmd.ini', 'w') as f:
                # Write all sections except Commands first
                for section, lines in sections.items():
                    if section != "[Commands]":
                        f.write(f"{section}\n")
                        for line in lines:
                            f.write(f"{line}\n")
                        f.write("\n")

                # Write commands section
                f.write("[Commands]\n")
                for cmd in self.commands:
                    line = f"{int(cmd.command_enabled)}|{cmd.command_source}|{cmd.command_channel}|{cmd.command_str}|{int(cmd.command_relay_command)}|{int(cmd.command_relay_msg)}\n"
                    f.write(line)

                # Ensure there's a newline at end of file if other sections existed
                if sections:
                    f.write("\n")

            # QMessageBox.information(self, "Success", "Command configuration saved successfully")

        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error saving file: {e}")

