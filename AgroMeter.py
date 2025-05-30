import re
import sys
import os
import time
import datetime
import configparser
from NetworkThread import *

from PyQt5.Qt import *
from PyQt5.QtCore import QTimer, QDateTime
from PyQt5 import QtCore, QtGui, QtWidgets

#globe definition
#hit type const
HIT=0
SLASH=1
CRUSH=2
PIERCE=3
PUNCH=4
KICK=5

WEAPON_TRANSLATION={"1hs":SLASH,
            "1hb":CRUSH,
            "1hp":PIERCE,
            "2hs":SLASH,
            "2hb":CRUSH,
            "2hp":PIERCE,
            "h2h":PUNCH,
            "shield":7,
}


#main hand vs off hand swing rate const
MAIN_HAND_RATE=0.55
OFF_HAND_RATE=1-MAIN_HAND_RATE
#Imaj's server
AM_SERVER="44.213.107.109"
AM_PORT=12345
#Heart beat to server.
HEART_BEAT=300

class AgroTable:
    def __init__(self):
        self.mobName=""
        self.MHSwing=0
        self.OHSwing=0
        self.TiedSwing=0
        self.ProcCount=0
        self.TotalAgro=0.0
        self.threatList=[]
        self.engageTime=time.time()
        self.lastSeenTime=self.engageTime

class Weapon:
    def __init__(self):
        self.weaponName=""
        self.weaponAlias=[str]
        self.damage=0
        self.delay=0
        self.type="" #???/1hs/1hp/1hb/2hs/2hb/2hp/h2h/shield
        self.damageBonus=0
        self.procAgro=0
        self.procResistMsg=""
        self.procLandMsg=""
        self.procDirectDamage = 0          # 默认值0
        self.procCanAlwaysTakeHold = True  # 默认值True

