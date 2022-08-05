from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import Qt,pyqtSlot
from .visualizer import newOGRScene
from .visualizer.qt_support import GradRecToStops,StopsToGradRec
from ._autoforms.ui_resultsdlg import Ui_resultDialog

from .view_models import ResultTreeModel

class ResultDlg(QDialog):

    def __init__(self, cg_workspace=None, pe_workspace=None, logText='',parent=None):

        super().__init__(parent)

        self._ui = Ui_resultDialog()
        self._ui.setupUi(self)

        # disable "?" button (remove to enable context hint functionality)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self._ui.logTextView.setPlainText(logText)
        self._ui.rasterView.scene = newOGRScene()
        self._selectedNode=None

        self.treeMdl=ResultTreeModel(self._ui.resultTreeView)

        if cg_workspace is not None:
            grp=self.treeMdl.newTopGroup('Create Grid Results')
            for path in cg_workspace:
                self.treeMdl.addSubNode(grp,path)

        if pe_workspace is not None:
            grp = self.treeMdl.newTopGroup('PE Scoring Results')
            for path in pe_workspace:
                self.treeMdl.addSubNode(grp,path)

        self._ui.resultTreeView.setModel(self.treeMdl)
        self._ui.resultTreeView.selectionModel().selectionChanged.connect(self.refresh_display)
        self._ui.gradientValButton.gradientChanged.connect(self._gradient_update)
        self._ui.rasterView.mouseMoved.connect(self._coordUpdate)
        self._ui.rasterView.mouseInOut.connect(self._coordShowHide)
        self._coordShowHide(False)

        self._ui.resultTreeView.expandAll()

    @pyqtSlot('QItemSelection','QItemSelection')
    def refresh_display(self, selected,deselected):

        if len(deselected.indexes())>0:
            node = deselected.indexes()[0].internalPointer()
            self._ui.rasterView.scene.SetLayerVisible(node.id,False)
            self._ui.gradientValButton.setEnabled(False)
            self._selectedNode = None
        if len(selected.indexes())>0:
            node = selected.indexes()[0].internalPointer()
            if node.id is None:
                node.id=self._ui.rasterView.scene.OpenRasterIndexLayer(node.path,node.gradRec)
            else:
                self._ui.rasterView.scene.SetLayerVisible(node.id,True)
            self._selectedNode = node

            self._ui.gradientValButton.setEnabled(True)
            # prevent accidental assignment by blocking signals
            self._ui.gradientValButton.blockSignals(True)
            self._ui.gradientValButton.stops=GradRecToStops(node.gradRec)
            self._ui.gradientValButton.blockSignals(False)

    @pyqtSlot('QLinearGradient')
    def _gradient_update(self, linGrad):
        if self._selectedNode is not None:
            grad = StopsToGradRec(linGrad.stops())
            self._ui.rasterView.scene.UpdateIndexRasterGradient(self._selectedNode.id,grad)
            self._selectedNode.gradRec=grad

    @pyqtSlot(float, float)
    def _coordUpdate(self, x, y):
        if self._ui.resultTreeView.selectionModel().hasSelection():
            self._ui.coordLbl.setText(f'( {x:.5f}, {y:.5f})')

    @pyqtSlot(bool)
    def _coordShowHide(self, visible):
        if not visible:
            self._ui.coordLbl.setText('--')
