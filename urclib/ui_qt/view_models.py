import os.path

from PyQt5.QtCore import Qt,QAbstractListModel,QAbstractItemModel,QItemSelectionModel,QModelIndex,QVariant,pyqtSignal

from .visualizer import GradientRecord

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
            sMdl = self.parent().selectionModel()
            sMdl.clear()
            sMdl.select(index,QItemSelectionModel.Select)
            oldState = self._entries[row][1]
            self._entries[row][1]= value==Qt.Checked
            if oldState!=value:
                self.taskToggled.emit(row,*self._entries[row])
            return True
        return False

    def stateForRow(self,r):
        return tuple(self._entries[r])

    def setStateForRow(self,r,state):

        if self._entries[r][1]!=state:
            self.beginResetModel()
            self._entries[r][1]=state
            self.taskToggled.emit(r, *self._entries[r])
            self.endResetModel()

    def anyEnabled(self):
        for _,enabled in self._entries:
            if enabled:
                return True
        return False

    def emitAllStates(self):
        for r,e in enumerate(self._entries):
            self.taskToggled.emit(r, *e)

######################################################################

# based on example:
# https://doc.qt.io/qt-6/qtwidgets-itemviews-simpletreemodel-example.html

class ResultTreeModel(QAbstractItemModel):

    # internal classes
    class _BaseNode(object):
        def __init__(self,name,parent=None):
            self.name=name
            self.parent=parent

        def isRoot(self):
            return self.parent is None

        @property
        def index(self):
            if self.parent is None:
                return -1
            return self.parent._subnodes.index(self)

    class GroupNode(_BaseNode):
        def __init__(self, name='', parent=None):
            super().__init__(name,parent)
            self._subnodes = []

        def addGroup(self, name):
            newGrp = ResultTreeModel.GroupNode(name, self)
            self._subnodes.append(newGrp)
            return newGrp

        def addNode(self, path):
            newNode = ResultTreeModel.EntryNode(path, self)
            self._subnodes.append(newNode)
            return newNode

        def __len__(self):
            return len(self._subnodes)

        def __getitem__(self, item):
            return self._subnodes[item]

        @property
        def nodeCount(self):
            tot = 0
            for n in self._subnodes:
                if isinstance(n, ResultTreeModel.GroupNode):
                    tot += n.nodeCount

                tot += 1
            return tot

    class EntryNode(_BaseNode):

        def __init__(self, path, parent):
            name = os.path.splitext(os.path.basename(path))[0]
            super().__init__(name,parent)
            self.id = None
            self.path = path
            self.gradRec = GradientRecord()

    # /internal classes

    def __init__(self,parent=None):
        super().__init__(parent)

        self._root= ResultTreeModel.GroupNode()

    def newTopGroup(self,name):
        self.beginResetModel()
        ret = self._root.addGroup(name)
        self.endResetModel()
        return ret

    def addSubNode(self,parent,path):

        self.beginResetModel()
        ret= parent.addNode(path)
        self.endResetModel()
        return ret

    def index(self, row, column, parent = QModelIndex()):

        if not self.hasIndex(row,column,parent):
            return QModelIndex()

        if not parent.isValid():
            parentItem=self._root
        else:
            parentItem = parent.internalPointer()

        if isinstance(parentItem,ResultTreeModel.GroupNode):
            child = parentItem[row]
            return self.createIndex(row,column,child)
        return QModelIndex()

    def parent(self,index):

        if not index.isValid():
            return QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent

        if parentItem is None or parentItem.isRoot():
            return QModelIndex()

        return self.createIndex(parentItem.index,0,parentItem)

    def rowCount(self, parent=QModelIndex()):

        if not parent.isValid():
            parentItem=self._root
        else:
            parentItem=parent.internalPointer()

        return len(parentItem) if isinstance(parentItem,ResultTreeModel.GroupNode) else 0

    def columnCount(self,parent=QModelIndex()):
        return 1

    def data(self, index, role = Qt.DisplayRole):

        if index.isValid() and role==Qt.DisplayRole:
            node = index.internalPointer()
            if node.parent is not None:
                return QVariant(node.name)

        return QVariant()

    def flags(self, index):

        if not index.isValid():
            return Qt.NoItemFlags

        ret = Qt.ItemIsEnabled
        if isinstance(index.internalPointer(),ResultTreeModel.EntryNode):
            ret |= Qt.ItemIsSelectable

        return ret