class AgroMeter(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.width = 0
        self.height= 0
        self.widthMargin=2
        self.heigthMargin=2
        self.yourName = ""
        self.MHWeapon = "???"                       #Need save and load this config
        self.OHWeapon = "???"                       #Need save and load this config
        self.isHide=True
        self.isNetMeterHide = True
        self.weaponDict = {}
        self.agroTableDict={}                      #Key domain mobName:str Value:AgroTable instance
        self.currentTarget=""
        self.currentMHProcLandMessage=""
        self.currentOHProcLandMessage = ""
        self.cleansingTimerExpired=False
        self.cleansingNetDataTimerExpired=False
        self.agroTableExpireDuration=0

        self.anyNewActionDetected = False
        self.newNetFlowDetected = False
        self.basicMHFireRate = MAIN_HAND_RATE      #default rate if mh delay == oh delay
        self.basicOHFireRate = OFF_HAND_RATE
        self.realMHFireRate = 0.55                 #doesn't matter much since this will be loaded from configuration file
        self.realOHFireRate = 0.45
        self.isCastingTotem = False
        self.isCastingBioOrb = False
        self.isCastingFlameLick = False
        self.isCastingEnvelopingRoots = False
        self.isCastingJolt = False
        self.isCastingCinderJolt = False
        self.lastFlameLickCastingStartTime = datetime.datetime.now()
        self.lastEnvelopingRootsCastingStartTime = datetime.datetime.now()
        self.lastJoltCastingStartTime = datetime.datetime.now()
        self.lastCinderJoltCastingStartTime = datetime.datetime.now()
        self.lastBioOrbCastingStartTime = datetime.datetime.now()
        self.latencyTolerance = 100   #default latency tolerance is 100ms
        self.agroToUnknownTarget=0
        self.lastNonMeleeDamage = 0
        self.lastNonMeleeDamageLine = 0
        self.currentTargetTotalAgroSnapshot = 0
        self.lastLogline = ""
        self.checkNextFewLinesforMHProc = False
        self.blockSequenceNumberToCheck = 0

        self.isOnlineSyncEnabled = False
        self.isCheckingAggroUpdate = False
        self.network_thread = None
        self.last_clear_time = 0
        self.threat_data = {}  # 存储网络仇恨数据 {mob_name: aggro_table}
        self.hasNetworkData = False
        self.lastUpdatedMob = ""
        self.ifShowEqualDBGBEnabled = False
        self.ifShowEqualSlowEnabled = False
        self.ifShowTankDiscEnabled = False

        self.funcCalculateSwingAgro={
            ("???", "???"): self.viewer_mode,

            ("???", "1hs"): self.combo_default,
            ("???", "1hp"): self.combo_default,
            ("???", "1hb"): self.combo_default,
            ("???", "2hs"): self.combo_default,
            ("???", "2hb"): self.combo_default,
            ("???", "2hp"): self.combo_default,
            ("???", "h2h"): self.combo_default,
            ("???", "shield"): self.combo_default,
            ("1hs", "???"): self.combo_default,
            ("1hp", "???"): self.combo_default,
            ("1hb", "???"): self.combo_default,
            ("2hs", "???"): self.combo_default,
            ("2hb", "???"): self.combo_default,
            ("2hp", "???"): self.combo_default,
            ("h2h", "???"): self.combo_default,
            ("shield", "???"): self.combo_default,
            ("1hs", "N/A"): self.combo_default,
            ("1hp", "N/A"): self.combo_default,
            ("1hb", "N/A"): self.combo_default,
            ("h2h", "N/A"): self.combo_default,
            ("shield", "N/A"): self.combo_default,

            ("1hs", "1hs"): self.combo_1hs_1hs,
            ("1hs", "shield"): self.combo_1hs_shield,
            ("1hs", "1hp"): self.combo_1hs_1hp,
            ("1hs", "1hb"): self.combo_1hs_1hb,
            ("1hs", "h2h"): self.combo_1hs_h2h,
            ("1hs", "2hs"): self.combo_default,
            ("1hs", "2hp"): self.combo_default,
            ("1hs", "2hb"): self.combo_default,

            ("1hp", "1hs"): self.combo_1hp_1hs,
            ("1hp", "1hp"): self.combo_1hp_1hp,
            ("1hp", "shield"): self.combo_1hp_shield,
            ("1hp", "1hb"): self.combo_1hp_1hb,
            ("1hp", "h2h"): self.combo_1hp_h2h,
            ("1hp", "2hs"): self.combo_default,
            ("1hp", "2hp"): self.combo_default,
            ("1hp", "2hb"): self.combo_default,

            ("1hb", "1hs"): self.combo_1hb_1hs,
            ("1hb", "1hp"): self.combo_1hb_1hp,
            ("1hb", "1hb"): self.combo_1hb_1hb,
            ("1hb", "shield"): self.combo_1hb_shield,
            ("1hb", "h2h"): self.combo_1hb_h2h,
            ("1hb", "2hs"): self.combo_default,
            ("1hb", "2hp"): self.combo_default,
            ("1hb", "2hb"): self.combo_default,

            ("h2h", "1hs"): self.combo_h2h_1hs,
            ("h2h", "1hp"): self.combo_h2h_1hp,
            ("h2h", "1hb"): self.combo_h2h_1hb,
            ("h2h", "h2h"): self.combo_h2h_h2h,
            ("h2h", "shield"): self.combo_h2h_shield,
            ("h2h", "2hs"): self.combo_default,
            ("h2h", "2hp"): self.combo_default,
            ("h2h", "2hb"): self.combo_default,

            ("shield", "1hs"): self.combo_default,
            ("shield", "1hp"): self.combo_default,
            ("shield", "1hb"): self.combo_default,
            ("shield", "h2h"): self.combo_default,
            ("shield", "shield"): self.combo_default,
            ("shield", "2hs"): self.combo_default,
            ("shield", "2hp"): self.combo_default,
            ("shield", "2hb"): self.combo_default,

            ("2hs", "N/A"): self.combo_2hs_NA,
            ("2hp", "N/A"): self.combo_2hp_NA,
            ("2hb", "N/A"): self.combo_2hb_NA,

            ("2hs", "1hs"): self.combo_default,
            ("2hs", "1hp"): self.combo_default,
            ("2hs", "1hb"): self.combo_default,
            ("2hs", "h2h"): self.combo_default,
            ("2hs", "shield"): self.combo_default,
            ("2hs", "2hs"): self.combo_default,
            ("2hs", "2hp"): self.combo_default,
            ("2hs", "2hb"): self.combo_default,

            ("2hp", "1hs"): self.combo_default,
            ("2hp", "1hp"): self.combo_default,
            ("2hp", "1hb"): self.combo_default,
            ("2hp", "h2h"): self.combo_default,
            ("2hp", "shield"): self.combo_default,
            ("2hp", "2hs"): self.combo_default,
            ("2hp", "2hp"): self.combo_default,
            ("2hp", "2hb"): self.combo_default,

            ("2hb", "1hs"): self.combo_default,
            ("2hb", "1hp"): self.combo_default,
            ("2hb", "1hb"): self.combo_default,
            ("2hb", "h2h"): self.combo_default,
            ("2hb", "shield"): self.combo_default,
            ("2hb", "2hs"): self.combo_default,
            ("2hb", "2hp"): self.combo_default,
            ("2hb", "2hb"): self.combo_default,


        }



        #test example of Agro table
        self.test_at=AgroTable()
        self.test_at.TotalAgro = 460
        self.test_at.MHSwing = 40
        self.test_at.OHSwing = 22
        self.test_at.ProcCount = 1
        self.test_at.mobName = "TEST Mob"
        self.test_at.engageTIme=time.time()
        self.test_timer = QTimer(self)
        self.test_timer.timeout.connect(self.testAgroMeterHandler)



        self.initializeWeaponBase()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Real Time Aggro Meter')
        #self.setStyleSheet('background: black;')
        #self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Tool)
        #self.setAttribute(QtCore.Qt.WA_TranslucentBackground)  # 设置窗口背景透明
        #self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)  # 永远最前，无边框标题栏，去任务栏标签

        #Qobject.setAttribute(QtCore.Qt.WA_TranslucentBackground) # 设置窗口背景透明
        #Qobject.setAutoFillBackground(True)
        #Qobject.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)  # 永远最前，无边框标题栏，去任务栏标签
        #Qobject.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents) #窗口点击而过，不响应鼠标（貌似无效）。


        self.label_agroMeterYellow=QtWidgets.QLabel()
        self.label_agroMeterYellow.resize(200,45)
        #self.label_agroMeterYellow.setWordWrap(True)
        self.label_agroMeterYellow.setAttribute(QtCore.Qt.WA_TranslucentBackground)  # 设置窗口背景透明
        self.label_agroMeterYellow.setAutoFillBackground(True)
        self.label_agroMeterYellow.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool) # 永远最前，无边框标题栏，去任务栏标签
        self.label_agroMeterYellow.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents) #窗口点击而过，不响应鼠标（貌似无效）
        self.label_agroMeterYellow.setStyleSheet('color: lightgreen;')           #was yellow but too hard to see in bright environment.

        self.label_agroMeterGreen = QtWidgets.QLabel()
        self.label_agroMeterGreen.resize(200,120)
        #self.label_agroMeterGreen.setWordWrap(True)
        self.label_agroMeterGreen.setAttribute(QtCore.Qt.WA_TranslucentBackground)  # 设置窗口背景透明
        self.label_agroMeterGreen.setAutoFillBackground(True)
        self.label_agroMeterGreen.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool) # 永远最前，无边框标题栏，去任务栏标签
        self.label_agroMeterGreen.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents) #窗口点击而过，不响应鼠标（貌似无效）
        self.label_agroMeterGreen.setStyleSheet('color: lightgreen;')

        self.label_errorMessage = QtWidgets.QLabel()
        self.label_errorMessage.resize(200,45)
        self.label_errorMessage.setWordWrap(True)
        self.label_errorMessage.setAttribute(QtCore.Qt.WA_TranslucentBackground)  # 设置窗口背景透明
        self.label_errorMessage.setAutoFillBackground(True)
        self.label_errorMessage.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool) # 永远最前，无边框标题栏，去任务栏标签
        self.label_errorMessage.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents) #窗口点击而过，不响应鼠标（貌似无效）
        self.label_errorMessage.setStyleSheet('color: red;')
        self.errorMessage_timer = QTimer(self)
        self.errorMessage_timer.timeout.connect(self.label_errorMessage.hide)

        self.window_network = QWidget()
        self.window_network.setWindowTitle("Online Aggro Meter")
        self.window_network.hide()
        self.label_network = QtWidgets.QLabel()  # 新增用于显示网络仇恨的组件
        self.label_network.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.label_network.setAutoFillBackground(True)
        self.label_network.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.label_network.setStyleSheet('color: cyan;')
        self.label_network.resize(400, 300)
        self.label_network.hide()



    def reAdjustPanel(self):
        self.posx = self.geometry().getRect()[0]
        self.posy = self.geometry().getRect()[1]
        self.width = self.geometry().getRect()[2]
        self.height=self.geometry().getRect()[3]
        self.label_agroMeterYellow.move(self.posx,self.posy)
        self.label_agroMeterYellow.resize(self.width,60)
        self.label_agroMeterGreen.move(self.posx,self.posy+20)
        self.label_agroMeterGreen.resize(self.width,120)
        self.label_errorMessage.move(self.posx,self.posy-45)
        self.label_errorMessage.resize(self.width,45)

        self.network_posx = self.window_network.geometry().getRect()[0]
        self.network_posy = self.window_network.geometry().getRect()[1]
        self.network_width = self.window_network.geometry().getRect()[2]
        self.network_height = self.window_network.geometry().getRect()[3]
        self.label_network.move(self.network_posx, self.network_posy)
        self.label_network.resize(self.network_width, self.network_height)


    def initializeWeaponBase(self):

        self.weaponDict.clear()
        #Following are system predefined weapons. If Weapons.ini doesn't exists, these will be used and
        #saved to weapons.ini ,which file will be created as needed too.
        defaultWeapon=Weapon()           #default weapon is ???
        defaultWeapon.weaponName="???"
        defaultWeapon.weaponAlias=[]
        defaultWeapon.type="???"
        defaultWeapon.procLandMsg=""
        defaultWeapon.procResistMsg=""
        self.weaponDict[defaultWeapon.weaponName]=defaultWeapon

        weapon=Weapon()                  #offhand weapon for 2hander in main hand
        weapon.weaponName="N/A"
        weapon.weaponAlias=[]
        weapon.type="N/A"
        weapon.procLandMsg=""
        weapon.procResistMsg=""
        self.weaponDict[weapon.weaponName]=weapon


        weapon=Weapon()           #default  h2h for all races except monk
        weapon.weaponName="Hand_to_hand"
        weapon.weaponAlias=["h2h","hand","hands"]
        weapon.damage=4
        weapon.delay=36
        weapon.type="h2h"
        weapon.procLandMsg=""
        weapon.procResistMsg=""
        self.weaponDict[weapon.weaponName]=weapon

        weapon=Weapon()           #monk epic h2h fist
        weapon.weaponName="Monk_Epic_Fist"
        weapon.weaponAlias=["monkfist","epicfist","monkepic"]
        weapon.damage=9
        weapon.delay=16
        weapon.type="h2h"
        weapon.procLandMsg=""
        weapon.procResistMsg=""
        self.weaponDict[weapon.weaponName]=weapon

        weapon=Weapon()
        weapon.weaponName="Blade_of_Strategy"
        weapon.weaponAlias=["red","redblade","redepic"]
        weapon.damage=14
        weapon.delay=24
        weapon.type="1hs"
        weapon.procAgro=600
        weapon.procLandMsg="Someone is weakened by the Rage of Vallon."
        weapon.procResistMsg="Your target resisted the Rage of Vallon"
        weapon.procDirectDamage = 100
        weapon.procCanAlwaysTakeHold = True
        self.weaponDict[weapon.weaponName]=weapon

        weapon=Weapon()
        weapon.weaponName="Howling_Cutlass"
        weapon.weaponAlias=["hc","howlingcutlass","cutlass"]
        weapon.damage=10
        weapon.delay=19
        weapon.type="1hs"
        weapon.procAgro=520
        weapon.procLandMsg="Someone is deafened."
        weapon.procResistMsg="Your target resisted the Shrieking Howl"
        weapon.procDirectDamage = 120
        weapon.procCanAlwaysTakeHold = True
        self.weaponDict[weapon.weaponName]=weapon

        weapon=Weapon()
        weapon.weaponName="Blade_of_Tactics"
        weapon.weaponAlias=["blue","blueblade","blueepic"]
        weapon.damage=14
        weapon.delay=24
        weapon.type="1hs"
        weapon.procLandMsg=""
        weapon.procResistMsg=""
        self.weaponDict[weapon.weaponName]=weapon

        weapon=Weapon()
        weapon.weaponName="Swiftblade_of_Zek"
        weapon.weaponAlias=["swiftblade","swift","sboz"]
        weapon.damage=11
        weapon.delay=18
        weapon.type="1hs"
        weapon.procLandMsg=""
        weapon.procResistMsg=""
        self.weaponDict[weapon.weaponName]=weapon

        weapon=Weapon()
        weapon.weaponName="Hammer_of_Battle"
        weapon.weaponAlias=["statuehammer","hammerofbattle","hob"]
        weapon.damage=17
        weapon.delay=25
        weapon.type="1hb"
        weapon.procLandMsg=""
        weapon.procResistMsg=""
        self.weaponDict[weapon.weaponName]=weapon

        weapon=Weapon()
        weapon.weaponName="Primal_Velium_Fist_Wraps"
        weapon.weaponAlias=["primalfist","pvfw","pf"]
        weapon.damage=15
        weapon.delay=20
        weapon.type="1hb"
        weapon.procLandMsg=""
        weapon.procResistMsg=""
        self.weaponDict[weapon.weaponName]=weapon

        weapon=Weapon()
        weapon.weaponName="Whitestone_Shield"
        weapon.weaponAlias=["whitestone","shield","wss"]
        weapon.damage=0
        weapon.delay=10000
        weapon.type="shield"
        weapon.procLandMsg=""
        weapon.procResistMsg=""
        self.weaponDict[weapon.weaponName]=weapon

        weapon=Weapon()
        weapon.weaponName="Jagged_Blade_of_War"
        weapon.weaponAlias=["2hepic","redblue","jbow"]
        weapon.damage=36
        weapon.delay=41
        weapon.type="2hs"
        weapon.damageBonus=70-36
        weapon.procAgro=675
        weapon.procLandMsg="Someone's soul is consumed by the fury of Zek."
        weapon.procResistMsg="Your target resisted the Rage of Zek"
        weapon.procDirectDamage = 175
        weapon.procCanAlwaysTakeHold = True
        self.weaponDict[weapon.weaponName]=weapon

        weapon=Weapon()
        weapon.weaponName="Primal_Velium_Claidhmore"
        weapon.weaponAlias=["2hsprimal","primal2hs","pvc"]
        weapon.damage=45
        weapon.delay=44
        weapon.type="2hs"
        weapon.damageBonus=82-45
        weapon.procLandMsg=""
        weapon.procResistMsg=""
        self.weaponDict[weapon.weaponName]=weapon

        #end of predefination. start to load Weapons.ini

        self.loadWeaponsFromFile()
        if self.MHWeapon not in self.weaponDict:
            self.MHWeapon="???"
        if self.OHWeapon not in self.weaponDict:
            self.OHWeapon="???"


    def saveWeaponsToFile(self):
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
                'procLandMsg': weapon.procLandMsg,
                'procDirectDamage': str(weapon.procDirectDamage),
                'procCanAlwaysTakeHold': str(weapon.procCanAlwaysTakeHold)
            }

        with open('Weapons.ini', 'w') as configfile:
            config.write(configfile)

    def loadWeaponsFromFile(self):
        config = configparser.ConfigParser()
        if not os.path.exists('Weapons.ini'):
            self.saveWeaponsToFile()
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

            # 处理新增字段（兼容旧版本）
            try:
                weapon.procDirectDamage = int(config[section_name]['procDirectDamage'])
            except (configparser.NoOptionError, KeyError):
                weapon.procDirectDamage = 0  # 旧版本默认0

            try:
                weapon.procCanAlwaysTakeHold = config.getboolean(section_name, 'procCanAlwaysTakeHold')
            except (configparser.NoOptionError, KeyError):
                weapon.procCanAlwaysTakeHold = True  # 旧版本默认True

            self.weaponDict[weapon.weaponName] = weapon

    def addNewWeapon(self, weapon_name, weapon_alias, damage, delay, weapon_type, damage_bonus=0, proc_agro=0,
                     proc_resist_msg="", proc_land_msg=""):
        weapon = Weapon()
        weapon.weaponName = weapon_name
        weapon.weaponAlias = weapon_alias
        weapon.damage = damage
        weapon.delay = delay
        weapon.type = weapon_type
        weapon.damageBonus = damage_bonus
        weapon.procAgro = proc_agro
        weapon.procResistMsg = proc_resist_msg
        weapon.procLandMsg = proc_land_msg

        self.weaponDict[weapon_name] = weapon
        self.saveWeaponsToFile()  # 保存到配置文件

    def UpdateMHWeapons(self,MHWeaponName:str):

        if MHWeaponName == "???":
            self.MHWeapon = "???"
            self.OHWeapon = "???"
            return True

        for weaponName in self.weaponDict.keys():
            if MHWeaponName==self.weaponDict[weaponName].weaponName:
                self.MHWeapon=self.weaponDict[weaponName].weaponName
                self.recompileProcLandMsg(self.currentTarget)
                if self.weaponDict[weaponName].type =="2hs" or self.weaponDict[weaponName].type =="2hp" or self.weaponDict[weaponName].type =="2hb":
                    self.OHWeapon="N/A"
                    #self.setup2HanderDamageBonus()
                else:
                    self.setup1hWeaponFireRate()

                return True
            for wa in self.weaponDict[weaponName].weaponAlias:
                if MHWeaponName==wa:
                    self.MHWeapon = self.weaponDict[weaponName].weaponName
                    self.recompileProcLandMsg(self.currentTarget)
                    if self.weaponDict[weaponName].type == "2hs" or self.weaponDict[weaponName].type == "2hp" or \
                            self.weaponDict[weaponName].type == "2hb":
                        self.OHWeapon = "N/A"
                        #self.setup2HanderDamageBonus()
                    else:
                        self.setup1hWeaponFireRate()

                    return True
        self.MHWeapon="???"
        return False

    def UpdateOHWeapons(self,OHWeaponName:str):

        if OHWeaponName == "???":
            self.MHWeapon = "???"
            self.OHWeapon = "???"
            return True


        for weaponName in self.weaponDict.keys():
            if OHWeaponName==self.weaponDict[weaponName].weaponName:
                #off hand can not be 2hander.
                if self.weaponDict[weaponName].type =="2hs" or self.weaponDict[weaponName].type =="2hp" or self.weaponDict[weaponName].type =="2hb":
                    self.OHWeapon = "???"
                    return False
                self.OHWeapon=self.weaponDict[weaponName].weaponName
                self.recompileProcLandMsg(self.currentTarget)

                self.setup1hWeaponFireRate()
                return True
            for wa in self.weaponDict[weaponName].weaponAlias:
                if OHWeaponName==wa:
                    # off hand can not be 2hander.
                    if self.weaponDict[weaponName].type == "2hs" or self.weaponDict[weaponName].type == "2hp" or \
                            self.weaponDict[weaponName].type == "2hb":
                        self.OHWeapon = "???"
                        return False
                    self.OHWeapon = self.weaponDict[weaponName].weaponName
                    self.recompileProcLandMsg(self.currentTarget)

                    self.setup1hWeaponFireRate()
                    return True
        self.OHWeapon="???"
        return False

    def setup2HanderDamageBonus(self):

        #The formula below was from the post https://www.project1999.com/forums/showthread.php?t=79696
        #But after test, these are totally inaccurate. for example 2h epic is 70 per swing, 2hs primal is 82
        #So this function left unused here to be find out what's the real machenic is.
        if self.weaponDict[self.MHWeapon].delay <= 27:
            self.weaponDict[self.MHWeapon].damageBonus=(60 - 22) / 3 # Just 1h bonus + 1.
            return

        base=int((60 - 25) / 2)

        if self.weaponDict[self.MHWeapon].delay <= 39:
            self.weaponDict[self.MHWeapon].damageBonus = base
            return

        if self.weaponDict[self.MHWeapon].delay <= 42:
            self.weaponDict[self.MHWeapon].damageBonus = base+1
            return

        if self.weaponDict[self.MHWeapon].delay <= 44:
            self.weaponDict[self.MHWeapon].damageBonus = base+3
            return

        self.weaponDict[self.MHWeapon].damageBonus = int(base+(self.weaponDict[self.MHWeapon].delay-31)/3)


    def setup1hWeaponFireRate(self):
        if self.MHWeapon=="???" or self.OHWeapon=="???" or self.OHWeapon=="N/A":
            return
        # using Warrior's formula here from https://wiki.project1999.com/Dual_Wield , also tested on 2025-1-30 , it's like 41% are from off hand swing.

        if self.weaponDict[self.MHWeapon].type==self.weaponDict[self.OHWeapon].type:
            #self.realMHFireRate=self.basicMHFireRate/(self.weaponDict[self.MHWeapon].delay/self.weaponDict[self.OHWeapon].delay*self.basicOHFireRate+self.basicMHFireRate)
            self.realMHFireRate = self.basicMHFireRate           #after test to test , this rate seems irrelavant to haste status on player. guess it's a static rate of MH swing:OH swing
            self.realOHFireRate = 1-self.realMHFireRate
        #print(f'real mh={self.realMHFireRate:0.3f},real oh={self.realOHFireRate:0.3f}')

    def logProcessor(self,line:str,blockSequenceNumber:int):

        if self.checkNextFewLinesforMHProc:
            if blockSequenceNumber - self.blockSequenceNumberToCheck <= 5 :  #wait 50ms to see if any self melee happens.
                hitType, target = self.checkHitTypeAndTarget(line)
                if hitType == WEAPON_TRANSLATION[self.weaponDict[self.MHWeapon].type]:  # If hit type matches
                    self.setCurrentTarget(target)
                    self.agroTableDict[self.currentTarget].ProcCount += 1
                    self.agroTableDict[self.currentTarget].TotalAgro += self.weaponDict[self.MHWeapon].procAgro
                    self.updateAgroMeter()
                    self.checkNextFewLinesforMHProc = False
            else:
                self.checkNextFewLinesforMHProc = False


        self.currentLineProcessor(line,blockSequenceNumber)
        #self.logErrorMessage(f"Block:{blockSequenceNumber},Line:{line}","info")
        self.lastLogline=line

    def currentLineProcessor(self,line:str,blockSequenceNumber:int):

        self.cleansingAgroTableDict()

        if self.checkWeaponSwing(line)==True:
            return

        if self.checkProcEffects(line,blockSequenceNumber)==True:
            return

        if line[26:]==" Your spell is interrupted.\n":                    #spell interruption

            self.anyNewActionDetected = True
            self.isCastingTotem = False
            self.isCastingBioOrb = False
            self.isCastingFlameLick = False
            self.isCastingEnvelopingRoots = False
            self.isCastingJolt = False
            self.isCastingCinderJolt = False

            return

        if self.checkClickyEffects(line)==True:
            return

        if self.checkRangerSpellEffects(line) == True:
            return

        if self.checkSkillEffects(line)==True:
            return

        if self.checkDiscStatus(line) == True:
            return


        #if self.checkAnySeenMobs(line)==True:  #not very needed as for now. skipped
        #    return

        if self.checkAndSetCurrentTarget(line)==True:
            return

        if line[26:42]==" You have slain " :          #your target perished
            mobName=line[42:-2]
            mobName=mobName[0].upper() + mobName[1:]
            if self.agroTableDict.get(mobName)!=None:
                message=f"Mob:{mobName}|Agro total:{self.agroTableDict[mobName].TotalAgro/1000:0.1f}k|Proc count:{self.agroTableDict[mobName].ProcCount}"
                duration = time.time() - self.agroTableDict[mobName].engageTime
                tpm = self.agroTableDict[mobName].TotalAgro / (duration + 1) * 60
                if tpm < 1000:
                    message += "|Threat/min : {:0.0f}".format(tpm)
                else:
                    message += "|Threat/min : {:0.1f}k".format(tpm / 1000)
                message += f"|Main hand:{self.MHWeapon}|Off hand:{self.OHWeapon}"
                self.logErrorMessage(message,"info")
                self.agroTableDict.pop(mobName)
                self.send_mob_slain(mobName)
            return


        index = line.find(" has been slain by ")      #mob got slain.
        if index !=-1:
            mobName=line[27:index]
            mobName=mobName[0].upper() + mobName[1:]
            if self.agroTableDict.get(mobName)==None:
                return
            if self.currentTarget!=mobName:
                self.agroTableDict.pop(mobName)
                self.send_mob_slain(mobName)
                return
            message=f"Mob:{mobName}|Agro total:{self.agroTableDict[mobName].TotalAgro/1000:0.1f}k|Proc count:{self.agroTableDict[mobName].ProcCount}"
            duration = time.time() - self.agroTableDict[mobName].engageTime
            tpm = self.agroTableDict[mobName].TotalAgro / (duration + 1) * 60
            if tpm < 1000:
                message += "|Threat/min : {:0.0f}".format(tpm)
            else:
                message += "|Threat/min : {:0.1f}k".format(tpm / 1000)
            message += f"|Main hand:{self.MHWeapon}|Off hand:{self.OHWeapon}"
            self.logErrorMessage(message,"info")
            self.agroTableDict.pop(mobName)
            self.send_mob_slain(mobName)
            return


        if line[26:]==" LOADING, PLEASE WAIT...\n" :    #Player died or zoned.

            self.clearAgroTable()

            if not self.isHide:
                self.updateAgroMeter()

            return

        if line[26:]==" clearam is not online at this time.\n" or line[26:]==" clram is not online at this time.\n" :    #player input /t clearam in game.
            self.hideAgroMeter()
            self.clearAgroTable()
            return

        if line[26:]==" Welcome to EverQuest!\n" :    #Cycled back or swapped charactor.

            self.clearAgroTable()

            if not self.isHide:
                self.updateAgroMeter()

            return


        if line[26:30]==" mh=":                 #use /t mh=weaponname(or alias) to set current main hand weapon.
            tailIndex=line[30:].find(" is not online at this time.")
            if tailIndex!=-1:
                weapon=line[30:30+tailIndex]
                isKnownWeapon=self.UpdateMHWeapons(weapon)
                if not isKnownWeapon:
                    self.logErrorMessage(f"Error:Unknow main hand weapon of {weapon}","error")
                else:
                    self.logErrorMessage(f"Info:Main hand weapon set to {weapon} now","info")
                self.updateAgroMeter()
            return

        if line[26:30]==" oh=":                 #use /t oh=weaponname(or alias) to set current off hand weapon.
            tailIndex=line[30:].find(" is not online at this time.")
            if tailIndex!=-1:
                weapon=line[30:30+tailIndex]
                isKnownWeapon=self.UpdateOHWeapons(weapon)
                if not isKnownWeapon:
                    self.logErrorMessage(f"Error:Unknow off hand weapon of {weapon}","error")
                else:
                    self.logErrorMessage(f"Info:Off hand weapon set to {weapon} now","info")
                self.updateAgroMeter()
            return

    def clearAgroTable(self):
        self.agroTableDict.clear()
        self.currentTarget = ""
        self.anyNewActionDetected = False
        self.agroToUnknownTarget = 0

    def cleansingAgroTableDict(self):
        if self.cleansingTimerExpired:
            if len(self.agroTableDict)>1000:
                self.agroTableDict.clear()                 #if amount of items in agro table dictionary >1000 there maybe member leak happening. reset it allover.
                self.logErrorMessage("Error:Agro table dictionary overflew.","error")
            else:
                now=time.time()
                mobNames=list(self.agroTableDict.keys())
                for mobName in mobNames:
                    if now-self.agroTableDict[mobName].lastSeenTime>=self.agroTableExpireDuration*60:
                        message = f"Mob:{mobName}|Agro total:{self.agroTableDict[mobName].TotalAgro / 1000:0.1f}k|Proc count:{self.agroTableDict[mobName].ProcCount}"
                        duration = self.agroTableDict[mobName].lastSeenTime - self.agroTableDict[mobName].engageTime
                        tpm = self.agroTableDict[mobName].TotalAgro / (duration + 1) * 60
                        if tpm < 1000:
                            message += "|Threat/min : {:0.0f}".format(tpm)
                        else:
                            message += "|Threat/min : {:0.1f}k".format(tpm / 1000)
                        message += f"|Main hand:{self.MHWeapon}|Off hand:{self.OHWeapon}"
                        self.logErrorMessage(message, "info")
                        self.agroTableDict.pop(mobName)
            self.cleansingTimerExpired=False

    def cleansingNetworkAgroTableDict(self):
        if self.cleansingNetDataTimerExpired:
            if len(self.threat_data)>1000:
                self.threat_data.clear()                 #if amount of items in network agro table dictionary >1000 there maybe member leak happening. reset it allover.
                self.logErrorMessage("Error:Network Agro table dictionary overflew.","error")
            else:
                now=time.time()
                mobNames=list(self.threat_data.keys())
                for mobName in mobNames:
                    if now-self.threat_data[mobName].lastSeenTime>=120:        #2 minutes to expire
                        self.threat_data.pop(mobName)
            self.cleansingNetDataTimerExpired=False



    def cleansingTimerHandler(self):
        if not self.cleansingTimerExpired:
            self.cleansingTimerExpired=True
            self.cleansingNetDataTimerExpired=True


    def setupYourName(self,yourName:str):

        if self.isOnlineSyncEnabled:
           self.send_clear_all_aggro()

        self.yourName=yourName


    def onlineSyncHandler(self):


        if not self.isOnlineSyncEnabled:
            return

        if self.hasNetworkData == True:

            self.updateNetworkThreatDisplay()
            self.hasNetworkData = False


        if not self.yourName:
            return

        if not self.agroTableDict:
            current_time = time.time()
            if current_time - self.last_clear_time >= 29:  #send clear_all_aggro to server every 30s as a keep alive method.
                self.send_clear_all_aggro()
                self.last_clear_time = current_time
            return


        if self.isCheckingAggroUpdate:
            return
        self.isCheckingAggroUpdate = True

        sendCount=0
        mobNames = list(self.agroTableDict.keys())
        for mobName in mobNames:
            if self.agroTableDict[mobName].TotalAgro > 0.5:
                self.send_threat_data(self.yourName,mobName,int(self.agroTableDict[mobName].TotalAgro))
                sendCount+=1
        if sendCount == 0:
            current_time = time.time()
            if current_time - self.last_clear_time >= 29:  # send clear_all_aggro to server every 30s as a keep alive method.
                self.send_clear_all_aggro()
                self.last_clear_time = current_time

        self.isCheckingAggroUpdate = False

    def send_threat_data(self, character:str, mobName:str, totalAgro:int):
        if self.network_thread and self.network_thread.is_alive():
            self.network_thread.send_data("threat_update",character, mobName, totalAgro)
        else:
            self.logErrorMessage("Error:No available connection when trying to send aggro table to server", "error")

    def send_clear_all_aggro(self):

        if not self.isOnlineSyncEnabled:
            return

        if not self.yourName:
            return

        if self.network_thread and self.network_thread.is_alive():
            self.network_thread.send_data("clear_all_aggro",self.yourName, "NA", 0)
        else:
            self.logErrorMessage("Error:No available connection when trying to clear_all_aggro to server", "error")

    def send_mob_slain(self,mobName:str):

        if not self.isOnlineSyncEnabled:
            return

        if not self.yourName:
            return

        if self.network_thread and self.network_thread.is_alive():
            self.network_thread.send_data("mob_slain",self.yourName, mobName, 0)
        else:
            self.logErrorMessage("Error:No available connection when trying to send mob_slain to server", "error")

    def send_disc_update(self,discName:str,status:str,time:int):


        if not self.isOnlineSyncEnabled:
            return

        if not self.yourName:
            return

        if self.network_thread and self.network_thread.is_alive():
            self.network_thread.send_data(discName,self.yourName, status, time)
        else:
            self.logErrorMessage("Error:No available connection when trying to send mob_slain to server", "error")





    def _handle_message(self, message):

        self.cleansingNetworkAgroTableDict()

        #self.logErrorMessage(f"[Network Thread] Message received: {message}", "info")
        try:
            data = json.loads(message)
            if data.get("type") == "threat_broadcast":
                mob_name = data["mob_name"][0].upper() + data["mob_name"][1:]
                threat_list = sorted(data["threat_list"],
                                     key=lambda x: x["threat"], reverse=True)
                # 更新数据存储
                if not mob_name in self.threat_data:
                    aggro_table=AgroTable()
                    aggro_table.threatList=threat_list
                    aggro_table.mobName=mob_name
                    self.threat_data[mob_name] = aggro_table
                else:
                    self.threat_data[mob_name].threatList=threat_list
                    self.threat_data[mob_name].lastSeenTime=time.time()

                self.newNetFlowDetected = True
                self.hasNetworkData = True
                self.lastUpdatedMob=mob_name

        except Exception as e:
            self.logErrorMessage(f"Network data unmarshal failed: {str(e)}", "error")

    def updateNetworkThreatDisplay(self):


        if self.currentTarget in self.threat_data:
            threat_list = self.threat_data[self.currentTarget].threatList
            target = self.currentTarget
            if time.time() - self.threat_data[target].lastSeenTime < 120:   # threat_data that's over 120s expires
                self.updateNetworkThreatDisplayPanel(target, threat_list)
                return

        if self.lastUpdatedMob in self.threat_data:
            threat_list = self.threat_data[self.lastUpdatedMob].threatList
            target=self.lastUpdatedMob
            if time.time() - self.threat_data[target].lastSeenTime < 120:   # threat_data that's over 120s expires
                self.updateNetworkThreatDisplayPanel(target, threat_list)
                return



    def updateNetworkThreatDisplayPanel(self,target:str,threat_list:[]):
        display_text = [f"Mob Name : {target}"]

        header = "#|Player Name|Threat|Flux"
        if self.ifShowEqualDBGBEnabled:
            header += "|Banes"
        if self.ifShowEqualSlowEnabled:
            header += "|Slows"
        if self.ifShowTankDiscEnabled:
            header += "|Tank Disc"
        display_text.append(header)

        current_time = time.time()
        for idx, entry in enumerate(threat_list[:9], 1):  # 显示前9名
            name = entry["character"].ljust(11)[:11]
            threat = entry["threat"]

            # 格式化数值
            threat_str = f"{threat / 1000:.1f}k" if threat >= 1000 else f"{threat}"
            threat_str=threat_str.ljust(6)
            flux_str = str(threat // 50).ljust(4)
            row = f"{idx:<2}{name} {threat_str:>6} {flux_str:>4}"

            # 动态添加列
            if self.ifShowEqualDBGBEnabled:
                banes_str = str(threat // 2000).ljust(5)
                row += f" {banes_str:>5}"
            if self.ifShowEqualSlowEnabled:
                slows_str = str(threat // 1200).ljust(5)
                row += f" {slows_str:>5}"
            if self.ifShowTankDiscEnabled:
                start_time = entry.get('tank_disc_start_time', current_time)
                remaining = max(180 - int(current_time - start_time), 0)
                row += f"{ remaining:>3}s"

            display_text.append(row)



        # 用等宽字体保证对齐
        self.label_network.setText("\n".join(display_text))
        self.label_network.setFont(QtGui.QFont("Courier New"))
        self.isNetMeterHide = False
        self.label_network.show()



    def toggle_connection(self,isSynchronising:bool):

        if isSynchronising:
            self._connect()
            return

        if self.network_thread and self.network_thread.is_alive():
            self._disconnect()


    def _connect(self):
        self.network_thread = NetworkThread(AM_SERVER, AM_PORT)
        self.network_thread.logHandler=self.logErrorMessage
        self.network_thread.on_message_received = self._handle_message

        self.network_thread.start()
        self.logErrorMessage("Status:Connecting to Imaj's server(44.213.107.109:12345)","info")

    def _disconnect(self):
        if self.network_thread:
            self.network_thread.stop()
            self.network_thread.join()
        self.logErrorMessage("Status:disconnected from server manually.","info")

    def test_reconnect(self):

        if self.network_thread:
            self.network_thread.simulate_server_restart()

    def checkWeaponSwing(self,line:str):

        hitType,target=self.checkHitTypeAndTarget(line)
        if hitType==-1:                                         #it's not a weapon swing log line.
            return False


        result=self.funcCalculateSwingAgro[(self.weaponDict[self.MHWeapon].type,self.weaponDict[self.OHWeapon].type,)](hitType,target)
        if result==True:

            if self.currentTargetTotalAgroSnapshot+self.agroToUnknownTarget < 0:
                self.agroTableDict[self.currentTarget].TotalAgro=0
                self.funcCalculateSwingAgro[(self.weaponDict[self.MHWeapon].type, self.weaponDict[self.OHWeapon].type,)](hitType, target)
                self.agroToUnknownTarget = 0
            else:
                self.agroTableDict[self.currentTarget].TotalAgro+=self.agroToUnknownTarget          #add the unknown target spell agro after the 1st swing, which was from early spell msg.
                self.agroToUnknownTarget=0
            self.updateAgroMeter()
        else:
            if self.MHWeapon == "???" and self.OHWeapon == "???":  #In viewer mode do nothing except set current target.
                pass
            else:
                self.logErrorMessage("Weapon setting mismatch with log.Use /t mh=xxx and /t oh=yyy to update weapon names.","error")
        return True

    def checkHitTypeAndTarget(self,line:str):

        if line[26:31] != " You ":
            return -1, "none"

        if line[26:37]==" You slash ":
            tailIndex=line[37:].find(" for ")
            if tailIndex!=-1:
                mobName=line[37:37+tailIndex]
                return SLASH,mobName

        if line[26:44]==" You try to slash ":
            tailIndex=line[44:].find(", but ")
            if tailIndex!=-1:
                mobName=line[44:44+tailIndex]
                return SLASH,mobName

        if line[26:38]==" You pierce ":
            tailIndex=line[38:].find(" for ")
            if tailIndex!=-1:
                mobName=line[38:38+tailIndex]
                return PIERCE,mobName

        if line[26:45]==" You try to pierce ":
            tailIndex=line[45:].find(", but ")
            if tailIndex!=-1:
                mobName=line[45:45+tailIndex]
                return PIERCE,mobName

        if line[26:37]==" You punch ":
            tailIndex=line[37:].find(" for ")
            if tailIndex!=-1:
                mobName=line[37:37+tailIndex]
                return PUNCH,mobName

        if line[26:44]==" You try to punch ":
            tailIndex=line[44:].find(", but ")
            if tailIndex!=-1:
                mobName=line[44:44+tailIndex]
                return PUNCH,mobName

        if line[26:37]==" You crush ":
            tailIndex=line[37:].find(" for ")
            if tailIndex!=-1:
                mobName=line[37:37+tailIndex]
                return CRUSH,mobName

        if line[26:44]==" You try to crush ":
            tailIndex=line[44:].find(", but ")
            if tailIndex!=-1:
                mobName=line[44:44+tailIndex]
                return CRUSH,mobName

        return -1,"none"


    def combo_default(self,hitType:int,target:str):
        return False

    def viewer_mode(self,hitType:int,target:str):
        self.setCurrentTarget(target)
        return False


    def combo_1hs_1hs(self,hitType:int,target:str):

        self.setCurrentTarget(target)
        self.anyNewActionDetected = True

        if hitType!=SLASH:
            return False

        self.agroTableDict[self.currentTarget].TotalAgro+=(self.weaponDict[self.MHWeapon].damage+11)*self.realMHFireRate+(self.weaponDict[self.OHWeapon].damage+12)* self.realOHFireRate
        # can't tell which is which , so all swings goes to split proportionally.
        self.agroTableDict[self.currentTarget].TiedSwing += 1
        self.agroTableDict[self.currentTarget].MHSwing = int(self.agroTableDict[self.currentTarget].TiedSwing * self.realMHFireRate)
        self.agroTableDict[self.currentTarget].OHSwing = int(self.agroTableDict[self.currentTarget].TiedSwing * self.realOHFireRate)
        return True

    def combo_1hs_shield(self,hitType:int,target:str):

        self.setCurrentTarget(target)
        self.anyNewActionDetected = True

        if hitType!=SLASH:
            return False

        self.agroTableDict[self.currentTarget].TotalAgro+=(self.weaponDict[self.MHWeapon].damage+11)
        self.agroTableDict[self.currentTarget].MHSwing += 1
        return True


    def combo_1hs_1hp(self,hitType:int,target:str):

        self.setCurrentTarget(target)
        self.anyNewActionDetected = True

        if hitType==SLASH :
            self.agroTableDict[self.currentTarget].TotalAgro +=self.weaponDict[self.MHWeapon].damage+11
            self.agroTableDict[self.currentTarget].MHSwing += 1
            return True

        if hitType==PIERCE :
            self.agroTableDict[self.currentTarget].TotalAgro +=self.weaponDict[self.OHWeapon].damage+12
            self.agroTableDict[self.currentTarget].OHSwing += 1
            return True

        return False

    def combo_1hs_1hb(self, hitType: int, target: str):

        self.setCurrentTarget(target)
        self.anyNewActionDetected = True

        if hitType == SLASH:
            self.agroTableDict[self.currentTarget].TotalAgro += self.weaponDict[self.MHWeapon].damage + 11
            self.agroTableDict[self.currentTarget].MHSwing += 1
            return True

        if hitType == CRUSH:
            self.agroTableDict[self.currentTarget].TotalAgro += self.weaponDict[self.OHWeapon].damage + 12
            self.agroTableDict[self.currentTarget].OHSwing += 1
            return True

        return False

    def combo_1hs_h2h(self, hitType: int, target: str):

        self.setCurrentTarget(target)
        self.anyNewActionDetected = True

        if hitType == SLASH:
            self.agroTableDict[self.currentTarget].TotalAgro += self.weaponDict[self.MHWeapon].damage + 11
            self.agroTableDict[self.currentTarget].MHSwing += 1
            return True

        if hitType == PUNCH:
            self.agroTableDict[self.currentTarget].TotalAgro += self.weaponDict[self.OHWeapon].damage + 12
            self.agroTableDict[self.currentTarget].OHSwing += 1
            return True

        return False

    def combo_1hp_1hs(self, hitType: int, target: str):

        self.setCurrentTarget(target)
        self.anyNewActionDetected = True

        if hitType == PIERCE:
            self.agroTableDict[self.currentTarget].TotalAgro += self.weaponDict[self.MHWeapon].damage + 11
            self.agroTableDict[self.currentTarget].MHSwing += 1
            return True

        if hitType == SLASH:
            self.agroTableDict[self.currentTarget].TotalAgro += self.weaponDict[self.OHWeapon].damage + 12
            self.agroTableDict[self.currentTarget].OHSwing += 1
            return True

        return False

    def combo_1hp_1hp(self,hitType:int,target:str):

        self.setCurrentTarget(target)
        self.anyNewActionDetected = True

        if hitType!=PIERCE:
            return False

        self.agroTableDict[self.currentTarget].TotalAgro+=(self.weaponDict[self.MHWeapon].damage+11)*self.realMHFireRate+(self.weaponDict[self.OHWeapon].damage+12)* self.realOHFireRate
        # can't tell which is which , so all swings goes to split proportionally.
        self.agroTableDict[self.currentTarget].TiedSwing += 1
        self.agroTableDict[self.currentTarget].MHSwing = int(self.agroTableDict[self.currentTarget].TiedSwing * self.realMHFireRate)
        self.agroTableDict[self.currentTarget].OHSwing = int(self.agroTableDict[self.currentTarget].TiedSwing * self.realOHFireRate)
        return True

    def combo_1hp_shield(self,hitType:int,target:str):
        self.setCurrentTarget(target)
        self.anyNewActionDetected = True

        if hitType!=PIERCE:
            return False

        self.agroTableDict[self.currentTarget].TotalAgro+=(self.weaponDict[self.MHWeapon].damage+11)
        self.agroTableDict[self.currentTarget].MHSwing += 1
        return True


    def combo_1hp_1hb(self, hitType: int, target: str):

        self.setCurrentTarget(target)
        self.anyNewActionDetected = True

        if hitType == PIERCE:
            self.agroTableDict[self.currentTarget].TotalAgro += self.weaponDict[self.MHWeapon].damage + 11
            self.agroTableDict[self.currentTarget].MHSwing += 1
            return True

        if hitType == CRUSH:
            self.agroTableDict[self.currentTarget].TotalAgro += self.weaponDict[self.OHWeapon].damage + 12
            self.agroTableDict[self.currentTarget].OHSwing += 1
            return True

        return False

    def combo_1hp_h2h(self, hitType: int, target: str):

        self.setCurrentTarget(target)
        self.anyNewActionDetected = True

        if hitType == PIERCE:
            self.agroTableDict[self.currentTarget].TotalAgro += self.weaponDict[self.MHWeapon].damage + 11
            self.agroTableDict[self.currentTarget].MHSwing += 1
            return True

        if hitType == PUNCH:
            self.agroTableDict[self.currentTarget].TotalAgro += self.weaponDict[self.OHWeapon].damage + 12
            self.agroTableDict[self.currentTarget].OHSwing += 1
            return True

        return False



    def combo_1hb_1hs(self, hitType: int, target: str):

        self.setCurrentTarget(target)
        self.anyNewActionDetected = True

        if hitType == CRUSH:
            self.agroTableDict[self.currentTarget].TotalAgro += self.weaponDict[self.MHWeapon].damage + 11
            self.agroTableDict[self.currentTarget].MHSwing += 1
            return True

        if hitType == SLASH:
            self.agroTableDict[self.currentTarget].TotalAgro += self.weaponDict[self.OHWeapon].damage + 12
            self.agroTableDict[self.currentTarget].OHSwing += 1
            return True

        return False



    def combo_1hb_1hp(self, hitType: int, target: str):

        self.setCurrentTarget(target)
        self.anyNewActionDetected = True

        if hitType == CRUSH:
            self.agroTableDict[self.currentTarget].TotalAgro += self.weaponDict[self.MHWeapon].damage + 11
            self.agroTableDict[self.currentTarget].MHSwing += 1
            return True

        if hitType == PIERCE:
            self.agroTableDict[self.currentTarget].TotalAgro += self.weaponDict[self.OHWeapon].damage + 12
            self.agroTableDict[self.currentTarget].OHSwing += 1
            return True

        return False

    def combo_1hb_1hb(self,hitType:int,target:str):

        self.setCurrentTarget(target)
        self.anyNewActionDetected = True

        if hitType!=CRUSH:
            return False


        self.agroTableDict[self.currentTarget].TotalAgro+=(self.weaponDict[self.MHWeapon].damage+11)*self.realMHFireRate+(self.weaponDict[self.OHWeapon].damage+12)* self.realOHFireRate
        # can't tell which is which ,so all swings goes to split proportionally.
        self.agroTableDict[self.currentTarget].TiedSwing += 1
        self.agroTableDict[self.currentTarget].MHSwing = int(self.agroTableDict[self.currentTarget].TiedSwing * self.realMHFireRate)
        self.agroTableDict[self.currentTarget].OHSwing = int(self.agroTableDict[self.currentTarget].TiedSwing * self.realOHFireRate)
        return True

    def combo_1hb_shield(self,hitType:int,target:str):
        self.setCurrentTarget(target)
        self.anyNewActionDetected = True

        if hitType!=CRUSH:
            return False


        self.agroTableDict[self.currentTarget].TotalAgro+=(self.weaponDict[self.MHWeapon].damage+11)
        self.agroTableDict[self.currentTarget].MHSwing += 1
        return True


    def combo_1hb_h2h(self, hitType: int, target: str):

        self.setCurrentTarget(target)
        self.anyNewActionDetected = True

        if hitType == CRUSH:
            self.agroTableDict[self.currentTarget].TotalAgro += self.weaponDict[self.MHWeapon].damage + 11
            self.agroTableDict[self.currentTarget].MHSwing += 1
            return True

        if hitType == PUNCH:
            self.agroTableDict[self.currentTarget].TotalAgro += self.weaponDict[self.OHWeapon].damage + 12
            self.agroTableDict[self.currentTarget].OHSwing += 1
            return True

        return False

    def combo_h2h_1hs(self, hitType: int, target: str):

        self.setCurrentTarget(target)
        self.anyNewActionDetected = True

        if hitType == PUNCH:
            self.agroTableDict[self.currentTarget].TotalAgro += self.weaponDict[self.MHWeapon].damage + 11
            self.agroTableDict[self.currentTarget].MHSwing += 1

            return True

        if hitType == SLASH:
            self.agroTableDict[self.currentTarget].TotalAgro += self.weaponDict[self.OHWeapon].damage + 12
            self.agroTableDict[self.currentTarget].OHSwing += 1

            return True

        return False

    def combo_h2h_1hp(self, hitType: int, target: str):

        self.setCurrentTarget(target)
        self.anyNewActionDetected = True

        if hitType == PUNCH:
            self.agroTableDict[self.currentTarget].TotalAgro += self.weaponDict[self.MHWeapon].damage + 11
            self.agroTableDict[self.currentTarget].MHSwing += 1
            return True

        if hitType == PIERCE:
            self.agroTableDict[self.currentTarget].TotalAgro += self.weaponDict[self.OHWeapon].damage + 12
            self.agroTableDict[self.currentTarget].OHSwing += 1

            return True

        return False


    def combo_h2h_1hb(self, hitType: int, target: str):

        self.setCurrentTarget(target)
        self.anyNewActionDetected = True

        if hitType == PUNCH:
            self.agroTableDict[self.currentTarget].TotalAgro += self.weaponDict[self.MHWeapon].damage + 11
            self.agroTableDict[self.currentTarget].MHSwing += 1

            return True

        if hitType == CRUSH:
            self.agroTableDict[self.currentTarget].TotalAgro += self.weaponDict[self.OHWeapon].damage + 12
            self.agroTableDict[self.currentTarget].OHSwing += 1

            return True

        return False

    def combo_h2h_h2h(self,hitType:int,target:str):
        self.setCurrentTarget(target)
        self.anyNewActionDetected = True

        if hitType!=PUNCH:
            return False


        self.agroTableDict[self.currentTarget].TotalAgro+=(self.weaponDict[self.MHWeapon].damage+11)*self.realMHFireRate+(self.weaponDict[self.OHWeapon].damage+12)* self.realOHFireRate
        # can't tell which is which , so all swings goes to split equally.
        self.agroTableDict[self.currentTarget].TiedSwing += 1
        self.agroTableDict[self.currentTarget].MHSwing = int(self.agroTableDict[self.currentTarget].TiedSwing * self.realMHFireRate)
        self.agroTableDict[self.currentTarget].OHSwing = int(self.agroTableDict[self.currentTarget].TiedSwing * self.realOHFireRate)
        return True

    def combo_h2h_shield(self,hitType:int,target:str):
        self.setCurrentTarget(target)
        self.anyNewActionDetected = True

        if hitType!=PUNCH:
            return False


        self.agroTableDict[self.currentTarget].TotalAgro+=(self.weaponDict[self.MHWeapon].damage+11)
        self.agroTableDict[self.currentTarget].MHSwing += 1
        return True

    def combo_2hp_NA(self,hitType:int,target:str):
        self.setCurrentTarget(target)
        self.anyNewActionDetected = True

        if hitType!=PIERCE:
            return False


        self.agroTableDict[self.currentTarget].TotalAgro+=(self.weaponDict[self.MHWeapon].damage+self.weaponDict[self.MHWeapon].damageBonus)
        self.agroTableDict[self.currentTarget].MHSwing += 1
        return True

    def combo_2hb_NA(self,hitType:int,target:str):

        self.setCurrentTarget(target)
        self.anyNewActionDetected = True

        if hitType!=CRUSH:
            return False

        self.agroTableDict[self.currentTarget].TotalAgro+=(self.weaponDict[self.MHWeapon].damage+self.weaponDict[self.MHWeapon].damageBonus)
        self.agroTableDict[self.currentTarget].MHSwing += 1
        return True

    def combo_2hs_NA(self,hitType:int,target:str):

        self.setCurrentTarget(target)
        self.anyNewActionDetected = True

        if hitType!=SLASH:
            return False

        self.agroTableDict[self.currentTarget].TotalAgro+=(self.weaponDict[self.MHWeapon].damage+self.weaponDict[self.MHWeapon].damageBonus)
        self.agroTableDict[self.currentTarget].MHSwing += 1
        return True



    def checkProcEffects(self,line:str,blockSequenceNumber:int):

        if self.weaponDict[self.MHWeapon].procResistMsg!="":
            index=line[26:].find(self.weaponDict[self.MHWeapon].procResistMsg)
            if index==0 or index==1:
                if self.currentTarget in self.agroTableDict:
                    self.agroTableDict[self.currentTarget].ProcCount+=1
                    self.agroTableDict[self.currentTarget].TotalAgro+=self.weaponDict[self.MHWeapon].procAgro
                    self.updateAgroMeter()
                else:
                    self.agroToUnknownTarget+=self.weaponDict[self.MHWeapon].procAgro
                return True

        if self.weaponDict[self.OHWeapon].procResistMsg!="":
            index=line[26:].find(self.weaponDict[self.OHWeapon].procResistMsg)
            if index==0 or index==1:
                if self.currentTarget in self.agroTableDict:
                    self.agroTableDict[self.currentTarget].ProcCount+=1
                    self.agroTableDict[self.currentTarget].TotalAgro+=self.weaponDict[self.OHWeapon].procAgro
                    self.updateAgroMeter()
                else:
                    self.agroToUnknownTarget+=self.weaponDict[self.OHWeapon].procAgro
                return True


        if self.weaponDict[self.MHWeapon].procDirectDamage > 0:
            index=line[26:].find(self.weaponDict[self.MHWeapon].procLandMsg.replace("Someone","", 1))
            if index!=-1:
                mobName = line[27:26+index].strip()
                mobName = mobName[0].upper() + mobName[1:]

                if len(self.lastLogline) < 70:  # example: [Sun Jul 07 08:27:52 2024] Someone was hit by non-melee for 100 points of damage. length of this must be longer than 70
                    return True

                if self.lastLogline[27].upper() + self.lastLogline[28:] == mobName + f" was hit by non-melee for {self.weaponDict[self.MHWeapon].procDirectDamage} points of damage.\n":
                    self.setCurrentTarget(mobName)
                    self.agroTableDict[self.currentTarget].ProcCount+=1
                    self.agroTableDict[self.currentTarget].TotalAgro += self.weaponDict[self.MHWeapon].procAgro
                    self.anyNewActionDetected = True
                    self.updateAgroMeter()
                return True

        if self.weaponDict[self.OHWeapon].procDirectDamage > 0:
            index=line[26:].find(self.weaponDict[self.OHWeapon].procLandMsg.replace("Someone","", 1))
            if index!=-1:
                mobName = line[27:26+index].strip()
                mobName = mobName[0].upper() + mobName[1:]

                if len(self.lastLogline) < 70:  # example: [Sun Jul 07 08:27:52 2024] Someone was hit by non-melee for 100 points of damage. length of this must be longer than 70
                    return True

                if self.lastLogline[27].upper() + self.lastLogline[28:] == mobName + f" was hit by non-melee for {self.weaponDict[self.OHWeapon].procDirectDamage} points of damage.\n":
                    self.setCurrentTarget(mobName)
                    self.agroTableDict[self.currentTarget].ProcCount+=1
                    self.agroTableDict[self.currentTarget].TotalAgro += self.weaponDict[self.OHWeapon].procAgro
                    self.anyNewActionDetected = True
                    self.updateAgroMeter()
                return True



        if self.currentMHProcLandMessage!="":
            index=line[26:].find(self.currentMHProcLandMessage)
            if index==0 or index==1:
                self.checkNextFewLinesforMHProc = True
                self.blockSequenceNumberToCheck=blockSequenceNumber
                return True



        if self.currentOHProcLandMessage!="":
            index=line[26:].find(self.currentOHProcLandMessage)
            if index==0 or index==1:
                if self.currentTarget in self.agroTableDict:
                    self.agroTableDict[self.currentTarget].ProcCount+=1
                    self.agroTableDict[self.currentTarget].TotalAgro+=self.weaponDict[self.OHWeapon].procAgro
                    self.updateAgroMeter()
                else:
                    self.agroToUnknownTarget+=self.weaponDict[self.OHWeapon].procAgro
                return True


        if self.weaponDict[self.MHWeapon].procCanAlwaysTakeHold == False:
            if line[26:] == " Your spell did not take hold.\n":
                self.checkNextFewLinesforMHProc = True
                self.blockSequenceNumberToCheck=blockSequenceNumber
                return True

        # Offhand weapon proc and next swing seemed quite desync. Not sure if server side has different mechanic than Main hand. So this part probably won't be very accurate.
        '''
        if self.weaponDict[self.OHWeapon].procCanAlwaysTakeHold == False:
            if line[26:] == " Your spell did not take hold.\n":
                self.checkNextLinesforOHProc = True
                return True
        '''




        return False

    def checkClickyEffects(self,line:str):

        current_time=datetime.datetime.now()


        if line[26:]==" Your Forlorn Totem of Rolfron Zek begins to glow.\n":    #your casting a totem stun.
            self.isCastingTotem=True
            self.anyNewActionDetected = True
            return True

        index=line[26:].find(" is stunned.\n")
        if index!=-1 and self.isCastingTotem:

            mobName = line[27:26 + index].strip()
            mobName = mobName[0].upper() + mobName[1:]

            if len(self.lastLogline) < 70:  # example: [Sun Jul 07 08:27:52 2024] Someone was hit by non-melee for 60 points of damage. length of this must be longer than 70
                return True

            if self.lastLogline[27].upper() + self.lastLogline[28:] == mobName + f" was hit by non-melee for 60 points of damage.\n":
                self.setCurrentTarget(mobName)
                self.agroTableDict[self.currentTarget].TotalAgro += 460      #totem agro is 460
                self.isCastingTotem=False
                self.anyNewActionDetected = True
                self.updateAgroMeter()

            return True


        if line[26:]==" Your target resisted the Holy Might spell.\n":    #your casting a totem stun.
            self.agroToUnknownTarget+=460                                    #totem agro is 460
            self.isCastingTotem=False
            self.anyNewActionDetected = True
            self.updateAgroMeter()
            return True


        if line[26:]==" Your Bioluminescent Orb begins to glow.\n":    #your casting a bio orb.
            self.isCastingBioOrb=True
            self.anyNewActionDetected = True
            self.lastBioOrbCastingStartTime = current_time

            return True

        index=line.find(" is blinded by a flash of light.\n")
        if index!=-1 and self.isCastingBioOrb:

            casting_time = (current_time - self.lastBioOrbCastingStartTime).total_seconds() * 1000
            if casting_time < 5000 - self.latencyTolerance or casting_time > 5000 + self.latencyTolerance:
                return True

            self.agroToUnknownTarget+=800                                    #bio orb agro is 800
            self.isCastingBioOrb=False
            self.anyNewActionDetected = True
            self.updateAgroMeter()
            return True

        if line[26:]==" Your target resisted the Blinding Luminance spell.\n":    #your casting a bio orb.
            self.agroToUnknownTarget+=800                                    #bio orb agro is 800
            self.isCastingBioOrb=False
            self.anyNewActionDetected = True
            self.updateAgroMeter()
            return True



        index=line[26:].find(" is surrounded by darkness.\n")
        if index!=-1:
            if self.currentTarget==line[27].upper()+line[28:26+index]:
                self.agroTableDict[self.currentTarget].TotalAgro+=400                  #scepter agro is 400
                self.anyNewActionDetected = True
                self.updateAgroMeter()
                return True

        if line[26:]==" Your target resisted the Clinging Darkness spell.\n":    #scepter agro is 400
            self.agroToUnknownTarget+=400
            self.anyNewActionDetected = True
            self.updateAgroMeter()
            return True

        if line[26:]==" Your target is immune to changes in its run speed.\n":    #scepter agro is 400
            self.agroToUnknownTarget+=400
            self.anyNewActionDetected = True
            self.updateAgroMeter()
            return True


        return False

    def checkRangerSpellEffects(self, line: str):

        current_time=datetime.datetime.now()
        if line[26:] == " You begin casting Flame Lick.\n":  # your casting Flame Lick.
            self.isCastingFlameLick = True
            self.anyNewActionDetected = True
            self.lastFlameLickCastingStartTime = current_time
            return True

        index = line.find(" is surrounded by flickering flames.\n")
        if index != -1 and self.isCastingFlameLick:

            casting_time = (current_time - self.lastFlameLickCastingStartTime).total_seconds() * 1000
            if  casting_time <1500-self.latencyTolerance or casting_time > 1500 + self.latencyTolerance:
                return True

            self.agroToUnknownTarget += 1206  # FL agro is 1200 , assuming 2 ticks of dot can sustain
            self.isCastingFlameLick = False
            self.anyNewActionDetected = True
            self.updateAgroMeter()
            return True

        if line[26:] == " Your target resisted the Flame Lick spell.\n":  # your casting Flame Lick.

            self.agroToUnknownTarget += 1200  # FL agro is 1200
            self.isCastingFlameLick = False
            self.anyNewActionDetected = True
            self.updateAgroMeter()
            return True

        if line[26:] == " You begin casting Enveloping Roots.\n":  # your casting Enveloping Roots.

            self.isCastingEnvelopingRoots = True
            self.anyNewActionDetected = True
            self.lastEnvelopingRootsCastingStartTime = current_time

            return True

        index = line.find("'s feet become entwined.\n")
        if index != -1 and self.isCastingEnvelopingRoots:

            casting_time = (current_time - self.lastEnvelopingRootsCastingStartTime).total_seconds() * 1000
            if  casting_time < 1750 - self.latencyTolerance or casting_time > 1750 + self.latencyTolerance:
                return True

            self.agroToUnknownTarget += 1310  # Enveloping Roots agro is 1310
            self.isCastingEnvelopingRoots = False
            self.anyNewActionDetected = True
            self.updateAgroMeter()
            return True

        if line[26:] == " Your target resisted the Enveloping Roots spell.\n":  # your casting Enveloping Roots.
            self.agroToUnknownTarget += 1310  # Enveloping Roots agro is 1310
            self.isCastingEnvelopingRoots = False
            self.anyNewActionDetected = True
            self.updateAgroMeter()
            return True

        if line[26:] == " You begin casting Jolt.\n":  # your casting Jolt.
            self.isCastingJolt = True
            self.anyNewActionDetected = True
            self.lastJoltCastingStartTime =current_time
            return True

        index = line.find("'s head snaps back.\n")
        if index != -1 and self.isCastingJolt:

            casting_time = (current_time - self.lastJoltCastingStartTime).total_seconds() * 1000
            if  casting_time <1500-self.latencyTolerance or casting_time > 1500 + self.latencyTolerance:
                return True

            self.agroToUnknownTarget -= 500  # Jolt agro is -500
            self.isCastingJolt = False
            self.anyNewActionDetected = True
            self.updateAgroMeter()
            return True

        if line[26:] == " Your target resisted the Jolt spell.\n":  # your casting Jolt.
            self.agroToUnknownTarget -= 500  # Jolt agro is -500
            self.isCastingJolt = False
            self.anyNewActionDetected = True
            self.updateAgroMeter()
            return True

        if line[26:] == " You begin casting Cinder Jolt.\n":  # your casting Cinder Jolt.
            self.lastCinderJoltCastingStartTime =current_time
            self.isCastingCinderJolt = True
            self.anyNewActionDetected = True
            return True


        index = line.find("'s head snaps back.\n")
        if index != -1 and self.isCastingCinderJolt:

            casting_time = (current_time - self.lastCinderJoltCastingStartTime).total_seconds() * 1000
            if  casting_time <1500-self.latencyTolerance or casting_time > 1500 + self.latencyTolerance:
                return True


            self.agroToUnknownTarget -= 500  # Cinder Jolt agro is -500
            self.isCastingCinderJolt = False
            self.anyNewActionDetected = True
            self.updateAgroMeter()
            return True


        if line[26:] == " Your target resisted the Cinder Jolt spell.\n":  # your casting Cinder Jolt.
            self.agroToUnknownTarget -= 500  # Cinder Jolt agro is -500
            self.isCastingCinderJolt = False
            self.anyNewActionDetected = True
            self.updateAgroMeter()
            return True

        return False


    def checkSkillEffects(self,line:str):

        if line[26:30] != " You":
            return False

        if line[26:36]==" You kick ":
            tailIndex=line[36:].find(" for ")
            if tailIndex!=-1:
                mobName = line[36].upper() + line[37:36 + tailIndex]
                self.setCurrentTarget(mobName)
                self.agroTableDict[self.currentTarget].TotalAgro += 5  # kick agro is 5
                self.anyNewActionDetected = True
                self.updateAgroMeter()
                return True

        if line[26:43]==" You try to kick ":
            tailIndex=line[43:].find(", but ")
            if tailIndex!=-1:
                mobName = line[43].upper() + line[44:43 + tailIndex]
                self.setCurrentTarget(mobName)
                self.agroTableDict[self.currentTarget].TotalAgro += 5  # kick agro is 5
                self.anyNewActionDetected = True
                self.updateAgroMeter()
                return True


        if line[26:40]==" You disarmed ":
            tailIndex=line[40:].find("!")
            if tailIndex!=-1:
                mobName = line[40].upper() + line[41:40 + tailIndex]
                self.setCurrentTarget(mobName)
                self.agroTableDict[self.currentTarget].TotalAgro += 20  # disarm agro is 20
                self.anyNewActionDetected = True
                self.updateAgroMeter()
                return True

        if line[26:]==" Your attempt to disarm failed.\n":
                self.agroToUnknownTarget += 20  # disarm agro is 20
                self.anyNewActionDetected = True
                self.updateAgroMeter()
                return True

        #skip Begging , since it seems zero agro.

        if line[26:36]==" You bash ":
            tailIndex=line[36:].find(" for ")
            if tailIndex!=-1:
                mobName = line[36].upper() + line[37:36 + tailIndex]
                self.setCurrentTarget(mobName)
                self.agroTableDict[self.currentTarget].TotalAgro += 7  # Bash agro is 7. Slam use same fight msg.but agro is 5. so never use bash , use kick istead. to make it accurate
                self.anyNewActionDetected = True
                self.updateAgroMeter()
                return True

        if line[26:43]==" You try to bash ":
            tailIndex=line[43:].find(", but ")
            if tailIndex!=-1:
                mobName = line[43].upper() + line[44:43 + tailIndex]
                self.setCurrentTarget(mobName)
                self.agroTableDict[self.currentTarget].TotalAgro += 7  # Bash agro is 7. Slam use same fight msg.but agro is 5.so never use bash , use kick istead. to make it accurate
                self.anyNewActionDetected = True
                self.updateAgroMeter()
                return True

        return False


    def checkDiscStatus(self,line:str):

        # disc name: defensive ,evasive etc.
        # status=activated/ended/cooling_down
        # time = disc remaining time or disc cooling down time

        # You can use the ability Silentfist Discipline again in 3 minute(s) 57 seconds.
        if line[26:].startswith(" You can use the ability "):    #Player's disc is cooling down
            result = re.search(r' Discipline again in (\d{1,2}) minute\(s\) (\d{1,2}) seconds', line)
            remaining_time = int(result.group(1))*60 + int(result.group(2))
            self.send_disc_update("disc_cooling_down","any_disc",remaining_time)
            return True

        if line[26:].startswith(" You return to your normal fighting style.") :    #Player disc ended
            self.send_disc_update("disc_ended","any_disc",0)
            return True

        if line[26:].startswith(" You have been slain by"):    #Player's disc is cooling down
            self.send_disc_update("disc_ended","any_disc",0)
            return True

        if line[26:]==" You assume a defensive fighting style..\n" :    #Player activated defensive disc.
            self.send_disc_update("disc_activated","defensive",180)
            return True

        if line[26:]==" You assume an evasive fighting style.\n" :    #Player activated evasive disc.
            self.send_disc_update("disc_activated","evasive",180)
            return True


        if line[26:]==" You assume a precise fighting style.\n" :    #Player activated Precision disc.
            self.send_disc_update("disc_activated","precision",180)
            return True


        if line[26:]==" A consuming rage takes over your weapons.\n" :    #Player activated furious disc.
            self.send_disc_update("disc_activated","furious",9)
            return True


        if line[26:]==" The rage leaves you.\n" :                         #Player furious disc ended.
            self.send_disc_update("disc_ended","any_disc",0)
            return True

        if line[26:]==" You instincts take over as you avoid every attack.\n" :    #Player activated Fortitude disc.
            self.send_disc_update("disc_activated","fortitude",8)
            return True


        if line[26:]==" Your battle instinct leaves you.\n" :                         #Player Fortitude disc ended.
            self.send_disc_update("disc_ended","any_disc",0)
            return True


        if line[26:]==" Your weapons begin to spin.\n" :                   #Player activated weapon shield disc.
            self.send_disc_update("disc_activated","weaponshield",20)
            return True

        if line[26:]==" Your weapons slow down.\n" :                         #Player weapon shield disc ended.
            self.send_disc_update("disc_ended","any_disc",0)
            return True

        return False

    def checkAnySeenMobs(self,line:str):

        return False


    def checkAndSetCurrentTarget(self,line:str):

        if line[26:43]==" You say, 'Hail, ":    #use ingame hail hotkey to set current target.
            self.setCurrentTarget(line[43:-2])
            self.anyNewActionDetected = True
            self.updateAgroMeter()
            return True

        # index = line.find(" regards you as an ally -- ")
        # if index !=-1:  #use ingame /con hotkey to set current target.         Ally --
        #     self.setCurrentTarget(line[27:index])
        #     self.anyNewActionDetected = True
        #     self.updateAgroMeter()
        #     return True
        #
        # index = line.find(" looks upon you warmly -- ")
        # if index !=-1:  #use ingame /con hotkey to set current target.         Warmly --
        #     self.setCurrentTarget(line[27:index])
        #     self.anyNewActionDetected = True
        #     self.updateAgroMeter()
        #     return True
        #
        # index = line.find(" kindly considers you -- ")
        # if index !=-1:  #use ingame /con hotkey to set current target.         Kindly --
        #     self.setCurrentTarget(line[27:index])
        #     self.anyNewActionDetected = True
        #     self.updateAgroMeter()
        #     return True
        #
        # index = line.find(" judges you amiably -- ")
        # if index !=-1:  #use ingame /con hotkey to set current target.         Amiable --
        #     self.setCurrentTarget(line[27:index])
        #     self.anyNewActionDetected = True
        #     self.updateAgroMeter()
        #     return True
        #
        #
        # index = line.find(" regards you indifferently -- ")
        # if index !=-1:  #use ingame /con hotkey to set current target.         indifferently --
        #     self.setCurrentTarget(line[27:index])
        #     self.anyNewActionDetected = True
        #     self.updateAgroMeter()
        #     return True
        #
        # index = line.find(" looks your way apprehensively -- ")
        # if index != -1:  # use ingame /con hotkey to set current target.       apprehensively --
        #     self.setCurrentTarget(line[27:index])
        #     self.anyNewActionDetected = True
        #     self.updateAgroMeter()
        #     return True
        #
        # index = line.find(" glowers at you dubiously -- ")
        # if index !=-1:  #use ingame /con hotkey to set current target.         dubious --
        #     self.setCurrentTarget(line[27:index])
        #     self.anyNewActionDetected = True
        #     self.updateAgroMeter()
        #     return True
        #
        # index = line.find(" glares at you threateningly -- ")
        # if index !=-1:  #use ingame /con hotkey to set current target.         Threatening --
        #     self.setCurrentTarget(line[27:index])
        #     self.anyNewActionDetected = True
        #     self.updateAgroMeter()
        #     return True
        #
        #
        # index = line.find(" scowls at you, ready to attack -- ")
        # if index !=-1:  #use ingame /con hotkey to set current target.         Scowls --
        #     self.setCurrentTarget(line[27:index])
        #     self.anyNewActionDetected = True
        #     self.updateAgroMeter()
        #     return True

        return False

    def setCurrentTarget(self,mobName:str):

        capitalized_mobName = mobName[0].upper() + mobName[1:]

        if self.agroTableDict.get(capitalized_mobName)==None:
            at=AgroTable()
            at.mobName=capitalized_mobName
            self.agroTableDict[capitalized_mobName]=at
        else:
            self.agroTableDict[capitalized_mobName].lastSeenTime=time.time()


        if self.currentTarget!=capitalized_mobName:
            self.currentTarget=capitalized_mobName
            self.recompileProcLandMsg(capitalized_mobName)

        self.currentTargetTotalAgroSnapshot=self.agroTableDict[self.currentTarget].TotalAgro

        if self.isOnlineSyncEnabled:
            self.updateNetworkThreatDisplay()  # 目标切换时刷新显示

    def recompileProcLandMsg(self,capitalized_mobName:str):

        if capitalized_mobName == "":
            return

        if self.weaponDict[self.MHWeapon].procLandMsg != "":
            mh_proc_land_msg=self.weaponDict[self.MHWeapon].procLandMsg.replace("@PLAYERNAME",self.yourName,1)
            self.currentMHProcLandMessage = mh_proc_land_msg.replace("Someone",capitalized_mobName, 1)

        if self.weaponDict[self.OHWeapon].procLandMsg != "":
            oh_proc_land_msg = self.weaponDict[self.OHWeapon].procLandMsg.replace("@PLAYERNAME",self.yourName,1)
            self.currentOHProcLandMessage = oh_proc_land_msg.replace("Someone",capitalized_mobName, 1)


    def updateAgroMeter(self):
        if self.currentTarget=="" or self.currentTarget not in self.agroTableDict:
            at=AgroTable()
            at.mobName="???"
        else:
            at=self.agroTableDict[self.currentTarget]

        agroMeterStringYellow="Mob   Name : "+at.mobName
        if at.TotalAgro<1000:
            agroMeterStringYellow += "\nTotal Agro : {:0.0f}".format(at.TotalAgro)
        else:
            agroMeterStringYellow += "\nTotal Agro : {:0.1f}k".format(at.TotalAgro/1000)
        agroMeterStringYellow+="\nEqual Flux : {:,}".format(int(at.TotalAgro / 50))
        if self.agroToUnknownTarget!=0:
            agroMeterStringYellow += "\nSpell Agro : {:+}".format(self.agroToUnknownTarget)
        self.label_agroMeterYellow.setText(agroMeterStringYellow)

        #agroMeterString="\n===================="
        if self.MHWeapon == "???":
            agroMeterStringGreen=f"\nMain  Hand : ??? (try /t mh=weapon name)"
        else:
            agroMeterStringGreen=f"\nMain  Hand : {self.MHWeapon}"+" {:,}".format(at.MHSwing)

        if self.OHWeapon == "???":
            agroMeterStringGreen+=f"\nOff   Hand : ??? (try /t oh=weapon name)"
        else:
            agroMeterStringGreen+=f"\nOff   Hand : {self.OHWeapon}"+" {:,}".format(at.OHSwing)
        agroMeterStringGreen+="\nProc Count : {:,}".format(at.ProcCount)
        duration=time.time()-at.engageTime
        tpm=at.TotalAgro/(duration+1)*60
        if tpm < 1000:
            agroMeterStringGreen+="\nThreat/min : {:0.0f}".format(tpm)
        else:
            agroMeterStringGreen+="\nThreat/min : {:0.1f}k".format(tpm / 1000)


        self.label_agroMeterGreen.setText(agroMeterStringGreen)

        if self.isHide:
            self.isHide=False
            self.label_agroMeterGreen.show()
            self.label_agroMeterYellow.show()

    def logErrorMessage(self,message:str,type:str):
        #1）如果是错误提示，则显示到界面，持续n秒
        #2）记录到日志文件

        if type == "error":
            self.errorMessage=message
            self.label_errorMessage.setText(message)
            self.label_errorMessage.show()
            self.errorMessage_timer.start(10000)

        curr_time = datetime.datetime.now()
        time_str = datetime.datetime.strftime(curr_time, '%Y-%m-%d %H:%M:%S.%f')
        with open('AgroMeter RUN LOG.txt', 'a',encoding='utf-8') as f:
            message=message.rstrip()
            f.write('['+time_str+']  '+message+'\n')
            f.flush()



    def testAgroMeterHandler(self):

        # example Agro table data
        self.test_at.TotalAgro += 675
        self.test_at.ProcCount += 1
        self.test_at.MHSwing += 20
        self.test_at.OHSwing += 11
        self.test_at.lastSeenTime=time.time()
        self.updateAgroMeter()

    def testAgroMeter(self):
        self.agroTableDict[self.test_at.mobName] = self.test_at
        self.currentTarget = self.test_at.mobName
        self.test_timer.start(300)

    def stopTestAgroMeter(self):

        self.test_timer.stop()
        self.test_at.TotalAgro = 460
        self.test_at.MHSwing = 40
        self.test_at.OHSwing = 22
        self.test_at.ProcCount = 1

        if self.agroTableDict.get(self.test_at.mobName) == None:
            return
        self.agroTableDict.pop(self.test_at.mobName)
        self.send_mob_slain(self.test_at.mobName)


    def hideAgroMeterHandler(self):

        self.hideAgroMeter()
        self.hideNetworkAgroMeter()

    def hideAgroMeter(self):

        if self.isHide:
            return

        if self.anyNewActionDetected:                #if there's no new action in a period then hide it
            self.anyNewActionDetected=False
            return

        self.isHide = True
        self.label_agroMeterGreen.hide()
        self.label_agroMeterYellow.hide()
        self.label_errorMessage.hide()

    def hideNetworkAgroMeter(self):

        if self.isNetMeterHide:
            return

        if self.newNetFlowDetected:                #if there's no new network flow in a period then hide it.
            self.newNetFlowDetected=False

        else:
            self.isNetMeterHide = True
            self.label_network.hide()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AgroMeter()
    window.show()
    window.resize(500,200)


    #demo run of this tool
    window.testAgroMeter()

    sys.exit(app.exec_())
