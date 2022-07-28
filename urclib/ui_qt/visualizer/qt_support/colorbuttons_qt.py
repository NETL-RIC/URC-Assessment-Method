"""Contains Buttons for modifying color values.

External Dependencies:
    * `PyQt5 <https://www.riverbankcomputing.com/software/pyqt/download5>`_
"""
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QColor, QLinearGradient, QPalette,QPainter
from PyQt5.QtWidgets import QPushButton, QStylePainter, QStyleOptionButton, QStyle, QColorDialog,QWidget,QDialog


class ColorButton(QPushButton):
    """Button which acts as a colorwell with default color picking action attached to click.

    Attributes:
        baseColorChanged (PyQt5.QtCore.pyqtSignal): Signal indicating that the selected base color has changed.

    Args:
        *args: Forwarded to QPushButton.
        **kwargs: Forwarded to QPushButton.
    """
    # custom signals
    baseColorChanged = pyqtSignal(QColor)

    def __init__(self, *args, **kwargs):
        QPushButton.__init__(self, *args, **kwargs)
        self._baseColor = QColor.fromRgbF(1, 0, 0, 1)

        self.clicked.connect(self._clicked)

    @property
    def basecolor(self):
        """drawUtils.SimpaColor: The selected base color of the button."""
        ret = (self._baseColor.redF(), self._baseColor.greenF(), self._baseColor.blueF(),
                         self._baseColor.alphaF())
        return ret

    @basecolor.setter
    def basecolor(self, c):
        in_c = c
        if not isinstance(c,QColor):
            in_c = QColor.fromRgbF(*c)

        if in_c != self._baseColor:
            self._baseColor = in_c
            self.baseColorChanged.emit(self._baseColor)
            self.update()

    def paintEvent(self, pevent):
        """ Qt event handler for paint events.

        Args:
            pevent (PyQt5.QtGui.QPaintEvent): The triggering event object.

        Returns:

        """
        colorbox = pevent.rect()

        const_margin = 4
        colorbox.adjust(const_margin, const_margin, -const_margin - 1, -const_margin - 1)

        painter = QStylePainter()

        option = QStyleOptionButton()
        self.initStyleOption(option)
        option.text = ''

        painter.begin(self)
        painter.drawControl(QStyle.CE_PushButton, option)

        if self.isEnabled():
            painter.setPen(Qt.black)
            self._setfill(painter)

        else:
            painter.setPen(Qt.darkGray)
            painter.setBrush(Qt.transparent)

        painter.drawRect(colorbox)
        painter.end()

    def _setfill(self, painter):
        """Set the fill style for the paint object.

        Args:
            painter (PyQt5.QtWidgets.QStylePainter): The painter object drawing the button.

        """
        painter.setBrush(self._baseColor)

    def _clicked(self):
        """Default click action behavior.

        Results in launching color picker and assigning the selected color to the 'basecolor' property.
        """
        retColor = self._run_colorpicker(self._baseColor, 'Select color')
        if retColor.isValid():
            self.basecolor = retColor


    def _run_colorpicker(self, incolor, title):
        """Launch the color picker dialog.

        Args:
            incolor (PyQt5.QtGui.QColor): The initializing color for the dialog.
            title (str): The title to apply to the dialog.

        Returns:
            PyQt5.QtGui.QColor: The color selected by the user.
        """
        # call property to trigger drawing update
        return QColorDialog.getColor(incolor, self, title)


