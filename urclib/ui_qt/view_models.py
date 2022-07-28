from PyQt5.QtCore import Qt,QAbstractListModel,QModelIndex,QVariant,pyqtSignal

class TaskListMdl(QAbstractListModel):

    taskToggled=pyqtSignal(int,str,bool)

    def __init__(self,parent):
        super().__init__(parent)

        self._entries=[["Create Grid",False],
                      ["PE Score",False]]


    def flags(self, index):

        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable

    def rowCount(self, parent=QModelIndex()):
        return len(self._entries)

    def data(self, index, role = Qt.DisplayRole):

        if role==Qt.DisplayRole:
            return QVariant(self._entries[index.row()][0])
        elif role==Qt.CheckStateRole:
            return QVariant(Qt.Checked if self._entries[index.row()][1] else Qt.Unchecked)

        return QVariant()

    def setData(self, index, value, role= Qt.EditRole):

        if role==Qt.CheckStateRole:
            row = index.row()
            oldState = self._entries[row][1]
            self._entries[row][1]= value==Qt.Checked
            if oldState!=value:
                self.taskToggled.emit(row,*self._entries[row])
            return True
        return False

    def stateForRow(self,r):
        return tuple(self._entries[r])

    def anyEnabled(self):
        for _,enabled in self._entries:
            if enabled:
                return True
        return False

    def emitAllStates(self):
        for r,e in enumerate(self._entries):
            self.taskToggled.emit(r, *e)
