from PyQt5.QtWidgets import QDialog,QMessageBox,QFileDialog
from PyQt5.QtCore import Qt

from ._autoforms.ui_RunPEDlg import Ui_Dialog

from ..Calculate_PE_Score import RunPEScoreCalc
from ..common_utils import REE_Workspace


class RunPEDlg(QDialog):

    def __init__(self,parent=None):
        super().__init__(parent)

        self._ui = Ui_Dialog()
        self._ui.setupUi(self)

        self._gdbPath=None
        self._gridPath=None
        self._gridScorePath=None
        self._s1GridOutPath=None
        self._s1StatOutPath=None
        self._s3DFOutPath=None
        self._PEDFOutPath=None

        self._ui.gdbButton.clicked.connect(self._onGdbButtonClicked)
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

    def _ioPath(self,attr,lbl,filt,isOpen,isdir=False):
        initPath = ''
        if getattr(self,attr) is not None:
            initPath = getattr(self,attr)
        if isOpen:
            if not isdir:
                ioPath = QFileDialog.getOpenFileName(self,"Select File To Open",initPath,filt)[0]
            else:
                ioPath = QFileDialog.getExistingDirectory(self,"Select File To Open",initPath)
        else:
            ioPath = QFileDialog.getSaveFileName(self,'Select File Save Location',initPath,filt)[0]

        if len(ioPath)>0:
            setattr(self,attr,ioPath)
            lbl.setText(ioPath)
            lbl.setElideMode(Qt.ElideLeft)


    def _optToggled(self,enabled,attr):

        getattr(self._ui,attr+'Lbl').setEnabled(enabled)
        getattr(self._ui, attr+'Button').setEnabled(enabled)

    # Widget wiring
    def _onGdbButtonClicked(self):

        self._ioPath('_gdbPath',self._ui.gdbLbl,'FileGDB (*.gdb)',True,True)

    def _onGridButtonClicked(self):

        self._ioPath('_gridPath',self._ui.gridFileLbl,'FileGDB (*.shp)',True)

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

        fields=[('_gdbPath','Source GDB File'),
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

        RunPEScoreCalc(self._gdbPath,self._ui.targetCombo.currentText(),inWorkspace,outputs)
