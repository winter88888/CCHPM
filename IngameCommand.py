import copy
import datetime
import re
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QTableWidget, QTableWidgetItem, QCheckBox, QPushButton,
                             QComboBox, QHeaderView, QMessageBox, QDialog, QLabel, QLineEdit, QDialogButtonBox)
from PyQt5.QtCore import Qt, pyqtSignal
import os
import zlib
import hashlib
import base64

from WebhookSender import WebhookSender
from CommandEditor import *


class IngameCommand(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.commands = []
        self.parent()
        self.command_editor = CommandEditor()
        self.copy_commands()
        self.webhook_dialog = None  # Reference to webhook config dialog
        self.webhook_url = ""
        self.ifIngameDiscordCommandEnabled = False
        self.ifProxyIngameCommandEnabled = False
        self.yourName = ""
        self.webhook_sender = WebhookSender()
        # 初始化时设置Source列的可见性
        # 连接信号
        self.command_editor.data_changed.connect(self.copy_commands)
        self.webhook_sender.logHandler = self.logErrorMessage

    def setupYourName(self, yourName: str):

        if self.ifIngameDiscordCommandEnabled:
            self.webhook_sender.clear_queue()  # 添加清空队列的方法

        self.yourName = yourName

    def setIngameDiscordCommandEnable(self, ifIngameDiscordCommandEnabled):
        self.ifIngameDiscordCommandEnabled = ifIngameDiscordCommandEnabled

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

            # Update settings
            if "[Settings]" not in sections:
                sections["[Settings]"] = []

            # Update IDCEnabled setting
            settings = sections["[Settings]"]
            updated_settings = []
            idc_set = False

            for line in settings:
                if line.startswith("IDCEnabled="):
                    updated_settings.append(f"IDCEnabled={'YES' if ifIngameDiscordCommandEnabled else 'NO'}")
                    idc_set = True
                else:
                    updated_settings.append(line)

            if not idc_set:
                updated_settings.append(f"IDCEnabled={'YES' if ifIngameDiscordCommandEnabled else 'NO'}")

            sections["[Settings]"] = updated_settings

            # Write back to file
            with open('In-game cmd.ini', 'w') as f:
                # Write all sections except Commands first
                for section, lines in sections.items():
                    if section != "[Commands]":
                        f.write(f"{section}\n")
                        for line in lines:
                            f.write(f"{line}\n")
                        f.write("\n")

                # Write commands section if it exists
                if "[Commands]" in sections:
                    f.write("[Commands]\n")
                    for line in sections["[Commands]"]:
                        f.write(f"{line}\n")

        except Exception as e:
            self.logErrorMessage(f"Error saving IDCEnabled setting: {str(e)}", "ERROR")

    def setProxyIngameCommandEnable(self, ifProxyIngameCommandEnabled: bool):
        """Update PICEnabled setting in config file"""
        self.ifProxyIngameCommandEnabled = ifProxyIngameCommandEnabled
        # 当标志位改变时，更新Source列的可见性
        self.command_editor.set_source_column_visible(self.ifProxyIngameCommandEnabled)

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

            # Update settings
            if "[Settings]" not in sections:
                sections["[Settings]"] = []

            # Update PICEnabled setting
            settings = sections["[Settings]"]
            updated_settings = []
            pic_set = False

            for line in settings:
                if line.startswith("PICEnabled="):
                    updated_settings.append(f"PICEnabled={'YES' if ifProxyIngameCommandEnabled else 'NO'}")
                    pic_set = True
                else:
                    updated_settings.append(line)

            if not pic_set:
                updated_settings.append(f"PICEnabled={'YES' if ifProxyIngameCommandEnabled else 'NO'}")

            sections["[Settings]"] = updated_settings

            # Write back to file
            with open('In-game cmd.ini', 'w') as f:
                # Write all sections except Commands first
                for section, lines in sections.items():
                    if section != "[Commands]":
                        f.write(f"{section}\n")
                        for line in lines:
                            f.write(f"{line}\n")
                        f.write("\n")

                # Write commands section if it exists
                if "[Commands]" in sections:
                    f.write("[Commands]\n")
                    for line in sections["[Commands]"]:
                        f.write(f"{line}\n")

            self.logErrorMessage(
                f"Proxy in-game command setting updated to {'enabled' if ifProxyIngameCommandEnabled else 'disabled'}",
                "INFO"
            )

        except Exception as e:
            self.logErrorMessage(f"Error saving PICEnabled setting: {str(e)}", "ERROR")

    def copy_commands(self):
        self.commands = copy.deepcopy(self.command_editor.commands)
        # print("in copy command")

    def show_editor(self):

        """Show command editor, controlling Source column visibility based on proxy state"""
        self.command_editor.set_source_column_visible(self.ifProxyIngameCommandEnabled)
        # Reset editor state when showing
        self.command_editor.load_commands()
        self.command_editor.save_initial_state()
        self.command_editor.show()
        self.command_editor.activateWindow()
        self.command_editor.raise_()


    def setWebhook(self):
        """Show webhook configuration dialog and return True if successfully configured"""
        dialog = QDialog(self.parent())
        dialog.setWindowTitle("Configure Discord Webhook")
        dialog.setMinimumWidth(500)

        layout = QVBoxLayout()

        # Current webhook display
        current_webhook = self._get_current_webhook()
        current_label = QLabel(f"Current Webhook: {current_webhook if current_webhook else 'Not set'}")
        layout.addWidget(current_label)

        # Webhook input
        layout.addWidget(QLabel("New Webhook URL:"))
        self.webhook_input = QLineEdit()
        self.webhook_input.setPlaceholderText("https://discord.com/api/webhooks/...")
        if current_webhook:
            self.webhook_input.setText(current_webhook)
        layout.addWidget(self.webhook_input)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self._save_webhook(dialog))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.setLayout(layout)

        # Return False if user cancels
        if dialog.exec_() != QDialog.Accepted:
            self.logErrorMessage("Webhook configuration cancelled by user", "INFO")
            return False

        # If we get here, user accepted and _save_webhook was called
        # Update self.webhook_url with the newly set webhook
        self.webhook_url = self.webhook_input.text().strip()
        self.logErrorMessage(f"Webhook URL updated successfully.", "INFO")
        return True

    def _get_current_webhook(self):
        """Try to decrypt and return current webhook if exists"""
        try:
            if not os.path.exists('In-game cmd.ini'):
                self.logErrorMessage("Config file not found", "WARNING")
                return None

            creation_time = os.path.getctime('In-game cmd.ini')
            seed = str(int(creation_time)).encode('utf-8')

            with open('In-game cmd.ini', 'r') as f:
                content = f.read()

            settings = self._parse_settings_section(content)
            encrypted = settings.get('Webhook', '').strip()  # 添加 strip() 去除可能的空白字符
            stored_crc = settings.get('WHCRC', '')

            if not encrypted or not stored_crc:
                self.logErrorMessage("Webhook or WHCRC not found in settings", "WARNING")
                return None

            try:
                decrypted = self._decrypt_webhook_simple(encrypted, seed)
            except Exception as e:
                self.logErrorMessage(f"Failed to decrypt webhook: {str(e)}", "ERROR")
                return None

            # Verify CRC
            calculated_crc = self._calculate_crc(decrypted)
            if calculated_crc != stored_crc:
                self.logErrorMessage(f"CRC verification failed (stored:{stored_crc} calculated:{calculated_crc})",
                                     "WARNING")
                return None

            return decrypted

        except Exception as e:
            self.logErrorMessage(f"Error getting current webhook: {str(e)}", "ERROR")
            return None

    def _save_webhook(self, dialog):
        """Save new webhook to config file, returns (success, message)"""
        webhook_url = self.webhook_input.text().strip()

        if not webhook_url.startswith('https://discord.com/api/webhooks/'):
            msg = "Invalid URL - must start with https://discord.com/api/webhooks/"
            self.logErrorMessage(msg, "ERROR")
            QMessageBox.warning(dialog, "Invalid URL", msg)
            return False

        try:
            # Get or create config file to get creation time
            if not os.path.exists('In-game cmd.ini'):
                with open('In-game cmd.ini', 'w') as f:
                    f.write("[Settings]\n[Commands]\n")
                self.logErrorMessage("Created new config file", "INFO")

            creation_time = os.path.getctime('In-game cmd.ini')
            seed = str(int(creation_time)).encode('utf-8')

            # Encrypt and calculate CRC
            encrypted = self._encrypt_webhook_simple(webhook_url, seed)
            crc = self._calculate_crc(webhook_url)
            self.logErrorMessage(f"Encrypted webhook and calculated CRC: {crc}", "DEBUG")

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

            # Update settings
            if "[Settings]" not in sections:
                sections["[Settings]"] = []
                self.logErrorMessage("Added missing [Settings] section", "INFO")

            # Update webhook and CRC
            settings = sections["[Settings]"]
            updated_settings = []
            webhook_set = False
            crc_set = False

            for line in settings:
                if line.startswith("Webhook="):
                    updated_settings.append(f"Webhook={encrypted}")
                    webhook_set = True
                elif line.startswith("WHCRC="):
                    updated_settings.append(f"WHCRC={crc}")
                    crc_set = True
                else:
                    updated_settings.append(line)

            if not webhook_set:
                updated_settings.append(f"Webhook={encrypted}")
            if not crc_set:
                updated_settings.append(f"WHCRC={crc}")

            sections["[Settings]"] = updated_settings

            # Write back to file
            with open('In-game cmd.ini', 'w') as f:
                # Write all sections except Commands first
                for section, lines in sections.items():
                    if section != "[Commands]":
                        f.write(f"{section}\n")
                        for line in lines:
                            f.write(f"{line}\n")
                        f.write("\n")

                # Write commands section if it exists
                if "[Commands]" in sections:
                    f.write("[Commands]\n")
                    for line in sections["[Commands]"]:
                        f.write(f"{line}\n")

            msg = "Webhook configured successfully"
            self.logErrorMessage(msg, "INFO")
            QMessageBox.information(dialog, "Success", msg)
            dialog.accept()

            return True

        except Exception as e:
            msg = f"Failed to save webhook: {str(e)}"
            self.logErrorMessage(msg, "ERROR")
            QMessageBox.warning(dialog, "Error", msg)
            return False

    def _encrypt_webhook_simple(self, webhook_url, seed):
        """加密 Webhook 数据"""
        try:
            key = hashlib.sha256(seed).digest()
            encrypted = bytes([ord(c) ^ key[i % len(key)] for i, c in enumerate(webhook_url)])
            return base64.b64encode(encrypted).decode('utf-8')
        except Exception as e:
            self.logErrorMessage(f"Encryption failed: {str(e)}", "ERROR")
            raise

    def _decrypt_webhook_simple(self, encrypted_webhook, seed):
        """解密 Webhook 数据"""
        try:
            # 修复 Base64 字符串长度问题
            # Base64 长度应该是 4 的倍数，不足的补 =
            padding = len(encrypted_webhook) % 4
            if padding:
                encrypted_webhook += '=' * (4 - padding)

            key = hashlib.sha256(seed).digest()
            encrypted = base64.b64decode(encrypted_webhook)
            return ''.join([chr(encrypted[i] ^ key[i % len(key)]) for i in range(len(encrypted))])
        except Exception as e:
            self.logErrorMessage(f"Decryption failed: {str(e)}", "ERROR")
            raise

    def _parse_settings_section(self, content):
        settings = {}
        in_settings = False

        for line in content.split('\n'):
            line = line.strip()
            if line == "[Settings]":
                in_settings = True
                continue
            elif line.startswith("[") and line.endswith("]"):
                in_settings = False
                continue

            if in_settings and '=' in line:
                key, value = line.split('=', 1)
                settings[key.strip()] = value.strip()

        return settings


    def _calculate_crc(self, text):
        if not text:
            return "00000000"
        return format(zlib.crc32(text.encode('utf-8')) & 0xffffffff, '08X')

    def verify_webhook_config(self):
        """Verify if the stored webhook configuration is valid"""
        try:
            # 1. Check if config file exists
            if not os.path.exists('In-game cmd.ini'):
                self.logErrorMessage("Config file not found during verification", "WARNING")
                return False

            # 2. Read config file content
            with open('In-game cmd.ini', 'r') as f:
                content = f.read()

            # 3. Parse settings section
            settings = self._parse_settings_section(content)

            # 4. Check IDCEnabled flag first
            idc_enabled = settings.get('IDCEnabled', 'NO').upper() == 'YES'
            if not idc_enabled:
                self.logErrorMessage("In-game Discord commands are disabled (IDCEnabled=NO)", "INFO")
                return False

            # 5. Get file creation time as encryption seed
            creation_time = os.path.getctime('In-game cmd.ini')
            seed = str(int(creation_time)).encode('utf-8')

            # 6. Check webhook settings
            encrypted_webhook = settings.get('Webhook', '')
            stored_crc = settings.get('WHCRC', '')

            if not encrypted_webhook or not stored_crc:
                self.logErrorMessage("Webhook or WHCRC not found in settings during verification", "WARNING")
                return False

            # 7. Decrypt webhook
            try:
                decrypted_webhook = self._decrypt_webhook_simple(encrypted_webhook, seed)
            except Exception as e:
                self.logErrorMessage(f"Failed to decrypt webhook during verification: {str(e)}", "ERROR")
                return False

            # 8. Verify CRC
            calculated_crc = self._calculate_crc(decrypted_webhook)
            if calculated_crc != stored_crc:
                self.logErrorMessage(
                    f"CRC mismatch during verification (stored:{stored_crc} calculated:{calculated_crc})",
                    "WARNING"
                )
                return False

            # 9. Verify URL format
            if not decrypted_webhook.startswith('https://discord.com/api/webhooks/'):
                self.logErrorMessage(f"Invalid webhook URL format: {decrypted_webhook}", "WARNING")
                return False

            # 10. Store valid webhook URL for later use
            self.webhook_url = decrypted_webhook
            self.ifIngameDiscordCommandEnabled = True  # Make sure this is in sync
            self.logErrorMessage("Webhook verification successful", "INFO")
            return True

        except Exception as e:
            self.logErrorMessage(f"Error during webhook verification: {str(e)}", "ERROR")
            return False

    def verify_proxy_config(self):
        """Verify if proxy in-game commands are enabled and authorized"""
        try:
            # 1. Check if config file exists
            if not os.path.exists('In-game cmd.ini'):
                self.logErrorMessage("Config file not found during proxy config verification", "WARNING")
                return "N/A"

            # 2. Read config file content
            with open('In-game cmd.ini', 'r') as f:
                content = f.read()

            # 3. Parse settings section
            settings = self._parse_settings_section(content)

            # 4. Check PICEnabled parameter
            pic_enabled = settings.get('PICEnabled', '').upper()

            if pic_enabled != 'YES':
                self.logErrorMessage(f"Proxy in-game commands are disabled (PICEnabled={pic_enabled})", "INFO")
                return "NO" if pic_enabled == 'NO' else "N/A"

            # 5. Get PICCookie and verify
            pic_cookie_enc = settings.get('PICCookie', '')
            if not pic_cookie_enc:
                self.logErrorMessage("PICCookie missing when PICEnabled=YES", "WARNING")
                return "NO"

            # 6. Decrypt PICCookie (same algorithm as webhook)
            creation_time = os.path.getctime('In-game cmd.ini')
            seed = str(int(creation_time)).encode('utf-8')
            try:
                decrypted_cookie = self._decrypt_webhook_simple(pic_cookie_enc, seed)
            except Exception as e:
                self.logErrorMessage(f"Failed to decrypt PICCookie: {str(e)}", "ERROR")
                return "NO"

            # 7. Validate against hardcoded string
            if decrypted_cookie != "Kingdombot":
                self.logErrorMessage(f"Invalid PICCookie (decrypted: {decrypted_cookie})", "WARNING")
                return "NO"

            self.logErrorMessage("Proxy in-game commands authorized (valid PICCookie)", "INFO")
            self.ifProxyIngameCommandEnabled = True

            return "YES"

        except Exception as e:
            self.logErrorMessage(f"Error during proxy config verification: {str(e)}", "ERROR")
            return "N/A"

    def checkProxyAuthorization(self):
        """Check proxy authorization via password dialog"""
        try:
            # 1. First try to verify existing config
            config_status = self.verify_proxy_config()
            if config_status == "YES":
                return True

            # 2. Create password dialog
            dialog = QDialog(self.parent())
            dialog.setWindowTitle("Proxy Authorization")
            dialog.setMinimumWidth(300)

            layout = QVBoxLayout()

            # Password input
            layout.addWidget(QLabel("Enter Proxy Password:"))
            self.password_input = QLineEdit()
            self.password_input.setEchoMode(QLineEdit.Password)
            layout.addWidget(self.password_input)

            # Buttons
            button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            button_box.accepted.connect(lambda: self._validate_proxy_password(dialog))
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)

            dialog.setLayout(layout)

            # 3. Show dialog and wait for user input
            if dialog.exec_() != QDialog.Accepted:
                self.logErrorMessage("Proxy authorization cancelled by user", "INFO")
                return False

            return True

        except Exception as e:
            self.logErrorMessage(f"Error in proxy authorization: {str(e)}", "ERROR")
            return False

    def _validate_proxy_password(self, dialog):
        """Validate password and update config if correct"""
        password = self.password_input.text().strip()

        if password != "Kingdombot":
            QMessageBox.warning(dialog, "Invalid Password", "Incorrect proxy password")
            return

        try:
            # Generate encrypted cookie
            encrypted_cookie = self._generate_proxy_cookie("Kingdombot")

            # Read existing config
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

            # Update settings
            if "[Settings]" not in sections:
                sections["[Settings]"] = []

            # Update PICEnabled and PICCookie
            settings = sections["[Settings]"]
            updated_settings = []
            pic_enabled_set = False
            pic_cookie_set = False

            for line in settings:
                if line.startswith("PICEnabled="):
                    updated_settings.append("PICEnabled=YES")
                    pic_enabled_set = True
                elif line.startswith("PICCookie="):
                    updated_settings.append(f"PICCookie={encrypted_cookie}")
                    pic_cookie_set = True
                else:
                    updated_settings.append(line)

            if not pic_enabled_set:
                updated_settings.append("PICEnabled=YES")
            if not pic_cookie_set:
                updated_settings.append(f"PICCookie={encrypted_cookie}")

            sections["[Settings]"] = updated_settings

            # Write back to file
            with open('In-game cmd.ini', 'w') as f:
                # Write all sections except Commands first
                for section, lines in sections.items():
                    if section != "[Commands]":
                        f.write(f"{section}\n")
                        for line in lines:
                            f.write(f"{line}\n")
                        f.write("\n")

                # Write commands section if exists
                if "[Commands]" in sections:
                    f.write("[Commands]\n")
                    for line in sections["[Commands]"]:
                        f.write(f"{line}\n")

            self.logErrorMessage("Proxy authorization successful", "INFO")
            dialog.accept()

        except Exception as e:
            self.logErrorMessage(f"Failed to save proxy config: {str(e)}", "ERROR")
            QMessageBox.warning(dialog, "Error", "Failed to save configuration")

    def _generate_proxy_cookie(self, plaintext: str) -> str:
        """Generate encrypted PICCookie (call this in checkProxyAuthorization)"""
        if not os.path.exists('In-game cmd.ini'):
            raise FileNotFoundError("Config file missing")

        creation_time = os.path.getctime('In-game cmd.ini')
        seed = str(int(creation_time)).encode('utf-8')
        return self._encrypt_webhook_simple(plaintext, seed)

    def logProcessor(self, line: str):
        """
        Process a log line for in-game commands and execute actions based on configuration.

        Args:
            line: A line of text from the game log to be processed.
        """
        try:
            # Check if Discord command processing is enabled
            if not self.ifIngameDiscordCommandEnabled:
                return


            # Filter line against enabled commands
            matched_command = None
            for cmd in self.commands:
                if not cmd.command_enabled:
                    continue

                # Check if command matches (case sensitive)
                if line.upper().find(cmd.command_str.upper()) != -1:
                    matched_command = cmd
                    break

            if not matched_command:
                return  # No matching command found

            # Check source match
            if not self.ifProxyIngameCommandEnabled:
                # 非代理模式下的处理
                result = re.search(
                    r"^You (say to your guild|say out of character|shout|auction), '" + matched_command.command_str,
                    line[27:], re.IGNORECASE)
                if result:
                    # 处理自己的消息
                    channel_mapping = {
                        "say to your guild": "guild chat",
                        "say out of character": "ooc",
                        "shout": "shout",
                        "auction": "auction"
                    }
                    channel = channel_mapping.get(result.group(1), "something wrong")
                    char = self.yourName
                    self.match_and_send_msg(channel, char, line, matched_command)
                    return
            else:
                # 代理模式下的处理
                # 处理自己的消息
                result = re.search(
                    r"^You (say to your guild|say out of character|shout|auction), '" + matched_command.command_str,
                    line[27:], re.IGNORECASE)
                if result and matched_command.command_source in ["yourself", "anyone"]:
                    channel_mapping = {
                        "say to your guild": "guild chat",
                        "say out of character": "ooc",
                        "shout": "shout",
                        "auction": "auction"
                    }
                    channel = channel_mapping.get(result.group(1), "something wrong")
                    char = self.yourName
                    self.match_and_send_msg(channel, char, line, matched_command)
                    return

                # 处理他人的消息
                if matched_command.command_source in ["others", "anyone"]:
                    result = re.search(
                        r"^([\w]+) (tells the guild|says out of character|shouts|auctions), '" + matched_command.command_str,
                        line[27:], re.IGNORECASE)
                    if result:
                        channel_mapping = {
                            "tells the guild": "guild chat",
                            "says out of character": "ooc",
                            "shouts": "shout",
                            "auctions": "auction"
                        }
                        channel = channel_mapping.get(result.group(2), "something wrong")
                        char = result.group(1)
                        self.match_and_send_msg(channel, char, line, matched_command)
                        return

            self.logErrorMessage(f"In-game command matched,but mismatched other condition.The line is {line}","Warning")

        except Exception as e:
            self.logErrorMessage(f"Error in logProcessor: {str(e)}", "ERROR")



    def match_and_send_msg(self, channel, char, line, matched_command):
        # Check channel match
        if matched_command.command_channel.lower() != "all" and \
                matched_command.command_channel.lower() != channel.lower():
            self.logErrorMessage(
                f"Channel mismatch - Expected: {matched_command.command_channel}, Actual: {channel}",
                "DEBUG"
            )
            return

        # Execute actions based on command settings
        action_taken = False
        command = self.copy_from_match(line, matched_command.command_str).strip().rstrip("'")

        if matched_command.command_relay_command:
            self._copyCommand(command, char)
            action_taken = True
            self.logErrorMessage(
                f"Executed CopyCommand for {command} from : {char}",
                "DEBUG"
            )

        if matched_command.command_relay_msg:
            self._copyFullLine(line)
            action_taken = True
            self.logErrorMessage(
                f"Executed CopyFullLine for line: {line.strip()}",
                "DEBUG"
            )

        if not action_taken:
            self.logErrorMessage(
                f"Command {command} matched but no actions were enabled",
                "DEBUG"
            )

    def copy_from_match(self, text, pattern):
        """
        在字符串中查找模式，匹配后返回从匹配点到结尾的子串

        Args:
            text (str): 要搜索的原始字符串
            pattern (str): 要查找的模式/子串

        Returns:
            str: 从第一次匹配位置到字符串结尾的子串
            None: 如果未找到匹配
        """
        index = text.upper().find(pattern.upper())  # 查找模式第一次出现的位置
        if index != -1:  # 如果找到匹配
            return text[index:]  # 返回从匹配点到结尾的子串
        return None  # 未找到匹配

    def _copyCommand(self, command: str, char: str):
        """
        Send just the command and its arguments to Discord.

        """
        if not self.webhook_url:
            self.logErrorMessage("No webhook URL configured for _copyCommand", "error")
            return

        self.webhook_sender.enqueue_message(
            webhook_url=self.webhook_url,
            content=command,
            user_name=char
        )

    def _copyFullLine(self, line):
        """
        Send the entire line to Discord.

        Args:
            line: The complete log line to send
        """
        if not self.webhook_url:
            self.logErrorMessage("No webhook URL configured for _copyFullLine", "error")
            return

        self.webhook_sender.enqueue_message(
            webhook_url=self.webhook_url,
            content="`" + line.strip() + "`",
            user_name=self.yourName
        )

    def shutdown(self):
        """Clean up resources."""
        self.webhook_sender.shutdown()

    def save_settings(self):
        self.command_editor.save_command_to_file()
        self.command_editor.save_ui_settings()

    def logErrorMessage(self, message: str, type: str):

        # 记录到日志文件
        curr_time = datetime.datetime.now()
        time_str = datetime.datetime.strftime(curr_time, '%Y-%m-%d %H:%M:%S.%f')
        with open('Online BP RUN LOG.txt', 'a', encoding='utf-8') as f:
            message = message.rstrip()
            f.write('[' + time_str + ']  ' + message + '\n')
            f.flush()


if __name__ == "__main__":
    app = QApplication([])

    ingame_commands = IngameCommand()
    ingame_commands.show_editor()

    app.exec_()
