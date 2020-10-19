from PyQt5.QtWidgets import QDialog,QMessageBox,QFileDialog
from PyQt5.QtCore import Qt

from .RunDlgBase import RunDlgBase
from ._autoforms.ui_rungriddlg import Ui_CreateGridDlg

from ..create_pe_grid import RunCreatePEGrid
from ..common_utils import REE_Workspace

class RunGridDlg(RunDlgBase):

    def __init__(self,parent=None):
        super().__init__(parent)

        self._ui = Ui_CreateGridDlg()
        self._ui.setupUi(self)

        self._sdPath = None
        self._ldPath = None
        self._prjPath = None
        self._finalGridPath = None
        self._lgSdLdGridPath = None
        self._lgSdDSPath = None
        self._baseGridPath = None
        self._gridDataFramePath = None

        self._ui.sdInputButton.clicked.connect(self.on_sdInputButton_clicked)
        self._ui.ldInputButton.clicked.connect(self.on_ldInputButton_clicked)
        self._ui.projectionButton.clicked.connect(self.on_projectionButton_clicked)
        self._ui.finalGridButton.clicked.connect(self.on_finalGridButton_clicked)
        self._ui.lgsdldGridButton.clicked.connect(self.on_lgsdldGridButton_clicked)
        self._ui.lgsdDatasetButton.clicked.connect(self.on_lgsdDatasetButton_clicked)
        self._ui.baseGridButton.clicked.connect(self.on_baseGridButton_clicked)
        self._ui.gridDataframeButton.clicked.connect(self.on_gridDataframeButton_clicked)
            
        self._ui.projectionCB.toggled.connect(self.on_projectionCB_toggled)
        self._ui.lgsdldGridCB.toggled.connect(self.on_lgsdldGridCB_toggled)
        self._ui.lgsdDatasetCB.toggled.connect(self.on_lgsdDatasetCB_toggled)
        self._ui.baseGridCB.toggled.connect(self.on_baseGridCB_toggled)
        self._ui.gridDataframeCB.toggled.connect(self.on_gridDataframeCB_toggled)
            
        

    def accept(self):

        ...


    # wiring
    def on_sdInputButton_clicked(self):

        self._ioPath('_sdPath',self._ui.sdInputLbl,'ESRI Shapefile (*.shp)',True)

    def on_ldInputButton_clicked(self):
        self._ioPath('_ldPath', self._ui.ldInputLbl, 'ESRI Shapefile (*.shp)', True)

    def on_projectionButton_clicked(self):
        self._ioPath('_prjPath', self._ui.projectionLbl, 'Projection File (*.prj)', True)

    def on_finalGridButton_clicked(self):
        self._ioPath('_finalGridPath', self._ui.finalGridLbl, 'ESRI Shapefile (*.shp)', False)

    def on_lgsdldGridButton_clicked(self):
        self._ioPath('_lgSdLdGridPath', self._ui.lgsdldGridLbl, 'ESRI Shapefile (*.shp)', False)

    def on_lgsdDatasetButton_clicked(self):
        self._ioPath('_lgSdDSPath', self._ui.lgsdDatasetLbl, 'ESRI Shapefile (*.shp)', False)

    def on_baseGridButton_clicked(self):
        self._ioPath('_baseGridPath', self._ui.baseGridLbl, 'ESRI Shapefile (*.shp)', False)

    def on_gridDataframeButton_clicked(self):
        self._ioPath('_gridDataFramePath', self._ui.gridDataframeLbl, 'CSV File (*.csv)', False)

    def on_projectionCB_toggled(self,isChecked):
        self._optToggled(isChecked,'projection')

    def on_lgsdldGridCB_toggled(self,isChecked):
        self._optToggled(isChecked,'lgsdldGrid')

    def on_lgsdDatasetCB_toggled(self,isChecked):
        self._optToggled(isChecked,'lgsdDataset')

    def on_baseGridCB_toggled(self,isChecked):
        self._optToggled(isChecked,'baseGrid')

    def on_gridDataframeCB_toggled(self,isChecked):
        self._optToggled(isChecked,'gridDataframe')
