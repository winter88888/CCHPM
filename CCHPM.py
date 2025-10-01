import sys
import os
import time
from ui_CFGWIN import *
from CCHWIN import *
from AgroMeter import *
from PyQt5 import QtCore, QtGui, QtWidgets
import pathlib
import datetime
import pickle
import random
from systemtray import *
import WeaponEditor
import resource
from LogTaker import *
from IngameCommand import *
from StrafeRunLine import *
from LogImitation import *
from BotGinaProxy import *
from BackupRestoreDialog import *
from CopyUI import *

import time
import functools
from collections import defaultdict

'''# 性能统计字典 - 添加到文件开头
performance_stats = defaultdict(list)


def performance_monitor(func):
    """性能监控装饰器"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        elapsed = (end_time - start_time) * 1000  # 转换为毫秒

        # 记录性能数据
        performance_stats[func.__name__].append(elapsed)

        # 如果耗时超过阈值，记录警告
        if elapsed > 50:  # 50ms阈值
            try:
                args[0].msg(f"PERF WARNING: {func.__name__} took {elapsed:.2f}ms")
            except:
                pass

        return result

    return wrapper
'''


from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
class LogFileHandler(FileSystemEventHandler):
    def __init__(self, parent):
        self.parent = parent  # 保留对CFGWIN的引用

    def on_modified(self, event):
        if not event.is_directory:
            try:
                if os.access(event.src_path, os.R_OK) and self.parent.applyLogfileFilter(event.src_path):
                    self.parent.handle_log_change(event.src_path)
            except Exception as e:
                self.parent.msg(f"ERROR: Cannot access file {event.src_path}: {str(e)}")


#const definition
SERVERLIST = {"Any": 0, "P1999Green": 1, "project1999": 2, "KingdomDragons": 3}
POSlIST = {"On bar":0, "Under bar":1, "Above bar":2}
COLOR_DICT = {
            "Green": 0,
            "Red": 1,
            "Blue": 2,
            "Black": 3,
            "Brown": 4,
            "White": 5,
            "Yellow": 6,
            "Orange": 7,
            "Purple": 8,
            "Teal": 9
        }
LOG_MONITORING_INTERVAL=10 # 10 milliseconds
#LOGDIR_MONITORING_INTERVAL=3000 # 3 seconds
CCHWIN_MONITORING_INTERVAL=5000  # 5 seconds for garbage collection
TEST_CHAIN_INTERVAL=1000
CLEANSING_AGRO_METER_INTERVAL=10        #default is to cleanse agro table dictionary every 10s
HIDE_AGRO_METER_INTERVAL=60             #default is to hide agro meter if no new agro action in a minute
AGRO_TABLE_EXPIRE_DURATION= 10          #default is 10 mins for unseen slain msg, hence need to clear that mob.
ONLINE_SYNC_INTERVAL=100                  #default is to send data to server every 1/10 second.






