
import os

from osgeo import ogr
import pandas as pd
from common_utils import *


def IndexCalc(domainType : str, domain_shp : gdal.Dataset) -> gdal.Dataset:
    """
    Calculates index field for an STA domain type.

    Parameters
    ----------
    domainType: <str>
        Name of the domain type.  Only the following two-letter strings should be used:
        'LD' (lithologic domain)
        'SD' (structural domain)
        'SA' (secondary alteration)

    workspace_dir: <str>
        The working directory.  This should be the same as the location of the assessment geodatabase.

    domain_shp: <str>
        Full filepath and filename (including file extension) of the input shapefile or feature class.
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
    if os.path.exists(domain_output_file):
        os.remove(domain_output_file)
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

def buildIndices(ds : gdal.Dataset,SD_input_file : str,LD_input_file : str):
    """ Create PE_Grid step 1 of 3: Create indexes for local grids and SD, LD, SA domains """

    ### CODE TESETED AND SUCCESSFUL ###

    ### INCLUDES A FUNCTION THAT CALCULATES DOMAIN INDEX IF NOT ALREADY IN THE DOMAIN SHAPEFILE ###

    ### THIS CELL IS NEEDED IN THE FINAL SCRIPT ###


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
    ds.CreateLayer()
    PE_Grid_calc = workspace + r"/PE_Grid_calc"
    PE_Grid_clean = workspace + r"/PE_Grid_clean"
    # PE_Grid_calc = workspace + r"/PE_Grid_test_incl_UD"

    # Grid local variables
    grid_file = "Empty_Grid"
    inFeatures = LD_input_file  # the grid extent will match the extent of this file (LD should have largest spatial extent)
    polygonWidth = "1000 meters"
    polygonHeight = "1000 meters"

    ##################################################

    # ------ THIS SECTION IS FOR RE-RUNNING THE CODE (RELEVANT DURING DEVELOPMENT) ------
    try:
        arcpy.Delete_management(grid_file)
        print("Deleted existing files:", grid_file)
    except:
        print(grid_file, "not found in geodatabase!  Creating new...")

    try:
        LG_SD_out_featureclass = workspace + r"/LG_SD_join"
        arcpy.Delete_management(LG_SD_out_featureclass)
        print("Deleted existing file:", LG_SD_out_featureclass)
    except:
        print(LG_SD_out_featureclass, "not found in geodatabase!  Will create new...")

    try:
        LG_SD_LD_out_featureclass = workspace + r"/LG_SD_LD_join"
        arcpy.Delete_management(LG_SD_LD_out_featureclass)
        print("Deleted existing file:", LG_SD_LD_out_featureclass)
    except:
        print(LG_SD_LD_out_featureclass, "not found in geodatabase!  Will create new...")

    try:
        LG_SD_LD_SA_out_featureclass = workspace + r"/LG_SD_LD_join"
        arcpy.Delete_management(LG_SD_LD_SA_out_featureclass)
        print("Deleted existing file:", LG_SD_LD_SA_out_featureclass)
    except:
        print(LG_SD_LD_SA_out_featureclass, "not found in geodatabase!  Will create new...")

    try:
        grid_LG_SD_LD = workspace + "/grid_LG_SD_LD"
        arcpy.Delete_management(grid_LG_SD_LD)
        print("Deleted existing file:", grid_LG_SD_LD)
    except:
        print(grid_LG_SD_LD, "not found in geodatabase!  Will create new...")

    try:
        grid_LG_SD_LD_SA = workspace + "/grid_LG_SD_LD_SA"
        arcpy.Delete_management(grid_LG_SD_LD_SA)
        print("Deleted existing file:", grid_LG_SD_LD_SA)
    except:
        print(grid_LG_SD_LD_SA, "not found in geodatabase!  Will create new...")
    # ------------------------------------------------------------------

    print("\nCreating grid...")

    # Create a grid of rectangular polygon features
    arcpy.GridIndexFeatures_cartography(grid_file, inFeatures, "", "", "", polygonWidth, polygonHeight)

    # Add field for LG_index
    arcpy.AddField_management(grid_file, "LG_index", "TEXT")

    # Calculate LG_index field, starting at LG1
    counter = -1
    with arcpy.da.UpdateCursor(grid_file, 'LG_index') as cursor:
        for row in cursor:
            counter = counter + 1
            row[0] = 'LG' + str(counter)
            cursor.updateRow(row)

    print("LG_index generated. \n")

    # # Verify fields were added (used to QA/QC the script)
    # field_names = ListFieldNames(grid_file)
    # print("QAQC: LG index field name =", field_names[-1], "\n")

    # # Verify local grid correctly indexed (used to QA/QC the script)
    # LG_unique = FieldValues(grid_file, "LG_index")
    # print("QAQC: First row of LG_index =", LG_unique[0], "\n")

    ##### STRUCTURE DOMAINS #####
    # Generate index field for domains if not already present
    domainType = 'SD'
    domain_shp = SD_input_file
    idx_test = ListFieldNames(SD_input_file)
    test = [i for i in idx_test if domainType in i]  # test if there is a field name containing domainType
    if test == []:  # if blank, calculate index field
        print("Calculating SD index field...")
        SD_input_file = IndexCalc(domainType, workspace_dir, SD_input_file)

    # Join local grid to structure domains
    print("Joining structure domains to grid_file...")
    SD_target_features = grid_file
    SD_join_features = SD_input_file
    LG_SD_out_featureclass = workspace + r"/LG_SD_join"
    arcpy.SpatialJoin_analysis(SD_target_features, SD_join_features, LG_SD_out_featureclass,
                               match_option="HAVE_THEIR_CENTER_IN")
    print("Structure domains joined.\n")

    ##### LITHOLOGIC DOMAINS #####
    # Generate index field for domains if not already present
    domainType = 'LD'
    domain_shp = LD_input_file
    idx_test = ListFieldNames(LD_input_file)
    test = [i for i in idx_test if domainType in i]  # test if there is a field name containing domainType
    if test == []:  # if blank, calculate index field
        print("Calculating LD index field...")
        LD_input_file = IndexCalc(domainType, workspace_dir, LD_input_file)

    # Join lithologic domains
    print("Joining lithology domains...")
    LD_target_features = LG_SD_out_featureclass
    LD_join_features = LD_input_file
    LG_SD_LD_out_featureclass = workspace + r"/LG_SD_LD_join"
    arcpy.SpatialJoin_analysis(LD_target_features, LD_join_features, LG_SD_LD_out_featureclass,
                               match_option="HAVE_THEIR_CENTER_IN")
    print("Lithology domains joined.\n")

    # Copy SD and LD indices to new feature class
    grid_LG_SD_LD = workspace + "/grid_LG_SD_LD"
    arcpy.CopyFeatures_management(LG_SD_LD_out_featureclass, grid_LG_SD_LD)
    print("Created new file:", grid_LG_SD_LD)

    ### SA DOMAIN CODE BELOW STILL IN DEVELOPMENT; NEEDS TESTING ###

    # ##### SECONDARY ALTERATION DOMAINS #####
    # # Generate index field for domains if not already present
    # domainType = 'SA'
    # domain_shp = SA_input_file
    # idx_test = ListFieldNames(SA_input_file)
    # test = [i for i in idx_test if domainType in i]  # test if there is a field name containing domainType
    # if test == []:
    #     print("Calculating SA index field...")
    #     SA_input_file = IndexCalc(domainType, workspace_dir, SA_input_file)

    # # Join secondary alteration domains
    # print("Joining secondary alteration domains...")
    # SA_target_features = LG_SD_LD_out_featureclass
    # SA_join_features = SA_input_file
    # LG_SD_LD_SA_out_featureclass = workspace + r"/LG_SD_LD_join"
    # arcpy.SpatialJoin_analysis(SA_target_features, SA_join_features, LG_SD_LD_SA_out_featureclass, match_option="HAVE_THEIR_CENTER_IN")
    # print("Secondary alteration domains joined.\n")

    # # Copy SD, LD, and SA indices to new feature class
    # grid_LG_SD_LD_SA = workspace + "/grid_LG_SD_LD_SA"
    # arcpy.CopyFeatures_management(LG_SD_LD_SA_out_featureclass, grid_LG_SD_LD_SA)
    # print("Created new file:", grid_LG_SD_LD_SA)



def calcUniqueDomains():
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
    # print(UD_lookup['LD0']['SD0'])  # for development QAQC

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

    print("Successfully merged DataFrames.")

    """ Add UD_index to other indices in a feature class """

    ### CODE TESTED AND SUCCESSFUL ###

    # Export DataFrame as CSV
    exported_grid_df = workspace_dir + '/UD_domains_exported.csv'
    df_grid_merged.to_csv(exported_grid_df, index=False)

    # Convert the DataFrame CSV file to ArcGIS table (if not already created)
    try:
        arcpy.TableToTable_conversion(exported_grid_df, workspace, "exported_grid_df_table")
    except:
        print("DataFrame csv already converted to ArcGIS table!")

    # Join DataFrame table to PE_Grid
    inFeatures = grid_LG_SD_LD
    joinField = "LG_index"
    joinTable = "exported_grid_df_table"
    fieldList = ['UD_index']
    arcpy.JoinField_management(inFeatures, joinField, joinTable, joinField, fieldList)

    # Create final copy of feature class with grid indicies
    try:
        arcpy.CopyFeatures_management(grid_LG_SD_LD, PE_Grid_calc)
    except:
        print(PE_Grid_calc, "already exists, trying again...")
        arcpy.Delete_management(PE_Grid_calc)
        arcpy.CopyFeatures_management(grid_LG_SD_LD, PE_Grid_calc)

    print("\nCreated", PE_Grid_calc)


def copyPE_Grid():
    """ Create PE_Grid step 3 of 3: Create a copy of PE_Grid that has only the fields for the indicies """

    ### CODE TESTED AND SUCCESSFUL ###

    ### THIS CELL IS NEEDED IN THE FINAL SCRIPT ###

    # Create a clean copy of the grid with only essential and relevant fields for the grid indicies
    try:
        arcpy.CopyFeatures_management(PE_Grid_calc, PE_Grid_clean)
    except:
        arcpy.Delete_management(PE_Grid_clean)
        arcpy.CopyFeatures_management(PE_Grid_calc, PE_Grid_clean)

    # Update fields names
    field_names_del = ListFieldNames("PE_Grid_clean")

    # List of fields to be preserved
    keep = ["OBJECTID", "Shape", "Shape_Length", "Shape_Area", "LG_index", "SD_index", "LD_index", "SA_index", "UD_index"]
    for i in keep:
        try:
            field_names_del.remove(i)
        except:
            print('failed to remove:', i, "from field_names_del")

    # Delete unnecessary fields from PE_Grid_clean
    print("\nRemoving unnecessary fields from PE_Grid file...")
    for field in field_names_del:
        arcpy.DeleteField_management(PE_Grid_clean, field)

    print("\nCreated the indexed PE_Grid file to use for calculating PE Score:\n", PE_Grid_clean)


if __name__ == '__main__':

    buildIndices()
    print("\nStep 1 complete")

    calcUniqueDomains()
    print("\nStep 2 complete")

    copyPE_Grid()
    print("\nStep 3 complete")