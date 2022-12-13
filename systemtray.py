
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
import resource
import time

class TrayIcon(QtWidgets.QSystemTrayIcon):
    def __init__(self, MainWindow, parent=None):
        super(TrayIcon, self).__init__(parent)
        self.ui = MainWindow
        self.createMenu()
        self.setToolTip("CCHPM by Jumo")

    def createMenu(self):
        self.menu = QtWidgets.QMenu()
        self.showAction = QtWidgets.QAction("Show CCHPM", self, triggered=self.show_window)
        self.startAction = QtWidgets.QAction("Start parsing", self, triggered=self.start_parse)
        self.pauseAction = QtWidgets.QAction("Pause parsing", self, triggered=self.pause_parse)
        self.clearAction = QtWidgets.QAction("Clear screen", self, triggered=self.clear_screen)
        self.quitAction = QtWidgets.QAction("Quit CCHPM", self, triggered=self.quit)
        #self.msgAction = QtWidgets.QAction("notices", self, triggered=self.showMsg)

        self.menu.addAction(self.showAction)
        self.menu.addAction(self.startAction)
        self.menu.addAction(self.pauseAction)
        self.menu.addAction(self.clearAction)
        self.menu.addAction(self.quitAction)
        self.setContextMenu(self.menu)

        # 设置图标
        self.sync_menu()
        self.icon = self.MessageIcon()

        # 把鼠标点击图标的信号和槽连接
        self.activated.connect(self.onIconClicked)

    def showMsg(self):
        self.showMessage("Message", "example message", self.icon)

    def show_window(self):
        # 若是最小化，则先正常显示窗口，再变为活动窗口（暂时显示在最前面）
        self.ui.showNormal()
        self.ui.activateWindow()
        self.ui.setWindowFlags(QtCore.Qt.Window)
        self.ui.show()

    def start_parse(self):
        self.ui.started = False
        self.ui.startorstop()
        self.sync_menu()

    def pause_parse(self):
        self.ui.started = True
        self.ui.startorstop()
        self.sync_menu()

    def clear_screen(self):
        self.ui.restart()

    def quit(self):
        QtWidgets.qApp.quit()

    def sync_menu(self):
        self.startAction.setEnabled(not self.ui.started)
        self.pauseAction.setEnabled(self.ui.started)

        if self.ui.started:
            self.currentIcon=QtGui.QIcon(":/CCHPM.ico")
        else:
            self.currentIcon = QtGui.QIcon(":/CCHPM2.ico")

        self.setIcon(self.currentIcon)

    # 鼠标点击icon传递的信号会带有一个整形的值，1是表示单击右键，2是双击，3是单击左键，4是用鼠标中键点击
    def onIconClicked(self, reason):
        if reason == 2 or reason == 3:
            # self.showMessage("Message", "skr at here", self.icon)
            if self.ui.isMinimized() or not self.ui.isVisible():
                # 若是最小化，则先正常显示窗口，再变为活动窗口（暂时显示在最前面）
                self.ui.showNormal()
                self.ui.activateWindow()
                self.ui.setWindowFlags(QtCore.Qt.Window)
                self.ui.show()
            else:
                # 若不是最小化，则最小化
                self.ui.showMinimized()
                self.ui.setWindowFlags(QtCore.Qt.SplashScreen)
                #self.ui.show()

