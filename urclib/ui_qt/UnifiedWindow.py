import os

from PyQt5.QtWidgets import QMainWindow,QFileDialog,QMessageBox,QMenu
from PyQt5.QtGui import QDoubleValidator,QIntValidator,QColor,QPalette
from PyQt5.QtCore import Qt,pyqtSlot

from ..create_pe_grid import RunCreatePEGrid
from ..calculate_pe_score import RunPEScore
from ..common_utils import REE_Workspace
from .ProgLogDlg import ProgLogDlg
from .view_models import TaskListMdl
from ._autoforms.ui_unifiedwindow import Ui_MainWindow

def run_urc_tasks(cgArgs,peArgs,postProg):

    if cgArgs is not None:
        print("Running Create Grid...")
        RunCreatePEGrid(postProg=postProg,*cgArgs['args'],**cgArgs['kwargs'])
    if peArgs is not None:
        print("Running PE Score...")
        RunPEScore(postProg=postProg,*peArgs['args'],**peArgs['kwargs'])

class REEToolMainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self._ui = Ui_MainWindow()
        self._ui.setupUi(self)

        self._initCreateGrid()
        self._initPEScore()

        self._taskListMdl=TaskListMdl(self._ui.taskList)
        self._taskListMdl.taskToggled.connect(self.taskChecked)
        self._ui.taskList.setModel(self._taskListMdl)
        self._ui.taskList.selectionModel().selectionChanged.connect(self.taskChanged)
        self._ui.runButton.clicked.connect(self.runTask)
        self._taskListMdl.emitAllStates()

    # <editor-fold desc="Common methods">
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
        else:
            ioPath = None
        return ioPath

    def _optToggled(self,enabled,attr):

        getattr(self._ui,attr+'Lbl').setEnabled(enabled)
        getattr(self._ui, attr+'Button').setEnabled(enabled)

    @pyqtSlot('QItemSelection','QItemSelection')
    def taskChanged(self,selected,deselected):

        if len(selected) > 0:
            self._ui.taskStack.setCurrentIndex(selected.indexes()[0].row()+1)
        else:
            self._ui.taskStack.setCurrentIndex(0)

    @pyqtSlot(int, str, bool)
    def taskChecked(self, index, label, enabled):

        if label == 'Create Grid':
            page = self._ui.createGridPage
        else:   # label == 'PE Score':
            page = self._ui.peScorePage

        page.setEnabled(enabled)

        # update run button
        self._ui.runButton.setEnabled(self._taskListMdl.anyEnabled())

    @pyqtSlot()
    def runTask(self):

        do_cg = self._taskListMdl.stateForRow(0)[1]
        do_pe = self._taskListMdl.stateForRow(1)[1]

        missing=[]
        if do_cg:
            cg_miss=self.createGrid_checkmissing()
            if len(cg_miss)>0:
                missing.append("Create Grid Issues:")
            missing+=['   '+m for m in cg_miss]
        if do_pe:
            pe_miss=self.peScore_checkmissing()
            if len(pe_miss)>0:
                missing.append("PE Score Issues:")
            missing+=['   '+m for m in pe_miss]

        if len(missing)>0:
            missing.insert(0,"The following argmuents are missing:")
            QMessageBox.critical(self,'Missing arguments','\n'.join(missing))
            return

        cgParams=None
        peParams=None
        if do_cg:
            cgParams=self.createGrid_prep()
        if do_pe:
            peParams=self.peScore_prep()

        ProgLogDlg(run_urc_tasks, None, fnArgs=(cgParams,peParams),
                   title="Executing tasks...").show()
    # </editor-fold>

    # <editor-fold desc="CreateGrid methods">
    def _initCreateGrid(self):

        self._sdPath = None
        self._ldPath = None
        self._projFilePath = None
        self._ldOutPath = 'ld_inds.tif'
        self._lgOutPath = 'lg_inds.tif'
        self._sdOutPath = 'sd_inds.tif'
        self._udOutPath = 'ud_inds.tif'
        self._outDirPath = None

        self._ui.widthField.setValidator(QDoubleValidator(self._ui.widthField))
        self._ui.heightField.setValidator(QDoubleValidator(self._ui.heightField))
        self._ui.epsgField.setValidator(QIntValidator(self._ui.epsgField))

        # use explicit connection to avoid issues of double-binding that results
        # from name based auto-connect that results from inheriting from custom dialog
        self._ui.sdInputButton.clicked.connect(self._on_sdInputButton_clicked)
        self._ui.ldInputButton.clicked.connect(self._on_ldInputButton_clicked)
        self._ui.projFileButton.clicked.connect(self._on_projFileButton_clicked)
        self._ui.ldIndsButton.clicked.connect(self._on_ldIndsButton_clicked)
        self._ui.lgIndsButton.clicked.connect(self._on_lgIndsButton_clicked)
        self._ui.sdIndsButton.clicked.connect(self._on_sdIndsButton_clicked)
        self._ui.udIndsButton.clicked.connect(self._on_udIndsButton_clicked)
        self._ui.cgOutDirButton.clicked.connect(self._on_cgOutDir_clicked)

        self._ui.projCombo.currentIndexChanged.connect(self._ui.projStack.setCurrentIndex)
        self._ui.projBox.toggled.connect(self._on_projBox_toggled)

        # use provided labels to ensure frontend is in sync with backend
        overrides = [(self._ldOutPath, self._ui.ldIndsLbl),
                     (self._lgOutPath, self._ui.lgIndsLbl),
                     (self._sdOutPath, self._ui.sdIndsLbl),
                     (self._udOutPath, self._ui.udIndsLbl), ]
        for p, lbl in overrides:
            lbl.setText(p)

    def createGrid_checkmissing(self):
        fields = [('_sdPath', 'SD Input file'),
                  ('_ldPath', 'LD Input file'),
                  ]

        missing = []
        for a, n in fields:
            if getattr(self, a) is None:
                missing.append(n)

        try:
            float(self._ui.widthField.text())
        except:
            missing.append('Grid Width')
        try:
            float(self._ui.heightField.text())
        except:
            missing.append('Grid Height')

        if self._outDirPath is None:
            aPaths=[p for p in (self._ldOutPath,self._lgOutPath,self._sdOutPath,self._udOutPath) if not os.path.isabs(p)]
            if len(aPaths)>0:
                missing.append('The following paths are relative; either provide absolute paths, or an output directory:')
                missing.append(', '.join(aPaths))


        if self._ui.projBox.isChecked():
            if self._ui.projCombo.currentIndex() == 0 and self._projFilePath is None:
                missing.append('Projection File (is checked and selected).')
            elif self._ui.projCombo.currentIndex() == 1 and len(self._ui.epsgField.text()) == 0:
                missing.append('EPSG (is checked and selected).')

        return missing

    def createGrid_prep(self):

        epsg = None
        gwidth = float(self._ui.widthField.text())
        gheight = float(self._ui.heightField.text())



        inWorkspace= REE_Workspace(self._outDirPath if self._outDirPath is not None else '.')
        inWorkspace['SD_input_file'] = self._sdPath
        inWorkspace['LD_input_file'] = self._ldPath

        if self._ui.projBox.isChecked():
            if self._ui.projCombo.currentIndex()==0:
                inWorkspace['prj_file'] = self._projFilePath
            elif self._ui.projCombo.currentIndex()==1:
                epsg=int(self._ui.epsgField.text().strip())

        outWorkspace = REE_Workspace(self._outDirPath)
        outWorkspace['ld'] = self._ldOutPath
        outWorkspace['lg'] = self._lgOutPath
        outWorkspace['sd'] = self._sdOutPath
        outWorkspace['ud'] = self._udOutPath

        return {'args':(inWorkspace,outWorkspace,gwidth,gheight,epsg),
                'kwargs':{}}


    def _updateCommonPath(self,pAttr,lbl):
        path = lbl.text()
        if self._outDirPath is not None and os.path.isabs(path):
            common = os.path.commonpath([self._outDirPath,path])
            if path!=os.path.sep:
                rPath= os.path.relpath(path,common)
                lbl.setText(rPath)
                setattr(self,pAttr,rPath)

    # wiring
    @pyqtSlot()
    def _on_sdInputButton_clicked(self):

        self._ioPath('_sdPath',self._ui.sdInputLbl,'ESRI Shapefile (*.shp)',True)

    @pyqtSlot()
    def _on_ldInputButton_clicked(self):
        self._ioPath('_ldPath', self._ui.ldInputLbl, 'ESRI Shapefile (*.shp)', True)

    @pyqtSlot()
    def _on_projFileButton_clicked(self):
        self._ioPath('_projFilePath', self._ui.projFileLbl, 'Projection File (*.prj)', True)

    @pyqtSlot()
    def _on_ldIndsButton_clicked(self):
        path=self._ioPath('_ldOutPath', self._ui.ldIndsLbl, 'GeoTiff File (*.tif)', False)
        if path is not None:
            self._updateCommonPath('_ldOutPath', self._ui.ldIndsLbl)

    @pyqtSlot()
    def _on_lgIndsButton_clicked(self):
        path = self._ioPath('_lgOutPath', self._ui.lgIndsLbl, 'GeoTiff File (*.tif)', False)
        if path is not None:
            self._updateCommonPath('_lgOutPath', self._ui.lgIndsLbl)

    @pyqtSlot()
    def _on_sdIndsButton_clicked(self):
        path = self._ioPath('_sdOutPath', self._ui.sdIndsLbl, 'GeoTiff File (*.tif)', False)
        if path is not None:
            self._updateCommonPath('_sdOutPath',self._ui.sdIndsLbl)

    @pyqtSlot()
    def _on_udIndsButton_clicked(self):
        path = self._ioPath('_udOutPath', self._ui.udIndsLbl, 'GeoTiff File (*.tif)', False)
        if path is not None:
            self._updateCommonPath('_udOutPath', self._ui.udIndsLbl)

    @pyqtSlot()
    def _on_cgOutDir_clicked(self):
        path = self._ioPath('_outDirPath', self._ui.cgOutDirLbl, '', True,True)
        if path is not None:
            self._updateCommonPath('_ldOutPath',self._ui.ldIndsLbl)
            self._updateCommonPath('_lgOutPath',self._ui.lgIndsLbl)
            self._updateCommonPath('_sdOutPath',self._ui.sdIndsLbl)
            self._updateCommonPath('_udOutPath',self._ui.udIndsLbl)

    @pyqtSlot(bool)
    def _on_projBox_toggled(self, checked):
        # signal isn't propagating properly for the following widgets; update manually
        self._ui.projFileLbl.setEnabled(checked)
        self._ui.projFileButton.setEnabled(checked)

    # </editor-fold>

    # <editor-fold desc="PE Score">
    def _initPEScore(self):
        self._srcPath = None
        self._indexPath = None
        # self._lgName=None
        # self._ldName=None
        # self._sdName=None
        # self._udName=None
        self._clipPath = None
        self._outPath = None
        self._outRasterPath = None

        srcMenu = QMenu(self._ui.srcToolButton)
        gdbAction = srcMenu.addAction(".gdb file")
        sqlAction = srcMenu.addAction(".sqlite file")

        gdbAction.triggered.connect(self._onGdbActionTriggered)
        sqlAction.triggered.connect(self._onSQLActionTriggered)
        self._ui.srcToolButton.setMenu(srcMenu)
        self._ui.inputDirButton.clicked.connect(self._onIndexDirClicked)
        self._ui.ldIndField.editingFinished.connect(self._onIndexFieldEditFinished)
        self._ui.lgIndField.editingFinished.connect(self._onIndexFieldEditFinished)
        self._ui.sdIndField.editingFinished.connect(self._onIndexFieldEditFinished)
        self._ui.udIndField.editingFinished.connect(self._onIndexFieldEditFinished)
        self._ui.clipLyrCB.toggled.connect(self._clipLyrToggled)
        self._ui.clipLyrButton.clicked.connect(self._onClipLyrClicked)
        self._ui.peOutDirButton.clicked.connect(self._peOutDirClicked)

        self._ui.limitDaDsCB.toggled.connect(self._onLimitDaDsToggled)
        self._ui.rasterDirCB.toggled.connect(self._onRasterDirToggled)
        self._ui.rasterDirButton.clicked.connect(self._onRasterDirClicked)

    @pyqtSlot(bool)
    def _onGdbActionTriggered(self, checked):
        self._ioPath('_srcPath', self._ui.gdbLbl, 'FileGDB (*.gdb)', True, True)

    @pyqtSlot(bool)
    def _onSQLActionTriggered(self, checked):
        self._ioPath('_srcPath', self._ui.gdbLbl, 'Spatialite (*.sqlite)', True)

    @pyqtSlot()
    def _onIndexDirClicked(self):
        self._ioPath('_indexPath', self._ui.indexDirLbl, None, True, True)
        self._ui.ldIndField.editingFinished.emit()
        self._ui.lgIndField.editingFinished.emit()
        self._ui.sdIndField.editingFinished.emit()
        self._ui.udIndField.editingFinished.emit()

    @pyqtSlot()
    def _onClipLyrClicked(self):
        self._ioPath('_clipPath', self._ui.clipLyrLbl, 'ESRI Shapefile (*.shp)', True)

    @pyqtSlot()
    def _peOutDirClicked(self):
        self._ioPath('_outPath', self._ui.peOutDirLbl, None, True, True)

    @pyqtSlot()
    def _onRasterDirClicked(self):
        self._ioPath('_outRasterPath', self._ui.rasterDirLbl, None, True, True)

    @pyqtSlot(bool)
    def _onLimitDaDsToggled(self, isChecked):
        self._ui.dadsCombo.setEnabled(isChecked)

    @pyqtSlot(bool)
    def _onRasterDirToggled(self, isChecked):
        self._optToggled(isChecked, 'rasterDir')
        self._ui.exitOnRasterCB.setEnabled(isChecked)

    @pyqtSlot()
    def _onIndexFieldEditFinished(self):
        field = self.sender()
        found = self._testIndexPath(self._indexPath, field.text())

        txtColor = self.palette().color(QPalette.Active, QPalette.Text)
        fldPal = field.palette()
        if not found:
            txtColor = QColor('red')
        fldPal.setColor(QPalette.Active, QPalette.Text, txtColor)
        field.setPalette(fldPal)

    @pyqtSlot(bool)
    def _clipLyrToggled(self, checked):
        self._optToggled(checked, 'clipLyr')

    def peScore_checkmissing(self):
        fields = [('_srcPath', '   Source File'),
                  ('_indexPath', '   Index Files Directory'),
                  ('_outPath', '   Output Directory')]

        if self._ui.clipLyrCB.isChecked():
            fields.append(('_clipPath', '   Clip Layer File'))
        if self._ui.rasterDirCB.isChecked():
            fields.append(('_outRasterPath', '   Intermediate Rasters Directory'))

        missing = []
        for a, n in fields:
            if getattr(self, a) is None:
                missing.append(n)

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
                    missing.append('   ' + inWorkspace[k])

        if len(missing) > mInsert:
            missing.insert(mInsert, 'The following index files are missing')

        return missing

    def peScore_prep(self):

        inWorkspace = REE_Workspace(self._indexPath,
                                    ld_inds=self._ui.ldIndField.text(),
                                    lg_inds=self._ui.lgIndField.text(),
                                    sd_inds=self._ui.sdIndField.text(),
                                    ud_inds=self._ui.udIndField.text(),
                                    )

        outputs = REE_Workspace(self._outPath)
        optArgs = {}

        if self._ui.rasterDirCB.isChecked():
            outputs['raster_dir'] = self._outRasterPath
            if self._ui.exitOnRasterCB.isChecked():
                optArgs['rasters_only'] = True

        if self._ui.limitDaDsCB.isChecked():
            selection = self._ui.dadsCombo.currentText()
            if selection == 'DA':
                optArgs['doDS'] = False
            elif selection == 'DS':
                optArgs['doDA'] = False
            else:
                raise Exception("Undefined filter selection: " + selection)

        # def RunPEScore(gdbPath, inWorkspace, outWorkspace, doDA, doDS, rasters_only, postProg=None):
        return {'args':(self._srcPath, inWorkspace, outputs),
                'kwargs':optArgs}


    def _testIndexPath(self, inputDir, indName):

        # don't worry about it if there is no input Dir
        if inputDir is None:
            return True
        fullpath = os.path.join(inputDir, indName)
        return os.path.exists(fullpath)
    # </editor-fold>