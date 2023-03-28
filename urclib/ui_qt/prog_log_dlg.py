# This file is part of URC Assessment Method.
#
# URC Assessment Method is free software: you can redistribute it and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# URC Assessment Method is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with URC Assessment Method. If not, see
# <https://www.gnu.org/licenses/>.

"""Dialog and support functions for monitoring the progress of URC analysis"""
import sys
from contextlib import contextmanager
from io import StringIO
from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot, Qt, QObject, QTimer

from ._autoforms.ui_progressdlg import Ui_progLogDlg


@contextmanager
def redirect_print(prog_handler):
    """Context for redirecting print statements to dialog display and progress bar.

    Args:
        prog_handler (ProgHandler): The object capable of displaying messages.

    Yields:
        None: Required for context manager to function.

    """

    class Redirect(object):
        """Private class which manages redirects for stdout."""

        def write(self, msg):
            """Write `msg` to `prog_handler`.

            Args:
                msg (str): The message to write.
            """
            prog_handler.post_log_msg(msg)

        def flush(self):
            """Dummy plug for any flush calls."""
            pass

    old_stdout = sys.stdout
    sys.stdout = Redirect()

    try:
        yield
    finally:
        sys.stdout = old_stdout


class ProgHandler(QObject):
    """Object for managing inter-thread communication.

    Args:
        workfn (function): Method or function to be executed in a separate thread.
        fn_args (tuple): Positional arguments for `workFn`.
        fn_kwargs (dict): Keyword arguments for `workFn`.
        dlg (PyQt5.QtWidgets.QDialog): The parent dialog.

    Attributes:
        cancelled (bool): Flag indicating whether the process should be treated as user cancelled.

    """

    # https://nikolak.com/pyqt-threading-tutorial/

    # custom signal
    logMsg = pyqtSignal(str)
    progress = pyqtSignal(int)
    errMsg = pyqtSignal(Exception)

    # internal class used for cancelling sim
    class _CancelException(Exception):
        """Internal class for notifying a user requested cancellation."""
        pass

    def __init__(self, workfn, fn_args, fn_kwargs, dlg):
        super().__init__()
        self._dowork = workfn
        self._args = fn_args
        self._kwargs = fn_kwargs
        self.cancelled = False
        self._dlg = dlg
        self._thread = None

    # def __del__(self):
    #     # if hasattr(self,'cancelled'):
    #     #     self.logMsg.emit("cancelled")
    #     self.wait()

    def wire_up(self, update_fn, err_fn, progbar_fn, thread):
        """Wire up slots and signals.

        Args:
            update_fn (function): Function/slot to bind to `logMsg` signal.
            err_fn (function): Function/slot to bind to `errMsg` signal.
            progbar_fn (function): Function/slot to bind to `progbar_fn` signal.
            thread (PyQt5.QtCore.QSignal): Thread to bind to `run` method.
        """
        self.logMsg.connect(update_fn)
        self.errMsg.connect(err_fn)
        self.progress.connect(progbar_fn)
        self._thread = thread
        self._thread.started.connect(self.run)

    def _check_interrupt(self):
        """Check to see if a user has requested cancellation.
        Raises:
            SimThread._CancelException: If the simulation was cancelled by a user.
        """

        if self._thread.isInterruptionRequested() and self._markedForExit:
            raise ProgHandler._CancelException()

    def post_log_msg(self, msg):
        """Emit `logMsg` signal and check for thread interrupt.

        Args:
            msg (str): Payload for `logMsg` signal.
        """

        self.logMsg.emit(msg)
        self._check_interrupt()

    def post_progress(self, val):
        """Emit `progress` signal and check for interrupt.

        Args:
            val (int): Payload for `progress` signal; should be in range [0,100].

        """
        self.progress.emit(val)
        self._check_interrupt()

    @pyqtSlot()
    def run(self):
        """Thread execution logic.
        """

        try:
            # configure connections
            self._markedForExit = False
            kwargs = {}
            kwargs.update(self._kwargs)
            # kwargs['printFn']=self.post_log_msg
            kwargs['post_prog'] = self.post_progress

            with redirect_print(self):
                self.results = self._dowork(*self._args, **kwargs)

        except ProgHandler._CancelException:
            # just exit
            self.cancelled = True
            self.post_log_msg("User Cancelled.")

        except Exception as err:

            self.post_log_msg("Error Encountered.")
            self.errMsg.emit(err)
        finally:
            self._thread.exit()

    def mark_for_exit(self):
        """Indicate that the thread is ready to exit at the next interrupt point."""
        self._markedForExit = True
        self._thread.requestInterruption()


#########################################################

