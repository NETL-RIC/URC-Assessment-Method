import os

from PyQt5.QtWidgets import QMessageBox,QMenu
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QPalette,QColor

from .RunDlgBase import RunDlgBase
from ._autoforms.ui_runpedlg import Ui_Dialog

from ..calculate_pe_score import RunPEScore
from ..common_utils import REE_Workspace
from .ProgLogDlg import ProgLogDlg

class RunPEDlg(RunDlgBase):

    def __init__(self,parent=None):
        super().__init__(parent)

        self._ui = Ui_Dialog()
        self._ui.setupUi(self)

        self._srcPath=None
        self._indexPath=None
        # self._lgName=None
        # self._ldName=None
        # self._sdName=None
        # self._udName=None
        self._outPath=None
        self._outRasterPath=None

        srcMenu = QMenu(self._ui.srcToolButton)
        gdbAction=srcMenu.addAction(".gdb file")
        sqlAction = srcMenu.addAction(".sqlite file")

        gdbAction.triggered.connect(self._onGdbActionTriggered)
        sqlAction.triggered.connect(self._onSQLActionTriggered)
        self._ui.srcToolButton.setMenu(srcMenu)
        self._ui.inputDirButton.clicked.connect(self._onIndexDirClicked)
        self._ui.ldIndField.editingFinished.connect(self._onIndexFieldEditFinished)
        self._ui.lgIndField.editingFinished.connect(self._onIndexFieldEditFinished)
        self._ui.sdIndField.editingFinished.connect(self._onIndexFieldEditFinished)
        self._ui.udIndField.editingFinished.connect(self._onIndexFieldEditFinished)
        self._ui.outDirButton.clicked.connect(self._onOutDirClicked)

        self._ui.limitDaDsCB.toggled.connect(self._onLimitDaDsToggled)
        self._ui.rasterDirCB.toggled.connect(self._onRasterDirToggled)
        self._ui.rasterDirButton.clicked.connect(self._onRasterDirClicked)


    # Widget wiring
    @pyqtSlot(bool)
    def _onGdbActionTriggered(self,checked):
        self._ioPath('_srcPath',self._ui.gdbLbl,'FileGDB (*.gdb)',True,True)

    @pyqtSlot(bool)
    def _onSQLActionTriggered(self,checked):
        self._ioPath('_srcPath', self._ui.gdbLbl, 'Spatialite (*.sqlite)', True)

    @pyqtSlot()
    def _onIndexDirClicked(self):
        self._ioPath('_indexPath',self._ui.indexDirLbl,None,True,True)
        self._ui.ldIndField.editingFinished.emit()
        self._ui.lgIndField.editingFinished.emit()
        self._ui.sdIndField.editingFinished.emit()
        self._ui.udIndField.editingFinished.emit()

    @pyqtSlot()
    def _onOutDirClicked(self):
        self._ioPath('_outPath',self._ui.outDirLbl,None,True,True)

    @pyqtSlot()
    def _onRasterDirClicked(self):
        self._ioPath('_outRasterPath', self._ui.rasterDirLbl, None, True, True)

    @pyqtSlot(bool)
    def _onLimitDaDsToggled(self, isChecked):
        self._ui.dadsCombo.setEnabled(isChecked)

    @pyqtSlot(bool)
    def _onRasterDirToggled(self, isChecked):
        self._optToggled(isChecked,'rasterDir')
        self._ui.exitOnRasterCB.setEnabled(isChecked)

    @pyqtSlot()
    def _onIndexFieldEditFinished(self):
        field = self.sender()
        found = self._testIndexPath(self._indexPath,field.text())

        txtColor = self.palette().color(QPalette.Active,QPalette.Text)
        fldPal = field.palette()
        if not found:
            txtColor =QColor('red')
        fldPal.setColor(QPalette.Active,QPalette.Text,txtColor)
        field.setPalette(fldPal)

    def accept(self):

        fields=[('_srcPath','   Source File'),
                ('_indexPath','   Index Files Directory'),
                ('_outPath','   Output Directory')]

        if self._ui.rasterDirCB.isChecked():
            fields.append(('_outRasterPath','   Intermediate Rasters Directory'))

        missing=[]
        for a,n in fields:
            if getattr(self,a) is None:
                missing.append(n)
        if len(missing)>0:
            missing.insert(0,'The following fields are required:')

        mInsert = len(missing)
        # at this point all inputs valid
        inWorkspace = REE_Workspace(self._indexPath,
                                    ld_inds=self._ui.ldIndField.text(),
                                    lg_inds=self._ui.lgIndField.text(),
                                    sd_inds=self._ui.sdIndField.text(),
                                    ud_inds=self._ui.udIndField.text(),
                                    )
        if self._indexPath is not None:
            for (k, found) in inWorkspace.TestFilesExist():
                if not found:
                    missing.append('   '+inWorkspace[k])

        if len(missing)>mInsert:
            missing.insert(mInsert,'The following index files are missing')

        if len(missing)>0:
            QMessageBox.critical(self,'Missing arguments','\n'.join(missing))
            return

        outputs = REE_Workspace(self._outPath)
        optArgs={}

        if self._ui.rasterDirCB.isChecked():
            outputs['raster_dir']=self._outRasterPath
            if self._ui.exitOnRasterCB.isChecked():
                optArgs['rasters_only'] = True

        if self._ui.limitDaDsCB.isChecked():
            selection = self._ui.dadsCombo.currentText()
            if selection == 'DA':
                optArgs['doDS']=False
            elif selection == 'DS':
                optArgs['doDA']=False
            else:
                raise Exception("Undefined filter selection: "+selection)
        super().accept()

        #def RunPEScore(gdbPath, inWorkspace, outWorkspace, doDA, doDS, rasters_only, postProg=None):
        ProgLogDlg(RunPEScore,None,fnArgs=(self._srcPath,inWorkspace,outputs),fnKwArgs=optArgs,title="Calculating PE Score...").show()

    def _testIndexPath(self,inputDir,indName):

        # don't worry about it if there is no input Dir
        if inputDir is None:
            return True
        fullpath=os.path.join(inputDir,indName)
        return os.path.exists(fullpath)