class CFGWIN(QWidget,Ui_CFGWIN):
    def __init__(self):
        super(CFGWIN,self).__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon(":/CCHPM.ico"))
        self.setFixedSize(self.size())
        self.cchwin = CCHWIN()
        self.agroMeter=AgroMeter()
        self.agroMeter.callback_to_CCHPM_setOnlineChannel=self.setOnlineChannel
        self.we=WeaponEditor.WeaponEditor()
        self.we.callbackToMain=self
        self.logTaker = LogTaker()
        self.ifRALogTakerEnabled=False
        self.autoPopupRALogTaker=False
        self.ingameCommands=IngameCommand(self)
        self.ifIngameDiscordCommandEnabled=False
        self.ifProxyIngameCommandEnabled=False
        self.left_strafe_line = StrafeLine()
        self.left_strafe_line.setWindowTitle("Left Strafe Line")
        self.right_strafe_line = StrafeLine()
        self.right_strafe_line.setWindowTitle("Right Strafe Line")
        self.ifRightStrafeLineEnabled=False
        self.ifLeftStrafeLineEnabled=False
        self.file_change_counter = 0
        self.ifBotGinaProxyEnabled = False
        self.bot_gina_proxy = BotGinaProxy(self)

        self.initializing = True
        self.msg('INFO:Initializing configuration.Please wait...')
        self.configdata={}
        self.initialize_from_configfile()
        self.lastSizesOfLogFiles={}
        self.curLogFile=''
        self.logfilechanged=False
        self.blockSequenceNumber=0

        self.yourName="none"
        self.f = None
        #self.defaultwindowflags=self.cchwin.windowFlags()
        self.init_style=self.style()

        self.cchwin_timer = QTimer(self.cchwin)
        self.cchwin_timer.timeout.connect(self.cchwin.destroy_ani)
        self.cchwin_timer.start(CCHWIN_MONITORING_INTERVAL)
        self.testchain_timer = QTimer(self)
        self.testchain_timer.timeout.connect(self.testchain)



        self.pushButton_6.setEnabled(False)
        self.pushButton_7.setEnabled(False)
        self.pushButton_8.setEnabled(False)
        self.pushButton_9.setEnabled(False)

        self.label_20.setEnabled(False)
        self.label_21.setEnabled(False)
        self.spinBox_11.setEnabled(False)
        self.spinBox_12.setEnabled(False)

        self.ti = TrayIcon(self)
        self.ti.show()
        self.ti.sync_menu()

        self.locked= True
        self.showcchwin = True
        self.testchain_started=False

        self.cleansingAgroMeter_timer = QTimer(self.agroMeter)
        self.cleansingAgroMeter_timer.timeout.connect(self.agroMeter.cleansingTimerHandler)
        self.cleansingAgroMeter_timer.start(CLEANSING_AGRO_METER_INTERVAL*1000)

        self.hideAgroMeter_timer = QTimer(self.agroMeter)
        self.hideAgroMeter_timer.timeout.connect(self.agroMeter.hideAgroMeterHandler)
        self.hideAgroMeter_timer.start(self.hideAgroMeterInterval*1000)

        self.onlineSyncHandler_timer = QTimer(self.agroMeter)
        self.onlineSyncHandler_timer.timeout.connect(self.agroMeter.onlineSyncHandler)
        if self.agroMeterOnlineSyncEnabled:
            self.onlineSyncHandler_timer.start(ONLINE_SYNC_INTERVAL)

        # 启动监控
        self.scanLogDir()

        self.log_imitation_dialog = None

        # Text to speak initialisation
        self.cchwin.tts_handler=self.TTS
        #here you can add more handler to other module if needed

    '''
        # 添加性能报告定时器
        self.perf_report_timer = QTimer(self)
        self.perf_report_timer.timeout.connect(self.report_performance)
        self.perf_report_timer.start(10000)  # 每10秒报告一次

    def report_performance(self):
        """性能报告功能"""
        if not performance_stats:
            return

        report_lines = ["Performance Report:"]
        for func_name, times in performance_stats.items():
            if times:
                avg = sum(times) / len(times)
                max_time = max(times)
                report_lines.append(f"{func_name}: avg={avg:.2f}ms, max={max_time:.2f}ms, calls={len(times)}")

        # 输出到日志
        self.msg("\n".join(report_lines))
        print("\n".join(report_lines))

        # 清空统计数据
        performance_stats.clear()
    '''

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.showMinimized()  # 按 ESC 最小化窗口
            event.accept()  # 标记事件已处理
        else:
            super().keyPressEvent(event)  # 其他按键交给父类处理

    def closeEvent(self,event):

        """确保关闭时停止observer"""
        if hasattr(self, 'observer'):
            try:
                if self.observer.is_alive():
                    self.observer.stop()
                    self.observer.join(timeout=1)  # 添加超时防止卡死
            except RuntimeError as e:
                self.msg(f"WARNING: {str(e)}")
            except Exception as e:
                self.msg(f"ERROR: Failed to stop directory monitor: {str(e)}")

        self.cfgwin_geo = self.geometry()
        self.MHWeapon = self.agroMeter.MHWeapon
        self.OHWeapon = self.agroMeter.OHWeapon
        self.saveconfig()

        self.cchwin.close()
        self.agroMeter.close()
        self.we.close()
        self.logTaker.close()
        self.agroMeter.window_network.close()
        self.agroMeter.toggle_connection(False)

        self.ingameCommands.shutdown()
        self.ingameCommands.save_settings()

        event.accept()
        QtWidgets.qApp.quit()

    def hideEvent(self,event):

        self.setWindowFlags(QtCore.Qt.SplashScreen)

        event.accept()

    def weaponEditeComplete(self):
        self.agroMeter.initializeWeaponBase()

    def msg(self,message:str):
        curr_time = datetime.datetime.now()
        time_str = datetime.datetime.strftime(curr_time, '%Y-%m-%d %H:%M:%S')

        self.label_2.setText('['+time_str+']  '+message)
        #time_str = datetime.datetime.strftime(curr_time, '%Y-%m-%d %H:%M:%S') 这里需要加入显示毫秒，以便后续用于REPLAY。
        with open('CCHPM RUN LOG.txt', 'a',encoding='utf-8') as f:
            message=message.rstrip()
            f.write('['+time_str+']  '+message+'\n')
            f.flush()

    def loaddefaultconfig(self):
        # 下面设置程序各配置参数的默认值，如果没有INI文件或INI文件损坏，将以这些默认值创建缺省ini文件，从此后再打开程序还是以INI文件为准。
        # to add more default config data...

        self.configdata['eqLogDir'] = 'C:\\EQ main directory\Logs'
        self.configdata['serverSlect'] = 'Any'
        self.configdata['ifautostart'] = True


        self.configdata['ifstartCHMonitor'] = True
        self.configdata['mark_pos'] = 'On bar'
        self.configdata['chInterval'] = 1
        self.configdata['cchwinGeo'] = QtCore.QRect(586, 669, 358, 126)
        self.configdata['railheight'] = 20
        self.configdata['cchwinwidthMargin'] = 2
        self.configdata['heigthMargin'] = 2
        self.configdata['cfgwin_geo'] = QtCore.QRect(546, 257, 827, 526)
        self.configdata['hotkeyFormatstr'] = 'KCH - tankname - ###'
        self.configdata['hotkeyFormatList'] = ['KCH - tankname - ###','### - CH - tankname','GG ### CH -- tankname']
        self.configdata['mtNameLength'] = 7
        self.configdata['mtNameMargin'] = 1



        self.configdata['agroMeterEnabled'] = True
        self.configdata['agroMeterGeo'] = QtCore.QRect(1003, 664, 267, 146)
        self.configdata['agroNetworkMeterGeo'] = QtCore.QRect(1282, 663, 296, 155)
        self.configdata['hideAgroMeterInterval'] =HIDE_AGRO_METER_INTERVAL
        self.configdata['agroTableExpireDuration'] =AGRO_TABLE_EXPIRE_DURATION
        self.configdata['weaponDict']={"None":("???","???")}
        self.configdata['agroMeterOpacity']=100
        self.configdata['mainHandSwingRate']=569             #This initial value might not be accurate. Need more test. but close to what it truly is for Warrior.
        self.configdata['agroMeterOnlineSyncEnabled'] = True
        self.configdata['latencyTolerance'] = 100            #+/-100ms tolerance window
        self.configdata['ifShowEqualDBGBEnabled'] = True
        self.configdata['ifShowEqualSlowEnabled'] = True
        self.configdata['ifShowTankDiscEnabled'] =  False

        self.configdata['ifRALogTakerEnabled'] = True
        self.configdata['autoPopupRALogTaker'] = False
        self.configdata['tellWaitingTime']=10                #minute
        self.configdata["logTakerGeo"] = QtCore.QRect(358, 319, 1167, 587)
        self.configdata['max_loaded_event']=20               #20 events

        self.configdata['leftStrafeLineGeo'] = QtCore.QRect(394, 200, 132, 500)
        self.configdata['rightStrafeLineGeo'] = QtCore.QRect(1239, 200, 123, 500)
        self.configdata['leftStrafeLineEnabled'] = False
        self.configdata['rightStrafeLineEnabled'] = False
        self.configdata['strafe_line_width'] = 3
        self.configdata['strafe_line_color'] = "Red"

        self.configdata['ifBotGinaProxyEnabled'] = True
        self.configdata['ifMobSwingTimerEnabled'] = True

        self.configdata['mobSwingTimerGeo']: QtCore.QRect(586, 831, 351, 45)

        self.configdata['ifTTSEnabled'] = False


    def get_config_date_safely(self, argument: str):
        try:
            data = self.configdata[argument]
            return data
        except KeyError:
            # 为所有在 loaddefaultconfig 中定义的键提供默认值
            default_values = {
                "eqLogDir": 'C:\\EQ main directory\\Logs',
                "serverSlect": 'Any',
                "ifautostart": True,
                "ifstartCHMonitor": True,
                "mark_pos": 'On bar',
                "chInterval": 1,
                "cchwinGeo": QtCore.QRect(586, 669, 358, 126),
                "railheight": 20,
                "cchwinwidthMargin": 2,
                "heigthMargin": 2,
                "cfgwin_geo": QtCore.QRect(546, 257, 827, 526),
                "hotkeyFormatstr": 'KCH - tankname - ###',
                "hotkeyFormatList": ['KCH - tankname - ###', '### - CH - tankname', 'GG ### CH -- tankname'],
                "mtNameLength": 7,
                "mtNameMargin": 1,
                "agroMeterEnabled": True,
                "agroMeterGeo": QtCore.QRect(1003, 664, 267, 146),
                "agroNetworkMeterGeo": QtCore.QRect(1282, 663, 296, 155),
                "hideAgroMeterInterval": HIDE_AGRO_METER_INTERVAL,
                "agroTableExpireDuration": AGRO_TABLE_EXPIRE_DURATION,
                "weaponDict": {"None": ("???", "???")},
                "agroMeterOpacity": 100,
                "mainHandSwingRate": 569,
                "agroMeterOnlineSyncEnabled": True,
                "latencyTolerance": 100,
                "ifShowEqualDBGBEnabled": True,
                "ifShowEqualSlowEnabled": True,
                "ifShowTankDiscEnabled": False,
                "ifRALogTakerEnabled": True,
                "autoPopupRALogTaker": False,
                "tellWaitingTime": 10,
                "logTakerGeo": QtCore.QRect(358, 319, 1167, 587),
                "max_loaded_event": 20,
                "leftStrafeLineGeo": QtCore.QRect(394, 200, 132, 500),
                "rightStrafeLineGeo": QtCore.QRect(1239, 200, 123, 500),
                "leftStrafeLineEnabled": False,
                "rightStrafeLineEnabled": False,
                "strafe_line_width": 3,
                "strafe_line_color": "Red",
                "ifBotGinaProxyEnabled":True,
                "ifMobSwingTimerEnabled":True,
                "mobSwingTimerGeo":QtCore.QRect(586, 831, 351, 45),
                "ifTTSEnabled":False
            }

            # 返回默认值，如果键不存在于默认值中则返回 None
            return default_values.get(argument, None)

    def initialize_from_configfile(self):
        if os.path.exists('CCHPM.ini'):
            with open('CCHPM.ini', 'rb') as f:
                try:
                    self.configdata = pickle.load(f)
                except Exception as e:
                    self.msg(f'ERROR:{str(e)}.Using default configuration')
                    self.loaddefaultconfig()
        else:
            self.msg("INFO:CCHPM.ini doesn't exist.Using default configuration")
            self.loaddefaultconfig()

        try:
            # 获取配置值，如果为None则报错退出
            def get_config_or_exit(key, description):
                value = self.get_config_date_safely(key)
                if value is None:
                    self.msg(f"FATAL ERROR: Missing required configuration '{key}' ({description})")
                    QtWidgets.QApplication.quit()
                    sys.exit(1)
                return value

            # 基础配置
            self.eqLogDir = get_config_or_exit('eqLogDir', 'EQ log directory')
            self.lineEdit.setText(self.eqLogDir)

            self.serverSlect = get_config_or_exit('serverSlect', 'Server selection')
            self.comboBox.setCurrentIndex(SERVERLIST[self.serverSlect])

            self.ifautostart = get_config_or_exit('ifautostart', 'Auto start flag')
            self.started = self.ifautostart

            self.ifstartCHMonitor = get_config_or_exit('ifstartCHMonitor', 'CH monitor enabled flag')
            self.checkBox.setChecked(self.ifstartCHMonitor)
            if self.ifstartCHMonitor:
                self.checkBox.setStyleSheet("QCheckBox { color: green; }")
            else:
                self.checkBox.setStyleSheet("QCheckBox { color: red; }")

            self.mark_pos = get_config_or_exit('mark_pos', 'Mark position')
            self.comboBox_3.setCurrentIndex(POSlIST[self.mark_pos])
            self.cchwin.mark_pos = self.mark_pos

            self.chInterval = get_config_or_exit('chInterval', 'CH interval')
            self.spinBox_4.setValue(self.chInterval)
            self.cchwin.setinterval(self.chInterval)

            self.cchwinGeo = get_config_or_exit('cchwinGeo', 'CCH window geometry')
            self.cchwin.setGeometry(self.cchwinGeo)

            self.railheight = get_config_or_exit('railheight', 'Rail height')
            self.spinBox.setValue(self.railheight)
            self.cchwin.railheight = self.railheight

            self.mtNameLength = get_config_or_exit('mtNameLength', 'MT name length')
            self.spinBox_9.setValue(self.mtNameLength)

            self.mtNameMargin = get_config_or_exit('mtNameMargin', 'MT name margin')
            self.spinBox_10.setValue(self.mtNameMargin)
            self.cchwin.mt_name_margin = self.mtNameMargin

            self.logfile_moniter_timer = QTimer(self)
            self.logfile_moniter_timer.timeout.connect(self.scanCurrentLog)

            if self.started:
                self.pushButton_3.setText("ON AIR")
                self.pushButton_3.setFont(self.font())
                self.pushButton_3.setStyleSheet('background-color: green;')
                self.logfile_moniter_timer.start(LOG_MONITORING_INTERVAL)
            else:
                self.pushButton_3.setText("PAUSED")
                self.pushButton_3.setFont(self.font())
                self.pushButton_3.setStyleSheet('background-color: red;')

            self.cchwinwidthMargin = get_config_or_exit('cchwinwidthMargin', 'CCH window width margin')
            self.cchwin.widthMargin = self.cchwinwidthMargin
            self.spinBox_3.setValue(self.cchwinwidthMargin)

            self.cchwinheigthMargin = get_config_or_exit('heigthMargin', 'CCH window height margin')
            self.cchwin.heigthMargin = self.cchwinheigthMargin
            self.spinBox_2.setValue(self.cchwinheigthMargin)

            self.cfgwin_geo = get_config_or_exit('cfgwin_geo', 'Configuration window geometry')
            self.setGeometry(self.cfgwin_geo)

            self.hotkeyFormatstr = get_config_or_exit('hotkeyFormatstr', 'Hotkey format string')
            self.hotkeyFormat = self.hotkeyFormatParse(self.hotkeyFormatstr)
            self.hotkeyFormatList = get_config_or_exit('hotkeyFormatList', 'Hotkey format list')
            self.comboBox_2.clear()
            for i in range(len(self.hotkeyFormatList)):
                self.comboBox_2.addItem(self.hotkeyFormatList[i])
            self.comboBox_2.setCurrentText(self.hotkeyFormatstr)
            self.comboBox_2.setCurrentIndex(self.comboBox_2.findText(self.hotkeyFormatstr))
            self.pushButton_12.setEnabled(False)

            self.cchwin.restart_ani()
            self.cchwin.reAdjustRails()

            # Agro Meter 配置
            self.agroMeterEnabled = get_config_or_exit('agroMeterEnabled', 'Agro meter enabled flag')
            self.checkBox_2.setChecked(self.agroMeterEnabled)
            if self.agroMeterEnabled:
                self.checkBox_2.setStyleSheet("QCheckBox { color: green; }")
            else:
                self.checkBox_2.setStyleSheet("QCheckBox { color: red; }")

            self.agroMeterGeo = get_config_or_exit('agroMeterGeo', 'Agro meter geometry')
            self.agroMeter.setGeometry(self.agroMeterGeo)
            self.agroNetworkMeterGeo = get_config_or_exit('agroNetworkMeterGeo', 'Agro network meter geometry')
            self.agroMeter.window_network.setGeometry(self.agroNetworkMeterGeo)
            self.mobSwingTimerGeo = get_config_or_exit('mobSwingTimerGeo', 'Mob swing timer geometry')
            self.agroMeter.window_mst.setGeometry(self.mobSwingTimerGeo)
            self.agroMeter.reAdjustPanel()


            self.hideAgroMeterInterval = get_config_or_exit('hideAgroMeterInterval', 'Hide agro meter interval')
            self.spinBox_23.setValue(int(self.hideAgroMeterInterval))
            self.agroTableExpireDuration = get_config_or_exit('agroTableExpireDuration', 'Agro table expire duration')
            self.agroMeter.agroTableExpireDuration = self.agroTableExpireDuration
            self.spinBox_25.setValue(self.agroTableExpireDuration)

            self.weaponDict = get_config_or_exit('weaponDict', 'Weapon dictionary')
            self.MHWeapon = "???"
            self.OHWeapon = "???"
            self.agroMeterOpacity = get_config_or_exit('agroMeterOpacity', 'Agro meter opacity')
            self.spinBox_13.setValue(self.agroMeterOpacity)
            self.agroMeter.label_agroMeterGreen.setWindowOpacity(float(self.agroMeterOpacity) / 100)
            self.agroMeter.label_agroMeterYellow.setWindowOpacity(float(self.agroMeterOpacity) / 100)
            self.agroMeter.label_errorMessage.setWindowOpacity(float(self.agroMeterOpacity) / 100)

            self.mainHandSwingRate = get_config_or_exit('mainHandSwingRate', 'Main hand swing rate')
            self.spinBox_14.setValue(self.mainHandSwingRate)
            self.agroMeter.basicMHFireRate = float(self.mainHandSwingRate) / 1000
            self.agroMeter.basicOHFireRate = 1 - self.agroMeter.basicMHFireRate
            self.agroMeter.setup1hWeaponFireRate()

            self.agroMeterOnlineSyncEnabled = get_config_or_exit('agroMeterOnlineSyncEnabled',
                                                                 'Agro meter online sync enabled')
            self.agroMeter.isOnlineSyncEnabled = self.agroMeterOnlineSyncEnabled
            self.agroMeter.toggle_connection(self.agroMeterOnlineSyncEnabled)
            self.checkBox_5.setChecked(self.agroMeterOnlineSyncEnabled)

            self.latencyTolerance = get_config_or_exit('latencyTolerance', 'Latency tolerance')
            self.agroMeter.latencyTolerance = self.latencyTolerance
            self.spinBox_24.setValue(self.latencyTolerance)

            self.ifShowEqualDBGBEnabled = get_config_or_exit('ifShowEqualDBGBEnabled', 'Show equal DB/GB flag')
            self.agroMeter.ifShowEqualDBGBEnabled = self.ifShowEqualDBGBEnabled
            self.checkBox_6.setChecked(self.ifShowEqualDBGBEnabled)

            self.ifShowEqualSlowEnabled = get_config_or_exit('ifShowEqualSlowEnabled', 'Show equal slow flag')
            self.agroMeter.ifShowEqualSlowEnabled = self.ifShowEqualSlowEnabled
            self.checkBox_7.setChecked(self.ifShowEqualSlowEnabled)

            self.ifShowTankDiscEnabled = get_config_or_exit('ifShowTankDiscEnabled', 'Show tank disc flag')
            self.agroMeter.ifShowTankDiscEnabled = self.ifShowTankDiscEnabled

            # RA Log Taker 配置
            self.ifRALogTakerEnabled = get_config_or_exit('ifRALogTakerEnabled', 'RA log taker enabled flag')
            self.checkBox_3.setChecked(self.ifRALogTakerEnabled)
            if self.ifRALogTakerEnabled:
                self.checkBox_3.setStyleSheet("QCheckBox { color: green; }")
            else:
                self.checkBox_3.setStyleSheet("QCheckBox { color: red; }")

            self.autoPopupRALogTaker = get_config_or_exit('autoPopupRALogTaker', 'Auto popup RA log taker flag')
            self.checkBox_4.setChecked(self.autoPopupRALogTaker)
            self.logTaker.autoPopupRALogTaker = self.autoPopupRALogTaker
            self.tellWaitingTime = get_config_or_exit('tellWaitingTime', 'Tell waiting time')
            self.spinBox_24.setValue(self.tellWaitingTime)
            self.logTaker.tellWaitingTime = self.tellWaitingTime
            self.logTakerGeo = get_config_or_exit("logTakerGeo", 'Log taker geometry')
            self.logTaker.setGeometry(self.logTakerGeo)

            self.max_loaded_event = get_config_or_exit('max_loaded_event', 'Max loaded events')
            self.spinBox_27.setValue(self.max_loaded_event)
            self.logTaker.max_loaded_event_handler(self.max_loaded_event)

            # 游戏内命令配置
            valid = self.ingameCommands.verify_webhook_config()
            if valid:
                self.ifIngameDiscordCommandEnabled = True
                self.checkBox_8.setChecked(True)
                self.checkBox_8.setStyleSheet("QCheckBox { color: green; }")
            else:
                self.ifIngameDiscordCommandEnabled = False
                self.checkBox_8.setChecked(False)
                self.checkBox_8.setStyleSheet("QCheckBox { color: red; }")

            result = self.ingameCommands.verify_proxy_config()
            if result == "N/A":
                self.checkBox_9.setEnabled(False)
            elif result == "YES":
                self.checkBox_9.setEnabled(True)
                self.ifProxyIngameCommandEnabled = True
                self.checkBox_9.setChecked(True)
            elif result == "NO":
                self.checkBox_9.setEnabled(True)
                self.ifProxyIngameCommandEnabled = False
                self.checkBox_9.setChecked(False)

            # 走直线配置
            self.leftStrafeLineGeo = get_config_or_exit('leftStrafeLineGeo', 'Left strafe line geometry')
            self.rightStrafeLineGeo = get_config_or_exit('rightStrafeLineGeo', 'Right strafe line geometry')
            self.left_strafe_line.setGeometry(self.leftStrafeLineGeo)
            self.right_strafe_line.setGeometry(self.rightStrafeLineGeo)
            self.left_strafe_line.reAdjustLines()
            self.right_strafe_line.reAdjustLines()

            self.ifLeftStrafeLineEnabled = get_config_or_exit('leftStrafeLineEnabled', 'Left strafe line enabled flag')
            self.ifRightStrafeLineEnabled = get_config_or_exit('rightStrafeLineEnabled',
                                                               'Right strafe line enabled flag')
            self.checkBox_10.setChecked(self.ifLeftStrafeLineEnabled)
            self.checkBox_11.setChecked(self.ifRightStrafeLineEnabled)
            if self.ifLeftStrafeLineEnabled:
                self.left_strafe_line.show_line()
            if self.ifRightStrafeLineEnabled:
                self.right_strafe_line.show_line()

            self.strafe_line_width = get_config_or_exit('strafe_line_width', 'Strafe line width')
            self.left_strafe_line.set_width(self.strafe_line_width)
            self.right_strafe_line.set_width(self.strafe_line_width)
            self.spinBox_28.setValue(self.strafe_line_width)

            self.strafe_line_color = get_config_or_exit('strafe_line_color', 'Strafe line color')
            self.left_strafe_line.set_color(self.strafe_line_color)
            self.right_strafe_line.set_color(self.strafe_line_color)
            self.comboBox_4.setCurrentIndex(COLOR_DICT[self.strafe_line_color])

            self.ifBotGinaProxyEnabled = get_config_or_exit('ifBotGinaProxyEnabled', 'Bot Gina Proxy enabled flag')
            self.checkBox_12.setChecked(self.ifBotGinaProxyEnabled)
            if self.ifBotGinaProxyEnabled:
                self.bot_gina_proxy.setProxyEnabled()
            else:
                self.bot_gina_proxy.setProxyDisabled()

            self.ifMobSwingTimerEnabled = get_config_or_exit('ifMobSwingTimerEnabled', 'Mob Swing Timer enabled flag')
            self.checkBox_13.setChecked(self.ifMobSwingTimerEnabled)
            cchwin_width = self.cchwinGeo.getRect()[2]
            self.agroMeter.set_mst_pixels_per_second(cchwin_width/10)
            if self.ifMobSwingTimerEnabled:
                self.agroMeter.setMobSwingTimerEnabled()
            else:
                self.agroMeter.setMobSwingTimerDisabled()

            self.ifTTSEnabled = get_config_or_exit('ifTTSEnabled', 'TTS enabled flag')
            self.checkBox_14.setChecked(self.ifTTSEnabled)



            self.msg("INFO:CCHPM finished initialization. Waiting for your order now.")


        except Exception as e:
            self.msg(f'ERROR:{str(e)} during initialization')
            # 发生其他异常时也退出程序
            QtWidgets.QApplication.quit()
            sys.exit(1)


    def hotkeyFormatParse(self,hotkeyFormatstr:str):
        #headkeyword,  ###,middlekeyword,tankname,tailkeyword.
        hotkeyFormat={}
        tmpstr = hotkeyFormatstr.replace(' ', '')
        pos_of_clericid=tmpstr.find("###")
        if pos_of_clericid == -1:
            self.msg("ERROR: Can not find ###(cleric id) in this CH format.")
            return None
        pos_of_tankname = tmpstr.find("tankname")
        if pos_of_tankname == -1:
            self.msg("ERROR: Can not find tankname(tankname) in this CH format.")
            return None
        if pos_of_clericid < pos_of_tankname:
            mark1,mark2=pos_of_clericid,pos_of_tankname
            hotkeyFormat['headkeyword'] = tmpstr[0:mark1]
            hotkeyFormat['middlekeyword'] = tmpstr[mark1 + 3:mark2]
            hotkeyFormat['tailkeyword'] = tmpstr[mark2 + 8:]
            hotkeyFormat['pos_of_clericid'] = pos_of_clericid
            hotkeyFormat['pos_of_tankname'] = pos_of_tankname
        else:
            mark1,mark2=pos_of_tankname,pos_of_clericid
            hotkeyFormat['headkeyword']=tmpstr[0:mark1]
            hotkeyFormat['middlekeyword'] = tmpstr[mark1+8:mark2]
            hotkeyFormat['tailkeyword'] = tmpstr[mark2+3:]
            hotkeyFormat['pos_of_clericid'] = pos_of_clericid
            hotkeyFormat['pos_of_tankname'] = pos_of_tankname

        if  hotkeyFormat['middlekeyword'] == '':
            self.msg("ERROR:CH Hotkey key words are empty.Need define a word in the middle of your CH hotkey to differentiate from others.")
            return None

        return hotkeyFormat


    def saveconfig(self):
        # to save more config data...
        self.ifautostart=self.started
        self.configdata['ifautostart'] = self.ifautostart
        self.configdata['eqLogDir'] = self.eqLogDir
        self.configdata['serverSlect'] = self.serverSlect

        self.configdata['ifstartCHMonitor']=self.ifstartCHMonitor
        self.configdata['mark_pos'] = self.mark_pos
        self.configdata['chInterval'] = self.chInterval
        self.cchwinGeo = self.cchwin.geometry()
        self.configdata['cchwinGeo'] = self.cchwinGeo
        self.configdata['railheight'] = self.railheight
        self.configdata['cchwinwidthMargin'] = self.cchwinwidthMargin
        self.configdata['heigthMargin'] = self.cchwinheigthMargin
        self.configdata['mtNameLength'] = self.mtNameLength
        self.configdata['mtNameMargin'] = self.mtNameMargin
        self.configdata['cfgwin_geo'] = self.cfgwin_geo
        self.configdata['hotkeyFormatstr'] = self.hotkeyFormatstr
        self.hotkeyFormatList=[]
        for i in range(self.comboBox_2.count()):
            self.hotkeyFormatList.append(self.comboBox_2.itemText(i))
        self.configdata['hotkeyFormatList'] = self.hotkeyFormatList.copy()

        self.configdata['agroMeterEnabled'] =  self.agroMeterEnabled
        self.agroMeterGeo = self.agroMeter.geometry()
        self.configdata['agroMeterGeo'] = self.agroMeterGeo
        self.agroNetworkMeterGeo=self.agroMeter.window_network.geometry()
        self.configdata['agroNetworkMeterGeo'] =self.agroNetworkMeterGeo

        self.mobSwingTimerGeo=self.agroMeter.window_mst.geometry()
        self.configdata['mobSwingTimerGeo'] =self.mobSwingTimerGeo


        self.configdata["hideAgroMeterInterval"] = self.hideAgroMeterInterval
        self.configdata['agroTableExpireDuration']=self.agroTableExpireDuration
        self.configdata['agroMeterOpacity']=self.agroMeterOpacity
        self.weaponDict[self.yourName]=(self.MHWeapon,self.OHWeapon)
        self.configdata['weaponDict']=self.weaponDict
        self.configdata['mainHandSwingRate']=self.mainHandSwingRate
        self.configdata['agroMeterOnlineSyncEnabled'] = self.agroMeterOnlineSyncEnabled
        self.configdata['latencyTolerance'] = self.latencyTolerance
        self.configdata['ifShowEqualDBGBEnabled'] = self.ifShowEqualDBGBEnabled
        self.configdata['ifShowEqualSlowEnabled'] = self.ifShowEqualSlowEnabled
        self.configdata['ifShowTankDiscEnabled'] =  self.ifShowTankDiscEnabled

        self.configdata['ifRALogTakerEnabled']=self.ifRALogTakerEnabled
        self.configdata['autoPopupRALogTaker']=self.autoPopupRALogTaker
        self.configdata['tellWaitingTime']=self.tellWaitingTime
        self.logTakerGeo = self.logTaker.geometry()
        self.configdata["logTakerGeo"] = self.logTakerGeo
        self.configdata["max_loaded_event"] = self.max_loaded_event


        self.leftStrafeLineGeo=self.left_strafe_line.geometry()
        self.rightStrafeLineGeo = self.right_strafe_line.geometry()
        self.configdata['leftStrafeLineGeo'] = self.leftStrafeLineGeo
        self.configdata['rightStrafeLineGeo'] = self.rightStrafeLineGeo
        self.configdata['leftStrafeLineEnabled'] = self.ifLeftStrafeLineEnabled
        self.configdata['rightStrafeLineEnabled'] = self.ifRightStrafeLineEnabled
        self.configdata['strafe_line_width'] = self.strafe_line_width
        self.configdata['strafe_line_color'] = self.strafe_line_color

        self.configdata['ifBotGinaProxyEnabled'] = self.ifBotGinaProxyEnabled
        self.configdata['ifMobSwingTimerEnabled'] = self.ifMobSwingTimerEnabled

        self.configdata['ifTTSEnabled'] = self.ifTTSEnabled


        with open('CCHPM.ini', 'wb') as f:
            pickle.dump(self.configdata, f)

    def openlogdir(self):
        logdir = QFileDialog.getExistingDirectory(self,"Select the EQ log directory","C:\\")
        if logdir != '':
            self.eqLogDir = str(pathlib.PureWindowsPath(logdir))
            self.lineEdit.setText(self.eqLogDir)
            self.saveconfig()
            self.scanLogDir()
            self.msg(f"INFO:The EQ log directory has been set to {self.eqLogDir} ")

        return

    def editfinished(self):
        path=self.lineEdit.text()
        if os.path.exists(path):
            self.eqLogDir=path
            self.saveconfig()
            self.scanLogDir()
            self.msg(f"INFO: The EQ log directory has been set to {path}")
        else:
            self.msg(f"ERROR: The path you input doens't exist. Path={path}")

    def serverSelect(self):

        if self.initializing:
            return

        self.serverSlect=self.comboBox.currentText()
        self.saveconfig()
        self.scanLogDir()
        self.msg(f'INFO:You choose to monitor log files on {self.serverSlect} server')
        self.msg("INFO:In case you need to be playing EQ on 2 servers at same time , log file detection function will abnormally does ping-pong handover every second. Then you will have to choose a specific server here to make it work properly.")

    def markPosition(self):
        if self.initializing:
            return

        self.mark_pos=self.comboBox_3.currentText()
        self.cchwin.mark_pos=self.mark_pos
        self.cchwin.restart_ani()
        self.cchwin.reAdjustRails()
        cchwin_width = self.cchwinGeo.getRect()[2]
        self.agroMeter.set_mst_pixels_per_second(cchwin_width / 10)
        self.saveconfig()

        self.msg(f'INFO:You choose to show marks {self.mark_pos}')



    def scanLogDir(self):
        """简化的目录扫描，处理Watchdog初始化和重启"""
        if not os.path.exists(self.eqLogDir):
            # 如果目录不存在，停止现有监控
            if hasattr(self, 'observer') and self.observer.is_alive():
                try:
                    self.observer.stop()
                    self.observer.join()
                except RuntimeError as e:
                    self.msg(f"WARNING: {str(e)}")
            return

        # 停止现有监控（如果正在运行）
        if hasattr(self, 'observer') and self.observer.is_alive():
            try:
                self.observer.stop()
                self.observer.join()
            except RuntimeError as e:
                self.msg(f"WARNING: {str(e)}")

        # 初始化或重启Watchdog监控
        try:
            if not hasattr(self, 'observer'):
                self.observer = Observer()
                self.log_handler = LogFileHandler(self)

            # 确保没有重复调度
            if self.observer._handlers:  # 检查是否有已注册的处理程序
                self.observer.unschedule_all()

            self.observer.schedule(self.log_handler, self.eqLogDir, recursive=False)

            # 仅在未运行时启动
            if not self.observer.is_alive():
                self.observer.start()

        except Exception as e:
            self.msg(f"ERROR: Failed to start directory monitor: {str(e)}")
            return

        # 扫描目录中的现有文件
        try:
            for fn in os.listdir(self.eqLogDir):
                path = os.path.join(self.eqLogDir, fn)
                if self.applyLogfileFilter(path) and path not in self.lastSizesOfLogFiles:
                    size = os.path.getsize(path)
                    self.lastSizesOfLogFiles[path] = size

                    """
                    # 如果没有当前日志文件，选择第一个匹配的文件
                    if not self.curLogFile:
                        self.curLogFile = path
                        self.yourName = path.split("_")[1]
                        self.msg(f"INFO: Initial log file set to: {self.curLogFile}")
                        self.logfilechanged = True
                    """


        except Exception as e:
            self.msg(f"ERROR: Error scanning log directory: {str(e)}")



    def handle_log_change(self, new_file):
        """处理日志文件变化"""
        try:
            new_size = os.path.getsize(new_file)
            #self.file_change_counter+=1
            #print(f"new file change:{new_file},current counter {self.file_change_counter}")
            # 如果是当前文件且大小变化了
            if new_file == self.curLogFile:
                if new_size != self.lastSizesOfLogFiles.get(new_file, 0):
                    self.lastSizesOfLogFiles[new_file] = new_size
                return


            # 如果是文件只是其他属性改变，但大小未变，不做处理，可能被其他程序打开过，但实际无修改。
            if self.lastSizesOfLogFiles.get(new_file,0) == new_size:
                return


            # 如果变化确实是文件切换了，有实质文件内容增长
            self.lastSizesOfLogFiles[new_file] = new_size

            if self.curLogFile != "":
                self.yourName = self.curLogFile.split("_")[1]
                self.saveWeaponForYourName()
            self.curLogFile = new_file
            self.yourName = self.curLogFile.split("_")[1]
            self.setWeaponsForYourName()
            self.setupYourNameToAggroMeter()
            self.logTaker.initialize_filters(self.yourName)
            self.setupYourNameToIngamecommand()
            self.setupYourNameToBotGinaProxy()
            self.msg(f"INFO:Current log file is: {self.curLogFile}")
            self.logfilechanged = True

        except Exception as e:
            self.msg(f"ERROR:Error handling log change: {str(e)}")




    '''
    def scanLogDir(self):


        currentSizesOfLogFiles={}
        for fn in os.listdir(self.eqLogDir):
            path = os.path.join(self.eqLogDir, fn)
            if self.applyLogfileFilter(path):
                currentSizesOfLogFiles[path]=os.path.getsize(path)

        if self.lastSizesOfLogFiles == {}:
            self.lastSizesOfLogFiles=currentSizesOfLogFiles
            return

        newfileset=set(currentSizesOfLogFiles.keys()) - set(self.lastSizesOfLogFiles.keys())
        if newfileset != set():
            self.lastSizesOfLogFiles=currentSizesOfLogFiles
            return

        for filename in currentSizesOfLogFiles.keys():
            if currentSizesOfLogFiles[filename] != self.lastSizesOfLogFiles[filename]:
                if self.curLogFile==filename:
                    self.lastSizesOfLogFiles[filename]=currentSizesOfLogFiles[filename]
                    return


                if self.curLogFile!="":
                    self.yourName = self.curLogFile.split("_")[1]
                    self.saveWeaponForYourName()
                self.curLogFile=filename
                self.yourName=self.curLogFile.split("_")[1]
                self.setWeaponsForYourName()
                self.setupYourNameToAggroMeter()
                self.logTaker.initialize_filters(self.yourName)
                self.setupYourNameToIngamecommand()
                self.msg(f"INFO:Current log file is: {self.curLogFile}")
                self.logfilechanged = True
                self.lastSizesOfLogFiles = currentSizesOfLogFiles
                return

    '''

    def applyLogfileFilter(self, path: str):

        if os.path.isdir(path):
            return False
        if os.path.splitext(path)[1] !='.txt':
            return False
        if not os.path.basename(path).startswith('eqlog_'):
            return False
        if self.serverSlect == 'Any':
            return True
        if os.path.basename(path).find(self.serverSlect) != -1:
            return True

        return False

    #@performance_monitor
    def scanCurrentLog(self):

        if self.curLogFile=='':
            return

        # log file更改后，此标志为true，当切换到新log file上后，此标志需复位为False
        if self.logfilechanged == True:

            if self.f is not None:
                self.f.close()
            try:
                self.f=open(self.curLogFile,encoding='utf-8')
                self.f.seek(0,2)
            except UnicodeDecodeError:
                self.msg(f"ERROR: File {self.curLogFile} is not UTF-8 encoded")
                return
            except IOError as e:
                self.msg(f"ERROR: Cannot open file {self.curLogFile}: {str(e)}")
                return
            self.logfilechanged = False

        if not self.f:
            return

        line=self.f.readline()
        self.blockSequenceNumber+=1
        if self.blockSequenceNumber > 4294967196:
            self.blockSequenceNumber =0

        while(line):
            self.uiControlCommandHandler(line)
            if self.started:
                if self.ifstartCHMonitor == True:
                    self.logProcessor(line)
                if self.agroMeterEnabled == True:
                    self.agroMeter.logProcessor(line,self.blockSequenceNumber)
                if self.ifRALogTakerEnabled == True:
                    self.logTaker.online_process(line)
                if self.ifIngameDiscordCommandEnabled == True:
                    self.ingameCommands.logProcessor(line)
                if self.ifBotGinaProxyEnabled == True:
                    self.bot_gina_proxy.logProcessor(line)
            line = self.f.readline()

    def uiControlCommandHandler(self,line:str):


        if line[26:]==" cchpm-cch-monitor is not online at this time.\n":
            if self.ifstartCHMonitor:
                self.startCHMonitor(False)
                self.checkBox.setChecked(False)
            else:
                self.startCHMonitor(True)
                self.checkBox.setChecked(True)

        if line[26:]==" cchpm-aggro-meter is not online at this time.\n":
            if self.agroMeterEnabled:
                self.agroMeterEnablingHandler(False)
                self.checkBox_2.setChecked(False)
            else:
                self.agroMeterEnablingHandler(True)
                self.checkBox_2.setChecked(True)

        if line[26:]==" cchpm-ralog-taker is not online at this time.\n":
            if self.ifRALogTakerEnabled:
                self.RALogTakerEnabled(False)
                self.checkBox_3.setChecked(False)
            else:
                self.RALogTakerEnabled(True)
                self.checkBox_3.setChecked(True)

        if line[26:]==" cchpm-ingame-discord-bot-command is not online at this time.\n":
            if self.ifIngameDiscordCommandEnabled:
                self.enableIngameDiscordCommandHandler(False)
            else:
                self.enableIngameDiscordCommandHandler(True)



        if line[26:]==" cchpm-lstrafe is not online at this time.\n":
            if self.ifLeftStrafeLineEnabled:
                self.enableLeftStrafeLine(False)
                self.checkBox_10.setChecked(False)
            else:
                self.enableLeftStrafeLine(True)
                self.checkBox_10.setChecked(True)

        if line[26:]==" cchpm-rstrafe is not online at this time.\n":
            if self.ifRightStrafeLineEnabled:
                self.enableRightStrafeLine(False)
                self.checkBox_11.setChecked(False)
            else:
                self.enableRightStrafeLine(True)
                self.checkBox_11.setChecked(True)

        if line[26:] == " cchpm-bot-log-proxy is not online at this time.\n":
            if self.ifBotGinaProxyEnabled:
                self.enableBotGinaProxyHandler(False)
                self.checkBox_12.setChecked(False)
            else:
                self.enableBotGinaProxyHandler(True)
                self.checkBox_12.setChecked(True)

        if line[26:] == " cchpm-tts is not online at this time.\n":
            if self.ifTTSEnabled:
                self.enableTTSHandler(False)
                self.checkBox_14.setChecked(False)
            else:
                self.enableTTSHandler(True)
                self.checkBox_14.setChecked(True)

    #@performance_monitor
    def logProcessor(self,line:str):

        ki=line.upper().find('!KI')
        if ki != -1:
            KIline=line[ki:].replace(' ','')
            if KIline[3]>'0' and KIline[3]<='9':
                interval=int(KIline[3])
                self.cchwin.setinterval(interval)
                self.chInterval = interval
                self.spinBox_4.setValue(self.chInterval)
                self.msg(f'INFO:Someone changed the CH interval to {interval}s by command /gu !KI{interval} in game.')

        ki=line.find('clearcch is not online at this time')
        if ki != -1:
            self.cchwin.restart_ani()

        if(line.find('CH') != -1):
            self.CH_hotkey_match(line)

        if line[26:]==' Your spell is interrupted.\n':
            self.cchwin.yourSpellInterrupted()

        ki=line[26:].find("'s casting is interrupted!")
        if ki != -1:
            self.cchwin.someoneSpellInterrupted(line[27:26+ki])

    #@performance_monitor
    def CH_hotkey_match(self,line:str):

        clericSN = ''
        tankname = ''

        clericName=line[27:27+line[27:].find(" ")]
        CH_line = line[line.find(", '")+3:-2]
        CH_line=CH_line.replace(" ",'')

        if self.hotkeyFormat['headkeyword'] != '':
            head=CH_line.find(self.hotkeyFormat['headkeyword'])
            if head == -1:
                return
            CH_line = CH_line[head+len(self.hotkeyFormat['headkeyword']):]

        middle=CH_line.find(self.hotkeyFormat['middlekeyword'])
        if middle == -1:
            return
        if self.hotkeyFormat["pos_of_clericid"] < self.hotkeyFormat["pos_of_tankname"]:
            clericSN = CH_line[0:middle]
        else:
            tankname = CH_line[0:middle]
            tankname = tankname[0:self.mtNameLength]

        CH_line = CH_line[middle+len(self.hotkeyFormat['middlekeyword']):]

        tail=CH_line.find(self.hotkeyFormat['tailkeyword'])
        if self.hotkeyFormat['tailkeyword'] != '':
            if tail == -1:
                return
            else:
                if self.hotkeyFormat["pos_of_clericid"] > self.hotkeyFormat["pos_of_tankname"]:
                    clericSN = CH_line[0:tail]
                else:
                    tankname = CH_line[0:tail]
                    tankname = tankname[0:self.mtNameLength]
        else:
            if self.hotkeyFormat["pos_of_clericid"] > self.hotkeyFormat["pos_of_tankname"]:
                clericSN = CH_line[0:]
            else:
                tankname = CH_line[0:]
                tankname = tankname[0:self.mtNameLength]


        tankname=tankname.rstrip()

        self.msg(f"{clericName},{clericSN}, CH -> {tankname}")

        if tankname != '':
            self.cchwin.create_ani(tankname,clericSN,clericName)
            if clericName == 'You':
                self.cchwin.you= clericSN

    def chInterval(self):
        if self.initializing:
            return

        self.chInterval=self.spinBox_4.value()
        self.cchwin.setinterval(self.chInterval)
        self.saveconfig()
        self.msg(f'INFO:You changed the CH interval to {self.chInterval}s. You can also use /gu !KI{self.chInterval} command in game to change this.')


    def restart(self):

        self.cchwin.restart_ani()
        self.agroMeter.hideAgroMeter()
        self.agroMeter.hideAgroMeter()
        self.agroMeter.hideNetworkAgroMeter()
        self.agroMeter.hideNetworkAgroMeter()

        self.agroMeter.clearAgroTable()
        self.msg("INFO:Clearing screen. You can also use the in game command /t clearcch to do the same.")

    def startCHMonitor(self,ifstartCHMonitor:bool):

        if self.initializing:
            return

        self.ifstartCHMonitor=ifstartCHMonitor

        self.saveconfig()
        if self.ifstartCHMonitor:
            self.msg("INFO:CCHPM is enabled.")
            self.checkBox.setStyleSheet("QCheckBox { color: green; }")
        else:
            self.msg("INFO:CCHPM is disabled.")
            self.checkBox.setStyleSheet("QCheckBox { color: red; }")

    def agroMeterEnablingHandler(self,ifAgroMeterEnabled:bool):

        if self.initializing:
            return

        self.agroMeterEnabled=ifAgroMeterEnabled

        self.saveconfig()
        if self.agroMeterEnabled:
            self.msg("INFO:Agro Meter function enabled.")
            self.checkBox_2.setStyleSheet("QCheckBox { color: green; }")
            self.checkBox_5.setEnabled(True)
            self.checkBox_13.setEnabled(True)

        else:
            self.msg("INFO:Agro Meter function disabled.")
            self.checkBox_2.setStyleSheet("QCheckBox { color: red; }")
            self.checkBox_5.setEnabled(False)
            self.aggroMeterOnlineFuncHandler(False)
            self.checkBox_5.setChecked(False)
            self.agroMeter.hide()
            self.agroMeter.window_network.hide()
            self.agroMeter.window_mst.hide()
            self.agroMeter.hideAgroMeter()
            self.agroMeter.hideAgroMeter()
            self.agroMeter.hideNetworkAgroMeter()
            self.agroMeter.hideNetworkAgroMeter()

            self.checkBox_13.setEnabled(False)
            self.enableMobSwingTimerHandler(False)
            self.checkBox_13.setChecked(False)
            self.agroMeter.window_mst.hide_line()
            self.agroMeter.mst_text_label.hide()

    def aggroMeterOnlineFuncHandler(self,isOnlineSyncEnabled:bool):
        if self.initializing:
            return

        self.agroMeterOnlineSyncEnabled=isOnlineSyncEnabled
        self.agroMeter.isOnlineSyncEnabled=isOnlineSyncEnabled

        self.saveconfig()
        if self.agroMeterOnlineSyncEnabled:
            self.msg("INFO:Agro Meter online synchronisation function enabled.")
            self.onlineSyncHandler_timer.start(ONLINE_SYNC_INTERVAL)
            self.agroMeter.toggle_connection(self.agroMeterOnlineSyncEnabled)
        else:
            self.msg("INFO:Agro Meter online synchronisation function disabled.")
            self.onlineSyncHandler_timer.stop()
            self.agroMeter.toggle_connection(self.agroMeterOnlineSyncEnabled)

    def showEqualDBGBHandler(self,isShowEqualDBGBEnabled:bool):
        if self.initializing:
            return

        self.ifShowEqualDBGBEnabled=isShowEqualDBGBEnabled
        self.agroMeter.ifShowEqualDBGBEnabled=isShowEqualDBGBEnabled

        self.saveconfig()
        if self.ifShowEqualDBGBEnabled:
            self.msg("INFO:Agro Meter(online) show equal DB/GB enabled.")
        else:
            self.msg("INFO:Agro Meter(online) show equal DB/GB disabled.")

    def showEqualSlowHandler(self,isShowEqualSlowEnabled:bool):
        if self.initializing:
            return

        self.ifShowEqualSlowEnabled=isShowEqualSlowEnabled
        self.agroMeter.ifShowEqualSlowEnabled=isShowEqualSlowEnabled

        self.saveconfig()
        if self.ifShowEqualSlowEnabled:
            self.msg("INFO:Agro Meter(online) show equal slow enabled.")
        else:
            self.msg("INFO:Agro Meter(online) show equal slow disabled.")

    def showTankDiscHandler(self,isShowTankDiscEnabled:bool):
        if self.initializing:
            return

        self.ifShowTankDiscEnabled=isShowTankDiscEnabled
        self.agroMeter.ifShowTankDiscEnabled=isShowTankDiscEnabled

        self.saveconfig()
        if self.ifShowEqualDBGBEnabled:
            self.msg("INFO:Agro Meter(online) show tank disc enabled.")
        else:
            self.msg("INFO:Agro Meter(online) show tank disc disabled.")

    def setOnlineChannel(self,onlineChannelName:str):
        if self.initializing:
            return

        self.onlineChannel=onlineChannelName
        self.lineEdit_2.setText(onlineChannelName)

        #self.saveconfig()
        #We want to reset the channel to 'default' every time user restarts CCHPM. So no saving of it.
        #Then everyone will have a basic channel to make the synch work,need not to worry about losing synch often.
        #basically the security issue is not common , nothing need to hides most of time. But in the few cases
        #where aggro ammount does needs to hide, Raid leader can use /gu !kchannel channel_name to change online
        #aggro broadcasting into a private channel. or use /motd to put it into guild msg , so every time people
        #relog, they can get it through /get command. no need to spam the !kchannel command over and over.

        self.msg(f"INFO:Aggro Meter online synchronizing channel has been set to [{onlineChannelName}].")


    def latencyToleranceHandler(self,latencyTolerance:int):
        if self.initializing:
            return

        self.latencyTolerance=latencyTolerance
        self.agroMeter.latencyTolerance=latencyTolerance

        self.saveconfig()
        self.msg(f"INFO:Changed Aggro Meter's latency tolerance to {latencyTolerance} ms. Note:Turn down this value will"
                 f" help reduce counting other's proc as yours mistakenly. But will also increase the missing rate of your "
                 f"own proc. Tune this value based on your network jitter and IO bottleneck ")


    def weaponEditor(self):
        self.we.show()
        self.we.activateWindow()
        self.we.raise_()

    def setWeaponsForYourName(self):

        if self.yourName in self.weaponDict:
            self.MHWeapon=self.weaponDict[self.yourName][0]
            self.OHWeapon=self.weaponDict[self.yourName][1]
        else:
            self.MHWeapon="???"
            self.OHWeapon="???"

        self.agroMeter.UpdateMHWeapons(self.MHWeapon)
        self.agroMeter.UpdateOHWeapons(self.OHWeapon)

    def saveWeaponForYourName(self):

        self.MHWeapon = self.agroMeter.MHWeapon
        self.OHWeapon = self.agroMeter.OHWeapon
        self.saveconfig()

    def setupYourNameToAggroMeter(self):

        self.agroMeter.setupYourName(self.yourName)


    def setupYourNameToIngamecommand(self):

        self.ingameCommands.setupYourName(self.yourName)

    def setupYourNameToBotGinaProxy(self):

        self.bot_gina_proxy.setupYourName(self.yourName)


    def enableIngameDiscordCommandHandler(self,userChecked:bool):

        if self.initializing:
            return

        # 临时阻塞信号
        self.checkBox_8.blockSignals(True)

        if userChecked:
            self.ifIngameDiscordCommandEnabled = self.ingameCommands.setWebhook()
        else:
            self.ifIngameDiscordCommandEnabled = False

        if self.ifIngameDiscordCommandEnabled:
            self.ingameCommands.setIngameDiscordCommandEnable(True)
            self.msg("INFO:In-game Discord Command Enabled.")
            self.checkBox_8.setStyleSheet("QCheckBox { color: green; }")
            self.checkBox_8.setChecked(True)
        else:
            self.ingameCommands.setIngameDiscordCommandEnable(False)
            self.msg("INFO:In-game Discord Command Disabled.")
            self.checkBox_8.setStyleSheet("QCheckBox { color: red; }")
            self.checkBox_8.setChecked(False)

        # 恢复信号
        self.checkBox_8.blockSignals(False)

    def enableProxyIngameCommandHandler(self,userChecked:bool):

        if self.initializing:
            return

        if userChecked:
            self.ifProxyIngameCommandEnabled = self.ingameCommands.checkProxyAuthorization()
        else:
            self.ifProxyIngameCommandEnabled = False

        if self.ifProxyIngameCommandEnabled:
            self.ingameCommands.setProxyIngameCommandEnable(True)
            self.msg("INFO:Proxy In-game Command Enabled.")
            self.checkBox_9.setChecked(True)
        else:
            self.ingameCommands.setProxyIngameCommandEnable(False)
            self.msg("INFO:Proxy In-game Command Disabled.")
            self.checkBox_9.setChecked(False)

    def commandEditorHandler(self):

        self.ingameCommands.show_editor()

    def enableLeftStrafeLine(self,userChecked:bool):

        if self.initializing:
            return

        self.ifLeftStrafeLineEnabled = userChecked

        self.saveconfig()
        if self.ifLeftStrafeLineEnabled:
            self.left_strafe_line.show_line()
            self.msg("INFO:Left Strafe Line Enabled.")
        else:
            self.left_strafe_line.hide_line()
            self.msg("INFO:Left Strafe Line Disabled.")

    def enableRightStrafeLine(self, userChecked: bool):

        if self.initializing:
            return

        self.ifRightStrafeLineEnabled = userChecked

        self.saveconfig()
        if self.ifRightStrafeLineEnabled:
            self.right_strafe_line.show_line()
            self.msg("INFO:Right Strafe Line Enabled.")
        else:
            self.right_strafe_line.hide_line()
            self.msg("INFO:Right Strafe Line Disabled.")

    def strafeLineWidthHandler(self,width:int):
        if self.initializing:
            return

        self.strafe_line_width=width
        self.left_strafe_line.set_width(width)
        self.right_strafe_line.set_width(width)

        self.saveconfig()
        self.msg(f"INFO:Strafe run line width changed to {width} pixel.")

    def strafeLineColorHandler(self,color:str):
        if self.initializing:
            return

        self.strafe_line_color=color
        self.left_strafe_line.set_color(color)
        self.right_strafe_line.set_color(color)

        self.saveconfig()
        self.msg(f"INFO:Strafe run line color changed to {color}.")

    def enableBotGinaProxyHandler(self, userChecked: bool):

        if self.initializing:
            return

        self.ifBotGinaProxyEnabled = userChecked

        self.saveconfig()
        if self.ifBotGinaProxyEnabled:
            self.bot_gina_proxy.setProxyEnabled()
            self.msg("INFO:Bot Gina Proxy Enabled.")
        else:
            self.bot_gina_proxy.setProxyDisabled()
            self.msg("INFO:Bot Gina Proxy Disabled.")

    def botListHandler(self):
        if self.initializing:
            return

        # 显示bot编辑器对话框
        self.bot_gina_proxy.show_bot_editor()
        self.msg('Bot List Editor opened. Edit the list to proxy their log to GINA.')

    def backupEQHandler(self):
        if self.initializing:
            return

        """Handle backup EQ configuration"""
        if not self.eqLogDir:
            self.msg("ERROR: EQ log directory not set")
            return

        backup_dialog = BackupRestoreDialog(self, self.eqLogDir)
        backup_dialog.exec_()

    def copyUIHandler(self):
        if self.initializing:
            return

        """Handle copy EQ UI"""
        if not self.eqLogDir:
            self.msg("ERROR: EQ log directory not set")
            return

        # Get EQ directory (parent of log directory)
        eq_dir = os.path.dirname(self.eqLogDir)
        if not os.path.exists(eq_dir):
            self.msg(f"ERROR: EQ directory does not exist: {eq_dir}")
            return

        copyui_dialog = CopyUIDialog(self, eq_dir)
        copyui_dialog.exec_()

    def enableMobSwingTimerHandler(self, userChecked: bool):

        if self.initializing:
            return

        self.ifMobSwingTimerEnabled = userChecked

        self.saveconfig()
        if self.ifMobSwingTimerEnabled:
            self.agroMeter.setMobSwingTimerEnabled()
            self.msg("INFO:Mob Swing Timer Enabled.")
        else:
            self.agroMeter.setMobSwingTimerDisabled()
            self.msg("INFO:Mob Swing Timer Disabled.")



    def RALogTakerEnabled(self,ifRALogTakerEnabled:bool):
        if self.initializing:
            return

        self.ifRALogTakerEnabled=ifRALogTakerEnabled

        self.saveconfig()
        if self.ifRALogTakerEnabled:
            self.msg("INFO:Raid attendee log taker function enabled.")
            self.checkBox_3.setStyleSheet("QCheckBox { color: green; }")

        else:
            self.msg("INFO:Raid attendee log taker function disabled.")
            self.checkBox_3.setStyleSheet("QCheckBox { color: red; }")
            self.logTaker.hide()


    def AutoPopupRALogTaker(self,autoPopupRALogTaker:bool):
        if self.initializing:
            return

        self.autoPopupRALogTaker=autoPopupRALogTaker
        self.logTaker.autoPopupRALogTaker = self.autoPopupRALogTaker

        self.saveconfig()
        if self.autoPopupRALogTaker:
            self.msg("INFO:Auto pop up the raid attendee log taker window when see !KLOG.")
        else:
            self.msg("INFO:No auto pop up for !KLOG. But you can use /t log in game to pop RA Log taker manually still.")

    def tellWaitingTimeHandler(self,minute:int):
        if self.initializing:
            return

        self.tellWaitingTime=minute
        self.logTaker.tellWaitingTime=self.tellWaitingTime


        self.saveconfig()
        self.msg(f"Info: Tells waiting time has changed to {minute}")


    def RALogTaker(self):

        self.logTaker.show()
        self.logTaker.raise_()
        width=self.logTaker.geometry().getRect()[2]
        height=self.logTaker.geometry().getRect()[3]
        self.logTaker.resize(width+1, height)
        self.logTaker.resize(width, height)

    def historyRAEventToLoadHandler(self,event_count:int):


        if self.initializing:
            return

        self.max_loaded_event=event_count
        self.logTaker.max_loaded_event_handler(self.max_loaded_event)

        self.saveconfig()
        self.msg(f"Info: Number of events to load for RA log taker has changed to {event_count}.")




    def startorstop(self):

        if self.started:

            self.started = False
            self.logfile_moniter_timer.stop()
            self.cchwin.restart_ani()
            self.agroMeter.hideAgroMeter()
            self.agroMeter.hideNetworkAgroMeter()
            self.agroMeter.clearAgroTable()
            self.pushButton_3.setText("PAUSED")
            self.pushButton_3.setFont(self.font())
            self.pushButton_3.setStyleSheet('background-color: red;')
            self.ti.sync_menu()

            self.msg("INFO: Stop parsing log files.")
        else:
            self.started = True
            self.logfile_moniter_timer.start(LOG_MONITORING_INTERVAL)
            self.pushButton_3.setText("ON AIR")
            self.pushButton_3.setFont(self.font())
            self.pushButton_3.setStyleSheet('background-color: green;')
            self.ti.sync_menu()

            self.msg("INFO: Start parsing log files.")


    def modifyMonitorUIstart(self):

        self.locked = False
        #self.started = False
        self.cchwin.restart_ani()
        #self.cchwin.reAdjustRails()
        self.pushButton_4.setText("LOCK")
        self.pushButton_6.setEnabled(True)
        self.pushButton_7.setEnabled(True)
        self.pushButton_8.setEnabled(True)
        self.pushButton_9.setEnabled(True)
        self.pushButton_3.setEnabled(False)

        if self.ifstartCHMonitor:
            self.cchwin.setWindowOpacity(0.5)
            self.cchwin.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Tool)
            self.cchwin.setGeometry(self.cchwinGeo)
            self.cchwin.show()


        if self.agroMeterEnabled:
            self.agroMeter.setWindowOpacity(0.5)
            self.agroMeter.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Tool)
            self.agroMeter.setGeometry(self.agroMeterGeo)
            self.agroMeter.show()

            self.agroMeter.window_network.setWindowOpacity(0.5)
            self.agroMeter.window_network.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Tool)
            self.agroMeter.window_network.setGeometry(self.agroNetworkMeterGeo)
            self.agroMeter.window_network.show()

            self.agroMeter.window_mst.setWindowOpacity(0.5)
            self.agroMeter.window_mst.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Tool)
            self.agroMeter.window_mst.setGeometry(self.mobSwingTimerGeo)
            self.agroMeter.window_mst.show()

        if self.ifLeftStrafeLineEnabled:
            self.left_strafe_line.setWindowOpacity(0.5)
            self.left_strafe_line.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Tool)
            self.left_strafe_line.setGeometry(self.leftStrafeLineGeo)
            self.left_strafe_line.show()

        if self.ifRightStrafeLineEnabled:
            self.right_strafe_line.setWindowOpacity(0.5)
            self.right_strafe_line.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Tool)
            self.right_strafe_line.setGeometry(self.rightStrafeLineGeo)
            self.right_strafe_line.show()



    def modifyMonitorUIdone(self):

        self.locked = True
        #self.started = True
        self.pushButton_4.setText("UNLOCK")
        self.pushButton_6.setEnabled(False)
        self.pushButton_7.setEnabled(False)
        self.pushButton_8.setEnabled(False)
        self.pushButton_9.setEnabled(False)
        self.pushButton_3.setEnabled(True)
        self.testchain_started = False
        self.testchain_timer.stop()
