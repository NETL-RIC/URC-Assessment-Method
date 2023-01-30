"""The main window and associated functions for the URC tool GUI."""

import os,sys
from glob import iglob
from PyQt5.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QMenu
from PyQt5.QtGui import QDoubleValidator, QIntValidator, QColor, QPalette
from PyQt5.QtCore import Qt, pyqtSlot, QSettings

from ..create_pe_grid import run_create_pe_grid
from ..calculate_pe_score import run_pe_score
from ..common_utils import UrcWorkspace
from .. import settings
from .prog_log_dlg import ProgLogDlg
from .results_dlg import ResultDlg
from .about_dlg import AboutDlg
from .view_models import TaskListMdl
from ._autoforms.ui_unifiedwindow import Ui_MainWindow


def run_urc_tasks(cg_kwargs, pe_kwargs, post_prog):
    """Execute the assigned tasks.

    Args:
        cg_kwargs (dict or None): Keyword arguments for `run_create_pe_grid()`, or `None` if it isn't to be run.
        pe_kwargs  (dict or None): Keyword arguments for `run_pe_score()`, or `None` if it isn't to be run.
        post_prog (function): Method or function to be called on progress updates.

    Returns:
        dict: Results of requested analyses.
    """

    outfiles = {}
    if cg_kwargs is not None:
        print("~~~~ Running Create Grid... ~~~~")
        run_create_pe_grid(post_prog=post_prog, **cg_kwargs)
        outfiles['cg_workspace'] = cg_kwargs['out_workspace']
    if pe_kwargs is not None:
        print("~~~~ Running PE Score... ~~~~")
        outfiles['pe_workspace'] = run_pe_score(post_prog=post_prog, **pe_kwargs)

    return outfiles


