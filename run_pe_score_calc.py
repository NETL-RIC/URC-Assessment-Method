import sys
from ree_pe_score import REE_Workspace,ParseWorkspaceArgs,RunPEScore
from osgeo import gdal

if __name__=='__main__':
    from multiprocessing import freeze_support
    freeze_support()
    gdal.UseExceptions()

    if len(sys.argv)>1:
        from argparse import ArgumentParser

        prsr = ArgumentParser(description="Calculate the PE score.")
        prsr.add_argument('gdbPath',type=str,help="Path to the GDB file to process.")
        prsr.add_argument('workspace',type=REE_Workspace,help="The workspace directory.")
        prsr.add_argument('output_dir',type=REE_Workspace,help="Path to the output directory.")
        prsr.add_argument('--no_da', dest='use_da', action='store_false', help="Skip DA calculation")
        prsr.add_argument('--no_ds', dest='use_ds', action='store_false', help="Skip DS calculation")
        prsr.add_argument('--ld_raster',type=str,default='ld_inds.tif',dest='IN_ld_inds',help='Raster containing LD indices')
        prsr.add_argument('--lg_raster', type=str, default='lg_inds.tif', dest='IN_lg_inds',help='Raster containing LG indices')
        prsr.add_argument('--sd_raster', type=str, default='sd_inds.tif', dest='IN_sd_inds',help='Raster containing SD indices')
        prsr.add_argument('--ud_raster',type=str,default='ud_inds.tif',dest='IN_ud_inds',help='Raster containing UD indices')
        prsr.add_argument('--raster_dump_dir',type=str,dest='OUT_raster_dir',help="Optional directory to dump layer rasters")
        prsr.add_argument('--exit_on_raster_dump',action='store_true',help="Exit after Rasters have been dumped. has no effect if '--raster_dump_dir' is not provided")
        prsr.add_argument('--clip_layer',type=str,default=None,dest='IN_clip_layer',help="Vector-based layer to use for final clipping prior to fuzzy logic application")
        # prsr.add_argument('--step1_performance_csv', type=str, dest='OUT_step1_performance',help="Optional output of step 1 processing times.")
        # prsr.add_argument('--step1_grid', type=str, dest='OUT_step1_grid',help="Optional output of step 1 grid.")
        # prsr.add_argument('--step3_dataframe_csv', type=str, dest='OUT_step3_dataframe',help="Optional output of combined Dataframes from step 3.")
        # prsr.add_argument('--pe_calc_dataframe_csv', type=str, dest='OUT_pe_calc_dataframe',help="Optional output of final Pandas dataframe.")

        args = prsr.parse_args()

        ParseWorkspaceArgs(vars(args),args.workspace,args.output_dir)
        RunPEScore(args.gdbPath,args.workspace,args.output_dir,args.use_da,args.use_ds,args.exit_on_raster_dump)
    else:
        from PyQt5.QtWidgets import QApplication
        from ree_pe_score.ui_qt.RunPEDlg import RunPEDlg
        app = QApplication(sys.argv)

        runDlg = RunPEDlg()
        # mainWindow.set_devmode(flags.dev_mode)
        runDlg.show()
        sys.exit(app.exec_())