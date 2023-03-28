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

"""Simple About dialog.

External Dependencies:
    * `PyQt5 <https://www.riverbankcomputing.com/software/pyqt/download5>`_
"""

from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QPixmap
from ._autoforms.ui_aboutdlg import Ui_Dialog
from .._version import __version__ as urc_version, __release_date__ as release_date
from webbrowser import open
import sys
import os

class AboutDlg(QtWidgets.QDialog):
    """ A simple dialog for showing "About" information.

    Args:
        parent (PyQt5.QtWidgets.QWidget,optional): Parent container / window / widget.
    """

    LIC_PATH = 'file://'+os.path.abspath('./licenses' if getattr(sys,'frozen',False) else './lib_licenses')

    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)

        self._ui = Ui_Dialog()
        self._ui.setupUi(self)

        self._ui.ogaLogo.setPixmap(QPixmap('resources/urc_logo.png'))
        self._ui.netllogo.setPixmap(QPixmap('resources/DOE_NETL_logo.png'))
        self._ui.versionLbl.setText("Version "+urc_version)
        self._ui.releaseLbl.setText("Released {:%B %d, %Y}".format(release_date))
        self._ui.licensesLnk.linkActivated.connect(self._licensesClicked)

    @pyqtSlot(str)
    def _licensesClicked(self,href):
        open(AboutDlg.LIC_PATH)
