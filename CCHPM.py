import sys
import os
import time
from ui_CFGWIN import *
from CCHWIN import *
from PyQt5 import QtCore, QtGui, QtWidgets
import pathlib
import datetime
import pickle
import random
from systemtray import *
import resource

#const definition
SERVERLIST = {"Any": 0, "P1999Green": 1, "project1999": 2, "KingdomDragons": 3}
POSlIST = {"On bar":0, "Under bar":1, "Above bar":2}
LOG_MONITORING_INTERVAL=10 # 10 milliseconds
LOGDIR_MONITORING_INTERVAL=3000 # 3 seconds
CCHWIN_MONITORING_INTERVAL=100
TEST_CHAIN_INTERVAL=1000

class CFGWIN(QWidget,Ui_CFGWIN):
    def __init__(self):
        super(CFGWIN,self).__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon(":/CCHPM.ico"))
        self.setFixedSize(self.size())
        self.cchwin = CCHWIN()
        self.initializing = True
        self.msg('INFO:Initializing configuration.Please wait...')
        self.configdata={}
        self.initialize_from_configfile()
        self.lastSizesOfLogFiles={}
        self.curLogFile=''
        self.logfilechanged=False
        self.f = open('CCHPM RUN LOG.txt','r',encoding='utf-8')
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
        self.label_18.setEnabled(False)
        self.label_19.setEnabled(False)
        self.label_20.setEnabled(False)
        self.label_21.setEnabled(False)
        self.spinBox_9.setEnabled(False)
        self.spinBox_10.setEnabled(False)
        self.spinBox_11.setEnabled(False)
        self.spinBox_12.setEnabled(False)

        self.ti = TrayIcon(self)
        self.ti.show()
        self.ti.sync_menu()

        self.locked= True
        self.showcchwin = True
        self.testchain_started=False

    def closeEvent(self,event):
        self.cfgwin_geo = self.geometry()
        self.saveconfig()
        self.cchwin.close()
        event.accept()
        QtWidgets.qApp.quit()

    def hideEvent(self,event):

        self.setWindowFlags(QtCore.Qt.SplashScreen)
        event.accept()


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
        self.configdata['mark_pos'] = 'On bar'
        self.configdata['chInterval'] = 1
        self.configdata['cchwinGeo'] = QtCore.QRect(586, 669, 528, 126)
        self.configdata['railheight'] = 20

        self.configdata['ifautostart'] = True
        self.configdata['cchwinwidthMargin'] = 2
        self.configdata['heigthMargin'] = 2
        self.configdata['cfgwin_geo'] = QtCore.QRect(546, 257, 827, 526)
        self.configdata['hotkeyFormatstr'] = '### - CH - tankname'
        self.configdata['hotkeyFormatList'] = ['### - CH - tankname','ST ### CH -- tankname']

    def initialize_from_configfile(self):

        if os.path.exists('CCHPM.ini'):
            with open('CCHPM.ini','rb') as f:
                try:
                    self.configdata=pickle.load(f)
                except Exception as e:
                    self.msg(f'ERROR:{str(e)}.Using default configuration')
                    self.loaddefaultconfig()
        else:
            self.msg("INFO:CCHPM.ini doesn't exist.Using default configuration")
            self.loaddefaultconfig()

        #to add more attribute and intialize ui by saved settings.
        self.eqLogDir = self.configdata['eqLogDir']
        self.lineEdit.setText(self.eqLogDir)

        self.serverSlect = self.configdata['serverSlect']
        self.comboBox.setCurrentIndex(SERVERLIST[self.serverSlect])

        self.mark_pos = self.configdata['mark_pos']
        self.comboBox_3.setCurrentIndex(POSlIST[self.mark_pos])
        self.cchwin.mark_pos = self.mark_pos

        self.chInterval = self.configdata['chInterval']
        self.spinBox_4.setValue(self.chInterval)
        self.cchwin.setinterval(self.chInterval)

        self.cchwinGeo=self.configdata['cchwinGeo']
        self.cchwin.setGeometry(self.cchwinGeo)

        self.railheight=self.configdata['railheight']
        self.spinBox.setValue(self.railheight)
        self.cchwin.railheight=self.railheight

        self.ifautostart = self.configdata['ifautostart']
        self.started = self.ifautostart
        self.checkBox.setChecked(self.ifautostart)

        self.logfile_moniter_timer = QTimer(self)
        self.logfile_moniter_timer.timeout.connect(self.scanCurrentLog)

        self.logfiledir_moniter_timer = QTimer(self)
        self.logfiledir_moniter_timer.timeout.connect(self.scanLogDir)

        if self.started:
            self.pushButton_3.setText("ON AIR")
            self.pushButton_3.setFont(self.font())
            self.pushButton_3.setStyleSheet('background-color: green;')
            self.logfile_moniter_timer.start(LOG_MONITORING_INTERVAL)
            self.logfiledir_moniter_timer.start(LOGDIR_MONITORING_INTERVAL)
        else:
            self.pushButton_3.setText("PAUSED")
            self.pushButton_3.setFont(self.font())
            self.pushButton_3.setStyleSheet('background-color: red;')


        self.cchwinwidthMargin = self.configdata['cchwinwidthMargin']
        self.cchwin.widthMargin = self.cchwinwidthMargin
        self.spinBox_3.setValue(self.cchwinwidthMargin)

        self.cchwinheigthMargin = self.configdata['heigthMargin']
        self.cchwin.heigthMargin = self.cchwinheigthMargin
        self.spinBox_2.setValue(self.cchwinheigthMargin)

        self.cfgwin_geo = self.configdata['cfgwin_geo']
        self.setGeometry(self.cfgwin_geo)

        self.hotkeyFormatstr = self.configdata['hotkeyFormatstr']
        self.hotkeyFormat = self.hotkeyFormatParse(self.hotkeyFormatstr)
        self.hotkeyFormatList = self.configdata['hotkeyFormatList']
        self.comboBox_2.clear()
        for i in range(len(self.hotkeyFormatList)):
            self.comboBox_2.addItem(self.hotkeyFormatList[i])
        self.comboBox_2.setCurrentText(self.hotkeyFormatstr)
        self.comboBox_2.setCurrentIndex(self.comboBox_2.findText(self.hotkeyFormatstr))
        self.pushButton_12.setEnabled(False)

        self.msg("INFO:CCHPM finished initialization. Waiting for your order now.")
        self.cchwin.restart_ani()
        self.cchwin.reAdjustRails()

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
        self.configdata['eqLogDir'] = self.eqLogDir
        self.configdata['serverSlect'] = self.serverSlect
        self.configdata['mark_pos'] = self.mark_pos

        self.configdata['chInterval'] = self.chInterval
        self.cchwinGeo = self.cchwin.geometry()
        self.configdata['cchwinGeo'] = self.cchwinGeo
        self.configdata['railheight'] = self.railheight

        self.configdata['ifautostart'] = self.ifautostart
        self.configdata['cchwinwidthMargin'] = self.cchwinwidthMargin
        self.configdata['heigthMargin'] = self.cchwinheigthMargin
        self.configdata['cfgwin_geo'] = self.cfgwin_geo
        self.configdata['hotkeyFormatstr'] = self.hotkeyFormatstr

        self.hotkeyFormatList=[]
        for i in range(self.comboBox_2.count()):
            self.hotkeyFormatList.append(self.comboBox_2.itemText(i))
        self.configdata['hotkeyFormatList'] = self.hotkeyFormatList.copy()



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

        self.saveconfig()

        self.msg(f'INFO:You choose to show marks {self.mark_pos}')

    def scanLogDir(self):

        if not os.path.exists(self.eqLogDir):
            return

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
                self.curLogFile=filename
                self.msg(f"INFO:Current log file is: {self.curLogFile}")
                self.logfilechanged = True

                self.lastSizesOfLogFiles = currentSizesOfLogFiles
                return

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


    def scanCurrentLog(self):

        if self.curLogFile=='':
            return

        # log file更改后，此标志为true，当切换到新log file上后，此标志需复位为False
        if self.logfilechanged == True:
            self.f.close()
            self.f=open(self.curLogFile,encoding='utf-8')
            self.f.seek(0,2)
            self.logfilechanged = False

        line=self.f.readline()
        while(line):
            self.logProcessor(line)
            line = self.f.readline()

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
            tankname = tankname[0:5]

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
                    tankname = tankname[0:5]
        else:
            if self.hotkeyFormat["pos_of_clericid"] > self.hotkeyFormat["pos_of_tankname"]:
                clericSN = CH_line[0:]
            else:
                tankname = CH_line[0:]
                tankname = tankname[0:5]


        tankname=tankname.rstrip()

        self.msg(f"{clericName},{clericSN}, CH -> {tankname}")

        if self.started and tankname != '':
            self.cchwin.create_ani(tankname,clericSN)
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
        self.msg("INFO:Clearing screen. You can also use the in game command /t clearcch to do the same.")

    def autostart(self,ifautostart:bool):

        if self.initializing:
            return

        self.ifautostart=ifautostart

        self.saveconfig()
        if self.ifautostart:
            self.msg("INFO:CCHPM will automatically parse logs when it starts.")
        else:
            self.msg("INFO:CCHPM will not automatically parse log when it starts.")


    def startorstop(self):

        if self.started:

            self.started = False
            self.logfiledir_moniter_timer.stop()
            self.logfile_moniter_timer.stop()
            self.cchwin.restart_ani()
            self.pushButton_3.setText("PAUSED")
            self.pushButton_3.setFont(self.font())
            self.pushButton_3.setStyleSheet('background-color: red;')
            self.ti.sync_menu()

            self.msg("INFO: Stop parsing log files.")
        else:
            self.started = True
            self.logfiledir_moniter_timer.start(LOGDIR_MONITORING_INTERVAL)
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
        #print("CCHWIN GEO:", self.cchwinGeo)
        #print("CCHWIN actuall GEO:", self.cchwin.geometry())
        self.cchwin.setWindowOpacity(0.5)
        self.cchwin.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Tool)

