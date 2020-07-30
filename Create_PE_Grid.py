
import os

from osgeo import ogr,gdal
import pandas as pd
from common_utils import *

# alias the print function so we can override in different cases
cpg_print=print

def IndexCalc(domainType, domain_shp):
    """
    Calculates index field for an STA domain type.

    Parameters
    ----------
    domainType: <str>
        Name of the domain type.  Only the following two-letter strings should be used:
        'LD' (lithologic domain)
        'SD' (structural domain)
        'SA' (secondary alteration)

    domain_shp: <gdal.Dataset>
        Dataset containing the featues to index.
        Example 1: domain_shp = r"P:\02_DataWorking\REE\Central_App\Structural_domains\SD_CAB.shp"
        Example 2: domain_shp = workspace_dir + "/" + "SD_CAB_2_copy.shp"

    Returns
    -------
    domain_output_file: <file>
        A copy of the input file with a new field for the domain index.
        *IMPORTANT*: This file will be saved to the same directory as domain_shp.
    """

    domain_output_file = os.path.splitext(domain_shp.GetFileList()[0])[0] + "_indexed.shp"

    drvr = gdal.GetDriverByName("ESRI Shapefile")
    DeleteFile(domain_output_file,cpg_print)
    outputDS = drvr.Create(domain_output_file, 0, 0, 0, gdal.GDT_Unknown)

    outputDS.CopyLayer(domain_shp.GetLayer(0),domain_shp.GetLayer(0).GetName())
    outLyr = outputDS.GetLayer(0)

    # Add to output file a new field for the index
    newLbl = domainType + '_index'
    newField = ogr.FieldDefn(newLbl,ogr.OFTString)
    outLyr.CreateField(newField)
    idx = outLyr.GetLayerDefn().GetFieldIndex(newField)

    # Calculate index field, starting at index_0


    for counter,feat in enumerate(outLyr):
        feat.SetFieldString(idx,domainType + str(counter))
    outLyr.ResetReading()

    return outputDS

def indexDomainType(domainType,input_file):
    """

    Parameters
    ----------
    domainType
    input_file

    Returns
    -------

    """
    input_DS = gdal.OpenEx(input_file,gdal.OF_VECTOR)
    idx_test = ListFieldNames(input_DS.GetLayer(0))
    test = [i for i in idx_test if domainType in i]  # test if there is a field name containing domainType
    if len(test) == 0:  # if blank, calculate index field
        cpg_print(f"Calculating {domainType} index field...")
        input_DS = IndexCalc(domainType, input_DS)
    return input_DS


def ClearPEDatasets(paths):


    paths.DeleteFiles('grid_file',
                      'LG_SD_out_featureclass',
                      'LG_SD_LD_SA_out_featureclass',
                      'grid_LG_SD_LD',
                      'grid_LG_SD_LD_SA',
                 printFn=cpg_print)



