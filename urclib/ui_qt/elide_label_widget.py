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

"""Module Widget which elides as needed."""

from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontMetrics


# https://wiki.qt.io/Elided_Label

class ElideLabel(QLabel):
    """Custom dlg_label subclass which supports simple eliding.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._elideMode = Qt.ElideNone
        self._cachedElideText = ''
        self._cachedText = ''

    def set_elide_mode(self, elide_mode):
        """Set the elide mode to use.

        Args:
            elide_mode (int): The Qt elide flag to apply.

        """
        self._elideMode = elide_mode
        self._cachedText = ''
        self.update()

    def resizeEvent(self, e):
        """This is an overload of a Qt method; see the official documentation.

        Args:
            e (PyQt5.QtCore.QResizeEvent): The triggering event.

        See Also:
            [Official Qt Documentation](https://doc.qt.io/qt-5/qwidget.html#resizeEvent).

        """
        super().resizeEvent(e)
        self._cachedText = ''

    def paintEvent(self, e):
        """This is an overload of a Qt method; see the official documentation.

        Args:
            e (PyQt5.QtCore.QPaintEvent): The triggering event.

        See Also:
            [Official Qt Documentation](https://doc.qt.io/qt-5/qwidget.html#paintEvent).
        """

        if self._elideMode == Qt.ElideNone:
            return super().paintEvent(e)

        self.update_cached_texts()
        super().setText(self._cachedElideText)
        super().paintEvent(e)
        super().setText(self._cachedText)

    def update_cached_texts(self):
        """Update caches to configure what's presently displayed.
        """

        txt = self.text()
        if self._cachedText == txt:
            return

        self._cachedText = txt
        fm = self.fontMetrics()
        self._cachedElideText = fm.elidedText(txt, self._elideMode, self.width(), Qt.TextShowMnemonic)

        if len(self._cachedElideText) > 0:
            ind = 0 if self._elideMode != Qt.ElideLeft else -1
            show_first_char = self._cachedText[ind] + '...'
            self.setMinimumWidth(fm.horizontalAdvance(show_first_char) + 1)
