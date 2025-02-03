import sys
import os
import configparser
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QLineEdit, QLabel, QPushButton, QMessageBox
)
from PyQt5 import QtCore, QtGui, QtWidgets
#CONST DEFINATION
WEAPON_TYPE={"1hs":0,
            "1hb":1,
            "1hp":2,
            "2hs":3,
            "2hb":4,
            "2hp":5,
            "h2h":6,
            "shield":7,
}

class Weapon:
    def __init__(self):
        self.weaponName = ""
        self.weaponAlias = []
        self.damage = 0
        self.delay = 0
        self.type = ""
        self.damageBonus = 0
        self.procAgro = 0
        self.procResistMsg = ""
        self.procLandMsg = ""
        self.currentWeaponType=""


class WeaponEditor(QWidget):
    def __init__(self,):
        super().__init__()
        self.weaponDict = {}
        self.initUI()
        self.loadWeaponsFromFile()
        self.callbackToMain=None

    def initUI(self):
        self.setWindowTitle("Weapon Editor")
        self.setGeometry(100, 100, 800, 600)

        # 主布局
        main_layout = QHBoxLayout()

        # 左侧：武器列表
        self.weapon_list = QListWidget()
        self.weapon_list.itemClicked.connect(self.onWeaponSelected)
        main_layout.addWidget(self.weapon_list)

        # 右侧：武器属性编辑区域
        right_layout = QVBoxLayout()

        # 武器名称
        self.name_label = QLabel("Weapon Name:")
        self.name_input = QLineEdit()
        right_layout.addWidget(self.name_label)
        right_layout.addWidget(self.name_input)

        # 武器别名
        self.alias_label = QLabel("Weapon Aliases (comma separated):")
        self.alias_input = QLineEdit()
        right_layout.addWidget(self.alias_label)
        right_layout.addWidget(self.alias_input)

        # 武器伤害
        self.damage_label = QLabel("Damage:")
        self.damage_input = QLineEdit()
        right_layout.addWidget(self.damage_label)
        right_layout.addWidget(self.damage_input)

        # 武器延迟
        self.delay_label = QLabel("Delay:")
        self.delay_input = QLineEdit()
        right_layout.addWidget(self.delay_label)
        right_layout.addWidget(self.delay_input)

        # 武器类型
        self.type_label = QLabel("Type (e.g., 1hs, 1hb, 2hs, etc.):")
        right_layout.addWidget(self.type_label)

        self.type_input = QtWidgets.QComboBox(self)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.type_input.setFont(font)
        self.type_input.setObjectName("type_input")
        self.type_input.addItem("")
        self.type_input.addItem("")
        self.type_input.addItem("")
        self.type_input.addItem("")
        self.type_input.addItem("")
        self.type_input.addItem("")
        self.type_input.addItem("")
        self.type_input.addItem("")
        self.type_input.raise_()
        self.type_input.currentIndexChanged['QString'].connect(self.weaponTypeSelect)
        self.type_input.setItemText(0, "1hs")
        self.type_input.setItemText(1, "1hb")
        self.type_input.setItemText(2, "1hp")
        self.type_input.setItemText(3, "2hs")
        self.type_input.setItemText(4, "2hb")
        self.type_input.setItemText(5, "2hp")
        self.type_input.setItemText(6, "h2h")
        self.type_input.setItemText(7, "shield")
        right_layout.addWidget(self.type_input)


        # 伤害加成
        self.damage_bonus_label = QLabel("Damage Bonus:")
        self.damage_bonus_input = QLineEdit()
        right_layout.addWidget(self.damage_bonus_label)
        right_layout.addWidget(self.damage_bonus_input)

        # Proc Agro
        self.proc_agro_label = QLabel("Proc Agro:")
        self.proc_agro_input = QLineEdit()
        right_layout.addWidget(self.proc_agro_label)
        right_layout.addWidget(self.proc_agro_input)

        # Proc Resist Message
        self.proc_resist_msg_label = QLabel("Proc Resist Message:")
        self.proc_resist_msg_input = QLineEdit()
        right_layout.addWidget(self.proc_resist_msg_label)
        right_layout.addWidget(self.proc_resist_msg_input)

        # Proc Land Message
        self.proc_land_msg_label = QLabel("Proc Land Message:")
        self.proc_land_msg_input = QLineEdit()
        right_layout.addWidget(self.proc_land_msg_label)
        right_layout.addWidget(self.proc_land_msg_input)

        # 添加/更新按钮
        self.add_button = QPushButton("Add/Update Weapon")
        self.add_button.clicked.connect(self.addOrUpdateWeapon)
        right_layout.addWidget(self.add_button)

        # 删除按钮
        self.del_button = QPushButton("Delete Weapon")
        self.del_button.clicked.connect(self.deleteWeapon)
        right_layout.addWidget(self.del_button)


        # 清空按钮
        self.clear_button = QPushButton("Clear Fields")
        self.clear_button.clicked.connect(self.clearFields)
        right_layout.addWidget(self.clear_button)

        main_layout.addLayout(right_layout)
        self.setLayout(main_layout)

    def closeEvent(self,event):

        event.ignore()
        self.hide()
        self.callbackToMain.weaponEditeComplete()


    def loadWeaponsFromFile(self):
        """从 weapons.ini 文件中加载武器列表"""
        config = configparser.ConfigParser()
        if not os.path.exists('Weapons.ini'):
            return

        config.read('Weapons.ini')

        for section_name in config.sections():
            weapon = Weapon()
            weapon.weaponName = config[section_name]['weaponName']
            weapon.weaponAlias = config[section_name]['weaponAlias'].split(',')
            weapon.damage = int(config[section_name]['damage'])
            weapon.delay = int(config[section_name]['delay'])
            weapon.type = config[section_name]['type']
            weapon.damageBonus = int(config[section_name]['damageBonus'])
            weapon.procAgro = int(config[section_name]['procAgro'])
            weapon.procResistMsg = config[section_name]['procResistMsg']
            weapon.procLandMsg = config[section_name]['procLandMsg']

            self.weaponDict[weapon.weaponName] = weapon

        self.updateWeaponList()

    def updateWeaponList(self):
        """更新武器列表显示"""
        self.weapon_list.clear()
        for weapon_name in self.weaponDict.keys():
            self.weapon_list.addItem(weapon_name)

    def onWeaponSelected(self, item):
        """当选择武器时，填充表单"""
        weapon_name = item.text()
        weapon = self.weaponDict[weapon_name]

        self.name_input.setText(weapon.weaponName)
        self.alias_input.setText(','.join(weapon.weaponAlias))
        self.damage_input.setText(str(weapon.damage))
        self.delay_input.setText(str(weapon.delay))
        self.type_input.setCurrentIndex(WEAPON_TYPE[weapon.type])
        self.damage_bonus_input.setText(str(weapon.damageBonus))
        self.proc_agro_input.setText(str(weapon.procAgro))
        self.proc_resist_msg_input.setText(weapon.procResistMsg)
        self.proc_land_msg_input.setText(weapon.procLandMsg)

    def deleteWeapon(self):
        weapon_name = self.name_input.text().strip()
        if not weapon_name:
            QMessageBox.warning(self, "Error", "Weapon name cannot be empty!")
            return
        if not weapon_name in self.weaponDict:
            self.clearFields()
            return
        self.weaponDict.pop(weapon_name)
        self.updateWeaponList()
        self.saveWeaponsToFile()
        self.clearFields()
        QMessageBox.information(self, "Success", "Weapon deleted successfully!")


    def addOrUpdateWeapon(self):
        """添加或更新武器"""
        weapon_name = self.name_input.text().strip()
        if not weapon_name:
            QMessageBox.warning(self, "Error", "Weapon name cannot be empty!")
            return

        weapon = Weapon()
        weapon.weaponName = weapon_name
        weapon.weaponAlias = self.alias_input.text().strip().split(',')

        damagestr=self.damage_input.text().strip()
        if damagestr!="":
            weapon.damage = int(damagestr)
        else:
            weapon.damage = 0

        delaystr=self.delay_input.text().strip()
        if delaystr!="":
            weapon.delay = int(delaystr)
        else:
            weapon.delay = 0

        weapon.type = self.type_input.currentText()

        dbstr=self.damage_bonus_input.text().strip()
        if dbstr!="":
            weapon.damageBonus = int(dbstr)
        else:
            weapon.damageBonus = 0

        pastr=self.proc_agro_input.text().strip()
        if pastr!="":
            weapon.procAgro = int(pastr)
        else:
            weapon.procAgro = 0


        weapon.procResistMsg = self.proc_resist_msg_input.text().strip()
        weapon.procLandMsg = self.proc_land_msg_input.text().strip()

        self.weaponDict[weapon_name] = weapon
        self.updateWeaponList()
        self.saveWeaponsToFile()
        QMessageBox.information(self, "Success", "Weapon saved successfully!")

    def weaponTypeSelect(self):

        self.currentWeaponType=self.type_input.currentText()

    def saveWeaponsToFile(self):
        """将武器保存到 weapons.ini 文件"""
        config = configparser.ConfigParser()

        for weapon_name, weapon in self.weaponDict.items():
            if weapon_name =="???" or weapon_name == "N/A":
                continue

            section_name = weapon_name
            config[section_name] = {
                'weaponName': weapon.weaponName,
                'weaponAlias': ','.join(weapon.weaponAlias),
                'damage': str(weapon.damage),
                'delay': str(weapon.delay),
                'type': weapon.type,
                'damageBonus': str(weapon.damageBonus),
                'procAgro': str(weapon.procAgro),
                'procResistMsg': weapon.procResistMsg,
                'procLandMsg': weapon.procLandMsg
            }

        with open('weapons.ini', 'w') as configfile:
            config.write(configfile)

    def clearFields(self):
        """清空表单"""
        self.name_input.clear()
        self.alias_input.clear()
        self.damage_input.clear()
        self.delay_input.clear()
        #self.type_input.clear()
        self.damage_bonus_input.clear()
        self.proc_agro_input.clear()
        self.proc_resist_msg_input.clear()
        self.proc_land_msg_input.clear()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WeaponEditor()
    window.show()
    sys.exit(app.exec_())