def buildIndices(ds,workspace,outputs,polygonWidth=1000,polygonHeight=1000):

    """ Create PE_Grid step 1 of 3: Create indexes for local grids and SD, LD, SA domains """

    ######################################################################################################################

    ###### DEFINE THE WORKSPACE, INPUT, AND OUTPUT FILES HERE ######

    # # Identify working files, workspace, and input files (Powder River Basin)
    # workspace_dir = r"E:/REE/PE_Score_Calc/Development/10-10-19"
    # workspace_gdb = r"REE_EnrichmentDatabase_PRB_cgc.gdb"
    # workspace = workspace_dir + "/" + workspace_gdb

    # SD_input_file = r"P:/02_DataWorking/REE/PRB/Domains/PRB_structure_domains_extended_GC.shp"
    # LD_input_file = r"P:/02_DataWorking/REE/PRB/Domains/PRB_lithology_domains_extended_GC.shp"
    # # SA_input_file = r""  # not developed for PRB

    # Identify working files, workspace, and input files (Central App coal source region)
    # workspace_dir = r"E:/REE/PE_Score_Calc/Development/10-10-19"
    # workspace_gdb = r"REE_EnrichmentDatabase_CAB_cgc.gdb"
    # workspace = workspace_dir + "/" + workspace_gdb

    #SD_input_file = r"P:\02_DataWorking\REE\Central_App\Structural_domains\SD_CAB_2.shp"
    #LD_input_file = r"P:\05_AnalysisProjects_Working\REE\App basin drainage\AppBasinDrainageDomainPennsylvanian_BlakeBeuthin2008_snapped.shp"
    # SA_input_file = r""  # not yet developed for Central App

    # Final output files
    ds.CreateLayer("build_indices")
    # PE_Grid_calc = workspace + r"/PE_Grid_test_incl_UD"

    # Grid local variables
    # grid_file = "Empty_Grid"
    # inFeatures = LD_input_file  # the grid extent will match the extent of this file (LD should have largest spatial extent)
    # polygonWidth = "1000 meters"
    # polygonHeight = "1000 meters"

    ##################################################

    # ------ THIS SECTION IS FOR RE-RUNNING THE CODE (RELEVANT DURING DEVELOPMENT) ------

    # LG_SD_out_featureclass = workspace + r"/LG_SD_join"
    # LG_SD_LD_SA_out_featureclass = workspace + r"/LG_SD_LD_join"
    # grid_LG_SD_LD = workspace + "/grid_LG_SD_LD"
    # grid_LG_SD_LD_SA = workspace + "/grid_LG_SD_LD_SA"

    # clear each of the above files, if necessary

    # ------------------------------------------------------------------

    cpg_print("\nCreating grid...")

    inPath=workspace['LD_input_file']
    inFeatures = gdal.OpenEx(inPath,gdal.OF_VECTOR)
    # Create a grid of rectangular polygon features
    gridLyr = IndexFeatures(ds,inFeatures.GetLayer(0),polygonWidth,polygonHeight,[ogr.FieldDefn("LG_index",ogr.OFTString)])
    # Add field for LG_index
    #gDefn = gridLyr.GetLayerDefn()
    #fDefn = ogr.FieldDefn("LG_index",ogr.OFTString)
    #gDefn.AddFieldDefn(fDefn)
    fInd =gridLyr.GetLayerDefn().GetFieldIndex("LG_index")

    # Calculate LG_index field, starting at LG0
    for counter,feat in enumerate(gridLyr):
        feat.SetField(fInd,'LG'+str(counter))
        # SetFeature to refresh feature changes.
        # https://lists.osgeo.org/pipermail/gdal-dev/2009-November/022703.html
        gridLyr.SetFeature(feat)

    gridLyr.ResetReading()
    WriteIfRequested(gridLyr,outputs,'grid_file',printFn=cpg_print)

    cpg_print("LG_index generated. \n")

    # # Verify fields were added (used to QA/QC the script)
    # field_names = ListFieldNames(grid_file)
    # cpg_print("QAQC: LG index field name =", field_names[-1], "\n")

    # # Verify local grid correctly indexed (used to QA/QC the script)
    # LG_unique = FieldValues(grid_file, "LG_index")
    # cpg_print("QAQC: First row of LG_index =", LG_unique[0], "\n")

    ##### STRUCTURE DOMAINS #####
    # Generate index field for domains if not already present
    SD_input_DS = indexDomainType('SD',workspace['SD_input_file'])

    # Join local grid to structure domains
    cpg_print("Joining structure domains to grid_file...")
    SD_target_features = gridLyr
    SD_join_features = SD_input_DS
    structDomLyr=SpatialJoinCentroid(SD_target_features, SD_join_features.GetLayer(0), ds)
    cpg_print("Structure domains joined.\n")


    ##### LITHOLOGIC DOMAINS #####
    # Generate index field for domains if not already present
    LD_input_DS = indexDomainType('LD',workspace['LD_input_file'])


    # Join lithologic domains
    cpg_print("Joining lithology domains...")
    LD_target_features =structDomLyr

    LD_join_features = LD_input_DS.GetLayer(0)
    LG_SD_LDLyr=SpatialJoinCentroid(LD_target_features, LD_join_features, ds)

    cpg_print("Lithology domains joined.\n")

    # Copy SD and LD indices to new feature class
    WriteIfRequested(LG_SD_LDLyr,outputs,'grid_LG_SD_LD',printFn=cpg_print)


    return LG_SD_LDLyr
    ### SA DOMAIN CODE BELOW STILL IN DEVELOPMENT; NEEDS TESTING ###

    # ##### SECONDARY ALTERATION DOMAINS #####
    # # Generate index field for domains if not already present
    # domainType = 'SA'
    # domain_shp = SA_input_file
    # idx_test = ListFieldNames(SA_input_file)
    # test = [i for i in idx_test if domainType in i]  # test if there is a field name containing domainType
    # if test == []:
    #     cpg_print("Calculating SA index field...")
    #     SA_input_file = IndexCalc(domainType, workspace_dir, SA_input_file)

    # # Join secondary alteration domains
    # cpg_print("Joining secondary alteration domains...")
    # SA_target_features = LG_SD_LD_out_featureclass
    # SA_join_features = SA_input_file
    # LG_SD_LD_SA_out_featureclass = workspace + r"/LG_SD_LD_join"
    # arcpy.SpatialJoin_analysis(SA_target_features, SA_join_features, LG_SD_LD_SA_out_featureclass, match_option="HAVE_THEIR_CENTER_IN")
    # cpg_print("Secondary alteration domains joined.\n")

    # # Copy SD, LD, and SA indices to new feature class
    # grid_LG_SD_LD_SA = workspace + "/grid_LG_SD_LD_SA"
    # arcpy.CopyFeatures_management(LG_SD_LD_SA_out_featureclass, grid_LG_SD_LD_SA)
    # cpg_print("Created new file:", grid_LG_SD_LD_SA)



