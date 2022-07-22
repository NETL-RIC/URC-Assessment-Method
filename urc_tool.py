
import sys
import os
from argparse import ArgumentParser
from osgeo import gdal
from ree_pe_score import REE_Workspace,ParseWorkspaceArgs,RunCreatePEGrid,RunPEScore

def runCreateGridCLI(cli_args):
    prsr = ArgumentParser(prog=' '.join(sys.argv[:2]), description="Construct a PE grid.")
    prsr.add_argument('workspace', type=REE_Workspace, help="The workspace directory.")
    prsr.add_argument('outWorkspace', type=REE_Workspace, help="Path to the output directory")
    prsr.add_argument('-W', '--gridWidth', type=float, default=1000, help="Width of new grid.")
    prsr.add_argument('-H', '--gridHeight', type=float, default=1000, help='Height of new grid.')
    grp = prsr.add_argument_group("Input files", "Override as needed, Absolute, or relative to workdir.")
    grp.add_argument('--SD_input_file', dest='IN_SD_input_file', type=str, default='SD_input_file.shp',
                     help='Structural Domain input file.')
    grp.add_argument('--LD_input_file', dest='IN_LD_input_file', type=str, default='LD_input_file.shp',
                     help='Lithographic Domain input file.')
    grp.add_argument('--prj_file', dest='IN_prj_file', type=str, default=None,
                     help='Spatial Reference System/Projection for resulting grid.')
    grp.add_argument('--prj_epsg', type=int, default=None, help='EPSG Code for custom projection')
    grp = prsr.add_argument_group("Output Filename overrides",
                                  "Override as needed, Absolute, or relative to workdir.")
    grp.add_argument('--ld_raster', type=str, default='ld_inds.tif', dest='OUT_ld', help='Raster containing LD indices')
    grp.add_argument('--lg_raster', type=str, default='lg_inds.tif', dest='OUT_lg', help='Raster containing LG indices')
    grp.add_argument('--sd_raster', type=str, default='sd_inds.tif', dest='OUT_sd', help='Raster containing SD indices')
    grp.add_argument('--ud_raster', type=str, default='ud_inds.tif', dest='OUT_ud', help='Raster containing UD indices')

    args = prsr.parse_args(cli_args)

    ParseWorkspaceArgs(vars(args), args.workspace, args.outWorkspace)
    RunCreatePEGrid(args.workspace, args.outWorkspace, args.gridWidth, args.gridHeight, args.prj_epsg)

def runPEScoreCLI(cli_args):
    prsr = ArgumentParser(prog=' '.join(sys.argv[:2]),description="Calculate the PE score.")
    prsr.add_argument('gdbPath', type=str, help="Path to the GDB file to process.")
    prsr.add_argument('workspace', type=REE_Workspace, help="The workspace directory.")
    prsr.add_argument('output_dir', type=REE_Workspace, help="Path to the output directory.")
    prsr.add_argument('--no_da', dest='use_da', action='store_false', help="Skip DA calculation")
    prsr.add_argument('--no_ds', dest='use_ds', action='store_false', help="Skip DS calculation")
    prsr.add_argument('--ld_raster', type=str, default='ld_inds.tif', dest='IN_ld_inds',
                      help='Raster containing LD indices')
    prsr.add_argument('--lg_raster', type=str, default='lg_inds.tif', dest='IN_lg_inds',
                      help='Raster containing LG indices')
    prsr.add_argument('--sd_raster', type=str, default='sd_inds.tif', dest='IN_sd_inds',
                      help='Raster containing SD indices')
    prsr.add_argument('--ud_raster', type=str, default='ud_inds.tif', dest='IN_ud_inds',
                      help='Raster containing UD indices')
    prsr.add_argument('--raster_dump_dir', type=str, dest='OUT_raster_dir',
                      help="Optional directory to dump layer rasters")
    prsr.add_argument('--exit_on_raster_dump', action='store_true',
                      help="Exit after Rasters have been dumped. has no effect if '--raster_dump_dir' is not provided")
    prsr.add_argument('--clip_layer', type=str, default=None, dest='IN_clip_layer',
                      help="Vector-based layer to use for final clipping prior to fuzzy logic application")

    args = prsr.parse_args(cli_args)

    ParseWorkspaceArgs(vars(args), args.workspace, args.output_dir)
    RunPEScore(args.gdbPath, args.workspace, args.output_dir, args.use_da, args.use_ds, args.exit_on_raster_dump)


if __name__=='__main__':
    gdal.UseExceptions()

    if len(sys.argv)>1:

        prsr = ArgumentParser(description="Run a task from the URC tool.")
        prsr.add_argument('task',type=str,choices=['create_grid','pe_score'],help=f'The task to run; see {os.path.basename(sys.argv[0])} <task> -h for more information')
        prsr.add_argument('ARGS',type=str,nargs='*',help="Task-specific arguments")

        args=prsr.parse_args(sys.argv[1:2])

        if args.task=='create_grid':
            runCreateGridCLI(sys.argv[2:])
        else: # args.task=='pe_score'
            runPEScoreCLI(sys.argv[2:])
    else:
        from PyQt5.QtWidgets import QApplication
        from ree_pe_score.ui_qt.UnifiedWindow import REEToolMainWindow

        app = QApplication(sys.argv)

        mainWindow = REEToolMainWindow()
        mainWindow.show()
        sys.exit(app.exec_())