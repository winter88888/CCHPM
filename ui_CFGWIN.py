# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'CFGWIN.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_CFGWIN(object):
    def setupUi(self, CFGWIN):
        CFGWIN.setObjectName("CFGWIN")
        CFGWIN.resize(827, 526)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        CFGWIN.setFont(font)
        self.pushButton = QtWidgets.QPushButton(CFGWIN)
        self.pushButton.setGeometry(QtCore.QRect(630, 50, 81, 21))
        self.pushButton.setObjectName("pushButton")
        self.label = QtWidgets.QLabel(CFGWIN)
        self.label.setGeometry(QtCore.QRect(20, 30, 381, 20))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.lineEdit = QtWidgets.QLineEdit(CFGWIN)
        self.lineEdit.setGeometry(QtCore.QRect(20, 51, 601, 20))
        self.lineEdit.setObjectName("lineEdit")
        self.label_2 = QtWidgets.QLabel(CFGWIN)
        self.label_2.setGeometry(QtCore.QRect(10, 440, 701, 71))
        self.label_2.setAutoFillBackground(True)
        self.label_2.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.label_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.label_2.setLineWidth(5)
        self.label_2.setTextFormat(QtCore.Qt.RichText)
        self.label_2.setWordWrap(True)
        self.label_2.setIndent(-5)
        self.label_2.setOpenExternalLinks(True)
        self.label_2.setObjectName("label_2")
        self.groupBox = QtWidgets.QGroupBox(CFGWIN)
        self.groupBox.setGeometry(QtCore.QRect(0, 420, 731, 101))
        self.groupBox.setObjectName("groupBox")
        self.comboBox = QtWidgets.QComboBox(CFGWIN)
        self.comboBox.setGeometry(QtCore.QRect(20, 110, 151, 22))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.comboBox.setFont(font)
        self.comboBox.setObjectName("comboBox")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.label_3 = QtWidgets.QLabel(CFGWIN)
        self.label_3.setGeometry(QtCore.QRect(20, 90, 171, 16))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.label_3.setFont(font)
        self.label_3.setObjectName("label_3")
        self.pushButton_2 = QtWidgets.QPushButton(CFGWIN)
        self.pushButton_2.setGeometry(QtCore.QRect(730, 100, 81, 31))
        self.pushButton_2.setObjectName("pushButton_2")
        self.pushButton_3 = QtWidgets.QPushButton(CFGWIN)
        self.pushButton_3.setGeometry(QtCore.QRect(730, 40, 81, 31))
        self.pushButton_3.setObjectName("pushButton_3")
        self.groupBox_2 = QtWidgets.QGroupBox(CFGWIN)
        self.groupBox_2.setGeometry(QtCore.QRect(10, 150, 711, 101))
        self.groupBox_2.setObjectName("groupBox_2")
        self.label_5 = QtWidgets.QLabel(self.groupBox_2)
        self.label_5.setGeometry(QtCore.QRect(10, 30, 111, 21))
        self.label_5.setObjectName("label_5")
        self.spinBox = QtWidgets.QSpinBox(self.groupBox_2)
        self.spinBox.setGeometry(QtCore.QRect(120, 30, 42, 22))
        self.spinBox.setMinimum(5)
        self.spinBox.setMaximum(50)
        self.spinBox.setProperty("value", 20)
        self.spinBox.setObjectName("spinBox")
        self.spinBox_2 = QtWidgets.QSpinBox(self.groupBox_2)
        self.spinBox_2.setGeometry(QtCore.QRect(480, 30, 42, 22))
        self.spinBox_2.setMinimum(2)
        self.spinBox_2.setMaximum(100)
        self.spinBox_2.setObjectName("spinBox_2")
        self.label_6 = QtWidgets.QLabel(self.groupBox_2)
        self.label_6.setGeometry(QtCore.QRect(370, 30, 111, 21))
        self.label_6.setObjectName("label_6")
        self.spinBox_3 = QtWidgets.QSpinBox(self.groupBox_2)
        self.spinBox_3.setGeometry(QtCore.QRect(300, 30, 42, 22))
        self.spinBox_3.setMinimum(2)
        self.spinBox_3.setMaximum(100)
        self.spinBox_3.setObjectName("spinBox_3")
        self.label_7 = QtWidgets.QLabel(self.groupBox_2)
        self.label_7.setGeometry(QtCore.QRect(190, 30, 111, 21))
        self.label_7.setObjectName("label_7")
        self.label_18 = QtWidgets.QLabel(self.groupBox_2)
        self.label_18.setGeometry(QtCore.QRect(10, 70, 111, 21))
        self.label_18.setObjectName("label_18")
        self.spinBox_9 = QtWidgets.QSpinBox(self.groupBox_2)
        self.spinBox_9.setGeometry(QtCore.QRect(120, 70, 42, 22))
        self.spinBox_9.setMinimum(2)
        self.spinBox_9.setMaximum(100)
        self.spinBox_9.setObjectName("spinBox_9")
        self.spinBox_10 = QtWidgets.QSpinBox(self.groupBox_2)
        self.spinBox_10.setGeometry(QtCore.QRect(300, 70, 42, 22))
        self.spinBox_10.setMinimum(2)
        self.spinBox_10.setMaximum(100)
        self.spinBox_10.setObjectName("spinBox_10")
        self.label_19 = QtWidgets.QLabel(self.groupBox_2)
        self.label_19.setGeometry(QtCore.QRect(190, 70, 111, 21))
        self.label_19.setObjectName("label_19")
        self.spinBox_11 = QtWidgets.QSpinBox(self.groupBox_2)
        self.spinBox_11.setGeometry(QtCore.QRect(480, 70, 42, 22))
        self.spinBox_11.setMinimum(2)
        self.spinBox_11.setMaximum(100)
        self.spinBox_11.setObjectName("spinBox_11")
        self.label_20 = QtWidgets.QLabel(self.groupBox_2)
        self.label_20.setGeometry(QtCore.QRect(370, 70, 111, 21))
        self.label_20.setObjectName("label_20")
        self.spinBox_12 = QtWidgets.QSpinBox(self.groupBox_2)
        self.spinBox_12.setGeometry(QtCore.QRect(660, 70, 42, 22))
        self.spinBox_12.setMinimum(2)
        self.spinBox_12.setMaximum(100)
        self.spinBox_12.setObjectName("spinBox_12")
        self.label_21 = QtWidgets.QLabel(self.groupBox_2)
        self.label_21.setGeometry(QtCore.QRect(550, 70, 111, 21))
        self.label_21.setObjectName("label_21")
        self.label_11 = QtWidgets.QLabel(self.groupBox_2)
        self.label_11.setGeometry(QtCore.QRect(550, 30, 41, 21))
        self.label_11.setObjectName("label_11")
        self.pushButton_4 = QtWidgets.QPushButton(CFGWIN)
        self.pushButton_4.setGeometry(QtCore.QRect(730, 210, 81, 31))
        self.pushButton_4.setObjectName("pushButton_4")
        self.pushButton_5 = QtWidgets.QPushButton(CFGWIN)
        self.pushButton_5.setGeometry(QtCore.QRect(730, 160, 81, 31))
        self.pushButton_5.setObjectName("pushButton_5")
        self.line_2 = QtWidgets.QFrame(CFGWIN)
        self.line_2.setGeometry(QtCore.QRect(0, 140, 821, 20))
        self.line_2.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_2.setObjectName("line_2")
        self.line_3 = QtWidgets.QFrame(CFGWIN)
        self.line_3.setGeometry(QtCore.QRect(0, 410, 821, 16))
        self.line_3.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_3.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_3.setObjectName("line_3")
        self.pushButton_6 = QtWidgets.QPushButton(CFGWIN)
        self.pushButton_6.setGeometry(QtCore.QRect(750, 260, 61, 31))
        self.pushButton_6.setObjectName("pushButton_6")
        self.pushButton_7 = QtWidgets.QPushButton(CFGWIN)
        self.pushButton_7.setGeometry(QtCore.QRect(750, 300, 61, 31))
        self.pushButton_7.setObjectName("pushButton_7")
        self.pushButton_8 = QtWidgets.QPushButton(CFGWIN)
        self.pushButton_8.setGeometry(QtCore.QRect(750, 340, 61, 31))
        self.pushButton_8.setObjectName("pushButton_8")
        self.pushButton_9 = QtWidgets.QPushButton(CFGWIN)
        self.pushButton_9.setGeometry(QtCore.QRect(750, 380, 61, 31))
        self.pushButton_9.setObjectName("pushButton_9")
        self.line_4 = QtWidgets.QFrame(CFGWIN)
        self.line_4.setGeometry(QtCore.QRect(740, 390, 20, 20))
        self.line_4.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_4.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_4.setObjectName("line_4")
        self.line_5 = QtWidgets.QFrame(CFGWIN)
        self.line_5.setGeometry(QtCore.QRect(740, 350, 20, 20))
        self.line_5.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_5.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_5.setObjectName("line_5")
        self.line_6 = QtWidgets.QFrame(CFGWIN)
        self.line_6.setGeometry(QtCore.QRect(740, 310, 20, 20))
        self.line_6.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_6.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_6.setObjectName("line_6")
        self.line_7 = QtWidgets.QFrame(CFGWIN)
        self.line_7.setGeometry(QtCore.QRect(740, 270, 20, 20))
        self.line_7.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_7.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_7.setObjectName("line_7")
        self.line_8 = QtWidgets.QFrame(CFGWIN)
        self.line_8.setGeometry(QtCore.QRect(730, 240, 20, 161))
        self.line_8.setFrameShape(QtWidgets.QFrame.VLine)
        self.line_8.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_8.setObjectName("line_8")
        self.pushButton_10 = QtWidgets.QPushButton(CFGWIN)
        self.pushButton_10.setGeometry(QtCore.QRect(740, 460, 81, 31))
        self.pushButton_10.setObjectName("pushButton_10")
        self.label_8 = QtWidgets.QLabel(CFGWIN)
        self.label_8.setGeometry(QtCore.QRect(490, 110, 151, 21))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.label_8.setFont(font)
        self.label_8.setObjectName("label_8")
        self.spinBox_4 = QtWidgets.QSpinBox(CFGWIN)
        self.spinBox_4.setGeometry(QtCore.QRect(650, 110, 61, 22))
        self.spinBox_4.setMinimum(1)
        self.spinBox_4.setMaximum(9)
        self.spinBox_4.setProperty("value", 1)
        self.spinBox_4.setObjectName("spinBox_4")
        self.label_4 = QtWidgets.QLabel(CFGWIN)
        self.label_4.setGeometry(QtCore.QRect(490, 90, 231, 21))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.label_4.setFont(font)
        self.label_4.setObjectName("label_4")
        self.checkBox = QtWidgets.QCheckBox(CFGWIN)
        self.checkBox.setGeometry(QtCore.QRect(90, 270, 181, 21))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.checkBox.setFont(font)
        self.checkBox.setObjectName("checkBox")
        self.label_9 = QtWidgets.QLabel(CFGWIN)
        self.label_9.setGeometry(QtCore.QRect(190, 90, 191, 20))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.label_9.setFont(font)
        self.label_9.setObjectName("label_9")
        self.comboBox_2 = QtWidgets.QComboBox(CFGWIN)
        self.comboBox_2.setEnabled(True)
        self.comboBox_2.setGeometry(QtCore.QRect(190, 110, 211, 22))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.comboBox_2.setFont(font)
        self.comboBox_2.setEditable(True)
        self.comboBox_2.setObjectName("comboBox_2")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.label_10 = QtWidgets.QLabel(CFGWIN)
        self.label_10.setGeometry(QtCore.QRect(10, 270, 81, 21))
        self.label_10.setObjectName("label_10")
        self.pushButton_11 = QtWidgets.QPushButton(CFGWIN)
        self.pushButton_11.setGeometry(QtCore.QRect(410, 120, 61, 21))
        self.pushButton_11.setObjectName("pushButton_11")
        self.pushButton_12 = QtWidgets.QPushButton(CFGWIN)
        self.pushButton_12.setGeometry(QtCore.QRect(410, 90, 61, 21))
        self.pushButton_12.setObjectName("pushButton_12")
        self.comboBox_3 = QtWidgets.QComboBox(CFGWIN)
        self.comboBox_3.setGeometry(QtCore.QRect(620, 180, 91, 22))
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(11)
        self.comboBox_3.setFont(font)
        self.comboBox_3.setObjectName("comboBox_3")
        self.comboBox_3.addItem("")
        self.comboBox_3.addItem("")
        self.comboBox_3.addItem("")
        self.line_6.raise_()
        self.line_5.raise_()
        self.line_7.raise_()
        self.line_4.raise_()
        self.groupBox.raise_()
        self.pushButton.raise_()
        self.label.raise_()
        self.lineEdit.raise_()
        self.label_2.raise_()
        self.comboBox.raise_()
        self.label_3.raise_()
        self.pushButton_2.raise_()
        self.pushButton_3.raise_()
        self.groupBox_2.raise_()
        self.pushButton_4.raise_()
        self.pushButton_5.raise_()
        self.line_2.raise_()
        self.line_3.raise_()
        self.pushButton_6.raise_()
        self.pushButton_7.raise_()
        self.pushButton_8.raise_()
        self.pushButton_9.raise_()
        self.line_8.raise_()
        self.pushButton_10.raise_()
        self.label_8.raise_()
        self.spinBox_4.raise_()
        self.label_4.raise_()
        self.checkBox.raise_()
        self.label_9.raise_()
        self.comboBox_2.raise_()
        self.label_10.raise_()
        self.pushButton_11.raise_()
        self.pushButton_12.raise_()
        self.comboBox_3.raise_()

        self.retranslateUi(CFGWIN)
        self.pushButton.clicked.connect(CFGWIN.openlogdir)
        self.lineEdit.editingFinished.connect(CFGWIN.editfinished)
        self.comboBox.currentIndexChanged['QString'].connect(CFGWIN.serverSelect)
        self.pushButton_2.clicked.connect(CFGWIN.restart)
        self.pushButton_3.clicked.connect(CFGWIN.startorstop)
        self.pushButton_4.clicked.connect(CFGWIN.lockunlock)
        self.pushButton_5.clicked.connect(CFGWIN.default)
        self.spinBox.valueChanged['int'].connect(CFGWIN.chbarheight)
        self.spinBox_3.valueChanged['int'].connect(CFGWIN.monitorwidthmargin)
        self.spinBox_2.valueChanged['int'].connect(CFGWIN.monitorheightmargin)
        self.spinBox_4.valueChanged['int'].connect(CFGWIN.chInterval)
        self.pushButton_6.clicked.connect(CFGWIN.cchwinSave)
        self.pushButton_7.clicked.connect(CFGWIN.cchwinCreate)
        self.pushButton_8.clicked.connect(CFGWIN.cchwinStop)
        self.pushButton_9.clicked.connect(CFGWIN.cchwinAdapt)
        self.pushButton_10.clicked.connect(CFGWIN.openHistoryLog)
        self.checkBox.toggled['bool'].connect(CFGWIN.autostart)
        self.comboBox_2.editTextChanged['QString'].connect(CFGWIN.changeCHFormat)
        self.pushButton_11.clicked.connect(CFGWIN.deleteCHFormat)
        self.comboBox_2.currentIndexChanged['int'].connect(CFGWIN.CHFormatChanged)
        self.pushButton_12.clicked.connect(CFGWIN.addCHFormat)
        self.comboBox_3.currentIndexChanged['QString'].connect(CFGWIN.markPosition)
        QtCore.QMetaObject.connectSlotsByName(CFGWIN)

    def retranslateUi(self, CFGWIN):
        _translate = QtCore.QCoreApplication.translate
        CFGWIN.setWindowTitle(_translate("CFGWIN", "CCHPM -Chain CH Performance Monitor  ---Desinger: Jumo@Kingdom of P1999 Green server"))
        self.pushButton.setText(_translate("CFGWIN", "OPEN"))
        self.label.setText(_translate("CFGWIN", "Step 1.Setup your Everquest log file\'s directory below:"))
        self.lineEdit.setText(_translate("CFGWIN", "D:\\Everquest\\Logs"))
        self.label_2.setText(_translate("CFGWIN", "EXAMPLE MSG"))
        self.groupBox.setTitle(_translate("CFGWIN", "MESSAGE:"))
        self.comboBox.setItemText(0, _translate("CFGWIN", "Any"))
        self.comboBox.setItemText(1, _translate("CFGWIN", "P1999Green"))
        self.comboBox.setItemText(2, _translate("CFGWIN", "project1999"))
        self.comboBox.setItemText(3, _translate("CFGWIN", "KingdomDragons"))
        self.label_3.setText(_translate("CFGWIN", "Step 2. Choose server"))
        self.pushButton_2.setText(_translate("CFGWIN", "CLEAR"))
        self.pushButton_3.setText(_translate("CFGWIN", "ON AIR"))
        self.groupBox_2.setTitle(_translate("CFGWIN", "CH BAR Settings"))
        self.label_5.setText(_translate("CFGWIN", "CH bar height:"))
        self.label_6.setText(_translate("CFGWIN", "Height Margin"))
        self.label_7.setText(_translate("CFGWIN", "Width Margin:"))
        self.label_18.setText(_translate("CFGWIN", "BG COLOR"))
        self.label_19.setText(_translate("CFGWIN", "BAR COLOR"))
        self.label_20.setText(_translate("CFGWIN", "BG Opacity"))
        self.label_21.setText(_translate("CFGWIN", "BAR Opacity"))
        self.label_11.setText(_translate("CFGWIN", "Marks"))
        self.pushButton_4.setText(_translate("CFGWIN", "UNLOCK"))
        self.pushButton_5.setText(_translate("CFGWIN", "DEFAULT"))
        self.pushButton_6.setText(_translate("CFGWIN", "Save"))
        self.pushButton_7.setText(_translate("CFGWIN", "Create"))
        self.pushButton_8.setText(_translate("CFGWIN", "Stop"))
        self.pushButton_9.setText(_translate("CFGWIN", "Adapt"))
        self.pushButton_10.setText(_translate("CFGWIN", "HISTORY"))
        self.label_8.setWhatsThis(_translate("CFGWIN", "<html><head/><body><p>Use !KIn in game to change the CH interval. For this command \'n\' should be between 1 to 9 second(s).</p></body></html>"))
        self.label_8.setText(_translate("CFGWIN", "CH Intervals (second):"))
        self.spinBox_4.setWhatsThis(_translate("CFGWIN", "<html><head/><body><p>Use !KIn in game to change the CH interval. For this command \'n\' should be between 1 to 9 second(s).</p></body></html>"))
        self.label_4.setText(_translate("CFGWIN", "Step 4. Setup CH interval(second)"))
        self.checkBox.setText(_translate("CFGWIN", "Autostart CCH monitor"))
        self.label_9.setText(_translate("CFGWIN", "Step 3.Setup CH format"))
        self.comboBox_2.setItemText(0, _translate("CFGWIN", "### - CH - tankname"))
        self.comboBox_2.setItemText(1, _translate("CFGWIN", "ST ### CH -- tankname"))
        self.label_10.setText(_translate("CFGWIN", "Start mode:"))
        self.pushButton_11.setText(_translate("CFGWIN", "Delete"))
        self.pushButton_12.setText(_translate("CFGWIN", "Add"))
        self.comboBox_3.setItemText(0, _translate("CFGWIN", "On bar"))
        self.comboBox_3.setItemText(1, _translate("CFGWIN", "Under bar"))
        self.comboBox_3.setItemText(2, _translate("CFGWIN", "Above bar"))