#        self.cchwin.setWindowFlags(self.defaultwindowflags)
#        self.cchwin.setAttribute(QtCore.Qt.WA_TranslucentBackground)  # 设置窗口背景透明
#        self.cchwin.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents,on=False) #窗口点击而过，不响应鼠标（貌似无效）。

        self.cchwin.setGeometry(self.cchwinGeo)
        self.cchwin.show()

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

    def lockunlock(self):
        if self.locked:
            self.modifyMonitorUIstart()
        else:
            self.modifyMonitorUIdone()


    def cchwinSave(self):
        self.cchwin.restart_ani()
        self.cchwin.reAdjustRails()

        #此处需获取CCHWIN的相关参数，并保存到配置文件中，包括geometry
        self.msg("Saving current configurations and readjust UI layout.")
        print('cch window geo:'+str(self.cchwinGeo))
        print('saving!')
        self.saveconfig() #需补保存窗口位置的代码。

    def cchwinCreate(self):

        self.cchwin.resume_ani()
        self.testchain_timer.start(TEST_CHAIN_INTERVAL)
        self.msg("Creating test CH chain now.")
        self.testchain_started = True


    def testchain(self):

        tankname=random.choice(['Jumo','Balor','Tiggo','Grendol'])
        clericid=random.choice(['AAA','BBB','CCC','DDD','EEE','FFF','GGG','HHH','III'])
        self.cchwin.create_ani(tankname,clericid)



    def cchwinStop(self):
        self.testchain_started = False
        self.cchwin.pause_ani()
        self.testchain_timer.stop()
        self.msg("Test CH chain stops.")

    def cchwinAdapt(self):
        self.cchwin.restart_ani()
        self.cchwin.reAdjustRails()
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
        self.f.close()
        self.f = open('CCHPM RUN LOG.txt',encoding='utf-8')

        self.cchwinGeo=QtCore.QRect(586, 669, 528, 126)
        self.cchwin.setGeometry(self.cchwinGeo)
        self.cchwin.restart_ani()
        self.cchwin.reAdjustRails()
        self.msg("INFO:Reset all configuration to default value.")
        self.initializing = False

    def chbarheight(self,railheight:int):
        if self.initializing:
            return

        self.cchwin.railheight=railheight
        self.railheight=railheight
        self.cchwin.restart_ani()
        self.cchwin.reAdjustRails()

        self.saveconfig()
        self.msg(f"INFO:Chaged CH BAR height to {railheight}.")

    def monitorwidthmargin(self,widthMargin:int):
        if self.initializing:
            return

        self.cchwin.widthMargin=widthMargin
        self.cchwinwidthMargin=widthMargin
        self.cchwin.restart_ani()
        self.cchwin.reAdjustRails()

        self.saveconfig()
        self.msg(f"INFO:Chaged width margin to {widthMargin}.")


    def monitorheightmargin(self,heigthMargin:int):
        if self.initializing:
            return

        self.cchwin.heigthMargin=heigthMargin
        self.cchwinheigthMargin=heigthMargin
        self.cchwin.restart_ani()
        self.cchwin.reAdjustRails()

        self.saveconfig()
        self.msg(f"INFO:Chaged height margin to {heigthMargin}.")

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

    def openHistoryLog(self):
        os.startfile(".\\CCHPM RUN LOG.txt")

if __name__ == "__main__":

    app = QApplication(sys.argv)
    cfgWindow = CFGWIN()
    cfgWindow.show()
    cfgWindow.initializing = False


    result=app.exec_()
    cfgWindow.msg(f"INFO:Exiting CCHPM now. Return Code={result}")
    sys.exit(result)