#        print("CCHWIN GEO:",self.cchwinGeo)
        self.cchwinSave()

        #self.cchwin.setWindowOpacity(0.5) # 设置窗口透明度
        #self.cchwin.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Tool)
        #QtCore.Qt.Tool 这是指If there is a parent, the tool window will always be kept on top of it.
        #QtCore.Qt.WindowStaysOnTopHint 窗口永远在最前
        #self.cchwin.setAttribute(QtCore.Qt.WA_TranslucentBackground)  # 设置窗口背景透明
        #self.cchwin.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        #self.cchwin.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)  # 这个参数去掉标题栏。
        #self.cchwin.setAttribute(Qt.WA_TranslucentBackground)
        self.cchwin.hide()
        self.cchwinStop()
        self.cchwinAdapt()

        self.agroMeter.hide()
        self.agroMeter.window_network.hide()
        self.agroMeter.window_mst.hide()
        self.agroMeter.stopTestAgroMeter()
        self.agroMeter.reAdjustPanel()
        self.agroMeter.hideAgroMeter()
        self.agroMeter.hideAgroMeter()
        self.agroMeter.hideNetworkAgroMeter()
        self.agroMeter.hideNetworkAgroMeter()
        self.agroMeter.window_mst.hide_line()

        self.left_strafe_line.hide()
        self.right_strafe_line.hide()
        self.left_strafe_line.reAdjustLines()
        self.right_strafe_line.reAdjustLines()


    def lockunlock(self):
        if self.locked:
            self.modifyMonitorUIstart()
        else:
            self.modifyMonitorUIdone()


    def cchwinSave(self):
        self.cchwin.restart_ani()
        self.cchwin.reAdjustRails()
        self.agroMeter.reAdjustPanel()
        self.left_strafe_line.reAdjustLines()
        self.right_strafe_line.reAdjustLines()

        cchwin_width = self.cchwinGeo.getRect()[2]
        self.agroMeter.set_mst_pixels_per_second(cchwin_width / 10)

        #此处需获取CCHWIN的相关参数，并保存到配置文件中，包括geometry
        self.msg("Saving current configurations and readjust UI layout.")
        #print('cch window geo:'+str(self.cchwinGeo))
        #print('left line window geo:' + str(self.leftStrafeLineGeo))
        #print('right line window geo:' + str(self.rightStrafeLineGeo))
        #print('saving!')
        self.saveconfig() #需补保存窗口位置的代码。




    def cchwinCreate(self):

        self.cchwin.resume_ani()
        self.testchain_timer.start(TEST_CHAIN_INTERVAL)
        if self.agroMeterEnabled:
            self.agroMeter.testAgroMeter()
        self.msg("Creating test CH chain now.")
        self.testchain_started = True


    def testchain(self):

        tankname=random.choice(['Jumo','Balor','Tiggo','Grendol'])
        clericid=random.choice(["111", "3", "002", "BBB", "5", "004", "AAA", "222","6","GAp","wrong"])
        #clericid=random.choice(["GAp"])
        self.cchwin.create_ani(tankname,clericid)



    def cchwinStop(self):
        self.testchain_started = False
        self.cchwin.pause_ani()
        self.testchain_timer.stop()
        self.agroMeter.stopTestAgroMeter()
        self.msg("Test CH chain stops.")

    def cchwinAdapt(self):
        self.cchwin.restart_ani()
        self.cchwin.reAdjustRails()
        if self.agroMeterEnabled:
            self.agroMeter.reAdjustPanel()
        self.left_strafe_line.reAdjustLines()
        self.right_strafe_line.reAdjustLines()

        cchwin_width = self.cchwinGeo.getRect()[2]
        self.agroMeter.set_mst_pixels_per_second(cchwin_width / 10)

        self.msg("Readjust UI layout.")

    def default(self):
        try:
            os.remove("CCHPM.ini")
        except Exception as e:
            print('error:',e)
        self.initializing = True
        self.msg('INFO:Initializing configuration.Please wait...')
        self.configdata = {}
        self.initialize_from_configfile()
        self.lastSizesOfLogFiles = {}
        self.curLogFile = ''
        self.logfilechanged = False
        if self.f is not None:
            self.f.close()
        self.f = None

        self.cchwinGeo=QtCore.QRect(586, 669, 358, 126)
        self.cchwin.setGeometry(self.cchwinGeo)
        self.cchwin.restart_ani()
        self.cchwin.reAdjustRails()
        cchwin_width = self.cchwinGeo.getRect()[2]
        self.agroMeter.set_mst_pixels_per_second(cchwin_width / 10)

        self.msg("INFO:Reset all configuration to default value.")
        self.initializing = False

    def chbarheight(self,railheight:int):
        if self.initializing:
            return

        self.cchwin.railheight=railheight
        self.railheight=railheight
        self.cchwin.restart_ani()
        self.cchwin.reAdjustRails()
        cchwin_width = self.cchwinGeo.getRect()[2]
        self.agroMeter.set_mst_pixels_per_second(cchwin_width / 10)

        self.saveconfig()
        self.msg(f"INFO:Changed CH BAR height to {railheight}.")

    def mtNameLengthHandler(self,nameLength:int):
        if self.initializing:
            return

        self.mtNameLength=nameLength
        self.cchwin.restart_ani()

        self.saveconfig()
        self.msg(f"INFO:Changed MT Name Length to {nameLength} characters.")

    def mtNameMarginHandler(self,nameMargin:int):
        if self.initializing:
            return

        self.mtNameMargin=nameMargin
        self.cchwin.mt_name_margin=nameMargin
        self.cchwin.restart_ani()

        self.saveconfig()
        self.msg(f"INFO:Changed MT Name Margin to {nameMargin} pixels.")


    def monitorwidthmargin(self,widthMargin:int):
        if self.initializing:
            return

        self.cchwin.widthMargin=widthMargin
        self.cchwinwidthMargin=widthMargin
        self.cchwin.restart_ani()
        self.cchwin.reAdjustRails()
        cchwin_width = self.cchwinGeo.getRect()[2]
        self.agroMeter.set_mst_pixels_per_second(cchwin_width / 10)

        self.saveconfig()
        self.msg(f"INFO:Changed width margin to {widthMargin}.")


    def monitorheightmargin(self,heigthMargin:int):
        if self.initializing:
            return

        self.cchwin.heigthMargin=heigthMargin
        self.cchwinheigthMargin=heigthMargin
        self.cchwin.restart_ani()
        self.cchwin.reAdjustRails()
        cchwin_width = self.cchwinGeo.getRect()[2]
        self.agroMeter.set_mst_pixels_per_second(cchwin_width / 10)
        self.saveconfig()
        self.msg(f"INFO:Changed height margin to {heigthMargin}.")

    def messageFadeTimerChangedHandler(self,timer_sec:int):
        if self.initializing:
            return

        if timer_sec >= 0:
            self.hideAgroMeterInterval=timer_sec
            self.hideAgroMeter_timer.start(self.hideAgroMeterInterval*1000)

        self.saveconfig()
        self.msg(f"INFO:Changed hide agro meter interval to {timer_sec} seconds.")


    def lazyAgroTimerChangedHandler(self,timer_min:int):
        if self.initializing:
            return

        if timer_min >= 1:
            self.agroMeter.agroTableExpireDuration=timer_min

        self.saveconfig()
        self.msg(f"INFO:Changed lazy agro timer to {timer_min} minutes.")

    def setAgroMeterBackgroundColor(self):   #unusing function
        color = QtWidgets.QColorDialog.getColor()  # 打开颜色选择对话框
        if color.isValid():  # 如果用户选择了有效的颜色
            #print(color.name())
            self.agroMeter.label_agroMeterGreen.setStyleSheet(f"background: {color.name()};")  # 设置窗口背景颜色
            self.agroMeter.label_agroMeterYellow.setStyleSheet(f"background: {color.name()};")  # 设置窗口背景颜色
            self.agroMeter.label_errorMessage.setStyleSheet(f"background: {color.name()};")  # 设置窗口背景颜色

    def agroMeterOpacity(self,opactiy:int):
        if self.initializing:
            return

        self.agroMeterOpacity=opactiy
        self.agroMeter.label_agroMeterGreen.setWindowOpacity(float(opactiy)/100)
        self.agroMeter.label_agroMeterYellow.setWindowOpacity(float(opactiy) / 100)
        self.agroMeter.label_errorMessage.setWindowOpacity(float(opactiy) / 100)

        self.saveconfig()
        self.msg(f"INFO:Agro meter's pannel opacity changed to 0.{opactiy}")

    def setMainHandSwingRate(self,rate:int):
        if self.initializing:
            return

        self.mainHandSwingRate=rate

        self.agroMeter.basicMHFireRate=float(self.mainHandSwingRate)/1000
        self.agroMeter.basicOHFireRate=1-self.agroMeter.basicMHFireRate
        self.agroMeter.setup1hWeaponFireRate()

        self.saveconfig()
        self.msg(f"INFO:Agro meter's main hand swing rate changed to 0.{rate}")



    def changeCHFormat(self,formatstr):
        if self.initializing:
            return

        if self.comboBox_2.findText(formatstr) == -1:
            self.pushButton_12.setEnabled(True)
            self.pushButton_11.setEnabled(False)
        else:
            self.pushButton_11.setEnabled(True)
            self.pushButton_12.setEnabled(False)



        self.msg("INFO:The hotkey format should looks like: [headkeywords],###,middlekeywords,tankname,[tailkeywords]. or [headkeywords],tankname,middlekeywords,###,[tailkeywords]. Head or Tail keywords are optional.")

    def CHFormatChanged(self,index):
        if self.initializing:
            return

        self.hotkeyFormatstr=self.comboBox_2.itemText(index)
        print("current index",index)
        print("current format str",self.hotkeyFormatstr)
        #self.hotkeyFormatstr = self.configdata['hotkeyFormatstr']
        self.hotkeyFormat = self.hotkeyFormatParse(self.hotkeyFormatstr)
        #self.hotkeyFormatList = self.configdata['hotkeyFormatList']
        #self.comboBox_2.clear()
        #for i in range(len(self.hotkeyFormatList)):
        #    self.comboBox_2.addItem(self.hotkeyFormatList[i])
        #self.comboBox_2.setCurrentText(self.hotkeyFormatstr)
        #self.pushButton_12.setEnabled(False)



    def addCHFormat(self):
        if self.initializing:
            return

        text = self.comboBox_2.currentText()
        if self.comboBox_2.findText(text) == -1:
            self.comboBox_2.addItem(text)
            self.comboBox_2.setCurrentIndex(self.comboBox_2.findText(text))
            self.msg(f'INFO:Added a new CH format "{text}"')

            self.hotkeyFormatstr = text
            self.hotkeyFormat = self.hotkeyFormatParse(self.hotkeyFormatstr)

            self.pushButton_11.setEnabled(True)
            self.pushButton_12.setEnabled(False)

    def deleteCHFormat(self):
        if self.initializing:
            return
        result=QMessageBox.warning(self, 'Warning', 'Are you sure to delete the format "%s"'%self.comboBox_2.currentText(), QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if result == QMessageBox.Yes:
            self.comboBox_2.removeItem(self.comboBox_2.currentIndex())
            self.msg(f'WARNING:You deleted the CH format "{self.comboBox_2.currentText()}"')

    def logImitationHandler(self):
        if self.initializing:
            return

        # 检查对话框是否存在且正在运行
        if hasattr(self, 'log_imitation_dialog') and self.log_imitation_dialog:
            # 如果对话框存在但已经关闭，清理引用
            if not self.log_imitation_dialog.isVisible():
                self.log_imitation_dialog = None
            else:
                # 对话框已存在且可见，将其前置
                self.log_imitation_dialog.raise_()
                self.log_imitation_dialog.activateWindow()
                return

        # 创建新对话框
        self.log_imitation_dialog = LogImitationDialog(self, self.eqLogDir)
        # 连接finished信号，确保对话框关闭时正确清理
        self.log_imitation_dialog.finished.connect(self.on_imitation_dialog_closed)
        self.log_imitation_dialog.show()

        self.msg('Log Imitation tool opened. Select a log file to imitate.')

    def on_imitation_dialog_closed(self, result=None):
        """对话框关闭时的清理函数"""
        # 确保停止任何正在运行的模仿线程
        if (hasattr(self, 'log_imitation_dialog') and
                self.log_imitation_dialog and
                hasattr(self.log_imitation_dialog, 'is_running') and
                self.log_imitation_dialog.is_running):

            # 请求停止模仿
            self.log_imitation_dialog.stop_imitation()

            # 等待线程结束（非阻塞方式）
            if (hasattr(self.log_imitation_dialog, 'thread') and
                    self.log_imitation_dialog.thread and
                    self.log_imitation_dialog.thread.is_alive()):
                # 使用QTimer来延迟清理，避免阻塞UI
                QtCore.QTimer.singleShot(100, self.cleanup_imitation_dialog)
                return

        # 立即清理
        self.cleanup_imitation_dialog()

    def cleanup_imitation_dialog(self):
        """清理对话框引用"""
        if hasattr(self, 'log_imitation_dialog'):
            # 确保对话框被正确关闭和删除
            try:
                if self.log_imitation_dialog.isVisible():
                    self.log_imitation_dialog.close()
            except:
                pass
            finally:
                self.log_imitation_dialog = None

    def enableTTSHandler(self, userChecked: bool):

        if self.initializing:
            return

        self.ifTTSEnabled = userChecked

        self.saveconfig()
        if self.ifTTSEnabled:
            self.msg("INFO:Text to speach Enabled.Wonder and found!")
        else:
            self.msg("INFO:Text to speach Disabled.Wonder and found!")



    def TTS(self, text_to_speak: str, interruptable:bool):
        """
        将文本转换为语音命令，写入日志文件
        格式: [Fri Sep 12 22:05:03 2025] !TTS 要朗读的文字
        输出到: 程序当前目录/Logs/eqlog_TTS_P1999Green.txt
        """

        if not self.ifTTSEnabled:
            return

        if not text_to_speak or not text_to_speak.strip():
            self.msg("WARNING: TTS text is empty, skipping.")
            return

        try:
            # 获取当前时间并格式化为EQ日志格式
            current_time = datetime.datetime.now()
            timestamp = current_time.strftime("[%a %b %d %H:%M:%S %Y]")

            # 构建完整的TTS命令行
            if interruptable:
                tts_command = f"{timestamp} !TTSI {text_to_speak.strip()}"
            else:
                tts_command = f"{timestamp} !TTSNI {text_to_speak.strip()}"


            # Create log directory if it doesn't exist
            log_dir = pathlib.Path("./Logs")  # 修改为 ./Logs 目录
            log_dir.mkdir(exist_ok=True)  # 确保目录存在
            target_log_path = os.path.join(log_dir, "eqlog_TTS_P1999Green.txt")


            # 写入TTS命令到日志文件
            with open(target_log_path, 'a', encoding='utf-8') as log_file:
                log_file.write(tts_command + '\n')
                log_file.flush()

            self.msg(f"INFO: TTS command written to: {target_log_path}")
            self.msg(f"TTS content: {text_to_speak}")

        except Exception as e:
            self.msg(f"ERROR: Failed to write TTS command: {str(e)}")

    def openHistoryLog(self):
        os.startfile(".\\CCHPM RUN LOG.txt")
        os.startfile(".\\AgroMeter RUN LOG.txt")
        #self.agroMeter.test_reconnect()
        #print(f"Qt 版本: {QT_VERSION_STR}")  # 输出 Qt 库版本
        #print(f"PyQt5 版本: {PYQT_VERSION_STR}")  # 输出 PyQt5 绑定版本



if __name__ == "__main__":

    app = QApplication(sys.argv)
    cfgWindow = CFGWIN()
    cfgWindow.show()
    cfgWindow.initializing = False


    result=app.exec_()
    cfgWindow.msg(f"INFO:Exiting CCHPM now. Return Code={result}")
    sys.exit(result)
