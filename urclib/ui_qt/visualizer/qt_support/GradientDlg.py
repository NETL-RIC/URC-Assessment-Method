"""Classes and utilities relevant to displaying and manipulating a dialog for editing a gradient color ramp."""

try:
    from .pyqt5_support.ui_gradientdlg import Ui_GradientDialog
    from PyQt5.QtCore import pyqtSlot as Slot, pyqtSignal as Signal, QAbstractTableModel, QModelIndex, Qt, QVariant, QSize
    from PyQt5.QtWidgets import QDialog, QStyledItemDelegate, QSpinBox, QComboBox, qApp
    from PyQt5.QtGui import QColor, QLinearGradient

    def appfont(widget):
        return qApp.font()
except ImportError:

    from .pyside6_support.ui_gradientdlg import Ui_GradientDialog
    from PySide6.QtCore import Slot, Signal, QAbstractTableModel, QModelIndex, Qt,QSize
    from PySide6.QtWidgets import QDialog,QStyledItemDelegate,QSpinBox,QComboBox,QApplication
    from PySide6.QtGui import QColor,QLinearGradient

    def QVariant(v=None):
        return v

    def appfont(widget):
        return QApplication.font()

from enum import IntEnum

from .colorbuttons_qt import ColorButton


## NOTE: keep viewmodel and delegate here, so as to be self-contained

