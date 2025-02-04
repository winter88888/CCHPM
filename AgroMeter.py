import sys
import os
import time
import datetime
import configparser

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
#main hand vs off hand swing rate const
MAIN_HAND_RATE=0.55
OFF_HAND_RATE=1-MAIN_HAND_RATE


class AgroTable:
    def __init__(self):
        self.mobName=""
        self.MHSwing=0
        self.OHSwing=0
        self.TiedSwing=0
        self.ProcCount=0
        self.TotalAgro=0.0
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


class AgroMeter(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.width = 0
        self.height= 0
        self.widthMargin=2
        self.heigthMargin=2
        self.MHWeapon = "???" #Need save and load this config
        self.OHWeapon = "???" #Need save and load this config
        self.isHide=True
        self.weaponDict = {}
        self.agroTableDict={} #Key domain mobName:str Value:AgroTable instance
        self.currentTarget=""
        self.currentMHProcLandMessage=""
        self.currentOHProcLandMessage = ""
        self.cleansingTimerExpired=False
        self.anyNewActionDetected = False
        self.realMHFireRate = MAIN_HAND_RATE      #default rate if mh delay == oh delay
        self.realOHFireRate = OFF_HAND_RATE
        self.isCastingTotem = False
        self.isCastingBioOrb = False
        self.agroToUnknowTarget=0
        self.agroTableExpireDuration=0


        self.funcCalculateSwingAgro={
            ("???", "???"): self.combo_default,

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
        self.test_at.mobName = "Vulak"
        self.test_at.engageTIme=time.time()
        self.test_timer = QTimer(self)
        self.test_timer.timeout.connect(self.testAgroMeterHandler)



        self.initializeWeaponBase()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Real Time Agro Meter')
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
        self.label_agroMeterYellow.setStyleSheet('color: yellow;')

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
                'procLandMsg': weapon.procLandMsg
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
            self.realMHFireRate=MAIN_HAND_RATE/(self.weaponDict[self.MHWeapon].delay/self.weaponDict[self.OHWeapon].delay*OFF_HAND_RATE+MAIN_HAND_RATE)
            self.realOHFireRate=1-self.realMHFireRate


    def logProcessor(self,line:str):


        self.cleansingAgroTableDict()

        if self.checkWeaponSwing(line)==True:
            return

        if self.checkProcEffects(line)==True:
            return

        if self.checkSpellEffects(line)==True:
            return

        #if self.checkAnySeenMobs(line)==True:
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
            return


        index = line.find(" has been slain by ")      #mob got slain.
        if index !=-1:
            mobName=line[27:index]
            mobName=mobName[0].upper() + mobName[1:]
            if self.agroTableDict.get(mobName)==None:
                return
            if self.currentTarget!=mobName:
                self.agroTableDict.pop(mobName)
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
            self.agroTableDict.clear()
            self.currentTarget = ""
            self.anyNewActionDetected = False
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

    def cleansingTimerHandler(self):
        if not self.cleansingTimerExpired:
            self.cleansingTimerExpired=True

    def checkWeaponSwing(self,line:str):

        hitType,target=self.checkHitTypeAndTarget(line)
        if hitType==-1:                                         #it's not a weapon swing log line.
            return False

        result=self.funcCalculateSwingAgro[(self.weaponDict[self.MHWeapon].type,self.weaponDict[self.OHWeapon].type,)](hitType,target)
        if result==True:
            self.agroTableDict[self.currentTarget].TotalAgro+=self.agroToUnknowTarget          #add the unknown target spell agro after the 1st successful swing, which was from early spell msg.
            self.agroToUnknowTarget=0
            self.updateAgroMeter()
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


    def combo_1hs_1hs(self,hitType:int,target:str):
        if hitType!=SLASH:
            return False

        self.setCurrentTarget(target)
        self.anyNewActionDetected = True
        self.agroTableDict[self.currentTarget].TotalAgro+=(self.weaponDict[self.MHWeapon].damage+11)*self.realMHFireRate+(self.weaponDict[self.MHWeapon].damage+12)* self.realOHFireRate
        # can't tell which is which , so all swings goes to split proportionally.
        self.agroTableDict[self.currentTarget].TiedSwing += 1
        self.agroTableDict[self.currentTarget].MHSwing = int(self.agroTableDict[self.currentTarget].TiedSwing * self.realMHFireRate)
        self.agroTableDict[self.currentTarget].OHSwing = int(self.agroTableDict[self.currentTarget].TiedSwing * self.realOHFireRate)
        return True

    def combo_1hs_shield(self,hitType:int,target:str):
        if hitType!=SLASH:
            return False

        self.setCurrentTarget(target)
        self.anyNewActionDetected = True
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
        if hitType!=PIERCE:
            return False

        self.setCurrentTarget(target)
        self.anyNewActionDetected = True
        self.agroTableDict[self.currentTarget].TotalAgro+=(self.weaponDict[self.MHWeapon].damage+11)*self.realMHFireRate+(self.weaponDict[self.MHWeapon].damage+12)* self.realOHFireRate
        # can't tell which is which , so all swings goes to split proportionally.
        self.agroTableDict[self.currentTarget].TiedSwing += 1
        self.agroTableDict[self.currentTarget].MHSwing = int(self.agroTableDict[self.currentTarget].TiedSwing * self.realMHFireRate)
        self.agroTableDict[self.currentTarget].OHSwing = int(self.agroTableDict[self.currentTarget].TiedSwing * self.realOHFireRate)
        return True

    def combo_1hp_shield(self,hitType:int,target:str):
        if hitType!=PIERCE:
            return False

        self.setCurrentTarget(target)
        self.anyNewActionDetected = True
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
        if hitType!=CRUSH:
            return False

        self.setCurrentTarget(target)
        self.anyNewActionDetected = True
        self.agroTableDict[self.currentTarget].TotalAgro+=(self.weaponDict[self.MHWeapon].damage+11)*self.realMHFireRate+(self.weaponDict[self.MHWeapon].damage+12)* self.realOHFireRate
        # can't tell which is which ,so all swings goes to split proportionally.
        self.agroTableDict[self.currentTarget].TiedSwing += 1
        self.agroTableDict[self.currentTarget].MHSwing = int(self.agroTableDict[self.currentTarget].TiedSwing * self.realMHFireRate)
        self.agroTableDict[self.currentTarget].OHSwing = int(self.agroTableDict[self.currentTarget].TiedSwing * self.realOHFireRate)
        return True

    def combo_1hb_shield(self,hitType:int,target:str):
        if hitType!=CRUSH:
            return False

        self.setCurrentTarget(target)
        self.anyNewActionDetected = True
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
        if hitType!=PUNCH:
            return False

        self.setCurrentTarget(target)
        self.anyNewActionDetected = True
        self.agroTableDict[self.currentTarget].TotalAgro+=(self.weaponDict[self.MHWeapon].damage+11)*self.realMHFireRate+(self.weaponDict[self.MHWeapon].damage+12)* self.realOHFireRate
        # can't tell which is which , so all swings goes to split equally.
        self.agroTableDict[self.currentTarget].TiedSwing += 1
        self.agroTableDict[self.currentTarget].MHSwing = int(self.agroTableDict[self.currentTarget].TiedSwing * self.realMHFireRate)
        self.agroTableDict[self.currentTarget].OHSwing = int(self.agroTableDict[self.currentTarget].TiedSwing * self.realOHFireRate)
        return True

    def combo_h2h_shield(self,hitType:int,target:str):
        if hitType!=PUNCH:
            return False

        self.setCurrentTarget(target)
        self.anyNewActionDetected = True
        self.agroTableDict[self.currentTarget].TotalAgro+=(self.weaponDict[self.MHWeapon].damage+11)
        self.agroTableDict[self.currentTarget].MHSwing += 1
        return True

    def combo_2hp_NA(self,hitType:int,target:str):
        if hitType!=PIERCE:
            return False

        self.setCurrentTarget(target)
        self.anyNewActionDetected = True
        self.agroTableDict[self.currentTarget].TotalAgro+=(self.weaponDict[self.MHWeapon].damage+self.weaponDict[self.MHWeapon].damageBonus)
        self.agroTableDict[self.currentTarget].MHSwing += 1
        return True

    def combo_2hb_NA(self,hitType:int,target:str):
        if hitType!=CRUSH:
            return False

        self.setCurrentTarget(target)
        self.anyNewActionDetected = True
        self.agroTableDict[self.currentTarget].TotalAgro+=(self.weaponDict[self.MHWeapon].damage+self.weaponDict[self.MHWeapon].damageBonus)
        self.agroTableDict[self.currentTarget].MHSwing += 1
        return True

    def combo_2hs_NA(self,hitType:int,target:str):
        if hitType!=SLASH:
            return False

        self.setCurrentTarget(target)
        self.anyNewActionDetected = True
        self.agroTableDict[self.currentTarget].TotalAgro+=(self.weaponDict[self.MHWeapon].damage+self.weaponDict[self.MHWeapon].damageBonus)
        self.agroTableDict[self.currentTarget].MHSwing += 1
        return True



    def checkProcEffects(self,line:str):

        if self.weaponDict[self.MHWeapon].procResistMsg!="":
            index=line[26:].find(self.weaponDict[self.MHWeapon].procResistMsg)
            if index==0 or index==1:
                if self.currentTarget !="":
                    self.agroTableDict[self.currentTarget].ProcCount+=1
                    self.agroTableDict[self.currentTarget].TotalAgro+=self.weaponDict[self.MHWeapon].procAgro
                    self.updateAgroMeter()
                else:
                    self.agroToUnknowTarget+=self.weaponDict[self.MHWeapon].procAgro
                return True

        if self.weaponDict[self.OHWeapon].procResistMsg!="":
            index=line[26:].find(self.weaponDict[self.OHWeapon].procResistMsg)
            if index==0 or index==1:
                if self.currentTarget !="":
                    self.agroTableDict[self.currentTarget].ProcCount+=1
                    self.agroTableDict[self.currentTarget].TotalAgro+=self.weaponDict[self.OHWeapon].procAgro
                    self.updateAgroMeter()
                else:
                    self.agroToUnknowTarget+=self.weaponDict[self.OHWeapon].procAgro
                return True

        if self.currentMHProcLandMessage!="":
            index=line[26:].find(self.currentMHProcLandMessage)
            if index==0 or index==1:
                self.agroTableDict[self.currentTarget].ProcCount+=1
                self.agroTableDict[self.currentTarget].TotalAgro+=self.weaponDict[self.MHWeapon].procAgro
                self.updateAgroMeter()
                return True

        if self.currentOHProcLandMessage!="":
            index=line[26:].find(self.currentOHProcLandMessage)
            if index==0 or index==1:
                self.agroTableDict[self.currentTarget].ProcCount+=1
                self.agroTableDict[self.currentTarget].TotalAgro+=self.weaponDict[self.OHWeapon].procAgro
                self.updateAgroMeter()
                return True



        return False


    def checkSpellEffects(self,line:str):


        if line[26:]==" Your Forlorn Totem of Rolfron Zek begins to glow.\n":    #your casting a totem stun.
            self.isCastingTotem=True
            self.anyNewActionDetected = True
            return True

        index=line.find(" is stunned.\n")
        if index!=-1 and self.isCastingTotem:
            self.agroToUnknowTarget+=460                                    #totem agro is 460
            self.isCastingTotem=False
            self.anyNewActionDetected = True
            self.updateAgroMeter()
            return True

        if line[26:]==" Your target resisted the Holy Might spell.\n":    #your casting a totem stun.
            self.agroToUnknowTarget+=460                                    #totem agro is 460
            self.isCastingTotem=False
            self.anyNewActionDetected = True
            self.updateAgroMeter()
            return True


        if line[26:]==" Your Bioluminescent Orb begins to glow.\n":    #your casting a bio orb.
            self.isCastingBioOrb=True
            self.anyNewActionDetected = True
            return True

        index=line.find(" is blinded by a flash of light.\n")
        if index!=-1 and self.isCastingBioOrb:
            self.agroToUnknowTarget+=800                                    #bio orb agro is 800
            self.isCastingBioOrb=False
            self.anyNewActionDetected = True
            self.updateAgroMeter()
            return True

        if line[26:]==" Your target resisted the Blinding Luminance spell.\n":    #your casting a bio orb.
            self.agroToUnknowTarget+=800                                    #bio orb agro is 800
            self.isCastingBioOrb=False
            self.anyNewActionDetected = True
            self.updateAgroMeter()
            return True

        if line[26:]==" Your spell is interrupted.\n":                    #spell interruption
            self.isCastingTotem=False
            self.isCastingBioOrb=False
            self.anyNewActionDetected = True
            return True



        index=line[26:].find(" is surrounded by darkness.\n")
        if index!=-1 and self.currentTarget==line[27:26+index]:
            self.agroTableDict[self.currentTarget].TotalAgro+=400                  #scepter agro is 400
            self.anyNewActionDetected = True
            self.updateAgroMeter()
            return True

        if line[26:]==" Your target resisted the Clinging Darkness spell.\n":    #scepter agro is 400
            self.agroToUnknowTarget+=400
            self.anyNewActionDetected = True
            self.updateAgroMeter()
            return True




        return False

    def checkAnySeenMobs(self,line:str):

        return False


    def  checkAndSetCurrentTarget(self,line:str):

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


    def recompileProcLandMsg(self,capitalized_mobName:str):

        if capitalized_mobName == "":
            return

        if self.weaponDict[self.MHWeapon].procLandMsg != "":
            self.currentMHProcLandMessage = self.weaponDict[self.MHWeapon].procLandMsg.replace("Someone",capitalized_mobName, 1)
        if self.weaponDict[self.OHWeapon].procLandMsg != "":
            self.currentOHProcLandMessage = self.weaponDict[self.OHWeapon].procLandMsg.replace("Someone",capitalized_mobName, 1)

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
        agroMeterStringYellow+="\nEqual Flex : {:,}".format(int(at.TotalAgro / 50))
        if self.agroToUnknowTarget>0:
            agroMeterStringYellow += "\nSpell Agro : {:0.0f}".format(self.agroToUnknowTarget)
        self.label_agroMeterYellow.setText(agroMeterStringYellow)

        #agroMeterString="\n===================="
        agroMeterStringGreen=f"\nMain  Hand : {self.MHWeapon}"+" {:,}".format(at.MHSwing)
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
        time_str = datetime.datetime.strftime(curr_time, '%Y-%m-%d %H:%M:%S')
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

    def hideAgroMeterHandler(self):

        if self.isHide:
            return

        if self.anyNewActionDetected:
            self.anyNewActionDetected=False
            return

        self.hideAgroMeter()

    def hideAgroMeter(self):
        self.isHide = True
        self.label_agroMeterGreen.hide()
        self.label_agroMeterYellow.hide()
        self.label_errorMessage.hide()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AgroMeter()
    window.show()
    window.resize(500,200)


    #demo run of this tool
    window.testAgroMeter()

    sys.exit(app.exec_())
