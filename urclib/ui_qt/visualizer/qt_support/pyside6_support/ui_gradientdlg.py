# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'gradientDlg.ui'
##
## Created by: Qt User Interface Compiler version 6.4.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractButton, QAbstractItemView, QApplication, QDialog,
    QDialogButtonBox, QFrame, QHBoxLayout, QHeaderView,
    QLabel, QPushButton, QSizePolicy, QSlider,
    QSpacerItem, QTableView, QVBoxLayout, QWidget)

from ..colorbuttons_qt import GradientSwatch

class Ui_GradientDialog(object):
    def setupUi(self, GradientDialog):
        if not GradientDialog.objectName():
            GradientDialog.setObjectName(u"GradientDialog")
        GradientDialog.resize(500, 409)
        self.verticalLayout = QVBoxLayout(GradientDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label = QLabel(GradientDialog)
        self.label.setObjectName(u"label")

        self.verticalLayout.addWidget(self.label)

        self.gradientPreview = GradientSwatch(GradientDialog)
        self.gradientPreview.setObjectName(u"gradientPreview")
        self.gradientPreview.setMinimumSize(QSize(0, 20))

        self.verticalLayout.addWidget(self.gradientPreview)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.startValLbl = QLabel(GradientDialog)
        self.startValLbl.setObjectName(u"startValLbl")

        self.horizontalLayout.addWidget(self.startValLbl)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.endValLbl = QLabel(GradientDialog)
        self.endValLbl.setObjectName(u"endValLbl")

        self.horizontalLayout.addWidget(self.endValLbl)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_2)

        self.countLbl = QLabel(GradientDialog)
        self.countLbl.setObjectName(u"countLbl")

        self.horizontalLayout_2.addWidget(self.countLbl)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_2.addItem(self.horizontalSpacer_3)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.anchorTable = QTableView(GradientDialog)
        self.anchorTable.setObjectName(u"anchorTable")
        self.anchorTable.setMouseTracking(True)
        self.anchorTable.setEditTriggers(QAbstractItemView.AllEditTriggers)
        self.anchorTable.setSelectionMode(QAbstractItemView.SingleSelection)
        self.anchorTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.anchorTable.horizontalHeader().setDefaultSectionSize(50)
        self.anchorTable.horizontalHeader().setStretchLastSection(True)
        self.anchorTable.verticalHeader().setDefaultSectionSize(30)

        self.verticalLayout.addWidget(self.anchorTable)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_4)

        self.redistributeButton = QPushButton(GradientDialog)
        self.redistributeButton.setObjectName(u"redistributeButton")
        sizePolicy = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.redistributeButton.sizePolicy().hasHeightForWidth())
        self.redistributeButton.setSizePolicy(sizePolicy)

        self.horizontalLayout_3.addWidget(self.redistributeButton)

        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer_5)


        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.opactiyFrame = QFrame(GradientDialog)
        self.opactiyFrame.setObjectName(u"opactiyFrame")
        self.opactiyFrame.setFrameShape(QFrame.StyledPanel)
        self.opactiyFrame.setFrameShadow(QFrame.Raised)
        self.horizontalLayout_4 = QHBoxLayout(self.opactiyFrame)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.label_2 = QLabel(self.opactiyFrame)
        self.label_2.setObjectName(u"label_2")

        self.horizontalLayout_4.addWidget(self.label_2)

        self.label_3 = QLabel(self.opactiyFrame)
        self.label_3.setObjectName(u"label_3")

        self.horizontalLayout_4.addWidget(self.label_3)

        self.opacitySlider = QSlider(self.opactiyFrame)
        self.opacitySlider.setObjectName(u"opacitySlider")
        self.opacitySlider.setMaximum(100)
        self.opacitySlider.setOrientation(Qt.Horizontal)

        self.horizontalLayout_4.addWidget(self.opacitySlider)

        self.label_4 = QLabel(self.opactiyFrame)
        self.label_4.setObjectName(u"label_4")

        self.horizontalLayout_4.addWidget(self.label_4)


        self.verticalLayout.addWidget(self.opactiyFrame)

        self.buttonBox = QDialogButtonBox(GradientDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)

        self.verticalLayout.addWidget(self.buttonBox)

        QWidget.setTabOrder(self.anchorTable, self.redistributeButton)

        self.retranslateUi(GradientDialog)
        self.buttonBox.accepted.connect(GradientDialog.accept)
        self.buttonBox.rejected.connect(GradientDialog.reject)

        QMetaObject.connectSlotsByName(GradientDialog)
    # setupUi

    def retranslateUi(self, GradientDialog):
        GradientDialog.setWindowTitle(QCoreApplication.translate("GradientDialog", u"Customize Gradient", None))
        self.label.setText(QCoreApplication.translate("GradientDialog", u"Preview:", None))
        self.startValLbl.setText(QCoreApplication.translate("GradientDialog", u"0.0", None))
        self.endValLbl.setText(QCoreApplication.translate("GradientDialog", u"1.0", None))
        self.countLbl.setText(QCoreApplication.translate("GradientDialog", u"Number of Anchors:", None))
        self.redistributeButton.setText(QCoreApplication.translate("GradientDialog", u"Rebalance Weights", None))
        self.label_2.setText(QCoreApplication.translate("GradientDialog", u"Opacity:", None))
        self.label_3.setText(QCoreApplication.translate("GradientDialog", u"0.0", None))
        self.label_4.setText(QCoreApplication.translate("GradientDialog", u"1.0", None))
    # retranslateUi

