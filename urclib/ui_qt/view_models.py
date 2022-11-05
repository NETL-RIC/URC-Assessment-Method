"""Various models to drive table, list, and tree views."""
import os.path

from PyQt5.QtCore import Qt, QAbstractListModel, QAbstractItemModel, QItemSelectionModel, QModelIndex, QVariant, \
    pyqtSignal

from .visualizer import GradientRecord


class TaskListMdl(QAbstractListModel):
    """Model for Task List view."""

    taskToggled = pyqtSignal(int, str, bool)

    def __init__(self, parent):
        super().__init__(parent)

        self._entries = [["Create Grid", False],
                         ["PE Score", False]]

    def flags(self, index):
        """This is an overload of a `QAbstractListModel` method. See Qt documentation for details.

        Args:
            index (PyQt5.QtCore.QModelIndex): Cell being queried for flags.

        Returns:
            int: Bitflags signalling behaviors for the specified cell

        See Also:
            [Official Qt Documentation](https://doc.qt.io/qt-5/qabstractlistmodel.html#flags)
        """

        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable

    def rowCount(self, parent=QModelIndex()):
        """This is an overload of a `QAbstractListModel` method. See Qt documentation for details.

        Args:
            parent (PyQt5.QtCore.QModelIndex,optional): Parent cell, if any.

        Returns:
            int: The number of existing rows.

        See Also:
            [Official Qt Documentation](https://doc.qt.io/qt-5/qabstractitemmodel.html#rowCount)
        """
        return len(self._entries)

    def data(self, index, role=Qt.DisplayRole):
        """This is an overload of a `QAbstractListModel` method. See Qt documentation for details.

        Args:
            index (PyQt5.QtCore.QModelIndex): Cell being queried for data.
            role (int,optional): Flag indicating the type of data being requested.

        Returns:
            PyQt5.QtCore.QVariant: The requeseted data.

        See Also:
            [Official Qt Documentation](https://doc.qt.io/qt-5/qabstractitemmodel.html#data)
        """

        if role == Qt.DisplayRole:
            return QVariant(self._entries[index.row()][0])
        elif role == Qt.CheckStateRole:
            return QVariant(Qt.Checked if self._entries[index.row()][1] else Qt.Unchecked)

        return QVariant()

    def setData(self, index, value, role=Qt.EditRole):
        """This is an overload of a `QAbstractListModel` method. See Qt documentation for details.

        Args:
            index (PyQt5.QtCore.QModelIndex): Cell being assigned a value.
            value (PyQt5.QtCore.QVariant): The value to assign.
            role (int,optional): Flag indicating the type of data being assigned.

        Returns:
            bool: `True` if the data was assigned; `False` otherwise.

        See Also:
            [Official Qt Documentation](https://doc.qt.io/qt-5/qabstractitemmodel.html#setData)
        """

        if role == Qt.CheckStateRole:
            row = index.row()
            s_mdl = self.parent().selectionModel()
            s_mdl.clear()
            s_mdl.select(index, QItemSelectionModel.Select)
            old_state = self._entries[row][1]
            self._entries[row][1] = value == Qt.Checked
            if old_state != value:
                self.taskToggled.emit(row, *self._entries[row])
            return True
        return False

    def state_for_row(self, r):
        """Retrieve the checked state for a given model.

        Args:
            r (int): The row/record to query.

        Returns:
            bool: Return the active state for the entry.
        """

        return tuple(self._entries[r])

    def set_state_for_row(self, r, state):
        """Set the active state for a given row.

        Args:
            r (int): The row/record to modify.
            state (bool): The active state for the role.
        """
        if self._entries[r][1] != state:
            self.beginResetModel()
            self._entries[r][1] = state
            self.taskToggled.emit(r, *self._entries[r])
            self.endResetModel()

    def any_enabled(self):
        """Test to see if any entries are enabled.

        Returns:
            bool: `True` if one or more entries are enabled; `False` otherwise.
        """
        for _, enabled in self._entries:
            if enabled:
                return True
        return False

    def emit_all_states(self):
        """Emit the state for each row in the list."""
        for r, e in enumerate(self._entries):
            self.taskToggled.emit(r, *e)


