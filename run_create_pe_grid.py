
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
        prsr.add_argument('--prj_file', type=str, default=None,
                          help='Spatial Reference System/Projection for resulting grid.')
        grp = prsr.add_argument_group("Input files", "Override as needed, Absolute, or relative to workdir.")
        grp.add_argument('--SD_input_file', dest='IN_SD_input_file', type=str, default='SD_input_file.shp',
                         help='Structural Domain input file.')
        grp.add_argument('--LD_input_file', dest='IN_LD_input_file', type=str, default='LD_input_file.shp',
                         help='Lithographic Domain input file.')
        grp = prsr.add_argument_group("Optional Output files",
                                      "Optional output of intermediate files. Useful for debugging")
        grp.add_argument('--LG_SD_out_featureclass', dest='OUT_LG_SD_out_featureclass', type=str,
                         help='Name of Joint LG_SD output.')
        grp.add_argument('--grid_LG_SD_LD', dest='OUT_grid_LG_SD_LD', type=str, help='Name of gridded LG_SD_LD output.')
        grp.add_argument('--grid_file', dest='OUT_grid_file', type=str, help='Name of base grid')
        grp.add_argument('--exported_grid_df', dest='OUT_exported_grid_df', type=str, help='Name of exported dataframe')
        grp.add_argument('--PE_Grid_calc', dest='OUT_PE_Grid_calc', type=str, help='Name of PE_calc file')

        args = prsr.parse_args()

        ParseWorkspaceArgs(vars(args), args.workspace, args.output_dir)
        RunCreatePEGrid(args.workspace,args.output_dir,args.gridWidth,args.gridHeight,args.prj_file)
    else:
        ...