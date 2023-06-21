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

"""Launching script for URC tool. Run with -h to see options.

"""

import sys
import os
import platform
from argparse import ArgumentParser

from osgeo import gdal
from urclib.common_utils import UrcWorkspace, parse_workspace_args
from urclib.create_pe_grid import run_create_pe_grid
from urclib.calculate_pe_score import run_pe_score

def run_creategrid_cli(cli_args):
    """Run CreateGrid task as a command line process.

    Args:
        cli_args (list): List of strings representing arguments passed from the command line. Content is typically
            subset of sys.argv.
    """

    prsr = ArgumentParser(prog=' '.join(sys.argv[:2]), description="Construct a PE grid.")
    prsr.add_argument('workspace', type=UrcWorkspace, help="The workspace directory.")
    prsr.add_argument('out_workspace', type=UrcWorkspace, help="Path to the output directory")
    prsr.add_argument('-W', '--gridwidth', type=float, default=1000, help="Width of new grid.")
    prsr.add_argument('-H', '--gridheight', type=float, default=1000, help='Height of new grid.')
    grp = prsr.add_argument_group("Input files", "Override as needed, Absolute, or relative to workdir.")
    grp.add_argument('--SD_input_file', dest='IN_SD_input_file', type=str, default='SD_input_file.shp',
                     help='Structural Domain input file.')
    grp.add_argument('--LD_input_file', dest='IN_LD_input_file', type=str, default='LD_input_file.shp',
                     help='Lithographic Domain input file.')
    grp.add_argument('--SA_input_file', dest='IN_SA_input_file', type=str,
                     help='Optional Secondary Alteration Domain input file.')
    muxgrp = grp.add_mutually_exclusive_group()
    muxgrp.add_argument('--prj_file', dest='IN_prj_file', type=str, default=None,
                       help='Spatial Reference System/Projection for resulting grid.')
    muxgrp.add_argument('--prj_epsg', type=int, default=None, help='EPSG Code for custom projection')

    grp = prsr.add_argument_group("Output Filename overrides",
                                  "Override as needed, Absolute, or relative to workdir.")
    grp.add_argument('--ld_raster', type=str, default='ld_inds.tif', dest='OUT_ld', help='Raster containing LD indices')
    grp.add_argument('--lg_raster', type=str, default='lg_inds.tif', dest='OUT_lg', help='Raster containing LG indices')
    grp.add_argument('--sd_raster', type=str, default='sd_inds.tif', dest='OUT_sd', help='Raster containing SD indices')
    grp.add_argument('--ud_raster', type=str, default='ud_inds.tif', dest='OUT_ud', help='Raster containing UD indices')
    grp.add_argument('--sa_raster', type=str, default='sa_inds.tif', dest='OUT_sa', help='Raster containing SA indices')

    args = prsr.parse_args(cli_args)

    parse_workspace_args(vars(args), args.workspace, args.outWorkspace)
    run_create_pe_grid(args.workspace, args.outWorkspace, args.gridWidth, args.gridHeight, args.prj_epsg)