###########################################
class GradientButton(ColorButton):
    """Variant of the ColorButton which allows for defining a two-color gradient.

    Attributes:
        highColorChanged (PyQt5.QtCore.pyqtSignal): Signal indicating that the selected high boundary color has changed.

    Args:
        *args: Forwarded to ColorButton.
        **kwargs: Forwarded to ColorButton.

    """

    # custom signals
    gradientChanged = pyqtSignal(QLinearGradient)
    gradientWithAlphaChanged = pyqtSignal(QLinearGradient)

    def __init__(self, *args, **kwargs):
        ColorButton.__init__(self, *args, **kwargs)

        self._highColor = QColor(1, 1, 1, 1)
        self._gradient = QLinearGradient(0, 0, 1, 0)
        self._direction = 'horizontal'

        self._gradient.setCoordinateMode(QLinearGradient.ObjectBoundingMode)
        self.setBackgroundRole(QPalette.Base)
        self.setAutoFillBackground(True)
        self.minValue=0.
        self.maxValue=1.
        self.alphaVal=1.
        self.showAlpha=False

    def setDirection(self, direction):
        """Set the direction of the gradient.

        The default orientation for a new gradient button is equivalent to the
        __horizontal__ argument for _dir_, as described below.

        Args:
            direction (str): Indicates the direction of the gradient. Currently supports two values:
              * __vertical__: Gradient runs from top to bottom, high to low.
              * __horizontal__: Gradient runs from right to left, low to high.

        """
        if self._direction != direction:
            oldStops = self._gradient.stops()
            if direction == 'vertical':
                self._gradient=QLinearGradient(0., 1., 0., 0.)
            elif direction == 'horizontal':
                self._gradient=QLinearGradient(0., 0., 1., 0.)
            else:
                return
            self._gradient.setCoordinateMode(QLinearGradient.ObjectBoundingMode)
            self._gradient.setStops(oldStops)
            self._direction=direction

    def override_clickaction(self, newaction=None):
        """Replace the default click action with one provided from elsewhere

        Args:
            newaction (function, optional): The action to fire when the button is clicked; resets
              to the default action if the value is _None_. Defaults to _None_.

        Returns:

        """
        self.clicked.disconnect()
        if newaction is not None:
            self.clicked.connect(newaction)
        else:
            self.clicked.connect(self._clicked)

    @property
    def stops(self):

        return self._gradient.stops()

    @stops.setter
    def stops(self,stps):

        self._gradient.setStops(stps)

        self.update()
        self.gradientChanged.emit(self._gradient)

    def _setfill(self, painter):
        """Set the fill style for the paint object. Overloaded ColorButton method.

                Args:
                    painter (PyQt5.QtWidgets.QStylePainter): The painter object drawing the button.

                """

        painter.setBrush(self._gradient)

    def _clicked(self):

        # place import here to avoid import loop
        from .GradientDlg import GradientDialog

        dlg = GradientDialog(self.minValue,self.maxValue,self._gradient.stops(),self.showAlpha,self.alphaVal,parent=self)
        if dlg.exec_()==QDialog.Accepted:
            self._gradient.setStops(dlg.gradient().stops())
            if self.showAlpha:
                self.alphaVal=dlg.alphaValue
                self.gradientWithAlphaChanged.emit(dlg.gradientWithAlpha())
            self.gradientChanged.emit(self._gradient)
            self.update()


class GradientSwatch(QWidget):

    def __init__(self,parent=None):

        super().__init__(parent)

        self._gradient = None

    def paintEvent(self, pevent):
        """ Qt event handler for paint events.

        Args:
            pevent (PyQt5.QtGui.QPaintEvent): The triggering event object.

        Returns:

        """
        colorbox = pevent.rect()
        # const_margin = 0
        # colorbox.adjust(const_margin, const_margin, -const_margin - 1, -const_margin - 1)

        painter = QPainter()
        painter.begin(self)

        if self.isEnabled():
            painter.setPen(Qt.black)
            painter.setBrush(self._gradient if self._gradient is not None else Qt.transparent)

        else:
            painter.setPen(Qt.darkGray)
            painter.setBrush(Qt.transparent)

        #painter.fillRect(colorbox,self._gradient)
        painter.drawRect(colorbox)
        painter.end()


    @property
    def gradient(self):
        return self._gradient


    @gradient.setter
    def gradient(self,g):
        self._gradient=g
        self.update()

    @pyqtSlot(QLinearGradient)
    def setGradient(self,g):
        self.gradient = g