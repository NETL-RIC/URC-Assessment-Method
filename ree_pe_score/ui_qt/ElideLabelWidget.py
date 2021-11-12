
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontMetrics


# https://wiki.qt.io/Elided_Label

class ElideLabel(QLabel):

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)

        self._elideMode = Qt.ElideNone
        self._cachedElideText = ''
        self._cachedText = ''

    def setElideMode(self,elideMode):

        self._elideMode = elideMode
        self._cachedText=''
        self.update()

    def resizeEvent(self, e):

        super().resizeEvent(e)
        self._cachedText=''

    def paintEvent(self, e):

        if self._elideMode == Qt.ElideNone:
            return super().paintEvent(e)

        self.updateCachedTexts()
        super().setText(self._cachedElideText)
        super().paintEvent(e)
        super().setText(self._cachedText)

    def updateCachedTexts(self):

        txt = self.text()
        if self._cachedText==txt:
            return

        self._cachedText = txt
        fm = self.fontMetrics()
        self._cachedElideText = fm.elidedText(txt,self._elideMode,self.width(),Qt.TextShowMnemonic)

        if len(self._cachedElideText) > 0:
            ind = 0 if self._elideMode!= Qt.ElideLeft else -1
            showFirstChar = self._cachedText[ind] + '...'
            self.setMinimumWidth(fm.horizontalAdvance(showFirstChar)+1)