class REEToolMainWindow(QMainWindow):
    """Main Window for the URC tool GUI.

    """

    def __init__(self):
        super().__init__()

        self._ui = Ui_MainWindow()
        self._ui.setupUi(self)

        # cache recentList
        ui_settings = QSettings()
        self._recentList = ui_settings.value('recent_list', [])

        self._lastSavePath = None
        self._init_create_grid()
        self._init_pescore()

        self._taskListMdl = TaskListMdl(self._ui.taskList)
        self._taskListMdl.taskToggled.connect(self.task_checked)
        self._ui.taskList.setModel(self._taskListMdl)
        self._ui.taskList.selectionModel().selectionChanged.connect(self.task_changed)
        self._ui.runButton.clicked.connect(self.run_task)
        self._taskListMdl.emit_all_states()

        # menu actions
        self._ui.actionNew.triggered.connect(self.new_settings)
        self._ui.actionOpen.triggered.connect(self.open_settings)
        self._ui.actionSave.triggered.connect(self.save_settings)
        self._ui.actionSave_As.triggered.connect(self.save_as_settings)
        self._ui.actionExit.triggered.connect(self.close)

        self._ui.actionDocumentation.triggered.connect(self._onShowDocumentation)
        self._ui.actionAbout.triggered.connect(self._showAbout)

        self._refresh_recentmenu()

    # <editor-fold desc="Common methods">

    def _update_path_label(self, attr, io_path, lbl):
        """Update path and displayed dlg_label.
        Args:
            attr (str): The attribute to update with `ioPath`.
            io_path (str or `None`): The new path value; can be `None` if now path is assigned.
            lbl (.ElideLabelWidget.ElideLabelWidget): The dlg_label to update.

        """
        if io_path is not None and len(io_path) > 0:
            setattr(self, attr, io_path)
            lbl.setText(io_path)
            lbl.set_elide_mode(Qt.ElideLeft)
        else:
            setattr(self, attr, None)

    def _io_path(self, attr, lbl, filt, isopen, isdir=False, dlg_label=None):
        """Request new path from user.

        Args:
            attr (str): The attribute of the instance to assign the path to.
            lbl (.ElideLabelWidget.ElideLabelWidget): The Label to be updated with the new path.
            filt (str or None): The file pattern to use in the file dialog's filter. Can be `None` if `isdir` is `True`.
            isopen (bool): If `True`, displays an open dialog; otherwise, it displays a save dialog.
            isdir (bool,optional): If `True`, directories are selected by the dialog; otherwise, files are selected.
                Default is `False`.
            dlg_label (str,optional): The label to apply to the dialog; if `None`, display a generic title. Default is
                `None`.

        Returns:
            str: The selected path.
        """

        init_path = ''
        if getattr(self, attr) is not None:
            init_path = getattr(self, attr)

        if isopen:
            if dlg_label is None:
                dlg_label = "Select File To Open"
            if not isdir:
                io_path = QFileDialog.getOpenFileName(self, dlg_label, init_path, filt)[0]
            else:
                io_path = QFileDialog.getExistingDirectory(self, dlg_label, init_path)
        else:
            if dlg_label is None:
                dlg_label = 'Select File Save Location'
            io_path = QFileDialog.getSaveFileName(self, dlg_label, init_path, filt)[0]

        self._update_path_label(attr, io_path, lbl)
        return io_path

    def _opt_toggled(self, enabled, attr_prefix):
        """Toggle widgets associated with a boolean flag.

        Args:
            enabled (bool): The flag state.
            attr_prefix (str): The prefix for widgets to update.
        """

        getattr(self._ui, attr_prefix + 'Lbl').setEnabled(enabled)
        getattr(self._ui, attr_prefix + 'Button').setEnabled(enabled)

    def _remove_from_recentlist(self, path):
        """Remove path from recent menu.

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
            self.import_settings(settings.load_settings(path))
            self._update_recentlist(path)
        except Exception as e:
            QMessageBox.critical(self, 'Open Recent Error', 'The project file "' + path + '" could not be found.',
                                 QMessageBox.Ok)
            self._remove_from_recentlist(path)

    @pyqtSlot('QItemSelection', 'QItemSelection')
    def task_changed(self, selected, deselected):
        """Slot invoked when the task table selection has changed.

        Args:
            selected (PyQt5.QtCore.QItemSelection): List of indices of newly selected cells.
            deselected (PyQt5.QtCore.QItemSelection): unused

        """

        if len(selected) > 0:
            self._ui.taskStack.setCurrentIndex(selected.indexes()[0].row() + 1)
        else:
            self._ui.taskStack.setCurrentIndex(0)

    @pyqtSlot(int, str, bool)
    def task_checked(self, index, label, enabled):
        """Slot for responding to a task item being checked

        Args:
            index (int): Unused.
            label (str): The label of the table entry.
            enabled (bool): Reflects the state of the checkbox adjacent to the entry in the task table.

        """

        if label == 'Create Grid':
            page = self._ui.createGridPage
            self._ui.peInpStack.setCurrentWidget(self._ui.peNoInpPage if enabled else self._ui.peInpPage)
        else:  # dlg_label == 'PE Score':
            page = self._ui.peScorePage

        page.setEnabled(enabled)

        # update run button
        self._ui.runButton.setEnabled(self._taskListMdl.any_enabled())

    @pyqtSlot()
    def run_task(self):
        """Slot for executing any of the checked tasks.
        """

        do_cg = self._taskListMdl.state_for_row(0)[1]
        do_pe = self._taskListMdl.state_for_row(1)[1]

        missing = []
        if do_cg:
            cg_miss = self.create_grid_checkmissing()
            if len(cg_miss) > 0:
                missing.append("Create Grid Issues:")
            missing += ['   ' + m for m in cg_miss]
        if do_pe:
            pe_miss = self.pescore_checkmissing(do_cg)
            if len(pe_miss) > 0:
                missing.append("PE Score Issues:")
            missing += ['   ' + m for m in pe_miss]

        if len(missing) > 0:
            missing.insert(0, "The following arguments are missing:")
            QMessageBox.critical(self, 'Missing arguments', '\n'.join(missing))
            return

        cg_kwargs = None
        pe_kwargs = None
        if do_cg:
            cg_kwargs = self.create_grid_prep()
        if do_pe:
            pe_kwargs = self.pescore_prep(do_cg)

        self.statusBar().showMessage("Executing Tasks...")
        ProgLogDlg(run_urc_tasks, self.display_results if self._ui.resultDispCB.isChecked() else None,
                   fn_args=(cg_kwargs, pe_kwargs), title="Executing tasks...").exec_()
        self.statusBar().clearMessage()

    def _update_common_path(self, pattr, lbl):
        """Subtract common path from a given path.

        Args:
            pattr (str): The attribute of this object to update with the relative path.
            lbl (.ElideLabelWidget.ElideLabelWidget): The label to extract the path from.
        """

        path = lbl.text()
        if self._outDirPath is not None and os.path.isabs(path):
            common = os.path.commonpath([self._outDirPath, path])
            if path != os.path.sep:
                rpath = os.path.relpath(path, common)
                lbl.setText(rpath)
                setattr(self, pattr, rpath)

    @pyqtSlot()
    def new_settings(self):
        """Set widgets to the defaults."""
        self.statusBar().showMessage("Settings set to defaults", 8000)
        self.import_settings(settings.default_settings())
        self._lastSavePath = None

    @pyqtSlot()
    def open_settings(self):
        """Load settings from a project file."""
        path = QFileDialog.getOpenFileName(self, "Open URC Settings", '.', 'URC Settings File ( *.jurc )')[0]
        if path is not None and len(path) > 0:
            self.statusBar().showMessage(f'Opened "{path}"', 8000)
            self._lastSavePath = path
            self.import_settings(settings.load_settings(path))
            self._update_recentlist(path)

    @pyqtSlot()
    def save_settings(self):
        """Save settings to existing project file, or create a new one if one currently doesn't exist for the project.
        """
        if self._lastSavePath is not None:
            self.statusBar().showMessage(f'Saving "{self._lastSavePath}"', 8000)
            settings.save_settings(self._lastSavePath, self.export_settings())
            self._update_recentlist(self._lastSavePath)
        else:
            self.save_as_settings()

    @pyqtSlot()
    def save_as_settings(self):
        """Create a new file and save settings to it."""
        path = QFileDialog.getSaveFileName(self, "Save URC Settings As:", '.', 'URC Settings File ( *.jurc )')[0]
        if path is not None and len(path) > 0:
            self._lastSavePath = path
            self.save_settings()

    @pyqtSlot()
    def _onShowDocumentation(self, suffix='index.html'):
        import webbrowser as wb

        prefix = os.path.abspath(os.path.curdir).replace('\\', '/')

        if getattr(sys, 'frozen', False):
            fileURL = '/'.join(['file://', prefix, 'user_documentation', suffix])
        else:
            fileURL = '/'.join(['file://', prefix, 'user_doc', 'build', 'html', suffix])
        wb.open(fileURL)

    @pyqtSlot()
    def _showAbout(self):
        dlg = AboutDlg(self)
        dlg.exec_()

    def display_results(self, workspaces, prog_dlg):
        """

        Args:
            workspaces (dict): Collection of ReeWorkspaces which contain paths to the result files.
            prog_dlg (.ProgLogDlg.ProgLogDlg): The progress dialog which was running the analysis.

        """
        prog_dlg.close()

        if 'pe_workspace' in workspaces:
            pe_workspace = workspaces['pe_workspace']
            if 'raster_dir' in pe_workspace:
                # special case: this is just a directory; collect actual names
                rdir = pe_workspace['raster_dir']

                for collect in ('DA', 'DS'):
                    subpath = os.path.join(rdir, collect)
                    if os.path.exists(subpath):
                        for p in iglob(os.path.join(subpath, f'{collect}_*.tif')):
                            pe_workspace[os.path.splitext(os.path.basename(p))[0]] = p
                del pe_workspace['raster_dir']

        dlg = ResultDlg(**workspaces, log_text=prog_dlg.log_text(), parent=self)
        dlg.exec_()

    def export_settings(self):
        """Gather widget values into a dict for export.

        Returns:
            dict: The structured collection of widget values suitable for export.
        """

        cg_data = {
            'sd_path': self._sdPath,
            'ld_path': self._ldPath,
            'use_sa': self._ui.saInputCB.isChecked(),
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
            'do_proj': self._ui.projBox.isChecked(),
            'proj_file': self._projFilePath,
            'proj_source': self._ui.projCombo.currentText()

        }
        try:
            cg_data['proj_epsg'] = int(self._ui.epsgField.text())
        except ValueError:
            pass

        pe_data = {
            'inpath': self._ui.gdbLbl.text(),
            'use_clip': self._ui.clipLyrCB.isChecked(),
            'clip_path': self._clipPath,
            'index_dir': self._ui.indexDirLbl.text(),
            'ld_inds': self._ui.ldIndField.text(),
            'lg_inds': self._ui.lgIndField.text(),
            'sd_inds': self._ui.sdIndField.text(),
            'ud_inds': self._ui.udIndField.text(),
            'sa_inds': self._ui.saIndField.text() if len(self._ui.saIndField.text()) > 0 else None,
            'out_dir': self._outPath,
            'limit_dads': self._ui.limitDaDsCB.isChecked(),
            'use_only': self._ui.dadsCombo.currentText(),
            'save_sub_rasters': self._ui.rasterDirCB.isChecked(),
            'sub_raster_dir': self._outRasterPath,
            'skip_calcs': self._ui.exitOnRasterCB.isChecked()
        }

        return {
            'active': [self._taskListMdl.state_for_row(r)[1] for r in range(self._taskListMdl.rowCount())],
            'display_results': self._ui.resultDispCB.isChecked(),

            'create_grid': cg_data,
            'pe_score': pe_data,
        }

    def import_settings(self, params):
        """Import widget values from a dict.

        Args:
            params (dict): The settings to assign to the tool's widgets.
        """

        for r, a in enumerate(params['active']):
            self._taskListMdl.set_state_for_row(r, a)

        self._ui.resultDispCB.setChecked(params['display_results'])

        cg_data = params['create_grid']

        self._update_path_label('_sdPath', cg_data['sd_path'], self._ui.sdInputLbl)
        self._update_path_label('_ldPath', cg_data['ld_path'], self._ui.ldInputLbl)
        self._ui.saInputCB.setChecked(cg_data['use_sa'])
        self._update_path_label('_saPath', cg_data['sa_path'], self._ui.saInputLbl)

        self._ui.widthField.setText(str(cg_data['width']))
        self._ui.heightField.setText(str(cg_data['height']))
        self._update_path_label('_outDirPath', cg_data['out_dir'], self._ui.cgOutDirLbl)
        self._update_path_label('_ldOutPath', cg_data['ld_inds'], self._ui.ldIndsLbl)
        self._update_path_label('_lgOutPath', cg_data['lg_inds'], self._ui.lgIndsLbl)
        self._update_path_label('_sdOutPath', cg_data['sd_inds'], self._ui.sdIndsLbl)
        self._ui.saInputCB.setChecked(cg_data.get('use_sa', False))
        self._update_path_label('_saOutPath', cg_data.get('sa_inds', 'sa_inds.tif'), self._ui.saIndsLbl)
        self._update_path_label('_udOutPath', cg_data['ud_inds'], self._ui.udIndsLbl)
        self._update_common_path('_ldOutPath', self._ui.ldIndsLbl)
        self._update_common_path('_lgOutPath', self._ui.lgIndsLbl)
        self._update_common_path('_saOutPath', self._ui.saIndsLbl)
        self._update_common_path('_sdOutPath', self._ui.sdIndsLbl)
        self._update_common_path('_udOutPath', self._ui.udIndsLbl)

        self._ui.projBox.setChecked(cg_data['do_proj']),
        self._ui.projCombo.setCurrentText(cg_data['proj_source'])
        # useProjPath = 'proj_file' in cg_data
        if 'proj_epsg' in cg_data:
            self._ui.epsgField.setText(str(cg_data['proj_epsg']))
        else:
            self._ui.epsgField.setText('')

        pe_data = params['pe_score']

        self._update_path_label('_srcPath', pe_data['inpath'], self._ui.gdbLbl)
        self._update_path_label('_indexPath', pe_data['index_dir'], self._ui.indexDirLbl)
        self._ui.ldIndField.setText(pe_data['ld_inds'])
        self._ui.lgIndField.setText(pe_data['lg_inds'])
        self._ui.saIndField.setText(pe_data.get('sa_inds', ''))
        self._ui.sdIndField.setText(pe_data['sd_inds'])
        self._ui.udIndField.setText(pe_data['ud_inds'])
        # trick fields into doing validation check
        self._ui.ldIndField.editingFinished.emit()
        self._ui.lgIndField.editingFinished.emit()
        self._ui.saIndField.editingFinished.emit()
        self._ui.sdIndField.editingFinished.emit()
        self._ui.udIndField.editingFinished.emit()

        self._update_path_label('_outPath', pe_data['out_dir'], self._ui.peOutDirLbl)
        use_clip = pe_data.get('use_clip', False)
        self._ui.clipLyrCB.setChecked(use_clip)
        self._update_path_label('_clipPath', pe_data['clip_path'], self._ui.clipLyrLbl)

        self._ui.limitDaDsCB.setChecked(pe_data['limit_dads'])
        self._ui.dadsCombo.setCurrentText(pe_data['use_only'])

        self._ui.rasterDirCB.setChecked(pe_data['save_sub_rasters'])
        self._update_path_label('_outRasterPath', pe_data['sub_raster_dir'], self._ui.rasterDirLbl)
        self._ui.exitOnRasterCB.setChecked(pe_data['skip_calcs'])

    # </editor-fold>

    # <editor-fold desc="CreateGrid methods">
    def _init_create_grid(self):
        """Initialize widgets for Create Grid pane.
        """

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
        self._ui.saInputCB.toggled.connect(self._on_use_sa_toggled)
        self._ui.sdInputButton.clicked.connect(self._on_sd_inputbutton_clicked)
        self._ui.ldInputButton.clicked.connect(self._on_ld_inputbutton_clicked)
        self._ui.saInputButton.clicked.connect(self._on_sa_inputbutton_clicked)
        self._ui.projFileButton.clicked.connect(self._on_proj_filebutton_clicked)
        self._ui.ldIndsButton.clicked.connect(self._on_ldinds_button_clicked)
        self._ui.lgIndsButton.clicked.connect(self._on_lginds_button_clicked)
        self._ui.saIndsButton.clicked.connect(self._on_sainds_button_clicked)
        self._ui.sdIndsButton.clicked.connect(self._on_sdinds_button_clicked)
        self._ui.udIndsButton.clicked.connect(self._on_udinds_button_clicked)
        self._ui.cgOutDirButton.clicked.connect(self._on_cg_outdir_clicked)

        self._ui.projCombo.currentIndexChanged.connect(self._ui.projStack.setCurrentIndex)
        self._ui.projBox.toggled.connect(self._on_projbox_toggled)

        # use provided labels to ensure frontend is in sync with backend
        overrides = [(self._ldOutPath, self._ui.ldIndsLbl),
                     (self._lgOutPath, self._ui.lgIndsLbl),
                     (self._saOutPath, self._ui.saIndsLbl),
                     (self._sdOutPath, self._ui.sdIndsLbl),
                     (self._udOutPath, self._ui.udIndsLbl), ]
        for p, lbl in overrides:
            lbl.setText(p)

    def create_grid_checkmissing(self):
        """Validates the parameters for create grid prior to execution.

        Returns:
            list: A list of strings representing error messages. If this list is empty, then no required values are
                missing; otherwise, the check has failed.
        """
        fields = [('_sdPath', 'SD Input file'),
                  ('_ldPath', 'LD Input file'),
                  ]
        if self._ui.saInputCB.isChecked():
            fields.append(('_saPath', 'SA Input file (option checked)'))

        missing = []
        for a, n in fields:
            if getattr(self, a) is None:
                missing.append(n)

        try:
            float(self._ui.widthField.text())
        except Exception:
            missing.append('Grid Width')
        try:
            float(self._ui.heightField.text())
        except Exception:
            missing.append('Grid Height')

        if self._outDirPath is None:
            apaths = [p for p in (self._ldOutPath, self._lgOutPath, self._sdOutPath, self._udOutPath) if
                      not os.path.isabs(p)]
            if len(apaths) > 0:
                missing.append(
                    'The following paths are relative; either provide absolute paths, or an output directory:')
                missing.append(', '.join(apaths))

        if self._ui.projBox.isChecked():
            if self._ui.projCombo.currentIndex() == 0 and self._projFilePath is None:
                missing.append('Projection File (is checked and selected).')
            elif self._ui.projCombo.currentIndex() == 1 and len(self._ui.epsgField.text()) == 0:
                missing.append('EPSG (is checked and selected).')

        return missing

    def create_grid_prep(self):
        """Packages arguments for run_create_pe_grid() from the existing widgets.

        Returns:
            dict: Keyword arguments to pass through run_create_pe_grid().
        """
        epsg = None
        gwidth = float(self._ui.widthField.text())
        gheight = float(self._ui.heightField.text())

        in_workspace = UrcWorkspace(self._outDirPath if self._outDirPath is not None else '.')
        in_workspace['SD_input_file'] = self._sdPath
        in_workspace['LD_input_file'] = self._ldPath
        if self._ui.saInputCB.isChecked():
            in_workspace['SA_input_file'] = self._saPath

        if self._ui.projBox.isChecked():
            if self._ui.projCombo.currentIndex() == 0:
                in_workspace['prj_file'] = self._projFilePath
            elif self._ui.projCombo.currentIndex() == 1:
                epsg = int(self._ui.epsgField.text().strip())

        out_workspace = UrcWorkspace(self._outDirPath)
        out_workspace['ld'] = self._ldOutPath
        out_workspace['lg'] = self._lgOutPath
        out_workspace['sd'] = self._sdOutPath
        out_workspace['ud'] = self._udOutPath
        if self._ui.saInputCB.isChecked():
            out_workspace['sa'] = self._saOutPath

        return {'workspace': in_workspace,
                'out_workspace': out_workspace,
                'gridwidth': gwidth,
                'gridheight': gheight,
                'epsg': epsg}

    # wiring
    @pyqtSlot(bool)
    def _on_use_sa_toggled(self, is_checked):
        """Slot for toggling the use of Secondary Alteration inputs.

        Args:
            is_checked (bool): The state of include Secondary Alteration domains.
        """

        self._opt_toggled(is_checked, 'saInput')
        self._ui.saIndsFrame.setEnabled(is_checked)

    @pyqtSlot()
    def _on_sd_inputbutton_clicked(self):
        """User selection of structural domain input file.
        """
        self._io_path('_sdPath', self._ui.sdInputLbl, 'ESRI Shapefile (*.shp)', True,
                      dlg_label='Select Structural Domains File')

    @pyqtSlot()
    def _on_ld_inputbutton_clicked(self):
        """User selection of lithological domain input file.
        """
        self._io_path('_ldPath', self._ui.ldInputLbl, 'ESRI Shapefile (*.shp)', True,
                      dlg_label='Select Lithological Domains File')

    @pyqtSlot()
    def _on_sa_inputbutton_clicked(self):
        """User selection of secondary alteration domain input file.
        """
        self._io_path('_saPath', self._ui.saInputLbl, 'ESRI Shapefile (*.shp)', True,
                      dlg_label='Select Secondary Alteration Domains File')

    @pyqtSlot()
    def _on_proj_filebutton_clicked(self):
        """User selection of projection (*.prj) input file."""
        self._io_path('_projFilePath', self._ui.projFileLbl, 'Projection File (*.prj)', True,
                      dlg_label='Select WKT Projection File')

    @pyqtSlot()
    def _on_ldinds_button_clicked(self):
        """User selection for Lithologic domain index output raster."""
        path = self._io_path('_ldOutPath', self._ui.ldIndsLbl, 'GeoTiff File (*.tif)', False,
                             dlg_label='Set LD Index File Destination')
        if path is not None:
            self._update_common_path('_ldOutPath', self._ui.ldIndsLbl)

    @pyqtSlot()
    def _on_lginds_button_clicked(self):
        """User selection for Local group index output raster."""
        path = self._io_path('_lgOutPath', self._ui.lgIndsLbl, 'GeoTiff File (*.tif)', False,
                             dlg_label='Set LG Index File Destination')
        if path is not None:
            self._update_common_path('_lgOutPath', self._ui.lgIndsLbl)

    @pyqtSlot()
    def _on_sainds_button_clicked(self):
        """User selection for Secondary Alteration domain index output raster."""
        path = self._io_path('_saOutPath', self._ui.saIndsLbl, 'GeoTiff File (*.tif)', False,
                             dlg_label='Set SA Index File Destination')
        if path is not None:
            self._update_common_path('_saOutPath', self._ui.saIndsLbl)

    @pyqtSlot()
    def _on_sdinds_button_clicked(self):
        """User selection for Structural domain index output raster."""
        path = self._io_path('_sdOutPath', self._ui.sdIndsLbl, 'GeoTiff File (*.tif)', False,
                             dlg_label='Set SD Index File Destination')
        if path is not None:
            self._update_common_path('_sdOutPath', self._ui.sdIndsLbl)

    @pyqtSlot()
    def _on_udinds_button_clicked(self):
        """User selection for Unique domain index output raster."""
        path = self._io_path('_udOutPath', self._ui.udIndsLbl, 'GeoTiff File (*.tif)', False,
                             dlg_label='Set UD Index File Destination')
        if path is not None:
            self._update_common_path('_udOutPath', self._ui.udIndsLbl)

    @pyqtSlot()
    def _on_cg_outdir_clicked(self):
        """Update common paths for any existint output index files."""
        path = self._io_path('_outDirPath', self._ui.cgOutDirLbl, '', True, True, dlg_label='Select Outputs Directory')
        if path is not None:
            self._update_common_path('_ldOutPath', self._ui.ldIndsLbl)
            self._update_common_path('_lgOutPath', self._ui.lgIndsLbl)
            self._update_common_path('_saOutPath', self._ui.saIndsLbl)
            self._update_common_path('_sdOutPath', self._ui.sdIndsLbl)
            self._update_common_path('_udOutPath', self._ui.udIndsLbl)

    @pyqtSlot(bool)
    def _on_projbox_toggled(self, checked):
        """Enable or disables the box containing projection selection widgets.

        Args:
            checked (bool): Flag indicating the enabled/disabled state of the widgets used for projection selection.
        """

        # signal isn't propagating properly for the following widgets; update manually
        self._ui.projFileLbl.setEnabled(checked)
        self._ui.projFileButton.setEnabled(checked)

    @pyqtSlot()
    def _on_cliplyr_clicked(self):
        """User selection of a clipping layer to apply to the results of the grid creation."""
        self._io_path('_clipPath', self._ui.clipLyrLbl, 'ESRI Shapefile (*.shp)', True,
                      dlg_label='Select Polygon-based Clipping Layer')

    # </editor-fold>

    # <editor-fold desc="PE Score">
    def _init_pescore(self):
        """Initialize widgets for PE Score pane.
        """

        self._srcPath = None
        self._indexPath = None
        # self._lgName=None
        # self._ldName=None
        # self._sdName=None
        # self._udName=None
        self._outPath = None
        self._outRasterPath = None

        src_menu = QMenu(self._ui.srcToolButton)
        gdb_action = src_menu.addAction(".gdb file")
        sql_action = src_menu.addAction(".sqlite file")

        gdb_action.triggered.connect(self._on_gdb_action_triggered)
        sql_action.triggered.connect(self._on_sql_action_triggered)
        self._ui.srcToolButton.setMenu(src_menu)
        self._ui.inputDirButton.clicked.connect(self._on_indexdir_clicked)
        self._ui.ldIndField.editingFinished.connect(self._on_indexfield_edit_finished)
        self._ui.lgIndField.editingFinished.connect(self._on_indexfield_edit_finished)
        self._ui.sdIndField.editingFinished.connect(self._on_indexfield_edit_finished)
        self._ui.udIndField.editingFinished.connect(self._on_indexfield_edit_finished)
        self._ui.clipLyrCB.toggled.connect(self._on_cliplyr_toggled)
        self._ui.clipLyrButton.clicked.connect(self._on_cliplyr_clicked)
        self._ui.peOutDirButton.clicked.connect(self._pe_outdir_clicked)

        self._ui.limitDaDsCB.toggled.connect(self._on_limit_da_ds_toggled)
        self._ui.rasterDirCB.toggled.connect(self._on_rasterdir_toggled)
        self._ui.rasterDirButton.clicked.connect(self._on_rasterdir_clicked)

    def pescore_checkmissing(self, cg_enabled=False):
        """Validates the parameters for pe score prior to execution.

        Returns:
            list: A list of strings representing error messages. If this list is empty, then no required values are
                missing; otherwise, the check has failed.
        """

        fields = [('_srcPath', '   Source File'),
                  ('_outPath', '   Output Directory')]

        if self._ui.clipLyrCB.isChecked():
            fields.append(('_clipPath', '   Clip Layer File'))

        if self._ui.rasterDirCB.isChecked():
            fields.append(('_outRasterPath', '   Intermediate Rasters Directory'))

        if not cg_enabled:
            fields.append(('_indexPath', '   Index Files Directory'))

        missing = []
        for a, n in fields:
            if getattr(self, a) is None:
                missing.append(n)

        if not cg_enabled:
            minsert = len(missing)

            # at this point all inputs valid
            in_workspace = UrcWorkspace(self._indexPath,
                                        ld_inds=self._ui.ldIndField.text(),
                                        lg_inds=self._ui.lgIndField.text(),
                                        sd_inds=self._ui.sdIndField.text(),
                                        ud_inds=self._ui.udIndField.text(),
                                        )
            if len(self._ui.saIndField.text()) > 0:
                in_workspace['sa_inds'] = self._ui.saIndField.text()

            if self._indexPath is not None:
                for (k, found) in in_workspace.test_files_exist():
                    if not found:
                        missing.append('   ' + in_workspace[k])

            if len(missing) > minsert:
                missing.insert(minsert, 'The following index files are missing')

        return missing

    def pescore_prep(self, cg_enabled=False):
        """Packages arguments for run_pe_score() from the existing widgets.

        Args:
            cg_enabled (bool,optional) Whether or not Create Grid is also configured to run; defaults to `False`.
        Returns:
            dict: Keyword arguments to pass through run_pe_score().
        """
        if not cg_enabled:
            in_workspace = UrcWorkspace(self._indexPath,
                                        ld_inds=self._ui.ldIndField.text(),
                                        lg_inds=self._ui.lgIndField.text(),
                                        sd_inds=self._ui.sdIndField.text(),
                                        ud_inds=self._ui.udIndField.text(),
                                        )
            if len(self._ui.saIndField.text()) > 0:
                in_workspace['sa_inds'] = self._ui.saIndField.text()
        else:
            # take output fields from create grid and use as inputs for this task
            in_workspace = UrcWorkspace(self._outDirPath,
                                        ld_inds=self._ldOutPath,
                                        lg_inds=self._lgOutPath,
                                        sd_inds=self._sdOutPath,
                                        ud_inds=self._udOutPath,
                                        )
            if self._ui.saInputCB.isChecked():
                in_workspace['sa_inds'] = self._saOutPath

        if self._ui.clipLyrCB.isChecked():
            in_workspace['clip_layer'] = self._clipPath

        outputs = UrcWorkspace(self._outPath)
        kwargs = {'gdb_path': self._srcPath,
                  'in_workspace': in_workspace,
                  'out_workspace': outputs}

        if self._ui.rasterDirCB.isChecked():
            outputs['raster_dir'] = self._outRasterPath
            if self._ui.exitOnRasterCB.isChecked():
                kwargs['rasters_only'] = True

        if self._ui.limitDaDsCB.isChecked():
            selection = self._ui.dadsCombo.currentText()
            if selection == 'DA':
                kwargs['do_ds'] = False
            elif selection == 'DS':
                kwargs['do_da'] = False
            else:
                raise Exception("Undefined filter selection: " + selection)

        # def run_pe_score(gdb_path, inworkspace, out_workspace, do_da, do_ds, rasters_only, post_prog=None):
        return kwargs

    def _testindex_path(self, input_dir, ind_name):
        """Test to see if an index file exists at the input directory location.

        Args:
            input_dir (str): Path to the parent directory of the file.
            ind_name (str): Name of the file to query about.

        Returns:
            bool: `True` if the file exists; `False` otherwise.
        """

        # don't worry about it if there is no input Dir
        if input_dir is None:
            return True
        fullpath = os.path.join(input_dir, ind_name)
        return os.path.exists(fullpath)

    @pyqtSlot(bool)
    def _on_gdb_action_triggered(self, checked):
        """User selection of a GDB directory for input.

        Args:
            checked (bool): Unused.
        """
        self._io_path('_srcPath', self._ui.gdbLbl, 'FileGDB (*.gdb)', True, True, dlg_label='Select File Geodatabase')

    @pyqtSlot(bool)
    def _on_sql_action_triggered(self, checked):
        """User selection of a SQLite file for input.

        Args:
            checked (bool): Unused.
        """
        self._io_path('_srcPath', self._ui.gdbLbl, 'Spatialite (*.sqlite)', True, dlg_label='Select Spatialite Archive')

    @pyqtSlot()
    def _on_indexdir_clicked(self):
        """User selection of an input directory for input.
        """
        self._io_path('_indexPath', self._ui.indexDirLbl, None, True, True, dlg_label='Select Index Files Directory')
        self._ui.ldIndField.editingFinished.emit()
        self._ui.lgIndField.editingFinished.emit()
        self._ui.sdIndField.editingFinished.emit()
        self._ui.saIndField.editingFinished.emit()
        self._ui.udIndField.editingFinished.emit()

    @pyqtSlot()
    def _pe_outdir_clicked(self):
        """User selection of a directory for output files."""
        self._io_path('_outPath', self._ui.peOutDirLbl, None, True, True, dlg_label='Select Outputs Directory')

    @pyqtSlot()
    def _on_rasterdir_clicked(self):
        """User selection of a directory for saving intermediate raster files."""
        self._io_path('_outRasterPath', self._ui.rasterDirLbl, None, True, True,
                      'Select Intermediate Rasters Output Directory')

    @pyqtSlot(bool)
    def _on_limit_da_ds_toggled(self, is_checked):
        """Toggle to limit calculations to _only_ DA or _only_ DS.

        Args:
            is_checked (bool): If `True` then calculations will be limited to either DA or DS; otherwise, both will be
                calculated.
        """

        self._ui.dadsCombo.setEnabled(is_checked)

    @pyqtSlot(bool)
    def _on_rasterdir_toggled(self, is_checked):
        """Toggle for saving intermediate rasters.

        Args:
            is_checked (bool): If `True` intermediate rasters will be saved; otherwise, they will be omitted.
        """

        self._opt_toggled(is_checked, 'rasterDir')
        self._ui.exitOnRasterCB.setEnabled(is_checked)

    @pyqtSlot()
    def _on_indexfield_edit_finished(self):
        """Check to see if the file name exists in the input directory. If not, paint the text red."""
        field = self.sender()
        found = self._testindex_path(self._indexPath, field.text())

        txt_color = self.palette().color(QPalette.Active, QPalette.Text)
        fld_pal = field.palette()
        if not found:
            txt_color = QColor('red')
        fld_pal.setColor(QPalette.Active, QPalette.Text, txt_color)
        field.setPalette(fld_pal)

    @pyqtSlot(bool)
    def _on_cliplyr_toggled(self, checked):
        """Enables or disables the inclusion of a clipping layer.

        Args:
            checked (bool): Include a clip layer if checked; otherwise, omit the clip layer.

        """
        self._opt_toggled(checked, 'clipLyr')

    # </editor-fold>
