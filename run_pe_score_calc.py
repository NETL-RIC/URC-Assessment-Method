import sys
from ree_pe_score import REE_Workspace,ParseWorkspaceArgs,RunPEScoreCalc
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
        prsr.add_argument('--target_data',type=str,default='DA',choices=['DA','DS'],help="target prefix associated with data to target")
        prsr.add_argument('--input_grid',type=str, dest='IN_PE_Grid_file',default='PE_Grid_file',help="The grid file created from 'Create_PE_Grid.py'.")
        prsr.add_argument('--final_grid', type=str, dest='OUT_final_grid',default='PE_Grid_Calc.sqlite', help="The name of the output file.")
        prsr.add_argument('--step1_performance_csv', type=str, dest='OUT_step1_performance',help="Optional output of step 1 processing times.")
        prsr.add_argument('--step1_grid', type=str, dest='OUT_step1_grid',help="Optional output of step 1 grid.")
        prsr.add_argument('--step3_dataframe_csv', type=str, dest='OUT_step3_dataframe',help="Optional output of combined Dataframes from step 3.")
        prsr.add_argument('--pe_calc_dataframe_csv', type=str, dest='OUT_pe_calc_dataframe',help="Optional output of final Pandas dataframe.")

        args = prsr.parse_args()

        ParseWorkspaceArgs(vars(args),args.workspace,args.output_dir)
        RunPEScoreCalc(args.gdbPath,args.target_data,args.workspace,args.output_dir)
    else:
        from PyQt5.QtWidgets import QApplication
        from ree_pe_score.ui_qt.RunPEDlg import RunPEDlg
        app = QApplication(sys.argv)

        runDlg = RunPEDlg()
        # mainWindow.set_devmode(flags.dev_mode)
        runDlg.show()
        sys.exit(app.exec_())