def run_pescore_cli(cli_args):
    """Run PE Score task as a command line process.

    Args:
        cli_args (list): List of strings representing arguments passed from the command line. Content is typically
            subset of sys.argv.
    """

    prsr = ArgumentParser(prog=' '.join(sys.argv[:2]), description="Calculate the PE score.")
    prsr.add_argument('gdb_path', type=str, help="Path to the GDB file to process.")
    prsr.add_argument('workspace', type=UrcWorkspace, help="The workspace directory.")
    prsr.add_argument('output_dir', type=UrcWorkspace, help="Path to the output directory.")
    prsr.add_argument('--clip_layer', type=str, dest='IN_clip_layer',
                      help="Vector-based layer to use for final clipping")
    muxgrp = prsr.add_mutually_exclusive_group()
    muxgrp.add_argument('--no_da', dest='use_da', action='store_false', help="Skip DA calculation")
    muxgrp.add_argument('--no_ds', dest='use_ds', action='store_false', help="Skip DS calculation")
    prsr.add_argument('--ld_raster', type=str, default='ld_inds.tif', dest='IN_ld_inds',
                      help='Raster containing LD indices')
    prsr.add_argument('--lg_raster', type=str, default='lg_inds.tif', dest='IN_lg_inds',
                      help='Raster containing LG indices')
    prsr.add_argument('--sd_raster', type=str, default='sd_inds.tif', dest='IN_sd_inds',
                      help='Raster containing SD indices')
    prsr.add_argument('--ud_raster', type=str, default='ud_inds.tif', dest='IN_ud_inds',
                      help='Raster containing UD indices')
    prsr.add_argument('--sa_raster', type=str, default='sa_inds.tif', dest='IN_sa_inds',
                      help='Optional Raster containing SA indices')
    prsr.add_argument('--raster_dump_dir', type=str, dest='OUT_raster_dir',
                      help="Optional directory to dump layer rasters")
    prsr.add_argument('--exit_on_raster_dump', action='store_true',
                      help="Exit after Rasters have been dumped. has no effect if '--raster_dump_dir' is not provided")

    args = prsr.parse_args(cli_args)

    parse_workspace_args(vars(args), args.workspace, args.output_dir)
    run_pe_score(args.gdbPath, args.workspace, args.output_dir, args.use_da, args.use_ds, args.exit_on_raster_dump)


if __name__ == '__main__':
    from multiprocessing import freeze_support
    freeze_support()
    gdal.UseExceptions()

    # disable gdal warning log

    if len(sys.argv) > 1:
        print("!!!!! args:",sys.argv)
        prsr = ArgumentParser(description="Run a task from the URC tool.")
        prsr.add_argument('task', type=str, choices=['create_grid', 'pe_score'],
                          help=f'The task to run; see {os.path.basename(sys.argv[0])} <task> -h for more information')
        prsr.add_argument('ARGS', type=str, nargs='*', help="Task-specific arguments")

        args = prsr.parse_args(sys.argv[1:2])

        if args.task == 'create_grid':
            run_creategrid_cli(sys.argv[2:])
        else:  # args.task=='pe_score'
            run_pescore_cli(sys.argv[2:])
    else:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtGui import QIcon
        from PyQt5.QtCore import Qt
        from urclib.ui_qt.unified_window import REEToolMainWindow
        import ctypes

        if getattr(sys, 'frozen', False):
            iconPath = os.path.join(sys._MEIPASS, 'resources', 'urc_icon.png')
            gdalPath = os.path.join(sys._MEIPASS, 'Library', 'share', 'gdal')
            projPath = os.path.join(sys._MEIPASS, 'Library', 'share', 'proj')
            if os.path.isdir(gdalPath):
                os.environ['GDAL_DATA'] = gdalPath
            if os.path.isdir(projPath):
                os.environ['PROJ_LIB'] = projPath
        else:
            iconPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'urc_icon.png')

        app = QApplication(sys.argv)
        app.setOrganizationName('NETL')
        app.setOrganizationDomain('doe.gov')
        app.setApplicationName('urc')
        app.setAttribute(Qt.AA_DisableWindowContextHelpButton)
        logo = QIcon(iconPath)
        app.setWindowIcon(logo)

        if platform.system() == 'Windows':
            # set task id so taskbar will work. (windows-specific)
            # https://stackoverflow.com/questions/1551605/how-to-set-applications-taskbar-icon-in-windows-7/1552105#1552105
            urc_app_id = u'gov.netl.ric.urc'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(urc_app_id)


        mainWindow = REEToolMainWindow()
        mainWindow.show()


        def excepthook(exc_type, exc_value, exc_tb):
            """Exception hook/override for GUI.

            Args:
                exc_type: The type of the exception raised.
                exc_value: The value of the exception raised.
                exc_tb: Traceback to the point at which `raise` was called.
            """

            from PyQt5.QtWidgets import QMessageBox
            import traceback
            tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))

            print("error encountered:", tb, sep='\n')
            mb = QMessageBox(QMessageBox.Critical, "Error enountered",
                             'An error was encountered, and this tool must exit.'
                             '\nClick "Show Details..." for more information.',
                             QMessageBox.Ok, mainWindow)
            mb.setDetailedText(tb)
            mb.exec_()
            QApplication.quit()


        sys.excepthook = excepthook
        sys.exit(app.exec_())
