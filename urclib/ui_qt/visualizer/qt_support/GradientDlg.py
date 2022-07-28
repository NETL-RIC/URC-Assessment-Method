import typing

from .ui_gradientdlg import Ui_GradientDialog
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QAbstractTableModel, QModelIndex, Qt,QVariant,QSize
from PyQt5.QtWidgets import QDialog,QStyledItemDelegate,QSpinBox,QComboBox,qApp
from PyQt5.QtGui import QColor,QLinearGradient
from .colorbuttons_qt import ColorButton
from enum import IntEnum
## NOTE: keep viewmodel and delegate here, so as to be self-contained

class AnchorTableDelegate(QStyledItemDelegate):

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

        if isinstance(editor,QSpinBox):
            editor.valueChanged.disconnect()
        elif isinstance(editor, ColorButton):
            editor.baseColorChanged.disconnect()
        elif isinstance(editor,QComboBox):
            editor.currentTextChanged.disconnect()
        super().destroyEditor(editor,index)


    def setEditorData(self, editor, index):

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

        # https://www.qtcentre.org/threads/70447-QTableView-and-QStyledItemDelegate-Persistent-Editor-Issue

        w = self._dummyWidgets[index.column()]
        if w is not None:
            painter.save()
            if isinstance(w, QSpinBox):
                if index.row()==0 or index.row()==index.model().rowCount()-1:
                    super().paint(painter,option,index)
                    return
                w.setValue(int(index.data()))
            elif isinstance(w,ColorButton):
                w.basecolor = QColor(index.data())

            enabled = self.parent().isEnabled() and (int(index.model().flags(index)) & Qt.ItemIsEnabled) != 0
            w.setEnabled(enabled)
            w.resize(option.rect.width(),option.rect.height())
            map = w.grab()
            painter.drawPixmap(option.rect.x(),option.rect.y(),map)
            painter.restore()
        else:
            super().paint(painter,option,index)


    def _handleAction(self,action):

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

    @pyqtSlot(int)
    @pyqtSlot(QColor)
    def _valChanged(self,val):

        self.commitData.emit(self.sender())

    @pyqtSlot(str)
    def _comboChanged(self,val):
        self.sender().clearFocus()



##############################################################
class AnchorTableModel(QAbstractTableModel):

    gradientChanged = pyqtSignal(QLinearGradient)
    COLS = IntEnum('COLS',"Anchor Position Value Color Action",start=0)


    def __init__(self,minVal,maxVal,anchors,parent=None):
        super().__init__(parent)

        self._anchors= anchors
        self._minVal = minVal
        self._valRange = maxVal - minVal
        self._selectedRow=-1
        self.alphaVal = 1.

    def flags(self, index):
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

        if role == Qt.DisplayRole:
            if orientation==Qt.Horizontal:
                return QVariant(AnchorTableModel.COLS(section).name)
            else:
                return QVariant('    ' if section != self._selectedRow else '►')

        elif role == Qt.FontRole:
            # hi def screens scale the font; ensure that this
            # holds true for tableview
            fnt = qApp.font()
            return QVariant(fnt)
        return QVariant()

    def setData(self, index, value, role=Qt.DisplayRole):

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
        return False

    def data(self, index, role=Qt.DisplayRole):

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
        return len(AnchorTableModel.COLS)

    def rowCount(self, parent=QModelIndex()):
        return len(self._anchors)

    def _emitGradient(self):
        self.gradientChanged.emit(self.gradient)

    def getValueRange(self,r):
        minVal = self._anchors[r-1][0] if r>0 else self._anchors[r][0]
        maxVal = self._anchors[r+1][0] if r<(len(self._anchors) - 1) else self._anchors[r][0]

        return minVal,maxVal

    def markRow(self,row=-1):
        if row!=self._selectedRow:
            self._selectedRow = row
            self.headerDataChanged.emit(Qt.Horizontal,0,self.rowCount())

    @pyqtSlot(int)
    def adjustAnchorCount(self,count):
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

        self.beginInsertRows(parent,row,row)
        a = self._mixAnchors(self._anchors[row - 1], self._anchors[row])
        self._anchors.insert(row, a)

        self.endInsertRows()
        self._emitGradient()

    def removeRow(self,row,parent=QModelIndex()):

        self.beginRemoveRows(parent,row,row)
        self._anchors.pop(row)
        self.endRemoveRows()
        self._emitGradient()

    def swapColors(self,r1,r2):
        a1 = self._anchors[r1]
        a2 = self._anchors[r2]

        self.beginResetModel()
        tmp = a1[1]
        a1[1]=a2[1]
        a2[1]=tmp
        self.endResetModel()
        self._emitGradient()

    def _mixColors(self,c1,c2,wt = 0.5):
        ret= QColor()
        ret.setRgbF(
            (c1.redF()*(1.-wt))+(c2.redF()*wt),
            (c1.greenF()*(1.-wt))+(c2.greenF()*wt),
            (c1.blueF()*(1.-wt))+(c2.blueF()*wt),
            (c1.alphaF()*(1.-wt))+(c2.alphaF()*wt),
        )
        return ret

    def _mixWeights(self,w1,w2,wt=0.5):

        return (w1*(1.-wt))+(w2*wt)

    def _mixAnchors(self,a1,a2,wt=0.5):

        return [self._mixWeights(a1[0],a2[0],wt),self._mixColors(a1[1],a2[1],wt)]

    @pyqtSlot()
    def redistributeWeights(self):

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
        ret = QLinearGradient(0., 0., 1., 0.)
        ret.setCoordinateMode(QLinearGradient.ObjectBoundingMode)
        ret.setStops(self._anchors)
        return ret

    @property
    def gradientWithAlpha(self):
        ret = QLinearGradient(0., 0., 1., 0.)
        ret.setCoordinateMode(QLinearGradient.ObjectBoundingMode)
        for a in self._anchors:
            a[1].setAlphaF(self.alphaVal)
        ret.setStops(self._anchors)
        return ret

    @property
    def anchors(self):
        return self._anchors


##############################################################
class GradientDialog(QDialog):

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
        return self._tblMdl.gradient

    def gradientWithAlpha(self):
        return self._tblMdl.gradientWithAlpha

    @pyqtSlot('QItemSelection','QItemSelection')
    def _selectChanged(self,selected,deselected):
        if len(selected.indexes())==0:
            self._tblMdl.markRow(-1)
        else:
            self._tblMdl.markRow(selected.indexes()[0].row())

    @pyqtSlot('QModelIndex',int,int)
    def _anchorsChanged(self, index,first,last):

        count = self._tblMdl.rowCount()
        maxNote= ' (max reached)'
        self._ui.countLbl.setText(f'Anchor Count: {count}{maxNote if count>=GradientDialog.MAX_ANCHORS else ""}')

    @pyqtSlot(int)
    def _updateAlpha(self,val):
        self._tblMdl.alphaVal=float(val)/100.

    @property
    def alphaValue(self):
        return self._tblMdl.alphaVal

    @alphaValue.setter
    def alphaValue(self, value):
        self._tblMdl.alphaVal = value