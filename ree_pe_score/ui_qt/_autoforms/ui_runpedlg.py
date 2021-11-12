# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'RunPEDlg.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(542, 396)
        self.verticalLayout = QtWidgets.QVBoxLayout(Dialog)
        self.verticalLayout.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.verticalLayout.setObjectName("verticalLayout")
        self.groupBox = QtWidgets.QGroupBox(Dialog)
        self.groupBox.setObjectName("groupBox")
        self.gridLayout = QtWidgets.QGridLayout(self.groupBox)
        self.gridLayout.setSizeConstraint(QtWidgets.QLayout.SetMaximumSize)
        self.gridLayout.setObjectName("gridLayout")
        self.label_7 = QtWidgets.QLabel(self.groupBox)
        self.label_7.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_7.setIndent(-1)
        self.label_7.setObjectName("label_7")
        self.gridLayout.addWidget(self.label_7, 3, 0, 1, 1)
        self.indexDirLbl = ElideLabel(self.groupBox)
        font = QtGui.QFont()
        font.setItalic(True)
        self.indexDirLbl.setFont(font)
        self.indexDirLbl.setObjectName("indexDirLbl")
        self.gridLayout.addWidget(self.indexDirLbl, 1, 1, 1, 1)
        self.label_6 = QtWidgets.QLabel(self.groupBox)
        self.label_6.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_6.setIndent(-1)
        self.label_6.setObjectName("label_6")
        self.gridLayout.addWidget(self.label_6, 2, 0, 1, 1)
        self.gdbLbl = ElideLabel(self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.gdbLbl.sizePolicy().hasHeightForWidth())
        self.gdbLbl.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setItalic(True)
        self.gdbLbl.setFont(font)
        self.gdbLbl.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.gdbLbl.setObjectName("gdbLbl")
        self.gridLayout.addWidget(self.gdbLbl, 0, 1, 1, 1)
        self.label_5 = QtWidgets.QLabel(self.groupBox)
        self.label_5.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_5.setObjectName("label_5")
        self.gridLayout.addWidget(self.label_5, 1, 0, 1, 1)
        self.label_8 = QtWidgets.QLabel(self.groupBox)
        self.label_8.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_8.setIndent(-1)
        self.label_8.setObjectName("label_8")
        self.gridLayout.addWidget(self.label_8, 4, 0, 1, 1)
        self.label = QtWidgets.QLabel(self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.srcToolButton = QtWidgets.QToolButton(self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.srcToolButton.sizePolicy().hasHeightForWidth())
        self.srcToolButton.setSizePolicy(sizePolicy)
        self.srcToolButton.setMinimumSize(QtCore.QSize(0, 23))
        self.srcToolButton.setIconSize(QtCore.QSize(5, 5))
        self.srcToolButton.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.srcToolButton.setToolButtonStyle(QtCore.Qt.ToolButtonTextOnly)
        self.srcToolButton.setArrowType(QtCore.Qt.DownArrow)
        self.srcToolButton.setObjectName("srcToolButton")
        self.gridLayout.addWidget(self.srcToolButton, 0, 2, 1, 1)
        self.label_9 = QtWidgets.QLabel(self.groupBox)
        self.label_9.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_9.setIndent(-1)
        self.label_9.setObjectName("label_9")
        self.gridLayout.addWidget(self.label_9, 5, 0, 1, 1)
        self.inputDirButton = QtWidgets.QPushButton(self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.inputDirButton.sizePolicy().hasHeightForWidth())
        self.inputDirButton.setSizePolicy(sizePolicy)
        self.inputDirButton.setObjectName("inputDirButton")
        self.gridLayout.addWidget(self.inputDirButton, 1, 2, 1, 1)
        self.ldIndField = QtWidgets.QLineEdit(self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.ldIndField.sizePolicy().hasHeightForWidth())
        self.ldIndField.setSizePolicy(sizePolicy)
        self.ldIndField.setObjectName("ldIndField")
        self.gridLayout.addWidget(self.ldIndField, 2, 1, 1, 1)
        self.lgIndField = QtWidgets.QLineEdit(self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lgIndField.sizePolicy().hasHeightForWidth())
        self.lgIndField.setSizePolicy(sizePolicy)
        self.lgIndField.setObjectName("lgIndField")
        self.gridLayout.addWidget(self.lgIndField, 3, 1, 1, 1)
        self.sdIndField = QtWidgets.QLineEdit(self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sdIndField.sizePolicy().hasHeightForWidth())
        self.sdIndField.setSizePolicy(sizePolicy)
        self.sdIndField.setObjectName("sdIndField")
        self.gridLayout.addWidget(self.sdIndField, 4, 1, 1, 1)
        self.udIndField = QtWidgets.QLineEdit(self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.udIndField.sizePolicy().hasHeightForWidth())
        self.udIndField.setSizePolicy(sizePolicy)
        self.udIndField.setObjectName("udIndField")
        self.gridLayout.addWidget(self.udIndField, 5, 1, 1, 1)
        self.gridLayout.setColumnStretch(1, 1)
        self.verticalLayout.addWidget(self.groupBox)
        self.groupBox_2 = QtWidgets.QGroupBox(Dialog)
        self.groupBox_2.setObjectName("groupBox_2")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.groupBox_2)
        self.gridLayout_2.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.dadsCombo = QtWidgets.QComboBox(self.groupBox_2)
        self.dadsCombo.setEnabled(False)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.dadsCombo.sizePolicy().hasHeightForWidth())
        self.dadsCombo.setSizePolicy(sizePolicy)
        self.dadsCombo.setObjectName("dadsCombo")
        self.dadsCombo.addItem("")
        self.dadsCombo.addItem("")
        self.gridLayout_2.addWidget(self.dadsCombo, 1, 1, 1, 1)
        self.limitDaDsCB = QtWidgets.QCheckBox(self.groupBox_2)
        self.limitDaDsCB.setObjectName("limitDaDsCB")
        self.gridLayout_2.addWidget(self.limitDaDsCB, 1, 0, 1, 1)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setContentsMargins(20, -1, -1, -1)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.exitOnRasterCB = QtWidgets.QCheckBox(self.groupBox_2)
        self.exitOnRasterCB.setEnabled(False)
        self.exitOnRasterCB.setObjectName("exitOnRasterCB")
        self.horizontalLayout.addWidget(self.exitOnRasterCB)
        self.gridLayout_2.addLayout(self.horizontalLayout, 3, 0, 1, 1)
        self.outDirLbl = ElideLabel(self.groupBox_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.outDirLbl.sizePolicy().hasHeightForWidth())
        self.outDirLbl.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setItalic(True)
        self.outDirLbl.setFont(font)
        self.outDirLbl.setScaledContents(False)
        self.outDirLbl.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.outDirLbl.setTextInteractionFlags(QtCore.Qt.TextSelectableByKeyboard|QtCore.Qt.TextSelectableByMouse)
        self.outDirLbl.setObjectName("outDirLbl")
        self.gridLayout_2.addWidget(self.outDirLbl, 0, 1, 1, 1)
        self.rasterDirCB = QtWidgets.QCheckBox(self.groupBox_2)
        self.rasterDirCB.setObjectName("rasterDirCB")
        self.gridLayout_2.addWidget(self.rasterDirCB, 2, 0, 1, 1)
        self.rasterDirLbl = ElideLabel(self.groupBox_2)
        self.rasterDirLbl.setEnabled(False)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.rasterDirLbl.sizePolicy().hasHeightForWidth())
        self.rasterDirLbl.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setItalic(True)
        self.rasterDirLbl.setFont(font)
        self.rasterDirLbl.setObjectName("rasterDirLbl")
        self.gridLayout_2.addWidget(self.rasterDirLbl, 2, 1, 1, 1)
        self.rasterDirButton = QtWidgets.QPushButton(self.groupBox_2)
        self.rasterDirButton.setEnabled(False)
        self.rasterDirButton.setObjectName("rasterDirButton")
        self.gridLayout_2.addWidget(self.rasterDirButton, 2, 2, 1, 1)
        self.outDirButton = QtWidgets.QPushButton(self.groupBox_2)
        self.outDirButton.setObjectName("outDirButton")
        self.gridLayout_2.addWidget(self.outDirButton, 0, 2, 1, 1)
        self.label_3 = QtWidgets.QLabel(self.groupBox_2)
        self.label_3.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.label_3.setObjectName("label_3")
        self.gridLayout_2.addWidget(self.label_3, 0, 0, 1, 1)
        self.gridLayout_2.setColumnStretch(1, 1)
        self.verticalLayout.addWidget(self.groupBox_2)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Calculate PE Score"))
        self.groupBox.setTitle(_translate("Dialog", "Inputs"))
        self.label_7.setText(_translate("Dialog", "LG Index Raster:"))
        self.indexDirLbl.setText(_translate("Dialog", "None"))
        self.label_6.setText(_translate("Dialog", "LD Index Raster:"))
        self.gdbLbl.setText(_translate("Dialog", "None"))
        self.label_5.setText(_translate("Dialog", "Index Files Directory:"))
        self.label_8.setText(_translate("Dialog", "SD Index Raster:"))
        self.label.setText(_translate("Dialog", "Source File:"))
        self.srcToolButton.setText(_translate("Dialog", "Select..."))
        self.label_9.setText(_translate("Dialog", "UD Index Raster:"))
        self.inputDirButton.setText(_translate("Dialog", "Select..."))
        self.ldIndField.setText(_translate("Dialog", "ld_inds.tif"))
        self.lgIndField.setText(_translate("Dialog", "lg_inds.tif"))
        self.sdIndField.setText(_translate("Dialog", "sd_inds.tif"))
        self.udIndField.setText(_translate("Dialog", "ud_inds.tif"))
        self.groupBox_2.setTitle(_translate("Dialog", "Outputs"))
        self.dadsCombo.setItemText(0, _translate("Dialog", "DA"))
        self.dadsCombo.setItemText(1, _translate("Dialog", "DS"))
        self.limitDaDsCB.setText(_translate("Dialog", "Only Calculate Score for"))
        self.exitOnRasterCB.setText(_translate("Dialog", "Skip Calculations"))
        self.outDirLbl.setText(_translate("Dialog", "None"))
        self.rasterDirCB.setText(_translate("Dialog", "Save Intermediate Rasters"))
        self.rasterDirLbl.setText(_translate("Dialog", "None"))
        self.rasterDirButton.setText(_translate("Dialog", "Select..."))
        self.outDirButton.setText(_translate("Dialog", "Select..."))
        self.label_3.setText(_translate("Dialog", "Output Directory:"))
from ..ElideLabelWidget import ElideLabel
