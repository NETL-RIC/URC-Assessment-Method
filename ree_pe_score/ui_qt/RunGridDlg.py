import os
from PyQt5.QtWidgets import QDialog,QMessageBox,QFileDialog
from PyQt5.QtCore import Qt,pyqtSlot
from PyQt5.QtGui import QDoubleValidator

from .RunDlgBase import RunDlgBase
from ._autoforms.ui_rungriddlg import Ui_CreateGridDlg
from .ProgLogDlg import ProgLogDlg
from ..create_pe_grid import RunCreatePEGrid
from ..common_utils import REE_Workspace

class RunGridDlg(RunDlgBase):

    def __init__(self,parent=None):
        super().__init__(parent)

        self._ui = Ui_CreateGridDlg()
        self._ui.setupUi(self)

        self._sdPath = None
        self._ldPath = None
        self._clipPath = None
        self._ldOutPath = 'ld_inds.tif'
        self._lgOutPath = 'lg_inds.tif'
        self._sdOutPath = 'sd_inds.tif'
        self._udOutPath = 'ud_inds.tif'
        self._outDirPath = None


        self._ui.widthField.setValidator(QDoubleValidator(self._ui.widthField))
        self._ui.heightField.setValidator(QDoubleValidator(self._ui.heightField))

        # use explicit connection to avoid issues of double-binding that results
        # from name based auto-connect that results from inheriting from custom dialog
        self._ui.sdInputButton.clicked.connect(self._on_sdInputButton_clicked)
        self._ui.ldInputButton.clicked.connect(self._on_ldInputButton_clicked)
        self._ui.clipLayerCB.toggled.connect(self._clipGeomToggled)
        self._ui.clipLayerButton.clicked.connect(self._on_clipLayerButton_clicked)
        self._ui.ldIndsButton.clicked.connect(self._on_ldIndsButton_clicked)
        self._ui.lgIndsButton.clicked.connect(self._on_lgIndsButton_clicked)
        self._ui.sdIndsButton.clicked.connect(self._on_sdIndsButton_clicked)
        self._ui.udIndsButton.clicked.connect(self._on_udIndsButton_clicked)
        self._ui.outDirButton.clicked.connect(self._on_outputDir_clicked)

        # use provided labels to ensure frontend is in sync with backend
        overrides=[(self._ldOutPath,self._ui.ldIndsLbl),
                   (self._lgOutPath,self._ui.lgIndsLbl),
                   (self._sdOutPath,self._ui.sdIndsLbl),
                   (self._udOutPath,self._ui.udIndsLbl),]
        for p,lbl in overrides:
            lbl.setText(p)

    def accept(self):

        fields = [('_sdPath', 'SD Input file'),
                  ('_ldPath', 'LD Input file'),
                  ]

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

        if self._ui.clipLayerCB.isChecked() and self._clipPath is None:
            missing.append('Clip Layer (is checked).')

        if len(missing) > 0:
            missing.insert(0, 'The following fields are required:')
            QMessageBox.critical(self, 'Missing arguments', '\n'.join(missing))
            return

        if self._outDirPath is None:
            aPaths=[p for p in (self._ldOutPath,self._lgOutPath,self._sdOutPath,self._udOutPath) if not os.path.isabs(p)]
            if len(aPaths)>0:
                aPaths.insert(0, 'The following paths are relative; either provide absolute paths, or an output directory:')
                QMessageBox.critical(self, 'Pathing mismatch', '\n'.join(aPaths))
                return

        inWorkspace= REE_Workspace(self._outDirPath if self._outDirPath is not None else '.')
        inWorkspace['SD_input_file'] = self._sdPath
        inWorkspace['LD_input_file'] = self._ldPath

        if self._ui.clipLayerCB.isChecked():
            inWorkspace['clip_geom'] = self._clipPath

        outWorkspace = REE_Workspace(self._outDirPath)
        outWorkspace['ld'] = self._ldOutPath
        outWorkspace['lg'] = self._lgOutPath
        outWorkspace['sd'] = self._sdOutPath
        outWorkspace['ud'] = self._udOutPath

        super().accept()
        ProgLogDlg(RunCreatePEGrid,None,fnArgs=(inWorkspace,outWorkspace,gwidth,gheight),title='Creating Grid...').show()


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

    @pyqtSlot(bool)
    def _clipGeomToggled(self,checked):
        self._optToggled(checked,'clipLayer')

    @pyqtSlot()
    def _on_clipLayerButton_clicked(self):
        self._ioPath('_clipPath', self._ui.clipLayerLbl, 'ESRI Shapefile (*.shp)', True)

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
    def _on_outputDir_clicked(self):
        path = self._ioPath('_outDirPath', self._ui.outputDirLbl, '', True,True)
        if path is not None:
            self._updateCommonPath('_ldOutPath',self._ui.ldIndsLbl)
            self._updateCommonPath('_lgOutPath',self._ui.lgIndsLbl)
            self._updateCommonPath('_sdOutPath',self._ui.sdIndsLbl)
            self._updateCommonPath('_udOutPath',self._ui.udIndsLbl)