from PyQt5.QtWidgets import QDialog, QFileDialog
from PyQt5.QtCore import Qt


class RunDlgBase(QDialog):

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