class AnchorTableDelegate(QStyledItemDelegate):
    """Delegate for handling custom cell displays in anchor table.

    Args:
        maxAnchors (int): The maximum number of anchors to allow (minimum is always 2).
        parent (PyQt5.QtWidgets.QWidget or None, optional): The parent widget, if any.
    """

    def __init__(self,maxAnchors,parent=None):
        super().__init__(parent)

        dummyActionCombo = QComboBox()
        dummyActionCombo.addItem('Select...')
        self._dummyWidgets = (None,
                              QSpinBox(),
                              None,
                              ColorButton(),
                              dummyActionCombo,
                              )
        self._maxAnchors=maxAnchors


    def createEditor(self, parent, option, index):
        self._currIndex=index
        w = self._dummyWidgets[index.column()]
        fld = None
        if isinstance(w,QSpinBox):
            fld = QSpinBox(parent)
            minVal,maxVal=index.model().getValueRange(index.row())
            fld.setRange(int(minVal*100)+1,int(maxVal*100)-1)
            fld.setSingleStep(1)
            fld.valueChanged.connect(self._valChanged)

        elif isinstance(w,ColorButton):
            fld=ColorButton(parent)
            fld.baseColorChanged.connect(self._valChanged)
            fld.setFocusPolicy(Qt.StrongFocus)
            fld.setFocus()
        elif isinstance(w,QComboBox):
            r = index.row()
            rCount = index.model().rowCount()
            allOpts=['Remove',
             'Add Above',
             'Add Below',
             'Swap Above',
             'Swap Below',
             ]

            # truth table
            truths = [0<r<(rCount-1),
                      r>0 and rCount<self._maxAnchors,
                      r<(rCount-1) and rCount<self._maxAnchors,
                      r>0,
                      r < (rCount - 1)
                      ]

            fld = QComboBox(parent)
            fld.addItems(['Select...']+[n for n,t in zip(allOpts,truths) if t])
            fld.currentTextChanged.connect(self._comboChanged)
            fld.setFocusPolicy(Qt.StrongFocus)

        return fld

    def destroyEditor(self, editor, index):
        """This is an overloaded method of PyQt5.QtWidgets.QStyledItemDelegate. See official Qt Documentation.

        Args:
            editor (PyQt5.QtWidgets.QWidget): The widget created by invoking createEditor().
            index (PyQt5.QtCore.QModelIndex): Index of the table cell which requested the deletion of the editor.

        See Also:
            [Official Qt Documentation](https://doc.qt.io/qt-5/qabstractitemdelegate.html#destroyEditor)

        """

        if isinstance(editor,QSpinBox):
            editor.valueChanged.disconnect()
        elif isinstance(editor, ColorButton):
            editor.baseColorChanged.disconnect()
        elif isinstance(editor,QComboBox):
            editor.currentTextChanged.disconnect()
        super().destroyEditor(editor,index)


    def setEditorData(self, editor, index):
        """This is an overloaded method of PyQt5.QtWidgets.QStyledItemDelegate. See official Qt Documentation.

        Args:
            editor (PyQt5.QtWidgets.QWidget): The widget created by invoking createEditor().
            index (PyQt5.QtCore.QModelIndex): Index of the table cell which requested the deletion of the editor.

        See Also:
            [Official Qt Documentation](https://doc.qt.io/qt-5/qstyleditemdelegate.html#setEditorData)
        """

        val=index.data()
        if val is not None:
            if isinstance(editor,QSpinBox):
                editor.setValue(val)

            elif isinstance(editor,ColorButton):
                editor.basecolor = QColor(val)

            elif isinstance(editor,QComboBox):
                editor.setCurrentIndex(0)
                editor.showPopup()

    def setModelData(self, editor, model, index):
        """This is an overloaded method of PyQt5.QtWidgets.QStyledItemDelegate. See official Qt Documentation.

        Args:
            editor (PyQt5.QtWidgets.QWidget): The widget created by invoking createEditor().
            model (PyQt5.QtCore.QAbstractItemModel): The model to assign the committed data to.
            index (PyQt5.QtCore.QModelIndex): Index of the table cell which requested the deletion of the editor.

        See Also:
            [Official Qt Documentation](https://doc.qt.io/qt-5/qstyleditemdelegate.html#setModelData)

        """

        value=None
        if isinstance(editor, QSpinBox):
            value=float(editor.value())/100.
        elif isinstance(editor, ColorButton):
            value = QColor()
            value.setRgbF(*editor.basecolor)
        elif isinstance(editor,QComboBox):
            self._handleAction(editor.currentText())
            # do nothing
            return

        model.setData(index,value)

    def paint(self, painter, option, index):
        """This is an overloaded method of PyQt5.QtWidgets.QStyledItemDelegate. See official Qt Documentation.

        Args:
            painter (PyQt5.QtGui.QPainter): Painting object.
            option (PyQt5.QtWidgets.QStyleOptionViewItem): Style options for the painting process.
            index (PyQt5.QtCore.QModelIndex): Index of the table cell which requested the deletion of the editor.

        See Also:
            [Official Qt Documentation](https://doc.qt.io/qt-5/qabstractitemdelegate.html#paint)
        """
        # https://www.qtcentre.org/threads/70447-QTableView-and-QStyledItemDelegate-Persistent-Editor-Issue

        w = self._dummyWidgets[index.column()]
        if w is not None:
            painter.save()
            if isinstance(w, QSpinBox):
                if index.row()==0 or index.row()==index.model().rowCount()-1:
                    painter.restore()
                    super().paint(painter,option,index)
                    return
                w.setValue(int(index.data()))
            elif isinstance(w,ColorButton):
                w.basecolor = QColor(index.data())

            enabled = self.parent().isEnabled() and (index.model().flags(index) & Qt.ItemIsEnabled) != Qt.ItemFlag.NoItemFlags
            w.setEnabled(enabled)
            w.resize(option.rect.width(),option.rect.height())
            map = w.grab()
            painter.drawPixmap(option.rect.x(),option.rect.y(),map)
            painter.restore()
        else:
            super().paint(painter,option,index)


    def _handleAction(self,action):
        """Handle an action selected for a row in the table.

        Args:
            action (str): The text of the selected action
        """

        mdl = self._currIndex.model()
        r = self._currIndex.row()
        if action=='Remove':
            mdl.removeRow(r)
        elif action=='Add Above':
            mdl.insertRow(r)
        elif action=='Add Below':
            mdl.insertRow(r+1)
        elif action=='Swap Above':
            mdl.swapColors(r-1,r)
        elif action=='Swap Below':
            mdl.swapColors(r, r+1)

    @Slot(int)
    @Slot(QColor)
    def _valChanged(self,val):
        """Emits a signal when a value has changed.
        """

        self.commitData.emit(self.sender())

    @Slot(str)
    def _comboChanged(self,val):
        """Clears the focus of the widget which invoked this slot.
        """

        self.sender().clearFocus()



