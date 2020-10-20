# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ProgressDlg.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_progLogDlg(object):
    def setupUi(self, progLogDlg):
        progLogDlg.setObjectName("progLogDlg")
        progLogDlg.resize(547, 433)
        self.verticalLayout = QtWidgets.QVBoxLayout(progLogDlg)
        self.verticalLayout.setObjectName("verticalLayout")
        self.logText = QtWidgets.QPlainTextEdit(progLogDlg)
        self.logText.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.logText.setObjectName("logText")
        self.verticalLayout.addWidget(self.logText)
        self.logProgBar = QtWidgets.QProgressBar(progLogDlg)
        self.logProgBar.setProperty("value", 0)
        self.logProgBar.setTextVisible(False)
        self.logProgBar.setObjectName("logProgBar")
        self.verticalLayout.addWidget(self.logProgBar)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.cancellingLbl = QtWidgets.QLabel(progLogDlg)
        self.cancellingLbl.setTextInteractionFlags(QtCore.Qt.NoTextInteraction)
        self.cancellingLbl.setObjectName("cancellingLbl")
        self.horizontalLayout.addWidget(self.cancellingLbl)
        self.buttonBox = QtWidgets.QDialogButtonBox(progLogDlg)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel)
        self.buttonBox.setObjectName("buttonBox")
        self.horizontalLayout.addWidget(self.buttonBox)
        self.verticalLayout.addLayout(self.horizontalLayout)

        self.retranslateUi(progLogDlg)
        QtCore.QMetaObject.connectSlotsByName(progLogDlg)

    def retranslateUi(self, progLogDlg):
        _translate = QtCore.QCoreApplication.translate
        progLogDlg.setWindowTitle(_translate("progLogDlg", "Progress"))
        self.cancellingLbl.setText(_translate("progLogDlg", "Cancelling..."))