class ProgLogDlg(QDialog):
    """Dialog for displaying progress of URC calculations.

    Args:
            fn (function): Method or function to be executed and monitored.
            finish_fn (function): Method or function to call on successful completion.
            prog_count (int,optional): The total number of progress steps expected to be reported. Default is 0.
            fn_args (tuple,optional): Any positional arguments required by `fn`, or `None` if no positional arguments
                are required. Default is `None`.
            fn_kwargs (dict,optional): Any keyword arguments required by `fn`, or `None` if no keyword arguments are
                required. Default is `None`.
            parent (PyQt5.QtWidgets.QWidget,optional): Optional Qt parent widget, or `None`. Default is `None`.
            title (str,optional): The title to display at the top of the dialog. Defaultl is "Progress".
            use_progressbar (bool,optional): If `True` the progress bar is displayed; otherwise, it is hidden.
                Defaults to `False`.
        """

    def __init__(self, fn, finish_fn, prog_count=0, fn_args=None, fn_kwargs=None, parent=None, title="Progress",
                 use_progressbar=False):

        super().__init__(parent)

        # disable "?" button (remove to enable context hint functionality)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        if fn_args is None:
            fn_args = []
        if fn_kwargs is None:
            fn_kwargs = {}

        self._logbuff = StringIO()
        self._ui = Ui_progLogDlg()
        self._ui.setupUi(self)
        self._ui.cancellingLbl.hide()
        self._doFinish = finish_fn
        self._progCount = prog_count
        self.setWindowTitle(title)
        if not use_progressbar:
            self._ui.logProgBar.hide()
        else:
            self._ui.logProgBar.setValue(0)
            self._ui.logProgBar.setMaximum(prog_count)

        # Run function
        self._handler = ProgHandler(fn, fn_args, fn_kwargs, self)
        self._thread = QThread()
        self._handler.moveToThread(self._thread)
        self._handler.wire_up(self._update_log, self._err_msg, self._update_progressbar, self._thread)
        self._ui.buttonBox.rejected.connect(self._on_cancel)

        self._thread.finished.connect(self._run_finish)
        # self._handler.run()
        self._thread.start(QThread.TimeCriticalPriority)

        # use timer to regulate transferring messages from buffer to view.
        # setting text for QDocument can become expensive, and will flood
        # the event loop if left unchecked
        self._msgTimer = QTimer(self)
        self._msgTimer.timeout.connect(self._flush_msgs)
        self._msgTimer.start(500)  # 0.5 second interval

    def _on_cancel(self):
        """Cleanup method which is invoked when the user cancels the process.
        """
        # switch prog bar to indeterminant mode
        self._ui.logProgBar.setMaximum(0)
        self._ui.logProgBar.setMinimum(0)
        self._ui.cancellingLbl.show()
        self._ui.buttonBox.setEnabled(False)
        self._handler.mark_for_exit()
        self._handler.cancelled = True
        self._thread.terminate()
        self._update_log("User Cancelled")

    @pyqtSlot()
    def _flush_msgs(self):
        """Flush any messages awaiting writing to the text display
        """

        if len(self._logbuff.getvalue()) > 0:
            lt_vbar = self._ui.logText.verticalScrollBar()
            is_bottom = lt_vbar.value() == lt_vbar.maximum()

            self._ui.logText.setPlainText(self._ui.logText.toPlainText() + self._logbuff.getvalue())
            self._logbuff.seek(0)
            self._logbuff.truncate(0)

            if is_bottom:
                lt_vbar.setValue(lt_vbar.maximum())

    @pyqtSlot(str)
    def _update_log(self, msg):
        """Write message to a buffer which will be flushed regularly to a display widget.

        Args:
            msg (str): The message to submit to the log.
        """

        # TODO: fix vertical scrolling

        self._logbuff.write(msg)

    @pyqtSlot(int)
    def _update_progressbar(self, prog):
        """Refresh the progress bar.

        Args:
            prog (int): The current progress to display.

        """
        self._ui.logProgBar.setValue(prog)

    @pyqtSlot(Exception)
    def _err_msg(self, ex):
        """Receive a forwarded exception.

        Args:
            ex (Exception): The forwarded exception.

        Raises:
            ex: The forwarded exception (presumably from another thread).
        """
        raise ex

    @pyqtSlot()
    def _run_finish(self):
        """Cleanup details at the conclusion of a process run."""
        self._msgTimer.stop()
        self._flush_msgs()
        if not self._handler.cancelled:
            self._ui.logProgBar.setValue(self._progCount)

            if self._doFinish is not None:
                self._doFinish(self._handler.results, self)

        else:
            self._ui.logProgBar.setMaximum(self._progCount)
            self._ui.logProgBar.setEnabled(False)
        self._ui.buttonBox.setEnabled(False)
        self._ui.cancellingLbl.hide()

        # delete progthread here
        self._thread = None

    def closeEvent(self, event):
        """This is an overload of a method in the `QDialog` class. See the official Qt documentation.

        Args:
            event (PyQt5.QtGui.QCloseEvent): The triggering event.

        See Also:
            [Official Qt Documentation](https://doc.qt.io/qt-5/qdialog.html#closeEvent)
        """
        if self._thread is not None and self._thread.isRunning():
            self._handler.cancelled = True
            self._thread.terminate()
        super().closeEvent(event)

    def log_text(self):
        """Retrieve the text log.

        Returns:
            str: The log recorded during the run.
        """
        return self._ui.logText.toPlainText()