def calcUniqueDomains(inDS,grid_LG_SD_LD,outputs):
    """ Create PE_Grid step 2 of 3: Calculate unique domains (UD) using Pandas DataFrame """

    ### CODE TESTED AND SUCCESSFUL ###

    ### THIS CODE IS NEEDED IN THE FINAL SCRIPT ONCE IT INCLUDES SA DOMAINS (SEE OTHER CELL) ###

    # THIS CELL DOES NOT INCLUDE SA DOMAIN TYPES

    # Create a list of local grid index values, then create DataFrame
    LG_index_values = FieldValues(grid_LG_SD_LD, 'LG_index')
    df_grid_calc = pd.DataFrame(LG_index_values, columns={'LG_index'})

    # Create a list of domain index values (e.g, LD1, LD2, LD3, LD4), then add to DataFrame
    LD_index_values = FieldValues(grid_LG_SD_LD, 'LD_index')
    df_grid_calc['LD_index'] = LD_index_values
    # df_grid_calc['LD_index'].value_counts()  # for development QAQC

    SD_index_values = FieldValues(grid_LG_SD_LD, 'SD_index')
    df_grid_calc['SD_index'] = SD_index_values
    # df_grid_calc['SD_index'].value_counts()  # for development QAQC

    # Create column for unique domain index 'UD_index'
    df_grid_calc['UD_index'] = 0

    # Group by unique LD and SD index value combinations
    grouped = df_grid_calc.groupby(['LD_index', 'SD_index'])

    # Create a Pandas Series that will contain the unique index combinations
    UD_lookup = grouped['UD_index'].unique()
    # cpg_print(UD_lookup['LD0']['SD0'])  # for development QAQC

    # Calculate the UD_index (this will be a Pandas Series that gets merged with the parent DataFrame)
    counter = 0
    for i in range(len(UD_lookup)):
        UD_lookup[i] = "UD" + str(counter)
        counter = counter + 1
        # UD_lookup_df = pd.DataFrame(UD_lookup)  # this line is not needed; code works fine as Series (DataFrame not needed)

    # Merge calculated UD index with parent DataFrame
    df_grid_merged = df_grid_calc.merge(UD_lookup, how='left', left_on=('LD_index', 'SD_index'), right_index=True,
                                        sort=False, indicator=True)

    # Tidy the column names and values
    df_grid_merged.rename(columns={'UD_index_y': 'UD_index'}, inplace=True)
    df_grid_merged.drop(columns=['UD_index_x', '_merge'], inplace=True)
    df_grid_merged.fillna(value=0, inplace=True)
    # df_grid_merged['_merge'].value_counts()  # for development only, to ensure proper merging

    cpg_print("Successfully merged DataFrames.")

    """ Add UD_index to other indices in a feature class """

    ### CODE TESTED AND SUCCESSFUL ###

    # Export DataFrame as CSV
    if 'exported_grid_df' in outputs:
            exported_grid_df = outputs['exported_grid_df']
            df_grid_merged.to_csv(exported_grid_df, index=False)

    # Join DataFrame table to PE_Grid
    inFeatures = grid_LG_SD_LD
    joinField = "LG_index"
    fieldList = ['UD_index']
    OgrPandasJoin(inFeatures, joinField, df_grid_merged, joinField, fieldList)

    WriteIfRequested(inFeatures,outputs,'PE_Grid_calc',printFn=cpg_print)

    return inFeatures

