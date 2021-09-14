
import sys
from osgeo import gdal
from ree_pe_score import REE_Workspace,ParseWorkspaceArgs,RunCreatePEGrid

if __name__=='__main__':
    gdal.UseExceptions()

    if len(sys.argv)>1:
        from argparse import ArgumentParser

        prsr = ArgumentParser(description="Construct a PE grid.")
        prsr.add_argument('workspace', type=REE_Workspace, help="The workspace directory.")
        prsr.add_argument('output_dir', type=REE_Workspace, help="Path to the output directory")
        prsr.add_argument('-W', '--gridWidth', type=float, default=1000, help="Width of new grid.")
        prsr.add_argument('-H', '--gridHeight', type=float, default=1000, help='Height of new grid.')
        grp = prsr.add_argument_group("Input files", "Override as needed, Absolute, or relative to workdir.")
        grp.add_argument('--SD_input_file', dest='IN_SD_input_file', type=str, default='SD_input_file.shp',
                         help='Structural Domain input file.')
        grp.add_argument('--LD_input_file', dest='IN_LD_input_file', type=str, default='LD_input_file.shp',
                         help='Lithographic Domain input file.')
        # grp.add_argument('--prj_file', dest='IN_prj_file',type=str, default=None,
        #                   help='Spatial Reference System/Projection for resulting grid.')
        grp = prsr.add_argument_group("Output Filename overrides",
                                      "Override as needed, Absolute, or relative to workdir.")
        grp.add_argument('--ld_raster',type=str,default='ld_inds.tif',dest='OUT_ld',help='Raster containing LD indices')
        grp.add_argument('--lg_raster', type=str, default='lg_inds.tif', dest='OUT_lg',help='Raster containing LG indices')
        grp.add_argument('--sd_raster', type=str, default='sd_inds.tif', dest='OUT_sd',help='Raster containing SD indices')
        grp.add_argument('--ud_raster',type=str,default='ud_inds.tif',dest='OUT_ud',help='Raster containing UD indices')


        args = prsr.parse_args()

        ParseWorkspaceArgs(vars(args), args.workspace, args.output_dir)
        RunCreatePEGrid(args.workspace,args.output_dir,args.gridWidth,args.gridHeight)
    else:
        from PyQt5.QtWidgets import QApplication
        from ree_pe_score.ui_qt.RunGridDlg import RunGridDlg

        app = QApplication(sys.argv)

        runDlg = RunGridDlg()
        # mainWindow.set_devmode(flags.dev_mode)
        runDlg.show()
        sys.exit(app.exec_())