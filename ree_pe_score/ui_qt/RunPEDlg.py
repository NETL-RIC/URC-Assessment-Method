from PyQt5.QtWidgets import QMessageBox,QMenu

from .RunDlgBase import RunDlgBase
from ._autoforms.ui_runpedlg import Ui_Dialog

from ..calculate_pe_score import RunPEScoreDS
from ..common_utils import REE_Workspace
from .ProgLogDlg import ProgLogDlg

class RunPEDlg(RunDlgBase):

    def __init__(self,parent=None):
        super().__init__(parent)

        self._ui = Ui_Dialog()
        self._ui.setupUi(self)

        self._srcPath=None
        self._gridPath=None
        self._gridScorePath=None
        self._s1GridOutPath=None
        self._s1StatOutPath=None
        self._s3DFOutPath=None
        self._PEDFOutPath=None

        srcMenu = QMenu(self._ui.srcToolButton)
        gdbAction=srcMenu.addAction(".gdb file")
        sqlAction = srcMenu.addAction(".sqlite file")

        gdbAction.triggered.connect(self._onGdbActionTriggered)
        sqlAction.triggered.connect(self._onSQLActionTriggered)
        self._ui.srcToolButton.setMenu(srcMenu)
        self._ui.gridFileButton.clicked.connect(self._onGridButtonClicked)
        self._ui.finalGridButton.clicked.connect(self._onGridScoreButtonClicked)
        self._ui.s1GridOutButton.clicked.connect(self._onS1GridOutClicked)
        self._ui.s1StatOutButton.clicked.connect(self._onS1StatOutClicked)
        self._ui.s3DataframeOutButton.clicked.connect(self._onS3DFOutClicked)
        self._ui.PEDataframeOutButton.clicked.connect(self._onPEDFOutClicked)

        self._ui.s1GridOutCB.toggled.connect(self._onS1GridToggled)
        self._ui.s1StatOutCB.toggled.connect(self._onS1StatToggled)
        self._ui.s3DataframeOutCB.toggled.connect(self._onS3DataframeToggled)
        self._ui.PEDataframeOutCB.toggled.connect(self._onPEDataframeToggled)

    # Widget wiring
    def _onGdbActionTriggered(self,checked):

        self._ioPath('_srcPath',self._ui.gdbLbl,'FileGDB (*.gdb)',True,True)

    def _onSQLActionTriggered(self,checked):

        self._ioPath('_srcPath', self._ui.gdbLbl, 'Spatialite (*.sqlite)', True)

    def _onGridButtonClicked(self):

        self._ioPath('_gridPath',self._ui.gridFileLbl,'ESRI Shapefile (*.shp)',True)

    def _onGridScoreButtonClicked(self):

        self._ioPath('_gridScorePath',self._ui.finalGridLbl,'Spatialite (*.sqlite)',False)

    def _onS1GridOutClicked(self):

        self._ioPath('_s1GridOutPath',self._ui.s1GridOutLbl,'Spatialite (*.sqlite)',False)

    def _onS1StatOutClicked(self):

        self._ioPath('_s1StatOutPath',self._ui.s1StatOutLbl,'CSV (*.csv)',False)

    def _onS3DFOutClicked(self):

        self._ioPath('_s3DFOutPath',self._ui.s3DataframeOutLbl,'CSV (*.csv)',False)

    def _onPEDFOutClicked(self):

        self._ioPath('_PEDFOutPath',self._ui.PEDataframeOutLbl,'CSV (*.csv)',False)

    def _onS1GridToggled(self,isChecked):
        self._optToggled(isChecked,'s1GridOut')

    def _onS1StatToggled(self,isChecked):
        self._optToggled(isChecked,'s1StatOut')

    def _onS3DataframeToggled(self,isChecked):
        self._optToggled(isChecked,'s3DataframeOut')

    def _onPEDataframeToggled(self,isChecked):
        self._optToggled(isChecked,'PEDataframeOut')


    def accept(self):

        fields=[('_srcPath','Source GDB File'),
                ('_gridPath','PE Grid File'),
                ('_gridScorePath','Output PE Grid')]

        missing=[]
        for a,n in fields:
            if getattr(self,a) is None:
                missing.append(n)
        if len(missing)>0:
            missing.insert(0,'The following fields are required:')
            QMessageBox.critical(self,'Missing arguments','\n'.join(missing))
            return

        # at this point all inputs valid
        inWorkspace = REE_Workspace('.')
        inWorkspace['PE_Grid_file']=self._gridPath

        outputs = REE_Workspace('.')
        outputs['final_grid'] = self._gridScorePath
        optionals = [(self._ui.s1GridOutCB,self._s1GridOutPath,'step1_grid'),
                     (self._ui.s1StatOutCB,self._s1StatOutPath,'step1_performance'),
                     (self._ui.s3DataframeOutCB,self._s3DFOutPath,'step3_dataframe'),
                     (self._ui.PEDataframeOutCB,self._PEDFOutPath,'pe_calc_dataframe')]

        for cb, path,tag in optionals:
            if cb.isChecked():
                outputs[tag] = path

        super().accept()
        ProgLogDlg(RunPEScoreDS,None,fnArgs=(self._srcPath,self._ui.targetCombo.currentText(),inWorkspace,outputs),title="Calculating PE Score...").show()

