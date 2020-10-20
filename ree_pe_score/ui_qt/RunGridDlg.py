from PyQt5.QtWidgets import QDialog,QMessageBox,QFileDialog
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator

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

        self._ui.widthField.setValidator(QDoubleValidator(self._ui.widthField))
        self._ui.heightField.setValidator(QDoubleValidator(self._ui.heightField))

        # use explicit connection to avoid issues of double-binding that results
        # from name based auto-connect that results from inheriting from custom dialog
        self._ui.sdInputButton.clicked.connect(self._on_sdInputButton_clicked)
        self._ui.ldInputButton.clicked.connect(self._on_ldInputButton_clicked)
        self._ui.projectionButton.clicked.connect(self._on_projectionButton_clicked)
        self._ui.finalGridButton.clicked.connect(self._on_finalGridButton_clicked)
        self._ui.lgsdldGridButton.clicked.connect(self._on_lgsdldGridButton_clicked)
        self._ui.lgsdDatasetButton.clicked.connect(self._on_lgsdDatasetButton_clicked)
        self._ui.baseGridButton.clicked.connect(self._on_baseGridButton_clicked)
        self._ui.gridDataframeButton.clicked.connect(self._on_gridDataframeButton_clicked)

        self._ui.projectionCB.toggled.connect(self._on_projectionCB_toggled)
        self._ui.lgsdldGridCB.toggled.connect(self._on_lgsdldGridCB_toggled)
        self._ui.lgsdDatasetCB.toggled.connect(self._on_lgsdDatasetCB_toggled)
        self._ui.baseGridCB.toggled.connect(self._on_baseGridCB_toggled)
        self._ui.gridDataframeCB.toggled.connect(self._on_gridDataframeCB_toggled)
            
        

    def accept(self):

        fields = [('_sdPath', 'SD Input file'),
                  ('_ldPath', 'LD Input file'),
                  ('_finalGridPath', 'PE Grid')]

        missing = []
        for a, n in fields:
            if getattr(self, a) is None:
                missing.append(n)

        try:
            gwidth = float(self._ui.widthField.text())
        except:
            missing.append('Grid Width')
        try:
            gheight = float(self._ui.heightField.text())
        except:
            missing.append('Grid Height')

        if len(missing) > 0:
            missing.insert(0, 'The following fields are required:')
            QMessageBox.critical(self, 'Missing arguments', '\n'.join(missing))
            return

        inWorkspace= REE_Workspace('.')
        inWorkspace['SD_input_file'] = self._sdPath
        inWorkspace['LD_input_file'] = self._ldPath

        if self._ui.projectionCB.isChecked():
            inWorkspace['prj_file']=self._prjPath

        outWorkspace = REE_Workspace('.')
        outWorkspace['PE_Grid_calc']=self._finalGridPath
        optionals = [(self._ui.lgsdldGridCB,self._lgSdLdGridPath,'grid_LG_SD_LD'),
                     (self._ui.lgsdDatasetCB,self._lgSdDSPath,'LG_SD_out_featureclass'),
                     (self._ui.baseGridCB,self._baseGridPath,'grid_file'),
                     (self._ui.gridDataframeCB,self._gridDataFramePath,'exported_grid_df')]
        for cb, path,tag in optionals:
            if cb.isChecked():
                outWorkspace[tag] = path

        super().accept()
        RunCreatePEGrid(inWorkspace,outWorkspace,gwidth,gheight)

    # wiring
    def _on_sdInputButton_clicked(self):

        self._ioPath('_sdPath',self._ui.sdInputLbl,'ESRI Shapefile (*.shp)',True)

    def _on_ldInputButton_clicked(self):
        self._ioPath('_ldPath', self._ui.ldInputLbl, 'ESRI Shapefile (*.shp)', True)

    def _on_projectionButton_clicked(self):
        self._ioPath('_prjPath', self._ui.projectionLbl, 'Projection File (*.prj)', True)

    def _on_finalGridButton_clicked(self):
        self._ioPath('_finalGridPath', self._ui.finalGridLbl, 'ESRI Shapefile (*.shp)', False)

    def _on_lgsdldGridButton_clicked(self):
        self._ioPath('_lgSdLdGridPath', self._ui.lgsdldGridLbl, 'ESRI Shapefile (*.shp)', False)

    def _on_lgsdDatasetButton_clicked(self):
        self._ioPath('_lgSdDSPath', self._ui.lgsdDatasetLbl, 'ESRI Shapefile (*.shp)', False)

    def _on_baseGridButton_clicked(self):
        self._ioPath('_baseGridPath', self._ui.baseGridLbl, 'ESRI Shapefile (*.shp)', False)

    def _on_gridDataframeButton_clicked(self):
        self._ioPath('_gridDataFramePath', self._ui.gridDataframeLbl, 'CSV File (*.csv)', False)

    def _on_projectionCB_toggled(self,isChecked):
        self._optToggled(isChecked,'projection')

    def _on_lgsdldGridCB_toggled(self,isChecked):
        self._optToggled(isChecked,'lgsdldGrid')

    def _on_lgsdDatasetCB_toggled(self,isChecked):
        self._optToggled(isChecked,'lgsdDataset')

    def _on_baseGridCB_toggled(self,isChecked):
        self._optToggled(isChecked,'baseGrid')

    def _on_gridDataframeCB_toggled(self,isChecked):
        self._optToggled(isChecked,'gridDataframe')
