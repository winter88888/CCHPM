import sys
import os
from PyQt5.Qt import *
from PyQt5.QtCore import QTimer, QDateTime
from PyQt5 import QtCore, QtGui, QtWidgets

#const definition
CCHRAILPTR = 0
ANILISTPTR = 1
RAILCAPACITY = 20



class CCHWIN(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.btn_counter=0
        self.anidict= {} # key : tankname, Value[0]: cch rail , Value[1] : animation list of this rail. value[2] : index of railslots
        self.buttonlist=[]
        self.btnText2clericName={}
        self.interval=1
        self.railheight=20
        self.markheight=10
        self.mark_pos="On bar"  #On bar/Under bar/Above bar.
        self.railslots = []
        self.max_rails = 0
        for i in range(0,RAILCAPACITY):
            self.railslots.append(['NA',0])

        self.width = 0
        self.height= 0
        self.widthMargin=2
        self.heigthMargin=2
        self.markbynum = True
        self.you = ''

        self.init_ui()

    def init_ui(self):

        self.setWindowTitle('Realtime CH Chain Monitor')

    def __create_cchrail(self,tankname='someone'):

        rail_y = None
        pickedslot = None
        for i in range(0,len(self.railslots)):
            if self.railslots[i][0] == "FREE":
                self.railslots[i][0] = 'BUSY'
                rail_y=self.railslots[i][1]
                pickedslot= i
                break
        if pickedslot == None:
            return False

        cchrail = QWidget()
        cchrail.resize(self.width, self.railheight)
        cchrail.setAttribute(QtCore.Qt.WA_TranslucentBackground) # 设置窗口背景透明
        cchrail.setAutoFillBackground(True)
        cchrail.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)  # 永远最前，无边框标题栏，去任务栏标签
        cchrail.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents) #窗口点击而过，不响应鼠标（貌似无效）。
        if rail_y != None:
            cchrail.move(self.posx, rail_y+self.posy)
        cchrail.show()


        # CCH RAIL刻度这里实现。

        if self.mark_pos=="On bar":
            markrail=cchrail
            self.markheight=self.railheight
        else:
            markrail=QWidget()
            markrail.resize(self.width, self.markheight)
            markrail.setAttribute(QtCore.Qt.WA_TranslucentBackground)  # 设置窗口背景透明
            markrail.setAutoFillBackground(True)
            markrail.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
            markrail.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
            if rail_y != None:
                if self.mark_pos=="Above bar":
                    markrail.move(self.posx, rail_y + self.posy-self.markheight)
                else: #self.mark_pos=="Under bar"
                    markrail.move(self.posx, rail_y + self.posy+self.railheight)
            markrail.show()

        marklables=[]
        for i in range(9):
            lable = QLabel(markrail)

            if self.markbynum:
                lable.setText(str(i + 1))
            else:
                lable.setText('|')
            lable.resize(10,self.markheight)
            lable.move((i + 1) * (self.width/10)-5, 0)
            lable.setStyleSheet('color: red;')
            lable.show()
            marklables.append(lable)
        marklables[9-self.interval].setStyleSheet('color: yellow;')

        barlables = []
        if self.mark_pos != "On bar":
            for i in range(9):
                lable = QLabel(cchrail)
                lable.setText('|')
                lable.resize(10,self.railheight)
                lable.move((i + 1) * (self.width/10)-5, 0)
                lable.setStyleSheet('color: red;')
                lable.show()
                barlables.append((lable))
            barlables[9 - self.interval].setStyleSheet('color: yellow;')


        pos_x = cchrail.geometry().getRect()[0]
        pos_y = cchrail.geometry().getRect()[1]
        width = cchrail.geometry().getRect()[2]
        height = cchrail.geometry().getRect()[3]

        cchrail.railbackgroundbtn = QPushButton(cchrail)
        current_btn_width=width
        cchrail.railbackgroundbtn.resize(current_btn_width, height)
        cchrail.railbackgroundbtn.move(0, 0)
        cchrail.railbackgroundbtn.setStyleSheet('QPushButton{border: none; background: black;}')
        cchrail.railbackgroundbtn.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        op = QtWidgets.QGraphicsOpacityEffect()
        op.setOpacity(0.1) # 设置透明度的值，0.0到1.0，最小值0是透明，1是不透明
        cchrail.railbackgroundbtn.setGraphicsEffect(op)
        cchrail.railbackgroundbtn.show()


        mt_btn = QPushButton()
        current_btn_width=width/10
        mt_btn.resize(current_btn_width, height)
        mt_btn.move(pos_x-current_btn_width-self.widthMargin, pos_y)
        mt_btn.setStyleSheet('QPushButton{border: none; background: peru;}')

        mt_btn.setAttribute(QtCore.Qt.WA_TranslucentBackground) # 设置窗口背景透明
        mt_btn.setAutoFillBackground(True)
        mt_btn.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)  # 永远最前，无边框标题栏，去任务栏标签
        mt_btn.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents) #窗口点击而过，不响应鼠标（貌似无效）。

        op = QtWidgets.QGraphicsOpacityEffect()
        op.setOpacity(1) # 设置透明度的值，0.0到1.0，最小值0是透明，1是不透明
        mt_btn.setGraphicsEffect(op)
        mt_btn.show()
        mt_btn.setText(tankname)

        cleric_btn = QPushButton()
        current_btn_width=width/10
        cleric_btn.resize(current_btn_width, height)
        cleric_btn.move(pos_x+width+self.widthMargin, pos_y)
        cleric_btn.setStyleSheet('QPushButton{border: none; background: purple;}')
        cleric_btn.setAttribute(QtCore.Qt.WA_TranslucentBackground) # 设置窗口背景透明
        cleric_btn.setAutoFillBackground(True)
        cleric_btn.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)  # 永远最前，无边框标题栏，去任务栏标签
        cleric_btn.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents) #窗口点击而过，不响应鼠标（貌似无效）。

        op = QtWidgets.QGraphicsOpacityEffect()
        op.setOpacity(1) # 设置透明度的值，0.0到1.0，最小值0是透明，1是不透明
        cleric_btn.setGraphicsEffect(op)
        cleric_btn.show()


        self.anidict[tankname]= [cchrail,[],pickedslot,mt_btn,cleric_btn,markrail,marklables,barlables,[],'']
        return True


    def create_ani(self,tankname="name",clericid="AAA",clericName="name"):
        if self.anidict.get(tankname) == None:
            if not self.__create_cchrail(tankname):
                print("no enough space to display CH chain for",tankname)
                return
        self.anidict[tankname][8].append(clericid)
        self.anidict[tankname][8].sort()
        self.anidict[tankname][4].setText(self.nextid(tankname,clericid))
        if self.you == self.nextid(tankname,clericid):
            self.anidict[tankname][4].setStyleSheet('QPushButton{color: gold;border-width: 3px;border-style: solid;border-color: gold;background: purple;}')
        else:
            self.anidict[tankname][4].setStyleSheet('QPushButton{color: none;border: none; background: purple;}')

        current_cchrail=self.anidict[tankname][CCHRAILPTR]
        self.btn = QPushButton(current_cchrail)
        #self.btn = QPushButton()
        width = current_cchrail.geometry().getRect()[2]
        height = current_cchrail.geometry().getRect()[3]
        #self.btn.setWindowOpacity(1)  # 设置窗口透明度
        #self.btn.setAttribute(QtCore.Qt.WA_TranslucentBackground,on=False)  # 设置窗口背景透明

        current_btn_width=width/10*self.interval  #Interval depend on !KIn ,which n = CH interval(second)
        self.btn.resize(current_btn_width, height)
        self.btn.move(width-current_btn_width, 0)
        #print('width',width,'current_btn_width',current_btn_width)
        self.btn.setStyleSheet('QPushButton{border: none; background: green;}')
        self.btn.setText(clericid)
        self.buttonlist.append(self.btn)
        self.btnText2clericName[clericid]=clericName
        self.btn.show()


        self.animation = QPropertyAnimation(self.btn, b'pos', current_cchrail)
        self.animation.setKeyValueAt(0, QPoint(width-current_btn_width, 0))
        self.animation.setKeyValueAt(1, QPoint(-current_btn_width, 0))
        self.animation.setDuration(10000) # CH casting time =10s
        self.animation.start()
        self.anidict[tankname][ANILISTPTR].append(self.animation)
        self.btn_counter += 1

    def nextid(self,tankname:str,clericid:str):

        if clericid.upper() == 'R11':
            return "R22"
        if clericid.upper() == 'R22':
            return "R11"

        if clericid == self.anidict[tankname][8][0]:
            self.anidict[tankname][9]=self.anidict[tankname][8][-1]
        if clericid == self.anidict[tankname][9]:
            return self.anidict[tankname][8][0]

        newid=chr(ord(clericid[0].upper())+1)
        if newid==':':
            newid='0'
        if newid == '[':
            newid='A'
        return newid*3


    def destroy_ani(self):
        for key in self.anidict.keys():
            for ani in self.anidict[key][ANILISTPTR]:
                if ani.state() == 0:
                    btn=ani.targetObject()
                    ani.deleteLater()
                    self.anidict[key][ANILISTPTR].remove(ani)
                    btn.deleteLater()
                    self.buttonlist.remove(btn)

        mtnames=list(self.anidict.keys())
        #print('mtlist:',mtnames)
        #print(self.railslots)
        for key in mtnames:
            if len(self.anidict[key][ANILISTPTR]) == 0:
                a=self.anidict.pop(key)
                a[3].close()
                a[4].close()
                a[CCHRAILPTR].hide()
                a[CCHRAILPTR].deleteLater()
                self.railslots[a[2]][0]='FREE'

    def yourSpellInterrupted(self):

        for btn in self.buttonlist:
            if btn.text()==self.you:
                btn.hide()

    def someoneSpellInterrupted(self,clericName:str):
        for btn in self.buttonlist:
            if btn.text() in self.btnText2clericName:
                if self.btnText2clericName[btn.text()] == clericName:
                    btn.hide()


    def restart_ani(self):
        print('restarting animations')

        for key in self.anidict.keys():
            for ani in self.anidict[key][ANILISTPTR]:
                ani.stop()
        self.destroy_ani()

    def reAdjustRails(self):
        #print('adjusting cch rails',self.geometry())
        self.posx = self.geometry().getRect()[0]
        self.posy = self.geometry().getRect()[1]
        self.width = self.geometry().getRect()[2]
        self.height=self.geometry().getRect()[3]

        for i in range(0, RAILCAPACITY):
            self.railslots[i]=['NA', 0]

        if self.mark_pos=="On bar":
            self.markheight=0
        else:
            self.markheight = 10
        self.max_rails = int(self.height / (self.railheight + self.heigthMargin+self.markheight))
        for i in range(0, self.max_rails):
            self.railslots[i] = ['FREE', self.height - (self.railheight + self.heigthMargin+self.markheight) * (i + 1)]

    def pause_ani(self):
        print('trying to pause animations')
        for name in self.anidict.keys():
            for i in self.anidict[name][ANILISTPTR]:
                i.pause()


    def resume_ani(self):
        print('trying to resume animations')
        for name in self.anidict.keys():
            for i in self.anidict[name][ANILISTPTR]:
                i.resume()

    def hide_cch_rails(self):
        print('trying to hide CCH rails')
        for name in self.anidict.keys():
            self.anidict[name][CCHRAILPTR].hide()

    def show_cch_rails(self):
        print('trying to show CCH rails')
        for name in self.anidict.keys():
            self.anidict[name][CCHRAILPTR].show()




    def setinterval(self,interval:int):

        for tankname in self.anidict:
            self.anidict[tankname][6][9-self.interval].setStyleSheet('color: red;')
            self.anidict[tankname][6][9-interval].setStyleSheet('color: yellow;')
            if self.anidict[tankname][7]:
                self.anidict[tankname][7][9 - self.interval].setStyleSheet('color: red;')
                self.anidict[tankname][7][9 - interval].setStyleSheet('color: yellow;')

        self.interval=interval


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CCHWIN()
    window.show()

    timer=QTimer(window)
    timer.timeout.connect(window.destroy_ani)
    timer.start(1000)
    sys.exit(app.exec_())