##############################################################
class AnchorTableModel(QAbstractTableModel):
    """Model for use with the anchor editor table.

    Attributes:
        alphaValue (float): The alpha (opacity) to apply to a gradient.

    Args:
        minVal (float): The lower bound of the values to be represented by the gradient.
        maxVal (float): The upper bound of the values to be represented by the gradient.
        anchors (list): Lists of the form (weight, color) to represent anchor points for the gradient.
        parent (PyQt5.QtWidget.QWidget or None, optional): Parent widget, if any.
    """

    gradientChanged = Signal(QLinearGradient)
    COLS = IntEnum('COLS',"Anchor Position Value Color Action",start=0)


    def __init__(self,minVal,maxVal,anchors,parent=None):
        super().__init__(parent)

        self._anchors= anchors
        self._minVal = minVal
        self._valRange = maxVal - minVal
        self._selectedRow=-1
        self.alphaVal = 1.

    def flags(self, index):
        """This is an overload of a PyQt5.QtCore.QAbstractTableModel. See the official documentation for details.

        Args:
            index (PyQt5.QtCore.QModelIndex): The index of the cell being queried.

        Returns:
            int: The relevant bitflags as an integer.

        See Also:
            [Official Qt Documentation](https://doc.qt.io/qt-5/qabstracttablemodel.html#flags)
        """

        flags = super().flags(index)
        col=index.column()
        row = index.row()
        if col==AnchorTableModel.COLS.Color or \
                (col==AnchorTableModel.COLS.Position and
                 0<row<len(self._anchors)-1) or \
                col==AnchorTableModel.COLS.Action:
            flags |= Qt.ItemIsEditable

        return flags

    def headerData(self, section, orientation, role= Qt.DisplayRole):
        """This is an overload of a PyQt5.QtCore.QAbstractTableModel. See the official documentation for details.

        Args:
            section (int): The target section, either row or column depending on the specified orientation.
            orientation (int): Flag indicating direction; either `Qt.Horizontal` or `Qt.Vertical`
            role (int,optional): Constant indicating the role for which information is being requested.

        Returns:
            PyQt5.QtCore.QVariant: The requested variant value.

        See Also:
            [Official Qt Documentation](https://doc.qt.io/qt-5/qabstractitemmodel.html#headerData)
        """

        if role == Qt.DisplayRole:
            if orientation==Qt.Horizontal:
                return QVariant(AnchorTableModel.COLS(section).name)
            else:
                return QVariant('    ' if section != self._selectedRow else '►')

        elif role == Qt.FontRole:
            # hi def screens scale the font; ensure that this
            # holds true for tableview
            fnt = appfont(self)
            return fnt
        return None

    def setData(self, index, value, role=Qt.DisplayRole):
        """This is an overload of a PyQt5.QtCore.QAbstractTableModel. See the official documentation for details.

        Args:
            index (PyQt5.QtCore.QModelIndex): The index of the cell being modified.
            value (PyQt5.QtCore.QVariant): The value being assigned.
            role (int,optional): Constant indicating the role for which information is being requested.

        Returns:
            bool: `True` if the value assignment was successful; `False` otherwise.

        See Also:
            [Official Qt Documentation](https://doc.qt.io/qt-5/qabstractitemmodel.html#setData)
        """

        if role == Qt.DisplayRole:
            # self.beginResetModel()
            c = index.column()
            r = index.row()
            a = self._anchors[r]
            if c==AnchorTableModel.COLS.Position:
                a[0] = float(value)
            elif c==AnchorTableModel.COLS.Color:
                a[1] = QColor(value)

            # self.endResetModel()
            self._emitGradient()
            return True
        return False


    def data(self, index, role=Qt.DisplayRole):
        """This is an overload of a PyQt5.QtCore.QAbstractTableModel. See the official documentation for details.

        Args:
            index (PyQt5.QtCore.QModelIndex): The index of the cell being queried.
            role (int,optional): Constant indicating the role for which information is being requested.

        Returns:
            PyQt5.QtCore.QVariant: The requested value wrapped in a QVariant object.

        See Also:
            [Official Qt Documentation](https://doc.qt.io/qt-5/qabstractitemmodel.html#data)
        """

        if role == Qt.DisplayRole:
            r = index.row()
            c = index.column()

            a = self._anchors[r]
            if c==AnchorTableModel.COLS.Anchor:
                if r == 0:
                    return QVariant('Start')
                elif r == len(self._anchors) - 1:
                    return QVariant('End')
                else:
                    return QVariant(f'A{r}')
            elif c==AnchorTableModel.COLS.Position:
                return QVariant(int(a[0]*100))
            elif c == AnchorTableModel.COLS.Value:
                return QVariant(f'{(a[0]*self._valRange)+self._minVal :.3f}')
            elif c == AnchorTableModel.COLS.Color:
                return QVariant(a[1])

        return QVariant()


    def columnCount(self, parent=QModelIndex()):
        """This is an overload of a PyQt5.QtCore.QAbstractTableModel. See the official documentation for details.

        Args:
            parent (PyQt5.QtCore.QModelIndex): Unused

        Returns:
            int: The total number of columns.

        See Also:
            [Official Qt Documentation](https://doc.qt.io/qt-5/qabstractitemmodel.html#columnCount)
        """

        return len(AnchorTableModel.COLS)

    def rowCount(self, parent=QModelIndex()):
        """This is an overload of a PyQt5.QtCore.QAbstractTableModel. See the official documentation for details.

        Args:
            parent (PyQt5.QtCore.QModelIndex): Unused

        Returns:
            int: The total number of rows present in the table.

        See Also:
            [Official Qt Documentation](https://doc.qt.io/qt-5/qabstractitemmodel.html#rowCount)
        """

        return len(self._anchors)

    def _emitGradient(self):
        """Convenience method for emitting the model's stored gradient as a signal."""
        self.gradientChanged.emit(self.gradient)

    def getValueRange(self,r):
        """Find the range of values covered by a given anchor.

        Args:
            r (int): Index of the anchor to query.

        Returns:
            tuple: The lower and upper bounds of the range coverd by the anchor at index `r`.
        """

        minVal = self._anchors[r-1][0] if r>0 else self._anchors[r][0]
        maxVal = self._anchors[r+1][0] if r<(len(self._anchors) - 1) else self._anchors[r][0]

        return minVal,maxVal

    def markRow(self,row=-1):
        """Designate the row to be marked by a triangle.

        Args:
            row (int): index of the row to select. A value outside of the range of [0,rowCount()) will deselect
                       all rows.
        """
        if row!=self._selectedRow:
            self._selectedRow = row
            self.headerDataChanged.emit(Qt.Horizontal,0,self.rowCount())

    @Slot(int)
    def adjustAnchorCount(self,count):
        """Adjust the total number of anchors to display in the table.

        Args:
            count (int): The new count of anchors to display.
        """

        if count!=len(self._anchors):
            # add entry before end
            self.beginResetModel()
            while count > len(self._anchors):
                a = self._mixAnchors(self._anchors[-2],self._anchors[-1])
                # insert second to last
                self._anchors.insert(-1,a)
            # remove entry before end
            while count < len(self._anchors):
                self._anchors.pop(-2)
            self.endResetModel()
            self._emitGradient()

    def insertRow(self, row,parent=QModelIndex()):
        """This is an overload of a PyQt5.QtCore.QAbstractTableModel. See the official documentation for details.

        Args:
            row (int): The index before which to insert a new row.
            parent (PyQt5.QtCore.QModelIndex): Unused

        See Also:
            [Official Qt Documentation](https://doc.qt.io/qt-5/qabstractitemmodel.html#insertRow)
        """

        self.beginInsertRows(parent,row,row)
        a = self._mixAnchors(self._anchors[row - 1], self._anchors[row])
        self._anchors.insert(row, a)

        self.endInsertRows()
        self._emitGradient()

    def removeRow(self,row,parent=QModelIndex()):
        """This is an overload of a PyQt5.QtCore.QAbstractTableModel. See the official documentation for details.

        Args:
            row (int): The index of the row to remove.
            parent (PyQt5.QtCore.QModelIndex): Unused

        See Also:
            [Official Qt Documentation](https://doc.qt.io/qt-5/qabstractitemmodel.html#removeRow)
        """

        self.beginRemoveRows(parent,row,row)
        self._anchors.pop(row)
        self.endRemoveRows()
        self._emitGradient()

    def swapColors(self,r1,r2):
        """Swap colors between two anchors.

        Args:
            r1 (int): Row of the first anchor in the color swap.
            r2 (int): Row of the second anchor in the color swap.

        """
        a1 = self._anchors[r1]
        a2 = self._anchors[r2]

        self.beginResetModel()
        tmp = a1[1]
        a1[1]=a2[1]
        a2[1]=tmp
        self.endResetModel()
        self._emitGradient()

    def _mixColors(self,c1,c2,wt = 0.5):
        """Linearly mix two colors.

        Args:
            c1 (PyQt5.QtGui.QColor): The first color to include in mix.
            c2 (PyQt5.QtGui.QColor): The second color to include in mix.
            wt (float,optional): A value in the range of [0,1] indicating the relative contribution of each color.
                A value of 0 is just `c1`; a value of 1 is all `c2`. The default is 0.5 (equal contribution).

        Returns:
            PyQt5.QtGui.QColor: The new color that resulted from the mixing operation.
        """

        ret= QColor()
        ret.setRgbF(
            (c1.redF()*(1.-wt))+(c2.redF()*wt),
            (c1.greenF()*(1.-wt))+(c2.greenF()*wt),
            (c1.blueF()*(1.-wt))+(c2.blueF()*wt),
            (c1.alphaF()*(1.-wt))+(c2.alphaF()*wt),
        )
        return ret

    def _mixWeights(self,w1,w2,wt=0.5):
        """Linearly mix two anchor weights.

        Args:
            w1 (float): The first weight to mix.
            w2 (float): The second weight to mix.
            wt (float,optional): A value in the range of [0,1] indicating the relative contribution of each weight.
                A value of 0 is just `w1`; a value of 1 is all `w2`. The default is 0.5 (equal contribution).

        Returns:
            float: The new weight resulting from the mixing operation.

        """
        return (w1*(1.-wt))+(w2*wt)

    def _mixAnchors(self,a1,a2,wt=0.5):
        """Linearly mix two anchor entries.

        Args:
            w1 (tuple): The first weight and color to mix.
            w2 (tuple): The second weight and color to mix.
            wt (float,optional): A value in the range of [0,1] indicating the relative contribution of each anchor.
                A value of 0 is just `a1`; a value of 1 is all `a2`. The default is 0.5 (equal contribution).

        Returns:
            list: The new weight and color resulting from the mixing operation between anchor entries.

        """

        return [self._mixWeights(a1[0],a2[0],wt),self._mixColors(a1[1],a2[1],wt)]

    @Slot()
    def redistributeWeights(self):
        """Evenly redistribute weights across all entries."""
        step=1./(len(self._anchors)-1)
        wt = 0
        self.beginResetModel()
        for i in range(len(self._anchors)):
            self._anchors[i][0]=wt
            wt+=step
        self.endResetModel()
        self._emitGradient()

    @property
    def gradient(self):
        """PyQt5.QtGui.QLinearGradient: The gradient defined by the entries within this model."""
        ret = QLinearGradient(0., 0., 1., 0.)
        ret.setCoordinateMode(QLinearGradient.ObjectBoundingMode)
        ret.setStops(self._anchors)
        return ret

    @property
    def gradientWithAlpha(self):
        """PyQt5.QtGui.QLinearGradient: The gradient defined by the entries within this model, with an alpha
        value included"""
        ret = QLinearGradient(0., 0., 1., 0.)
        ret.setCoordinateMode(QLinearGradient.ObjectBoundingMode)
        for a in self._anchors:
            a[1].setAlphaF(self.alphaVal)
        ret.setStops(self._anchors)
        return ret

    @property
    def anchors(self):
        """list: lists of weights and colors representing the anchors which define the gradient."""
        return self._anchors


