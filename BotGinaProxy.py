from PyQt5.QtWidgets import QDialog, QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout, QPushButton, QHeaderView, \
    QCheckBox, QDialogButtonBox, QTextEdit, QLabel, QScrollArea, QWidget, QGroupBox
from PyQt5.QtCore import Qt
import os
import pathlib


class BotGinaProxy(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.ifBotGinaProxyEnable = False
        self.yourName = ""

        # Bot lists by class
        self.bot_lists = {
            "mag": "Carenn Devlin Cothwise Roachmilk Villageby Getinda Kayrin Lilcoth Peteer Cairrenn Cothpacatastic Raymand Ahti Bigmurgh Bubbrubbb Cairreen Cothasaurus Dahlbouk Gotoh Kairenn Keyge Mightymirgh Murgherer Sumtastic Cbwan Msjuju Pantsu Notbot Villageby Dadadada Laaria Mirghinator Shambies Bodyykount",
            "clr": "Restastic Reso Hazelnuts Suee Xovydal Caramello Deecu Estyra Fullcream Hershees Inyaga Mymoms Medexpress Mcbacon Menderz Curlyfri Mereal Mounds Mufins Redraven Almondjoy Hipe Mcgriddle Sighs Sweetiepies Acefriely Caffelatte HairyJane Halloe Icehealz Kingcleric Mclatte Miyaki Rezah Takingaaa Seeache Jarrominator Plasheal Bulten Animare Xovydal Mcgriddle Nunkin Poyzon Twitchpls",
            "rog": "Scarystacy Boudahl Holeena Snupey Racidnalz Bolea Peekuh Hidey Thighsclad Kingstab Seemme Legendstab Sebilina Naifu Mysstii Noif Hallsitter Nofunn Mswhiskers Mcpint Drainhair Rudager Gaba Squeelon Hallsitter",
            "wiz": "Hermiyone Legendzap Jarethin Hawrry Caocao Debbra Ezbane Niney Verbier Xinders Banfranklin Degta Beatiny Billy Bkingflux Coldwiz Eggdrop Hillzard Bunsen Debbra Plaslure Shrinkmedaddy Sowmedaddy Kingporlos",
            "enc": "Dozin Kaboomsmom Iceforce Icemaker Iceworks Robotussin Anchorz Plastitute Nougat",
            "brd": "Kingswag Jeptha Speedeey Tactile Ellasina Fondant Canklez Figo Ohhkay Tiina Powerade Smoflows",
            "war": "Ffezzik Tusked Slopper Kingfrost Matera Sauceress Plashcan Bagheera",
            "rng": "Scaryteri Bumperking Nockedn Twunkinthejunk Scarysteve Twosheds Loglizard Mylittlestump Virri Trackingyay Touchmybraces",
            "nec": "Kingnecro Nearcyde Deadfredd Angostura Necroking Kbon Brug Walki Icedmfwell",
            "dru": "Sowr Laalo Smoflow",
            "mnk": "Effdee Floppers Kingfu Giestt Scrowty",
            "pal": "Morzak Kingkazon Jehan",
            "shm": "Mmow Petete Scourge Kslo Shammblez"
        }

        # Create bot dictionary {name: (class, enabled)}
        self.bot_dict = {}

        # Load enabled bots from config
        self.load_bot_config()

    def load_bot_config(self):
        """Load bot enablement configuration from file"""
        config_file = "bot_gina_proxy.ini"
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and ',' in line:
                            parts = line.split(',', 2)  # Split into max 3 parts
                            if len(parts) >= 3:
                                name, class_name, enabled_str = parts[0], parts[1], parts[2]
                                # Only update if class matches our known classes
                                if class_name in self.bot_lists:
                                    self.bot_dict[name] = (class_name, enabled_str.lower() == 'true')

            except Exception as e:
                self.parent.msg(f"ERROR loading bot config: {str(e)}")
                # If config file is corrupted, recreate it with defaults
                for class_name, names in self.bot_lists.items():
                    for name in names.split():
                        self.bot_dict[name] = (class_name, True)  # Default to enabled
                self.save_bot_config()
        else:
            # If config file doesn't exist, recreate it with defaults
            for class_name, names in self.bot_lists.items():
                for name in names.split():
                    self.bot_dict[name] = (class_name, True)  # Default to enabled
            self.save_bot_config()

    def save_bot_config(self):
        """Save bot enablement configuration to file"""
        config_file = "bot_gina_proxy.ini"
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                for name, (class_name, enabled) in self.bot_dict.items():
                    f.write(f"{name},{class_name},{enabled}\n")
        except Exception as e:
            self.parent.msg(f"ERROR saving bot config: {str(e)}")

    def setProxyEnabled(self):
        self.ifBotGinaProxyEnable = True

    def setProxyDisabled(self):
        self.ifBotGinaProxyEnable = False

    def setupYourName(self, name: str):
        self.yourName = name

    def logProcessor(self, line: str):
        if not self.ifBotGinaProxyEnable or not self.yourName:
            return

        # Check if current character is a bot and proxy is enabled
        if self.yourName in self.bot_dict:
            class_name, enabled = self.bot_dict[self.yourName]
            if enabled:
                self.forward_log(line, class_name)

    def forward_log(self, line: str, class_name: str):
        """Forward log line to class-specific log file"""
        try:
            # Create log directory if it doesn't exist
            log_dir = pathlib.Path("./Logs")  # 修改为 ./Logs 目录
            log_dir.mkdir(exist_ok=True)  # 确保目录存在
            log_file = log_dir / f"eqlog_{class_name}bot_P1999Green.txt"

            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(line)
                f.flush()

        except Exception as e:
            self.parent.msg(f"ERROR forwarding bot log: {str(e)}")

    def show_bot_editor(self):
        """Show bot editor dialog"""
        dialog = BotEditorDialog(self.parent, self.bot_dict)
        if dialog.exec_() == QDialog.Accepted:
            # Update bot dictionary with changes
            self.bot_dict = dialog.get_updated_bots()
            self.save_bot_config()
            self.parent.msg("Bot configuration saved successfully.")


class BotEditorDialog(QDialog):
    def __init__(self, parent, bot_dict):
        super().__init__(parent)
        self.parent = parent
        self.original_bots = bot_dict
        self.updated_bots = bot_dict.copy()

        self.setWindowTitle("Bot List Editor")
        self.setGeometry(600, 100, 1000, 600)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Instructions
        instructions = QLabel("Edit bot configuration(one bot per line).Format: botname,class,if_enabled(true/false).")
        layout.addWidget(instructions)

        # Text edit area
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Example:\nCarenn,mag,true\nDevlin,mag,false")

        # Populate with current bot data
        self.populate_text_edit()

        layout.addWidget(self.text_edit)

        # Buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")
        self.reset_button = QPushButton("Reset to Default")

        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.reset_button.clicked.connect(self.reset_to_default)

        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def populate_text_edit(self):
        """Populate text edit with current bot data"""
        text_lines = []
        for bot_name, (class_name, enabled) in sorted(self.updated_bots.items()):
            text_lines.append(f"{bot_name},{class_name},{str(enabled).lower()}")

        self.text_edit.setText("\n".join(text_lines))

    def reset_to_default(self):
        """Reset to default bot configuration"""
        default_text = []
        bot_lists = {
            "mag": "Carenn Devlin Cothwise Roachmilk Villageby Getinda Kayrin Lilcoth Peteer Cairrenn Cothpacatastic Raymand Ahti Bigmurgh Bubbrubbb Cairreen Cothasaurus Dahlbouk Gotoh Kairenn Keyge Mightymirgh Murgherer Sumtastic Cbwan Msjuju Pantsu Notbot Villageby Dadadada Laaria Mirghinator Shambies Bodyykount",
            "clr": "Restastic Reso Hazelnuts Suee Xovydal Caramello Deecu Estyra Fullcream Hershees Inyaga Mymoms Medexpress Mcbacon Menderz Curlyfri Mereal Mounds Mufins Redraven Almondjoy Hipe Mcgriddle Sighs Sweetiepies Acefriely Caffelatte HairyJane Halloe Icehealz Kingcleric Mclatte Miyaki Rezah Takingaaa Seeache Jarrominator Plasheal Bulten Animare Xovydal Mcgriddle Nunkin Poyzon Twitchpls",
            "rog": "Scarystacy Boudahl Holeena Snupey Racidnalz Bolea Peekuh Hidey Thighsclad Kingstab Seemme Legendstab Sebilina Naifu Mysstii Noif Hallsitter Nofunn Mswhiskers Mcpint Drainhair Rudager Gaba Squeelon Hallsitter",
            "wiz": "Hermiyone Legendzap Jarethin Hawrry Caocao Debbra Ezbane Niney Verbier Xinders Banfranklin Degta Beatiny Billy Bkingflux Coldwiz Eggdrop Hillzard Bunsen Debbra Plaslure Shrinkmedaddy Sowmedaddy Kingporlos",
            "enc": "Dozin Kaboomsmom Iceforce Icemaker Iceworks Robotussin Anchorz Plastitute Nougat",
            "brd": "Kingswag Jeptha Speedeey Tactile Ellasina Fondant Canklez Figo Ohhkay Tiina Powerade Smoflows",
            "war": "Ffezzik Tusked Slopper Kingfrost Matera Sauceress Plashcan Bagheera",
            "rng": "Scaryteri Bumperking Nockedn Twunkinthejunk Scarysteve Twosheds Loglizard Mylittlestump Virri Trackingyay Touchmybraces",
            "nec": "Kingnecro Nearcyde Deadfredd Angostura Necroking Kbon Brug Walki Icedmfwell",
            "dru": "Sowr Laalo Smoflow",
            "mnk": "Effdee Floppers Kingfu Giestt Scrowty",
            "pal": "Morzak Kingkazon Jehan",
            "shm": "Mmow Petete Scourge Kslo Shammblez"
        }

        for class_name, names in bot_lists.items():
            for name in names.split():
                default_text.append(f"{name},{class_name},true")

        self.text_edit.setText("\n".join(sorted(default_text)))

    def get_updated_bots(self):
        """Parse text content and return updated bot dictionary"""
        updated = {}
        text = self.text_edit.toPlainText()

        for line in text.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):  # Skip empty lines and comments
                continue

            parts = line.split(',')
            if len(parts) >= 3:
                bot_name = parts[0].strip()
                class_name = parts[1].strip()
                enabled_str = parts[2].strip().lower()

                # Validate enabled status
                enabled = enabled_str == 'true'

                updated[bot_name] = (class_name, enabled)

        return updated