######################################################################

# based on example:
# https://doc.qt.io/qt-6/qtwidgets-itemviews-simpletreemodel-example.html

class ResultTreeModel(QAbstractItemModel):
    """Model for Result Tree heirarchy view.

    Args:
        parent (PyQt5.QtWidgets.QWidget,optional): The parent widget, if any.
    """

    # internal classes
    class _BaseNode(object):
        """Common Attributes for a tree node.

        Args:
            name (str): The name of the node.
            parent (_BaseNode or None,optional): The parent node, if any. Defaults to `None`.

        Attributes:
            name (str): The name of the node.
            parent (_BaseNode or None): The parent node, if any.
        """

        def __init__(self, name, parent=None):
            self.name = name
            self.parent = parent

        def is_root(self):
            """Test to see if a node is at the root of the tree.

            Returns:
                bool: `True` if node is at the root of the tree; `False` otherwise.
            """

            return self.parent is None

        @property
        def index(self):
            """int: index of this node in the parent node's list, or -1 if there is no parent node."""
            if self.parent is None:
                return -1
            return self.parent._subnodes.index(self)

    class GroupNode(_BaseNode):
        """Node containing subnodes.

        Args:
            name (str): The name of the node.
            parent (_BaseNode or None,optional): The parent node, if any. Defaults to `None`.
        """

        def __init__(self, name='', parent=None):
            super().__init__(name, parent)
            self._subnodes = []

        def add_group(self, name):
            """Add a new group node as a subnode.

            Args:
                name (str): The name of the new group node.

            Returns:
                GroupNode: The newly created node.
            """

            new_grp = ResultTreeModel.GroupNode(name, self)
            self._subnodes.append(new_grp)
            return new_grp

        def add_node(self, path):
            """Add a leaf node.

            Args:
                path (str): The path represented by the leaf.

            Returns:
                EntryNode: The newly created leaf node.
            """

            new_node = ResultTreeModel.EntryNode(path, self)
            self._subnodes.append(new_node)
            return new_node

        def __len__(self):
            return len(self._subnodes)

        def __getitem__(self, item):
            return self._subnodes[item]

        @property
        def node_count(self):
            """int: The total number of child nodes."""
            tot = 0
            for n in self._subnodes:
                if isinstance(n, ResultTreeModel.GroupNode):
                    tot += n.node_count

                tot += 1
            return tot

    class EntryNode(_BaseNode):
        """Leaf node representing a file entry.

        Args:
            path (str): Path to representative file.
            parent (_BaseNode or None,optional): The parent node, if any. Defaults to `None`.

        Attributes:
            id (int or None): Space for the visualizer to assign an id for the visual representation.
            path (str): The path to the represented file.
            gradRec (.visualizer.GradientRecord): Gradient to be applied to data on visualization.
        """

        def __init__(self, path, parent):
            name = os.path.splitext(os.path.basename(path))[0]
            super().__init__(name, parent)
            self.id = None
            self.path = path
            self.gradRec = GradientRecord()

    # end internal classes

    def __init__(self, parent=None):
        super().__init__(parent)

        self._root = ResultTreeModel.GroupNode()

    def new_top_group(self, name):
        """Add a new group node to the root node.

        Args:
            name (str): The name of the new node.

        Returns:
            GroupNode: The newly created node.
        """
        self.beginResetModel()
        ret = self._root.add_group(name)
        self.endResetModel()
        return ret

    def add_subnode(self, parent, path):
        """Add new leaf node.

        Args:
            parent (GroupNode): The node to add a new child node to.
            path (str): Path to the represented file.

        Returns:
            EntryNode: The newly created node.
        """
        self.beginResetModel()
        ret = parent.add_node(path)
        self.endResetModel()
        return ret

    def index(self, row, column, parent=QModelIndex()):
        """This is an overload of a `QAbstractItemModel` method. See Qt documentation for details.

        Args:
            row (int): The row of the index to retrieve.
            column (int): The column of the index to retrieve.
            parent (PyQt5.QtCore.QModelIndex,optional): The index object of the parent cell, if any.

        Returns:
            PyQt5.QtCore.QModelIndex: The index object representing the requested entry.

        See Also:
            [Official Qt Documentation](https://doc.qt.io/qt-5/qabstractitemmodel.html#index)
        """

        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parent_item = self._root
        else:
            parent_item = parent.internalPointer()

        if isinstance(parent_item, ResultTreeModel.GroupNode):
            child = parent_item[row]
            return self.createIndex(row, column, child)
        return QModelIndex()

    def parent(self, index):
        """This is an overload of a `QAbstractItemModel` method. See Qt documentation for details.

        Args:
            index (PyQt5.QtCore.QModelIndex): The index for which to retrieve the parent index object.

        Returns:
            PyQt5.QtCore.QModelIndex: The parent index object, if any.

        See Also:
            [Official Qt Documentation](https://doc.qt.io/qt-5/qabstractitemmodel.html#parent)
        """

        if not index.isValid():
            return QModelIndex()

        child_item = index.internalPointer()
        parent_item = child_item.parent

        if parent_item is None or parent_item.is_root():
            return QModelIndex()

        return self.createIndex(parent_item.index, 0, parent_item)

    def rowCount(self, parent=QModelIndex()):
        """This is an overload of a `QAbstractListModel` method. See Qt documentation for details.

        Args:
            parent (PyQt5.QtCore.QModelIndex,optional): Parent cell, if any.

        Returns:
            int: The number of existing rows.

        See Also:
            [Official Qt Documentation](https://doc.qt.io/qt-5/qabstractitemmodel.html#rowCount)
        """
        if not parent.isValid():
            parent_item = self._root
        else:
            parent_item = parent.internalPointer()

        return len(parent_item) if isinstance(parent_item, ResultTreeModel.GroupNode) else 0

    def columnCount(self, parent=QModelIndex()):
        """This is an overload of a `QAbstractListModel` method. See Qt documentation for details.

        Args:
            parent (PyQt5.QtCore.QModelIndex,optional): Parent cell, if any.

        Returns:
            int: The number of existing columns.

        See Also:
            [Official Qt Documentation](https://doc.qt.io/qt-5/qabstractitemmodel.html#columnCount)
        """
        return 1

    def data(self, index, role=Qt.DisplayRole):
        """This is an overload of a `QAbstractListModel` method. See Qt documentation for details.

        Args:
            index (PyQt5.QtCore.QModelIndex): Cell being queried for data.
            role (int,optional): Flag indicating the type of data being requested.

        Returns:
            PyQt5.QtCore.QVariant: The requeseted data.

        See Also:
            [Official Qt Documentation](https://doc.qt.io/qt-5/qabstractitemmodel.html#data)
        """

        if index.isValid() and role == Qt.DisplayRole:
            node = index.internalPointer()
            if node.parent is not None:
                return QVariant(node.name)

        return QVariant()

    def flags(self, index):
        """This is an overload of a `QAbstractListModel` method. See Qt documentation for details.

        Args:
            index (PyQt5.QtCore.QModelIndex): Cell being queried for flags.

        Returns:
            int: Bitflags signalling behaviors for the specified cell

        See Also:
            [Official Qt Documentation](https://doc.qt.io/qt-5/qabstractlistmodel.html#flags)
        """
        if not index.isValid():
            return Qt.NoItemFlags

        ret = Qt.ItemIsEnabled
        if isinstance(index.internalPointer(), ResultTreeModel.EntryNode):
            ret |= Qt.ItemIsSelectable

        return ret
