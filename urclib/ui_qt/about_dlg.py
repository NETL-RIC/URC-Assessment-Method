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

        # self._ui.ogaLogo.setPixmap(QPixmap('resources/icons/urc_icon.png'))
        self._ui.netllogo.setPixmap(QPixmap('resources/DOE_NETL_logo.png'))
        self._ui.versionLbl.setText("Version "+urc_version)
        self._ui.releaseLbl.setText("Released {:%B %d, %Y}".format(release_date))
        self._ui.licensesLnk.linkActivated.connect(self._licensesClicked)

    @pyqtSlot(str)
    def _licensesClicked(self,href):
        open(AboutDlg.LIC_PATH)
