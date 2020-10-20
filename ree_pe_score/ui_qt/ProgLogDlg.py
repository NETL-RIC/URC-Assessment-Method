import contextlib

from PyQt5.QtWidgets import QDialog, QDialogButtonBox
from PyQt5.QtCore import QThread, pyqtSignal,Qt

from ._autoforms.ui_progressdlg import Ui_progLogDlg

class ProgThread(QThread):
    """
    """

    # internal class used for cancelling sim
    class _CancelException(Exception):
        """Internal class for notifying a user requested cancellation."""
        pass

    # https://nikolak.com/pyqt-threading-tutorial/

    # custom signal
    logMsg = pyqtSignal(str)
    progress = pyqtSignal(int)
    errMsg = pyqtSignal(str)

    # internal class used for cancelling sim
    class _CancelException(Exception):
        """Internal class for notifying a user requested cancellation."""
        pass

    def __init__(self, workFn, fnArgs,fnKwArgs,onfinish,dlg):
        QThread.__init__(self)

        self._dowork = workFn
        self._args = fnArgs
        self._kwargs = fnKwArgs
        self.finished.connect(onfinish)
        self.cancelled = False
        self._dlg=dlg

    def __del__(self):
        # if hasattr(self,'cancelled'):
        #     self.logMsg.emit("cancelled")
        self.wait()

    def _check_interrupt(self):
        """Check to see if a user has requested cancellation.
        Raises:
            SimThread._CancelException: If the simulation was cancelled by a user.
        """

        if self.isInterruptionRequested() and self._markedForExit:
            raise ProgThread._CancelException()
        # QThread.yieldCurrentThread()

    def _PostLogMsg(self,*msgs,sep=' ',end='\n'):
        msgs=sep.join([str(m) for m in msgs])+end
        self.logMsg.emit(msgs)
        self._check_interrupt()

    def _PostProgress(self,val):
        self.progress.emit(val)
        self._check_interrupt()

    def run(self):
        """Thread execution logic.
        """

        try:
            # configure connections
            self._markedForExit = False
            kwargs={}
            kwargs.update(self._kwargs)
            kwargs['printFn']=self._PostLogMsg
            kwargs['postProg']=self._PostProgress

            self.results = self._dowork(*self._args,**kwargs)

        except ProgThread._CancelException:
            # just exit
            self.cancelled=True
            self._PostLogMsg("User Cancelled.")


        except Exception as err:

            self._PostLogMsg("Error Encountered.")
            self.errMsg.emit(err)



    def mark_for_exit(self):
        """Indicate that the thread is ready to exit at the next interrupt point."""
        self._markedForExit = True
        self.requestInterruption()

#########################################################

class ProgLogDlg(QDialog):

    def __init__(self, fn, finishFn,progCount=0,fnArgs=None, fnKwArgs=None, parent=None, title="Progress", useProgBar=False):
        super().__init__(parent)

        if fnArgs is None:
            fnArgs=[]
        if fnKwArgs is None:
            fnKwArgs = {}

        self._ui= Ui_progLogDlg()
        self._ui.setupUi(self)
        self._ui.cancellingLbl.hide()
        self._doFinish = finishFn
        self._progCount = progCount
        self.setWindowTitle(title)
        if not useProgBar:
            self._ui.logProgBar.hide()
        else:
            self._ui.logProgBar.setValue(0)
            self._ui.logProgBar.setMaximum(progCount)

        # Run function
        self._thread = ProgThread(fn,fnArgs,fnKwArgs,self._RunFinish, self)
        self._thread.logMsg.connect(self._updateLog)
        self._thread.errMsg.connect(self._errMsg)
        self._thread.progress.connect(self._updateProgBar)
        self._ui.buttonBox.rejected.connect(self._onCancel)

        self._thread.start(QThread.TimeCriticalPriority)

    def _onCancel(self):

        # switch prog bar to indeterminant mode
        self._ui.logProgBar.setMaximum(0)
        self._ui.logProgBar.setMinimum(0)
        self._ui.cancellingLbl.show()
        self._ui.buttonBox.setEnabled(False)
        self._thread.mark_for_exit()

    def _updateLog(self,msg):

        #TODO: fix vertical scrolling
        ltVbar = self._ui.logText.verticalScrollBar()
        isBottom = ltVbar.value() == ltVbar.maximum()

        self._ui.logText.setPlainText(self._ui.logText.toPlainText()+msg)

        if isBottom:
            ltVbar.setValue(ltVbar.maximum())

    def _updateProgBar(self,prog):
        self._ui.logProgBar.setValue(prog)

    def _errMsg(self,ex):
        raise ex

    def _RunFinish(self):
        if not self._thread.cancelled:
            self._ui.logProgBar.setValue(self._progCount)

            if self._doFinish is not None:
                self._doFinish(self._thread.results,self)

        else:
            self._ui.logProgBar.setMaximum(self._progCount)
            self._ui.logProgBar.setEnabled(False)
        self._ui.buttonBox.setEnabled(False)
        self._ui.cancellingLbl.hide()