##############################################################
class GradientDialog(QDialog):
    """Dialog for editing values that compose a color ramp/gradient.

    Attributes:
        alphaVal (float): Value in range [0,1] which represents the opacity of the gradient.

    Args:
        minVal (float): The lower bound value of the range represented by the color gradient.
        maxVal (float): The upper bound value of the range represented by the color gradient.
        anchors (list): List of lists, each with weight and color. Represents the anchors defining the gradient.
        modifyAlpha (bool,optional): If `True`, enables options to modify the gradient's alpha value. Defaults to
             `False`.
        alphaVal (float,optional): The alpha value to apply. Defaults to 1 (full opacity).
        parent (PyQt5.QtWidgets.QWidget or None, optional): Parent widget, or `None` if the dialog has no designated
             parent.

    """

    MIN_ANCHORS = 2
    MAX_ANCHORS = 20

    def __init__(self,minVal,maxVal,anchors,modifyAlpha=False,alphaVal=1.,parent=None):

        super().__init__(parent)

        self._ui = Ui_GradientDialog()
        self._ui.setupUi(self)

        initGradient = QLinearGradient(0., 0., 1., 0.)
        initGradient.setCoordinateMode(QLinearGradient.ObjectBoundingMode)
        # ensure for preview alpha is 1 when in use.
        for a in anchors:
            a[1].setAlphaF(1.)
        initGradient.setStops(anchors)
        self._anchors = [list(a) for a in anchors]
        self._minVal = minVal
        self._maxVal = maxVal


        self._tblMdl = AnchorTableModel(minVal,maxVal,self._anchors,self._ui.anchorTable)
        self._tblDelg = AnchorTableDelegate(self.MAX_ANCHORS,self._ui.anchorTable)
        self._ui.anchorTable.setModel(self._tblMdl)
        self._ui.anchorTable.setItemDelegate(self._tblDelg)
        self._ui.anchorTable.selectionModel().selectionChanged.connect(self._selectChanged)
        self._ui.gradientPreview.gradient=initGradient
        self._ui.startValLbl.setText(f'{self._minVal:.4f}')
        self._ui.endValLbl.setText(f'{self._maxVal:.4f}')

        # set anchor position column to stretch
        self._ui.anchorTable.setColumnWidth(AnchorTableModel.COLS.Position,100)

        # wire
        self._tblMdl.gradientChanged.connect(self._ui.gradientPreview.setGradient)
        self._tblMdl.rowsInserted.connect(self._anchorsChanged)
        self._tblMdl.rowsRemoved.connect(self._anchorsChanged)
        self._ui.redistributeButton.clicked.connect(self._tblMdl.redistributeWeights)

        self._anchorsChanged(None,None,None)
        self.alphaValue=alphaVal
        if modifyAlpha:
            self._ui.opacitySlider.valueChanged.connect(self._updateAlpha)
            self._ui.opacitySlider.setValue(int(alphaVal*100.))
        else:
            self._ui.opactiyFrame.hide()

    # using the property tag here caused issues with Qt if the
    # dialog was reconstructed (closed and reopened). Keeping
    # as normal function
    def gradient(self):
        """PyQt5.QtWidgets.QLinearGradient: The gradient edited by the dialog. """
        return self._tblMdl.gradient

    def gradientWithAlpha(self):
        """PyQt5.QtWidgets.QLinearGradient: The gradient edited by the dialog, with alpha. """
        return self._tblMdl.gradientWithAlpha

    @Slot('QItemSelection','QItemSelection')
    def _selectChanged(self,selected,deselected):
        """Update table when selected row changes.

        Args:
            selected (PyQt5.QtCore.QItemSelection): The newly selected row(s).
            deselected (PyQt5.QtCore.QItemSelection): unused.
        """

        if len(selected.indexes())==0:
            self._tblMdl.markRow(-1)
        else:
            self._tblMdl.markRow(selected.indexes()[0].row())

    @Slot('QModelIndex',int,int)
    def _anchorsChanged(self, index,first,last):
        """Called when anchors are either added or removed to the table.

        Args:
            index (PyQt5.QtCore.QModelIndex): Unused.
            first (int): Unused.
            last (int): Unused.
        """

        count = self._tblMdl.rowCount()
        maxNote= ' (max reached)'
        self._ui.countLbl.setText(f'Anchor Count: {count}{maxNote if count>=GradientDialog.MAX_ANCHORS else ""}')

    @Slot(int)
    def _updateAlpha(self,val):
        """Refresh the alpha value being used.

        Args:
            val (int): Value in the range of [0,100], representing percent of opacity.
        """

        self._tblMdl.alphaVal=float(val)/100.

    @property
    def alphaValue(self):
        """float: The designated alpha value to apply to all colors in the gradient."""
        return self._tblMdl.alphaVal

    @alphaValue.setter
    def alphaValue(self, value):
        self._tblMdl.alphaVal = value
