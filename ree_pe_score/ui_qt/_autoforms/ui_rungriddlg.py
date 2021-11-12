# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'RunGridDlg.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_CreateGridDlg(object):
    def setupUi(self, CreateGridDlg):
        CreateGridDlg.setObjectName("CreateGridDlg")
        CreateGridDlg.resize(351, 391)
        self.verticalLayout = QtWidgets.QVBoxLayout(CreateGridDlg)
        self.verticalLayout.setObjectName("verticalLayout")
        self.groupBox = QtWidgets.QGroupBox(CreateGridDlg)
        self.groupBox.setObjectName("groupBox")
        self.gridLayout = QtWidgets.QGridLayout(self.groupBox)
        self.gridLayout.setSizeConstraint(QtWidgets.QLayout.SetMaximumSize)
        self.gridLayout.setObjectName("gridLayout")
        self.sdInputButton = QtWidgets.QPushButton(self.groupBox)
        self.sdInputButton.setObjectName("sdInputButton")
        self.gridLayout.addWidget(self.sdInputButton, 0, 3, 1, 1)
        self.sdInputLbl = ElideLabel(self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sdInputLbl.sizePolicy().hasHeightForWidth())
        self.sdInputLbl.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setItalic(True)
        self.sdInputLbl.setFont(font)
        self.sdInputLbl.setObjectName("sdInputLbl")
        self.gridLayout.addWidget(self.sdInputLbl, 0, 1, 1, 1)
        self.ldInputLbl = ElideLabel(self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.ldInputLbl.sizePolicy().hasHeightForWidth())
        self.ldInputLbl.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setItalic(True)
        self.ldInputLbl.setFont(font)
        self.ldInputLbl.setObjectName("ldInputLbl")
        self.gridLayout.addWidget(self.ldInputLbl, 1, 1, 1, 1)
        self.widthField = QtWidgets.QLineEdit(self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widthField.sizePolicy().hasHeightForWidth())
        self.widthField.setSizePolicy(sizePolicy)
        self.widthField.setMaximumSize(QtCore.QSize(54, 16777215))
        self.widthField.setObjectName("widthField")
        self.gridLayout.addWidget(self.widthField, 2, 1, 1, 1)
        self.label_2 = QtWidgets.QLabel(self.groupBox)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 3, 0, 1, 1)
        self.label_3 = QtWidgets.QLabel(self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_3.sizePolicy().hasHeightForWidth())
        self.label_3.setSizePolicy(sizePolicy)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 0, 0, 1, 1)
        self.heightField = QtWidgets.QLineEdit(self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.heightField.sizePolicy().hasHeightForWidth())
        self.heightField.setSizePolicy(sizePolicy)
        self.heightField.setMaximumSize(QtCore.QSize(54, 16777215))
        self.heightField.setObjectName("heightField")
        self.gridLayout.addWidget(self.heightField, 3, 1, 1, 1)
        self.label_6 = QtWidgets.QLabel(self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_6.sizePolicy().hasHeightForWidth())
        self.label_6.setSizePolicy(sizePolicy)
        self.label_6.setObjectName("label_6")
        self.gridLayout.addWidget(self.label_6, 1, 0, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 1, 2, 1, 1)
        self.label = QtWidgets.QLabel(self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 2, 0, 1, 1)
        self.ldInputButton = QtWidgets.QPushButton(self.groupBox)
        self.ldInputButton.setObjectName("ldInputButton")
        self.gridLayout.addWidget(self.ldInputButton, 1, 3, 1, 1)
        self.verticalLayout.addWidget(self.groupBox)
        self.groupBox_2 = QtWidgets.QGroupBox(CreateGridDlg)
        self.groupBox_2.setObjectName("groupBox_2")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.groupBox_2)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.sdIndsButton = QtWidgets.QPushButton(self.groupBox_2)
        self.sdIndsButton.setEnabled(True)
        self.sdIndsButton.setObjectName("sdIndsButton")
        self.gridLayout_2.addWidget(self.sdIndsButton, 6, 2, 1, 1)
        self.lgIndsLbl = ElideLabel(self.groupBox_2)
        self.lgIndsLbl.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lgIndsLbl.sizePolicy().hasHeightForWidth())
        self.lgIndsLbl.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setItalic(True)
        self.lgIndsLbl.setFont(font)
        self.lgIndsLbl.setObjectName("lgIndsLbl")
        self.gridLayout_2.addWidget(self.lgIndsLbl, 4, 1, 1, 1)
        self.udIndsLbl = ElideLabel(self.groupBox_2)
        self.udIndsLbl.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.udIndsLbl.sizePolicy().hasHeightForWidth())
        self.udIndsLbl.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setItalic(True)
        self.udIndsLbl.setFont(font)
        self.udIndsLbl.setObjectName("udIndsLbl")
        self.gridLayout_2.addWidget(self.udIndsLbl, 8, 1, 1, 1)
        self.label_9 = QtWidgets.QLabel(self.groupBox_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_9.sizePolicy().hasHeightForWidth())
        self.label_9.setSizePolicy(sizePolicy)
        self.label_9.setObjectName("label_9")
        self.gridLayout_2.addWidget(self.label_9, 0, 0, 1, 1)
        self.outputDirLbl = ElideLabel(self.groupBox_2)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.outputDirLbl.sizePolicy().hasHeightForWidth())
        self.outputDirLbl.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setItalic(True)
        self.outputDirLbl.setFont(font)
        self.outputDirLbl.setObjectName("outputDirLbl")
        self.gridLayout_2.addWidget(self.outputDirLbl, 0, 1, 1, 1)
        self.label_7 = QtWidgets.QLabel(self.groupBox_2)
        self.label_7.setIndent(10)
        self.label_7.setObjectName("label_7")
        self.gridLayout_2.addWidget(self.label_7, 6, 0, 1, 1)
        self.outDirButton = QtWidgets.QPushButton(self.groupBox_2)
        self.outDirButton.setObjectName("outDirButton")
        self.gridLayout_2.addWidget(self.outDirButton, 0, 2, 1, 1)
        self.label_5 = QtWidgets.QLabel(self.groupBox_2)
        self.label_5.setIndent(10)
        self.label_5.setObjectName("label_5")
        self.gridLayout_2.addWidget(self.label_5, 4, 0, 1, 1)
        self.label_8 = QtWidgets.QLabel(self.groupBox_2)
        self.label_8.setIndent(10)
        self.label_8.setObjectName("label_8")
        self.gridLayout_2.addWidget(self.label_8, 8, 0, 1, 1)
        self.udIndsButton = QtWidgets.QPushButton(self.groupBox_2)
        self.udIndsButton.setEnabled(True)
        self.udIndsButton.setObjectName("udIndsButton")
        self.gridLayout_2.addWidget(self.udIndsButton, 8, 2, 1, 1)
        self.lgIndsButton = QtWidgets.QPushButton(self.groupBox_2)
        self.lgIndsButton.setEnabled(True)
        self.lgIndsButton.setObjectName("lgIndsButton")
        self.gridLayout_2.addWidget(self.lgIndsButton, 4, 2, 1, 1)
        self.ldIndsButton = QtWidgets.QPushButton(self.groupBox_2)
        self.ldIndsButton.setEnabled(True)
        self.ldIndsButton.setObjectName("ldIndsButton")
        self.gridLayout_2.addWidget(self.ldIndsButton, 2, 2, 1, 1)
        self.label_4 = QtWidgets.QLabel(self.groupBox_2)
        self.label_4.setIndent(10)
        self.label_4.setObjectName("label_4")
        self.gridLayout_2.addWidget(self.label_4, 2, 0, 1, 1)
        self.sdIndsLbl = ElideLabel(self.groupBox_2)
        self.sdIndsLbl.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.sdIndsLbl.sizePolicy().hasHeightForWidth())
        self.sdIndsLbl.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setItalic(True)
        self.sdIndsLbl.setFont(font)
        self.sdIndsLbl.setObjectName("sdIndsLbl")
        self.gridLayout_2.addWidget(self.sdIndsLbl, 6, 1, 1, 1)
        self.ldIndsLbl = ElideLabel(self.groupBox_2)
        self.ldIndsLbl.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.ldIndsLbl.sizePolicy().hasHeightForWidth())
        self.ldIndsLbl.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setItalic(True)
        self.ldIndsLbl.setFont(font)
        self.ldIndsLbl.setObjectName("ldIndsLbl")
        self.gridLayout_2.addWidget(self.ldIndsLbl, 2, 1, 1, 1)
        self.verticalLayout.addWidget(self.groupBox_2)
        self.buttonBox = QtWidgets.QDialogButtonBox(CreateGridDlg)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(CreateGridDlg)
        self.buttonBox.accepted.connect(CreateGridDlg.accept)
        self.buttonBox.rejected.connect(CreateGridDlg.reject)
        QtCore.QMetaObject.connectSlotsByName(CreateGridDlg)

    def retranslateUi(self, CreateGridDlg):
        _translate = QtCore.QCoreApplication.translate
        CreateGridDlg.setWindowTitle(_translate("CreateGridDlg", "Create PE Grid"))
        self.groupBox.setTitle(_translate("CreateGridDlg", "Inputs"))
        self.sdInputButton.setText(_translate("CreateGridDlg", "Select..."))
        self.sdInputLbl.setText(_translate("CreateGridDlg", "None"))
        self.ldInputLbl.setText(_translate("CreateGridDlg", "None"))
        self.widthField.setText(_translate("CreateGridDlg", "1000"))
        self.label_2.setText(_translate("CreateGridDlg", "Grid Height:"))
        self.label_3.setText(_translate("CreateGridDlg", "SD Input File:"))
        self.heightField.setText(_translate("CreateGridDlg", "1000"))
        self.label_6.setText(_translate("CreateGridDlg", "LD Input File:"))
        self.label.setText(_translate("CreateGridDlg", "Grid Width:"))
        self.ldInputButton.setText(_translate("CreateGridDlg", "Select..."))
        self.groupBox_2.setTitle(_translate("CreateGridDlg", "Outputs"))
        self.sdIndsButton.setText(_translate("CreateGridDlg", "Select..."))
        self.lgIndsLbl.setText(_translate("CreateGridDlg", "lg_inds.tif"))
        self.udIndsLbl.setText(_translate("CreateGridDlg", "ud_inds.tif"))
        self.label_9.setText(_translate("CreateGridDlg", "Output Directory:"))
        self.outputDirLbl.setText(_translate("CreateGridDlg", "None"))
        self.label_7.setText(_translate("CreateGridDlg", "SD Index Raster:"))
        self.outDirButton.setText(_translate("CreateGridDlg", "Select..."))
        self.label_5.setText(_translate("CreateGridDlg", "LG Index Raster:"))
        self.label_8.setText(_translate("CreateGridDlg", "UD Index Raster:"))
        self.udIndsButton.setText(_translate("CreateGridDlg", "Select..."))
        self.lgIndsButton.setText(_translate("CreateGridDlg", "Select..."))
        self.ldIndsButton.setText(_translate("CreateGridDlg", "Select..."))
        self.label_4.setText(_translate("CreateGridDlg", "LD Index Raster:"))
        self.sdIndsLbl.setText(_translate("CreateGridDlg", "sd_inds.tif"))
        self.ldIndsLbl.setText(_translate("CreateGridDlg", "ld_inds.tif"))
from ..ElideLabelWidget import ElideLabel