def copyPE_Grid(workingDS,PE_Grid_calc):
    """ Create PE_Grid step 3 of 3: Create a copy of PE_Grid that has only the fields for the indicies """

    ### CODE TESTED AND SUCCESSFUL ###

    ### THIS CELL IS NEEDED IN THE FINAL SCRIPT ###

    # Create a clean copy of the grid with only essential and relevant fields for the grid indicies

    PE_Grid_clean=workingDS.CopyLayer(PE_Grid_calc,"PE_Grid_Clean")

    lyrDefn = PE_Grid_clean.GetLayerDefn()
    # Update fields names
    keep = {"OBJECTID", "Shape", "Shape_Length", "Shape_Area", "LG_index", "SD_index", "LD_index", "SA_index", "UD_index"}
    # list comprehension to build field list using keep list to filter
    field_names_del = [lyrDefn.GetFieldDefn(i).GetName() for i in range(lyrDefn.GetFieldCount()) if lyrDefn.GetFieldDefn(i).GetName() in keep]

    # Delete unnecessary fields from PE_Grid_clean
    cpg_print("\nRemoving unnecessary fields from PE_Grid file...")
    for field in field_names_del:
        # use names instead of indices since indicess will shift after each delete.
        ind = lyrDefn.GetFieldIndex(field)
        PE_Grid_clean.DeleteField(ind)


    cpg_print("\nCreated the indexed PE_Grid file to use for calculating PE Score:\n", PE_Grid_clean)
    return PE_Grid_clean


if __name__ == '__main__':

    gdal.UseExceptions()
    from argparse import ArgumentParser
    prsr = ArgumentParser(description="Construct a PE grid.")
    prsr.add_argument('workspace',type=PE_Workspace,help="The workspace directory.")
    prsr.add_argument('output_dir',type=PE_Workspace,help="Path to the output file. For now assume .shp")
    prsr.add_argument('-W','--gridWidth',type=float,default=1000,help="Width of new grid.")
    prsr.add_argument('-H','--gridHeight',type=float,default=1000,help='Height of new grid.')
    grp=prsr.add_argument_group("Input files","Override as needed, Absolute, or relative to workdir.")
    grp.add_argument('--SD_input_file',dest='IN_SD_input_file',type=str,default='SD_input_file.shp',help='Structural Domain input file.')
    grp.add_argument('--LD_input_file', dest='IN_LD_input_file',type=str, default='LD_input_file.shp', help='Lithographic Domain input file.')
    grp = prsr.add_argument_group("Optional Output files", "Optional output of intermediate files. Useful for debugging")
    grp.add_argument('--LG_SD_out_featureclass', dest='OUT_LG_SD_out_featureclass',type=str, help='Name of Joint LG_SD output.')
    grp.add_argument('--grid_LG_SD_LD',dest='OUT_grid_LG_SD_LD',type=str,help='Name of gridded LG_SD_LD output.')
    grp.add_argument('--grid_file',dest='OUT_grid_file',type=str,help='Name of base grid')
    grp.add_argument('--exported_grid_df', dest='OUT_exported_grid_df', type=str, help='Name of exported dataframe')
    grp.add_argument('--PE_Grid_calc', dest='OUT_PE_Grid_calc', type=str,help='Name of PE_calc file')

    # grp.add_argument('--LG_SD_LD_SA_out_featureclass', type=str, default='LG_SD_LD_join', help='Name of Joint LG_SD_LD_join output.')
    # grp.add_argument('--grid_LG_SD_LD_SA',type=str,default='grid_LG_SD_LD_SA',help='Name of gridded grid_LG_SD_LD_SA output.')

    args = prsr.parse_args()

    for k,v in vars(args).items():
        if isinstance(v,str):
            if k.startswith('IN_'):
                args.workspace[k[3:]]=v
            elif k.startswith('OUT_'):
                args.output_dir[k[4:]]=v


    ClearPEDatasets(args.workspace)
    drvr = gdal.GetDriverByName("memory")
    scratchDS = drvr.Create('scratch',0,0,0,gdal.OF_VECTOR)
    drvr = gdal.GetDriverByName("ESRI Shapefile")

    #outDS = drvr.Create(os.path.join(args.output_dir.workspace,'outputs.shp'),0,0,0,gdal.OF_VECTOR)
    grid_LG_SD_LD=buildIndices(scratchDS,args.workspace,args.output_dir,args.gridWidth,args.gridHeight)
    cpg_print("\nStep 1 complete")

    PE_grid_calc=calcUniqueDomains(scratchDS,grid_LG_SD_LD,args.output_dir)
    cpg_print("\nStep 2 complete")

    #del outDS
    finalDS = drvr.Create(os.path.join(args.output_dir.workspace, 'PE_clean_grid.shp'), 0, 0, 0, gdal.OF_VECTOR)
    copyPE_Grid(finalDS,PE_grid_calc)
    cpg_print("\nStep 3 complete")