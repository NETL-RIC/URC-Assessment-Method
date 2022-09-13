import os
from glob import iglob
from PyQt5.QtWidgets import QMainWindow,QFileDialog,QMessageBox,QMenu
from PyQt5.QtGui import QDoubleValidator,QIntValidator,QColor,QPalette
from PyQt5.QtCore import Qt,pyqtSlot,QSettings

from ..create_pe_grid import RunCreatePEGrid
from ..calculate_pe_score import RunPEScore
from ..common_utils import REE_Workspace
from .. import settings
from .ProgLogDlg import ProgLogDlg
from .ResultsDlg import ResultDlg
from .view_models import TaskListMdl
from ._autoforms.ui_unifiedwindow import Ui_MainWindow

def run_urc_tasks(cg_kwargs,pe_kwargs,postProg):

    outFiles={}
    if cg_kwargs is not None:
        print("~~~~ Running Create Grid... ~~~~")
        RunCreatePEGrid(postProg=postProg,**cg_kwargs)
        outFiles['cg_workspace']=cg_kwargs['outWorkspace']
    if pe_kwargs is not None:
        print("~~~~ Running PE Score... ~~~~")
        outFiles['pe_workspace']=RunPEScore(postProg=postProg,**pe_kwargs)

    return outFiles

class REEToolMainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self._ui = Ui_MainWindow()
        self._ui.setupUi(self)

        # cache recentList
        ui_settings=QSettings()
        self._recentList = ui_settings.value('recent_list', [])

        self._lastSavePath=None
        self._initCreateGrid()
        self._initPEScore()

        self._taskListMdl=TaskListMdl(self._ui.taskList)
        self._taskListMdl.taskToggled.connect(self.taskChecked)
        self._ui.taskList.setModel(self._taskListMdl)
        self._ui.taskList.selectionModel().selectionChanged.connect(self.taskChanged)
        self._ui.runButton.clicked.connect(self.runTask)
        self._taskListMdl.emitAllStates()

        # menu actions
        self._ui.actionNew.triggered.connect(self.new_settings)
        self._ui.actionOpen.triggered.connect(self.open_settings)
        self._ui.actionSave.triggered.connect(self.save_settings)
        self._ui.actionSave_As.triggered.connect(self.save_as_settings)
        self._ui.actionExit.triggered.connect(self.close)

        self._refresh_recentmenu()

    # <editor-fold desc="Common methods">

    def _updatePathLabel(self,attr,ioPath,lbl):
        if ioPath is not None and len(ioPath)>0:
            setattr(self,attr,ioPath)
            lbl.setText(ioPath)
            lbl.setElideMode(Qt.ElideLeft)
        else:
            setattr(self,attr,None)

    def _ioPath(self,attr,lbl,filt,isOpen,isdir=False,label=None):
        initPath = ''
        if getattr(self,attr) is not None:
            initPath = getattr(self,attr)

        if isOpen:
            if label is None:
                label="Select File To Open"
            if not isdir:
                ioPath = QFileDialog.getOpenFileName(self,label,initPath,filt)[0]
            else:
                ioPath = QFileDialog.getExistingDirectory(self,label,initPath)
        else:
            if label is None:
                    label = 'Select File Save Location'
            ioPath = QFileDialog.getSaveFileName(self,label,initPath,filt)[0]

        self._updatePathLabel(attr,ioPath,lbl)
        return ioPath

    def _optToggled(self,enabled,attr):

        getattr(self._ui,attr+'Lbl').setEnabled(enabled)
        getattr(self._ui, attr+'Button').setEnabled(enabled)

    def _remove_from_recentlist(self, path):
        """Remove path from recent menu

        Args:
            path (str): The path to remove.

        """

        try:
            self._recentList.remove(path)
            ui_settings = QSettings()
            ui_settings.setValue('recent_list', self._recentList)
            ui_settings.sync()
            self._refresh_recentmenu()
        except Exception:
            pass

    def _update_recentlist(self, path):
        """Add path to top of open recent menu.

        Args:
            path (str): Path to add to top of open recent menu.

        """

        path = path.replace('\\', '/')
        max_lim = 10
        try:
            self._recentList.remove(path)
        except Exception:
            pass
        self._recentList.insert(0, path)
        if len(self._recentList) > max_lim:
            self._recentList.pop(-1)

        ui_settings = QSettings()
        ui_settings.setValue('recent_list', self._recentList)
        ui_settings.sync()
        self._refresh_recentmenu()

    def _refresh_recentmenu(self):
        """refresh list of most recently opened simulation projects.

        """
        self._ui.menuOpen_Recent.clear()
        self._ui.menuOpen_Recent.setEnabled(False)
        if len(self._recentList) > 0:
            for p in self._recentList:
                self._ui.menuOpen_Recent.addAction(p, self._do_openrecent)
            self._ui.menuOpen_Recent.setEnabled(True)

    @pyqtSlot()
    def _do_openrecent(self):
        """Menu action to call when an Open Recent entry is selected.
        """
        src = self.sender()
        path = src.text()
        try:
            self.statusBar().showMessage(f'Opened "{path}"', 8000)
            self._lastSavePath = path
            self.importSettings(settings.loadSettings(path))
            self._update_recentlist(path)
        except Exception as e:
            QMessageBox.critical(self, 'Open Recent Error', 'The project file "' + path + '" could not be found.',
                                 QMessageBox.Ok)
            self._remove_from_recentlist(path)

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
            self._ui.peInpStack.setCurrentWidget(self._ui.peNoInpPage if enabled else self._ui.peInpPage)
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
            pe_miss=self.peScore_checkmissing(do_cg)
            if len(pe_miss)>0:
                missing.append("PE Score Issues:")
            missing+=['   '+m for m in pe_miss]

        if len(missing)>0:
            missing.insert(0,"The following arguments are missing:")
            QMessageBox.critical(self,'Missing arguments','\n'.join(missing))
            return

        cg_kwargs=None
        pe_kwargs=None
        if do_cg:
            cg_kwargs=self.createGrid_prep()
        if do_pe:
            pe_kwargs=self.peScore_prep(do_cg)

        self.statusBar().showMessage("Executing Tasks...")
        ProgLogDlg(run_urc_tasks, self.display_results if self._ui.resultDispCB.isChecked() else None,
                   fnArgs=(cg_kwargs,pe_kwargs), title="Executing tasks...").exec_()
        self.statusBar().clearMessage()

    def _updateCommonPath(self,pAttr,lbl):
        path = lbl.text()
        if self._outDirPath is not None and os.path.isabs(path):
            common = os.path.commonpath([self._outDirPath,path])
            if path!=os.path.sep:
                rPath= os.path.relpath(path,common)
                lbl.setText(rPath)
                setattr(self,pAttr,rPath)

    @pyqtSlot()
    def new_settings(self):
        self.statusBar().showMessage("Settings set to defaults",8000)
        self.importSettings(settings.defaultSettings())
        self._lastSavePath=None

    @pyqtSlot()
    def open_settings(self):
        path=QFileDialog.getOpenFileName(self,"Open URC Settings",'.','URC Settings File ( *.jurc )')[0]
        if path is not None and len(path)>0:
            self.statusBar().showMessage(f'Opened "{path}"',8000)
            self._lastSavePath=path
            self.importSettings(settings.loadSettings(path))
            self._update_recentlist(path)


    @pyqtSlot()
    def save_settings(self):

        if self._lastSavePath is not None:
            self.statusBar().showMessage(f'Saving "{self._lastSavePath}"',8000)
            settings.saveSettings(self._lastSavePath,self.exportSettings())
            self._update_recentlist(self._lastSavePath)
        else:
            self.save_as_settings()

    @pyqtSlot()
    def save_as_settings(self):

        path = QFileDialog.getSaveFileName(self,"Save URC Settings As:",'.','URC Settings File ( *.jurc )')[0]
        if path is not None and len(path) > 0:
            self._lastSavePath=path
            self.save_settings()

    def display_results(self,workspaces,progDlg):

        progDlg.close()

        if 'pe_workspace' in workspaces:
            peWorkspace=workspaces['pe_workspace']
            if 'raster_dir' in peWorkspace:
                # special case: this is just a directory; collect actual names
                rDir=peWorkspace['raster_dir']

                for collect in ('DA','DS'):
                    subPath=os.path.join(rDir,collect)
                    if os.path.exists(subPath):
                        for p in iglob(os.path.join(subPath,f'{collect}_*.tif')):
                            peWorkspace[os.path.splitext(os.path.basename(p))[0]]=p
                del peWorkspace['raster_dir']

        dlg = ResultDlg(**workspaces,logText=progDlg.logText(),parent=self)
        dlg.exec_()

    def exportSettings(self):

        cgData = {
            'sd_path': self._sdPath,
            'ld_path': self._ldPath,
            'use_sa' : self._ui.saInputCB.isChecked(),
            'sa_path': self._saPath,
            # proj file handled below
            'width': float(self._ui.widthField.text()),
            'height': float(self._ui.heightField.text()),
            'out_dir': self._outDirPath,
            'ld_inds': self._ldOutPath,
            'lg_inds': self._lgOutPath,
            'sd_inds': self._sdOutPath,
            'ud_inds': self._udOutPath,
            'sa_inds': self._saOutPath,
            'clip_path': self._clipPath,
            'do_proj': self._ui.projBox.isChecked(),
            'proj_file': self._projFilePath,
            'proj_source':self._ui.projCombo.currentText()

        }
        try:
            cgData['proj_epsg'] = int(self._ui.epsgField.text())
        except ValueError:
            pass

        peData = {
            'inpath': self._ui.gdbLbl.text(),
            'index_dir': self._ui.indexDirLbl.text(),
            'ld_inds': self._ui.ldIndField.text(),
            'lg_inds': self._ui.lgIndField.text(),
            'sd_inds': self._ui.sdIndField.text(),
            'ud_inds': self._ui.udIndField.text(),
            'sa_inds': self._ui.saIndField.text() if len(self._ui.saIndField.text())>0 else None,
            'out_dir': self._outPath,
            'limit_dads':self._ui.limitDaDsCB.isChecked(),
            'use_only': self._ui.dadsCombo.currentText(),
            'save_sub_rasters': self._ui.rasterDirCB.isChecked(),
            'sub_raster_dir': self._outRasterPath,
            'skip_calcs': self._ui.exitOnRasterCB.isChecked()
        }

        return {
            'active': [self._taskListMdl.stateForRow(r)[1] for r in range(self._taskListMdl.rowCount())],
            'display_results': self._ui.resultDispCB.isChecked(),

            'create_grid': cgData,
            'pe_score': peData,
        }


    def importSettings(self, params):

        for r, a in enumerate(params['active']):
            self._taskListMdl.setStateForRow(r, a)

        self._ui.resultDispCB.setChecked(params['display_results'])

        cgData = params['create_grid']

        self._updatePathLabel('_sdPath', cgData['sd_path'], self._ui.sdInputLbl)
        self._updatePathLabel('_ldPath', cgData['ld_path'], self._ui.ldInputLbl)
        self._ui.saInputCB.setChecked(cgData['use_sa'])
        self._updatePathLabel('_saPath', cgData['sa_path'], self._ui.saInputLbl)
        self._updatePathLabel('_clipPath',cgData['clip_path'],self._ui.clipLyrLbl)

        self._ui.widthField.setText(str(cgData['width']))
        self._ui.heightField.setText(str(cgData['height']))
        self._updatePathLabel('_outDirPath', cgData['out_dir'], self._ui.cgOutDirLbl)
        self._updatePathLabel('_ldOutPath', cgData['ld_inds'], self._ui.ldIndsLbl)
        self._updatePathLabel('_lgOutPath', cgData['lg_inds'], self._ui.lgIndsLbl)
        self._updatePathLabel('_sdOutPath', cgData['sd_inds'], self._ui.sdIndsLbl)
        self._ui.saInputCB.setChecked(cgData.get('use_sa',False))
        self._updatePathLabel('_saOutPath',cgData.get('sa_inds','sa_inds.tif'),self._ui.saIndsLbl)
        self._updatePathLabel('_udOutPath', cgData['ud_inds'], self._ui.udIndsLbl)
        self._updateCommonPath('_ldOutPath', self._ui.ldIndsLbl)
        self._updateCommonPath('_lgOutPath', self._ui.lgIndsLbl)
        self._updateCommonPath('_saOutPath', self._ui.saIndsLbl)
        self._updateCommonPath('_sdOutPath', self._ui.sdIndsLbl)
        self._updateCommonPath('_udOutPath', self._ui.udIndsLbl)

        self._ui.projBox.setChecked(cgData['do_proj']),
        self._ui.projCombo.setCurrentText(cgData['proj_source'])
        # useProjPath = 'proj_file' in cgData
        if 'proj_epsg' in cgData:
            self._ui.epsgField.setText(str(cgData['proj_epsg']))
        else:
            self._ui.epsgField.setText('')

        peData = params['pe_score']

        self._updatePathLabel('_srcPath',peData['inpath'],self._ui.gdbLbl)
        self._updatePathLabel('_indexPath',peData['index_dir'],self._ui.indexDirLbl)
        self._ui.ldIndField.setText(peData['ld_inds'])
        self._ui.lgIndField.setText(peData['lg_inds'])
        self._ui.saIndField.setText(peData.get('sa_inds',''))
        self._ui.sdIndField.setText(peData['sd_inds'])
        self._ui.udIndField.setText(peData['ud_inds'])
        # trick fields into doing validation check
        self._ui.ldIndField.editingFinished.emit()
        self._ui.lgIndField.editingFinished.emit()
        self._ui.saIndField.editingFinished.emit()
        self._ui.sdIndField.editingFinished.emit()
        self._ui.udIndField.editingFinished.emit()

        self._updatePathLabel('_outPath',peData['out_dir'],self._ui.peOutDirLbl)

        self._ui.limitDaDsCB.setChecked(peData['limit_dads'])
        self._ui.dadsCombo.setCurrentText(peData['use_only'])

    # </editor-fold>

    # <editor-fold desc="CreateGrid methods">
    def _initCreateGrid(self):

        self._sdPath = None
        self._ldPath = None
        self._saPath = None
        self._clipPath = None
        self._projFilePath = None
        self._ldOutPath = 'ld_inds.tif'
        self._lgOutPath = 'lg_inds.tif'
        self._sdOutPath = 'sd_inds.tif'
        self._udOutPath = 'ud_inds.tif'
        self._saOutPath = 'sa_inds.tif'
        self._outDirPath = None

        self._ui.widthField.setValidator(QDoubleValidator(self._ui.widthField))
        self._ui.heightField.setValidator(QDoubleValidator(self._ui.heightField))
        self._ui.epsgField.setValidator(QIntValidator(self._ui.epsgField))

        # use explicit connection to avoid issues of double-binding that results
        # from name based auto-connect that results from inheriting from custom dialog
        self._ui.saInputCB.toggled.connect(self._onUseSAToggled)
        self._ui.sdInputButton.clicked.connect(self._on_sdInputButton_clicked)
        self._ui.ldInputButton.clicked.connect(self._on_ldInputButton_clicked)
        self._ui.saInputButton.clicked.connect(self._on_saInputButton_clicked)
        self._ui.clipLyrButton.clicked.connect(self._onClipLyrClicked)
        self._ui.projFileButton.clicked.connect(self._on_projFileButton_clicked)
        self._ui.ldIndsButton.clicked.connect(self._on_ldIndsButton_clicked)
        self._ui.lgIndsButton.clicked.connect(self._on_lgIndsButton_clicked)
        self._ui.saIndsButton.clicked.connect(self._on_saIndsButton_clicked)
        self._ui.sdIndsButton.clicked.connect(self._on_sdIndsButton_clicked)
        self._ui.udIndsButton.clicked.connect(self._on_udIndsButton_clicked)
        self._ui.cgOutDirButton.clicked.connect(self._on_cgOutDir_clicked)

        self._ui.projCombo.currentIndexChanged.connect(self._ui.projStack.setCurrentIndex)
        self._ui.projBox.toggled.connect(self._on_projBox_toggled)

        # use provided labels to ensure frontend is in sync with backend
        overrides = [(self._ldOutPath, self._ui.ldIndsLbl),
                     (self._lgOutPath, self._ui.lgIndsLbl),
                     (self._saOutPath, self._ui.saIndsLbl),
                     (self._sdOutPath, self._ui.sdIndsLbl),
                     (self._udOutPath, self._ui.udIndsLbl), ]
        for p, lbl in overrides:
            lbl.setText(p)

    def createGrid_checkmissing(self):
        fields = [('_sdPath', 'SD Input file'),
                  ('_ldPath', 'LD Input file'),
                  ('_clipPath','Clip Layer file')
                  ]
        if self._ui.saInputCB.isChecked():
            fields.append(('_saPath','SA Input file (option checked)'))

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
        inWorkspace['clip_layer']  = self._clipPath
        if self._ui.saInputCB.isChecked():
            inWorkspace['SA_input_file'] = self._saPath

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
        if self._ui.saInputCB.isChecked():
            outWorkspace['sa'] = self._saOutPath

        return {'workspace':inWorkspace,
                'outWorkspace':outWorkspace,
                'gridWidth':gwidth,
                'gridHeight':gheight,
                'epsg':epsg}


    # wiring
    @pyqtSlot(bool)
    def _onUseSAToggled(self, isChecked):
        self._optToggled(isChecked, 'saInput')
        self._ui.saIndsFrame.setEnabled(isChecked)

    @pyqtSlot()
    def _on_sdInputButton_clicked(self):

        self._ioPath('_sdPath',self._ui.sdInputLbl,'ESRI Shapefile (*.shp)',True,label='Select Structural Domains File')

    @pyqtSlot()
    def _on_ldInputButton_clicked(self):
        self._ioPath('_ldPath', self._ui.ldInputLbl, 'ESRI Shapefile (*.shp)', True, label='Select Lithological Domains File')

    @pyqtSlot()
    def _on_saInputButton_clicked(self):
        self._ioPath('_saPath', self._ui.saInputLbl, 'ESRI Shapefile (*.shp)', True, label='Select Secondary Alteration Domains File')

    @pyqtSlot()
    def _on_projFileButton_clicked(self):
        self._ioPath('_projFilePath', self._ui.projFileLbl, 'Projection File (*.prj)', True,label='Select WKT Projection File')

    @pyqtSlot()
    def _on_ldIndsButton_clicked(self):
        path=self._ioPath('_ldOutPath', self._ui.ldIndsLbl, 'GeoTiff File (*.tif)', False,label='Set LD Index File Destination')
        if path is not None:
            self._updateCommonPath('_ldOutPath', self._ui.ldIndsLbl)

    @pyqtSlot()
    def _on_lgIndsButton_clicked(self):
        path = self._ioPath('_lgOutPath', self._ui.lgIndsLbl, 'GeoTiff File (*.tif)', False,label='Set LG Index File Destination')
        if path is not None:
            self._updateCommonPath('_lgOutPath', self._ui.lgIndsLbl)

    @pyqtSlot()
    def _on_saIndsButton_clicked(self):
        path = self._ioPath('_saOutPath', self._ui.saIndsLbl, 'GeoTiff File (*.tif)', False,label='Set SA Index File Destination')
        if path is not None:
            self._updateCommonPath('_saOutPath', self._ui.saIndsLbl)

    @pyqtSlot()
    def _on_sdIndsButton_clicked(self):
        path = self._ioPath('_sdOutPath', self._ui.sdIndsLbl, 'GeoTiff File (*.tif)', False,label='Set SD Index File Destination')
        if path is not None:
            self._updateCommonPath('_sdOutPath',self._ui.sdIndsLbl)

    @pyqtSlot()
    def _on_udIndsButton_clicked(self):
        path = self._ioPath('_udOutPath', self._ui.udIndsLbl, 'GeoTiff File (*.tif)', False,label='Set UD Index File Destination')
        if path is not None:
            self._updateCommonPath('_udOutPath', self._ui.udIndsLbl)

    @pyqtSlot()
    def _on_cgOutDir_clicked(self):
        path = self._ioPath('_outDirPath', self._ui.cgOutDirLbl, '', True,True,label='Select Outputs Directory')
        if path is not None:
            self._updateCommonPath('_ldOutPath',self._ui.ldIndsLbl)
            self._updateCommonPath('_lgOutPath',self._ui.lgIndsLbl)
            self._updateCommonPath('_saOutPath',self._ui.saIndsLbl)
            self._updateCommonPath('_sdOutPath',self._ui.sdIndsLbl)
            self._updateCommonPath('_udOutPath',self._ui.udIndsLbl)


    @pyqtSlot(bool)
    def _on_projBox_toggled(self, checked):
        # signal isn't propagating properly for the following widgets; update manually
        self._ui.projFileLbl.setEnabled(checked)
        self._ui.projFileButton.setEnabled(checked)

    @pyqtSlot()
    def _onClipLyrClicked(self):
        self._ioPath('_clipPath', self._ui.clipLyrLbl, 'ESRI Shapefile (*.shp)', True,label='Select Polygon-based Clipping Layer')

    # </editor-fold>

    # <editor-fold desc="PE Score">
    def _initPEScore(self):
        self._srcPath = None
        self._indexPath = None
        # self._lgName=None
        # self._ldName=None
        # self._sdName=None
        # self._udName=None
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
        self._ui.peOutDirButton.clicked.connect(self._peOutDirClicked)

        self._ui.limitDaDsCB.toggled.connect(self._onLimitDaDsToggled)
        self._ui.rasterDirCB.toggled.connect(self._onRasterDirToggled)
        self._ui.rasterDirButton.clicked.connect(self._onRasterDirClicked)

    def peScore_checkmissing(self,cgEnabled=False):
        fields = [('_srcPath', '   Source File'),
                  ('_outPath', '   Output Directory')]

        if self._ui.rasterDirCB.isChecked():
            fields.append(('_outRasterPath', '   Intermediate Rasters Directory'))

        if not cgEnabled:
            fields.append(('_indexPath', '   Index Files Directory'))

        missing = []
        for a, n in fields:
            if getattr(self, a) is None:
                missing.append(n)

        if not cgEnabled:
            mInsert = len(missing)

            # at this point all inputs valid
            inWorkspace = REE_Workspace(self._indexPath,
                                        ld_inds=self._ui.ldIndField.text(),
                                        lg_inds=self._ui.lgIndField.text(),
                                        sd_inds=self._ui.sdIndField.text(),
                                        ud_inds=self._ui.udIndField.text(),
                                        )
            if len(self._ui.saIndField.text())>0:
                inWorkspace['sa_inds']=self._ui.saIndField.text()

            if self._indexPath is not None:
                for (k, found) in inWorkspace.TestFilesExist():
                    if not found:
                        missing.append('   ' + inWorkspace[k])

            if len(missing) > mInsert:
                missing.insert(mInsert, 'The following index files are missing')

        return missing

    def peScore_prep(self,cgEnabled=False):

        if not cgEnabled:
            inWorkspace = REE_Workspace(self._indexPath,
                                        ld_inds=self._ui.ldIndField.text(),
                                        lg_inds=self._ui.lgIndField.text(),
                                        sd_inds=self._ui.sdIndField.text(),
                                        ud_inds=self._ui.udIndField.text(),
                                        )
            if len(self._ui.saIndField.text()) > 0:
                inWorkspace['sa_inds'] = self._ui.saIndField.text()
        else:
            # take output fields from create grid and use as inputs for this task
            inWorkspace = REE_Workspace(self._outDirPath,
                                        ld_inds=self._ldOutPath,
                                        lg_inds=self._lgOutPath,
                                        sd_inds=self._sdOutPath,
                                        ud_inds=self._udOutPath,
                                        )
            if self._ui.saInputCB.isChecked():
                inWorkspace['sa_inds']=self._saOutPath

        outputs = REE_Workspace(self._outPath)
        kwargs = {'gdbPath': self._srcPath,
                  'inWorkspace': inWorkspace,
                  'outWorkspace': outputs}

        if self._ui.rasterDirCB.isChecked():
            outputs['raster_dir'] = self._outRasterPath
            if self._ui.exitOnRasterCB.isChecked():
                kwargs['rasters_only'] = True

        if self._ui.limitDaDsCB.isChecked():
            selection = self._ui.dadsCombo.currentText()
            if selection == 'DA':
                kwargs['doDS'] = False
            elif selection == 'DS':
                kwargs['doDA'] = False
            else:
                raise Exception("Undefined filter selection: " + selection)

        # def RunPEScore(gdbPath, inWorkspace, outWorkspace, doDA, doDS, rasters_only, postProg=None):
        return kwargs

    def _testIndexPath(self, inputDir, indName):

        # don't worry about it if there is no input Dir
        if inputDir is None:
            return True
        fullpath = os.path.join(inputDir, indName)
        return os.path.exists(fullpath)

    @pyqtSlot(bool)
    def _onGdbActionTriggered(self, checked):
        self._ioPath('_srcPath', self._ui.gdbLbl, 'FileGDB (*.gdb)', True, True,label='Select File Geodatabase')

    @pyqtSlot(bool)
    def _onSQLActionTriggered(self, checked):
        self._ioPath('_srcPath', self._ui.gdbLbl, 'Spatialite (*.sqlite)', True,label='Select Spatialite Archive')

    @pyqtSlot()
    def _onIndexDirClicked(self):
        self._ioPath('_indexPath', self._ui.indexDirLbl, None, True, True,label='Select Index Files Directory')
        self._ui.ldIndField.editingFinished.emit()
        self._ui.lgIndField.editingFinished.emit()
        self._ui.sdIndField.editingFinished.emit()
        self._ui.saIndField.editingFinished.emit()
        self._ui.udIndField.editingFinished.emit()


    @pyqtSlot()
    def _peOutDirClicked(self):
        self._ioPath('_outPath', self._ui.peOutDirLbl, None, True, True,label='Select Outputs Directory')

    @pyqtSlot()
    def _onRasterDirClicked(self):
        self._ioPath('_outRasterPath', self._ui.rasterDirLbl, None, True, True,'Select Intermediate Rasters Output Directory')

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


    # </editor-fold>
