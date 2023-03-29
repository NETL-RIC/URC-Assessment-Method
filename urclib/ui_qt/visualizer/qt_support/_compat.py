# This file is part of URC Assessment Method.
#
# URC Assessment Method is free software: you can redistribute it and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# URC Assessment Method is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with URC Assessment Method. If not, see
# <https://www.gnu.org/licenses/>.


import os

QT_MODE=os.environ.get('GAIA_VIS_QT_MODE',None)

if QT_MODE is None:
    # attempt to auto import
    try:
        import PyQt5
        QT_MODE='pyqt5'
    except ImportError:
        try:
            import PySide6
            QT_MODE='pyside6'
        except ImportError:
            raise ImportError("GAIAVisualizer: No compatible Qt found")



if QT_MODE.lower() == 'pyqt5':
    from PyQt5.QtCore import (
        Qt,
        pyqtSignal as Signal,
        pyqtSlot as Slot,
        QTimer,
        QAbstractTableModel,
        QModelIndex,
        QVariant,
        QSize,

    )
    from PyQt5.QtWidgets import (
        QOpenGLWidget,
        QPushButton,
        QStylePainter,
        QStyleOptionButton,
        QStyle,
        QColorDialog,
        QWidget,
        QDialog,
        QStyledItemDelegate,
        QSpinBox,
        QComboBox,
        qApp,
    )
    from PyQt5.QtGui import (
        QColor,
        QLinearGradient,
        QPalette,
        QPainter,
    )
    from PyQt5.Qt import QCursor, QSurfaceFormat

    from .pyqt5_support.ui_gradientdlg import Ui_GradientDialog

    def appfont():
        return qApp.font()
    QT_MODE = "pyqt5"

elif QT_MODE.lower() == 'pyside6':
    from PySide6.QtCore import (
        Qt,
        Signal,
        Slot,
        QTimer,
        QAbstractTableModel,
        QModelIndex,
        QSize
    )
    from PySide6.QtWidgets import (
        QPushButton,
        QStylePainter,
        QStyleOptionButton,
        QStyle,
        QColorDialog,
        QWidget,
        QDialog,
        QStyledItemDelegate,
        QSpinBox,
        QComboBox,
        QApplication,
    )
    from PySide6.QtGui import (
        QCursor,
        QSurfaceFormat,
        QColor,
        QLinearGradient,
        QPalette,
        QPainter
    )
    from PySide6.QtOpenGLWidgets import QOpenGLWidget

    from .pyside6_support.ui_gradientdlg import Ui_GradientDialog

    def QVariant(v=None):
        return v

    def appfont():
        return QApplication.font()
