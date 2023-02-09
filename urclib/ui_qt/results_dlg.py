"""Logic for displaying preview results of URC analysis."""

import sys,os
from PyQt5.QtWidgets import QDialog,QLabel,QSizePolicy
from PyQt5.QtCore import Qt, pyqtSlot, QSize
from PyQt5.QtGui import QPixmap
from .visualizer import newOGRScene,GradientRecord
from .visualizer.qt_support import GradRecToStops, StopsToGradRec,GradientDialog
from ._autoforms.ui_resultsdlg import Ui_resultDialog

from .view_models import ResultTreeModel


class ResultDlg(QDialog):
    """Dialog for displaying results of a URC calculation.

    Args:
        cg_workspace (..urc_common.UrcWorkspace,optional): Paths to Create Grid results, or `None` if Create Grid was
            not run. Defaults to `None`.
        pe_workspace (..urc_common.UrcWorkspace,optional): Paths to PE Score results, or `None` if PE Score was not run.
            Defaults to `None`.
        log_text (str,optional): Copy of log created during the processing. Defaults to an empty string.
        parent (PyQt5.QtWidgets.QWidget,optional): The parent widget, or `None`. Default is `None`.

    Attributes:
         treeMdl (.view_models.ResultTreeModel): The model for the tree list view displaying the results for selection.
    """

    def __init__(self, cg_workspace=None, pe_workspace=None, log_text='', parent=None):
        super().__init__(parent)

        self._ui = Ui_resultDialog()
        self._ui.setupUi(self)

        # disable "?" button (remove to enable context hint functionality)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self._ui.logTextView.setPlainText(log_text)
        self._ui.rasterView.scene = newOGRScene()

        watermark=QLabel(self._ui.rasterView)
        # sizePolicy = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        # sizePolicy.setHorizontalStretch(0)
        # sizePolicy.setVerticalStretch(0)
        # sizePolicy.setHeightForWidth(watermark.sizePolicy().hasHeightForWidth())
        # watermark.setSizePolicy(sizePolicy)
        # watermark.setMinimumSize(QSize(32, 37))
        # watermark.setMaximumSize(QSize(32, 37))
        watermark.setText("")
        watermark.setScaledContents(True)
        watermark.setPixmap(QPixmap('resources/NETL_Square_small.png'))
        watermark.setGeometry(20,40,32,37)
        watermark.raise_()

        self._watermark=watermark
        self._selectedNode = None

        self._defaultgrad = GradientRecord()
        self.treeMdl = ResultTreeModel(self._ui.resultTreeView)

        if cg_workspace is not None:
            grp = self.treeMdl.new_top_group('Create Grid Results')
            for path in cg_workspace:
                self.treeMdl.add_subnode(grp, path)

        if pe_workspace is not None:
            grp = self.treeMdl.new_top_group('PE Scoring Results')
            for path in pe_workspace:
                self.treeMdl.add_subnode(grp, path)

        self._ui.resultTreeView.setModel(self.treeMdl)
        self._ui.resultTreeView.selectionModel().selectionChanged.connect(self.refresh_display)
        self._ui.gradientValButton.gradientChanged.connect(self._gradient_update)
        self._ui.rasterView.mouseMoved.connect(self._coord_update)
        self._ui.rasterView.mouseInOut.connect(self._coord_show_hide)
        self._ui.allGradButton.clicked.connect(self._all_gradient_clicked)
        self._ui.rasterView.resized.connect(self._mapResized)
        self._coord_show_hide(False)

        self._ui.resultTreeView.expandAll()

    @pyqtSlot('QItemSelection', 'QItemSelection')
    def refresh_display(self, selected, deselected):
        """Refresh the display of results due to a selection change.

        Args:
            selected (PyQt5.QtCore.QItemSelection): List of indices of newly selected cells.
            deselected (PyQt5.QtCore.QItemSelection): List of indices of newly deselected cells.
        """
        if len(deselected.indexes()) > 0:
            node = deselected.indexes()[0].internalPointer()
            self._ui.rasterView.scene.SetLayerVisible(node.id, False)
            self._ui.gradientValButton.setEnabled(False)
            self._selectedNode = None
        if len(selected.indexes()) > 0:
            node = selected.indexes()[0].internalPointer()
            if node.id is None:
                node.gradRec=self._defaultgrad
                node.id = self._ui.rasterView.scene.OpenRasterIndexLayer(node.path, node.gradRec)
            else:
                self._ui.rasterView.scene.SetLayerVisible(node.id, True)
            self._selectedNode = node

            self._ui.gradientValButton.setEnabled(True)
            # prevent accidental assignment by blocking signals
            self._ui.gradientValButton.blockSignals(True)
            self._ui.gradientValButton.stops = GradRecToStops(node.gradRec)
            self._ui.gradientValButton.blockSignals(False)

    @pyqtSlot('QLinearGradient')
    def _gradient_update(self, linear_grad):
        """Update the color gradient used to display data

        Args:
            linear_grad (PyQt5.QtGui.QLinearGradient): The gradient to apply.

        """

        if self._selectedNode is not None:
            grad = StopsToGradRec(linear_grad.stops())
            self._ui.rasterView.scene.UpdateIndexRasterGradient(self._selectedNode.id, grad)
            self._selectedNode.gradRec = grad

    @pyqtSlot(float, float)
    def _coord_update(self, x, y):
        """Update the coordinate display.

        Args:
            x (float): The x-ordinate.
            y (float): The y-ordinate.

        """
        if self._ui.resultTreeView.selectionModel().hasSelection():
            self._ui.coordLbl.setText(f'( {x:.5f}, {y:.5f})')

    @pyqtSlot(bool)
    def _coord_show_hide(self, visible):
        """Show or hide the coordinates, displaying substitute text if no coordinates are to be displayed.

        Args:
            visible (bool): If `True`, display the coordinates; otherwise, display the placeholder string.

        """

        if not visible:
            self._ui.coordLbl.setText('--')

    @pyqtSlot()
    def _all_gradient_clicked(self):

        stops= self._ui.gradientValButton.stops
        dlg=GradientDialog(0.,1.,stops,parent=self)
        if dlg.exec_()==QDialog.Accepted:
            grad = StopsToGradRec(dlg.gradient().stops())
            for n in self.treeMdl:
                if n.id is None:
                    continue
                self._ui.rasterView.scene.UpdateIndexRasterGradient(n.id,grad)
                n.gradRec=grad
            self._defaultgrad=grad

    @pyqtSlot()
    def _mapResized(self):

        padding = 20

        self._watermark.setGeometry(padding, self._ui.rasterView.height()-self._watermark.height()-padding,
                                    self._watermark.width(), self._watermark.height())
