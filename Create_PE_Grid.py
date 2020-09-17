"""Create grid to be used for PE Scoring."""
import os
from osgeo import ogr,gdal,osr
from common_utils import *
import pandas as pd


# alias the print function so we can override in different cases
cpg_print=print

def IndexCalc(domainType, domainDS):
    """ Calculates index field for an STA domain type.

    Args:
        domainType (str): Name of the domain type.  Only the following two-letter strings should be used:
          * 'LD' (lithologic domain)
          * 'SD' (structural domain)
          * 'SA' (secondary alteration)
        domainDS (osgeo.gdal.Dataset): Dataset containing the featues to index.

    Returns:
        osgeo.gdal.Dataset: A copy of the input dataset with a new field for the domain index.
            **IMPORTANT**: This file will be saved to the same directory as `domainDS`.
    """

    domain_output_file = os.path.splitext(domainDS.GetFileList()[0])[0] + "_indexed.shp"

    drvr = gdal.GetDriverByName("ESRI Shapefile")
    DeleteFile(domain_output_file,cpg_print)
    outputDS = drvr.Create(domain_output_file, 0, 0, 0, gdal.GDT_Unknown)

    outputDS.CopyLayer(domainDS.GetLayer(0), domainDS.GetLayer(0).GetName())
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

def indexDomainType(domainType,input_file,layerInd=0):
    """Index domain for Layer in dataset.

    Args:
        domainType (str): Name of the domain type.  Only the following two-letter strings should be used:
          * 'LD' (lithologic domain)
          * 'SD' (structural domain)
          * 'SA' (secondary alteration)

        input_file (str): Path to the file to load.
        layerInd (int): Index to the layer to load. The default (0) will work for shape files.

    Returns:
        osgeo.gdal.Dataset: The newly loaded and indexed Dataset.
    """

    input_DS = gdal.OpenEx(input_file,gdal.OF_VECTOR)
    idx_test = ListFieldNames(input_DS.GetLayer(layerInd))
    test = [i for i in idx_test if domainType in i]  # test if there is a field name containing domainType
    if len(test) == 0:  # if blank, calculate index field
        cpg_print(f"Calculating {domainType} index field...")
        input_DS = IndexCalc(domainType, input_DS)
    return input_DS


def ClearPEDatasets(paths):
    """Remove any intermediate files from the workspace.

    Args:
        paths (common_utils.REE_Workspace): The tags identifying the workspace files to delete.

    """

    paths.DeleteFiles('grid_file',
                      'LG_SD_out_featureclass',
                      'LG_SD_LD_SA_out_featureclass',
                      'grid_LG_SD_LD',
                      'grid_LG_SD_LD_SA',
                     printFn=cpg_print)



def buildIndices(ds,workspace,outputs,polygonWidth,polygonHeight):
    """Create PE_Grid step 1 of 3: Create indexes for local grids and SD, LD, SA domains

    Args:
        ds (osgeo.gdal.Dataset): The Dateset to analyze.
        workspace (common_utils.REE_Workspace): Input workspace object.
        outputs (common_utils.REE_Workspace): Output workspace object.
        polygonWidth (float): The height to apply to generated grid; units derived from `ds`.
        polygonHeight (float): The width to apply to generated grid; units derived from `ds`.

    Returns:
        osgeo.ogr.Layer: Fully indexed culled fishnet Layer, which resides in `ds`.
    """

    # Final output files
    ds.CreateLayer("build_indices")

    cpg_print("\nCreating grid...")

    inPath=workspace['LD_input_file']
    inFeatures = gdal.OpenEx(inPath,gdal.OF_VECTOR)
    # Create a grid of rectangular polygon features
    gridLyr = IndexFeatures(ds,inFeatures.GetLayer(0),polygonWidth,polygonHeight,[ogr.FieldDefn('OBJECTID',ogr.OFTInteger),ogr.FieldDefn("LG_index",ogr.OFTString)])

    # Add field for LG_index
    fInd =gridLyr.GetLayerDefn().GetFieldIndex("LG_index")
    oInd = gridLyr.GetLayerDefn().GetFieldIndex("OBJECTID")

    # Calculate LG_index field, starting at LG0
    for counter,feat in enumerate(gridLyr):
        feat.SetField(fInd,'LG'+str(counter))
        feat.SetField(oInd,counter+1)
        # SetFeature to refresh feature changes.
        # https://lists.osgeo.org/pipermail/gdal-dev/2009-November/022703.html
        gridLyr.SetFeature(feat)
    gridLyr.ResetReading()

    WriteIfRequested(gridLyr,outputs,'grid_file',printFn=cpg_print)

    cpg_print("LG_index generated. \n")

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

def calcUniqueDomains(grid_LG_SD_LD,outputs):
    """Create PE_Grid step 2 of 3: Calculate unique domains (UD) using Pandas DataFrame.

    Args:
        grid_LG_SD_LD (osgeo.ogr.Layer): The layer to process and modify.
        outputs (common_utils.REE_Workspace): The outputs workspace object.

    Returns:
        osgeo.ogr.Layer: The layer with unique domain data. Presently just `grid_LG_SD_LD`.
    """

    # Create a list of local grid index values, then create DataFrame
    df_data = {'LG_index':FieldValues(grid_LG_SD_LD, 'LG_index'),
               # Create a list of domain index values (e.g, LD1, LD2, LD3, LD4)
               'LD_index':FieldValues(grid_LG_SD_LD, 'LD_index'),

               'SD_index':FieldValues(grid_LG_SD_LD, 'SD_index'),
               }

    df_grid_calc = pd.DataFrame(df_data, columns={'LG_index':object,'LD_index':object,'SD_index':object,'UD_index':object})

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

def copyPE_Grid(workingDS,PE_Grid_calc,sRef=None):
    """ Create PE_Grid step 3 of 3: Create a copy of PE_Grid that has only the fields for the indicies.
    Duplicate PEGrid Layer, potentially reprojecting.

    Args:
        workingDS (osgeo.gdal.Dataset): The active working dataset to store the copy.
        PE_Grid_calc (osgeo.ogr.Layer): The layer to copy.
        sRef (osgeo.osr.SpatialReference,optional): Optional spatial reference to reproject into.

    Returns:
        osgeo.ogr.Layer: The properly scrubbed `PE_Grid_calc` Layer copy.
    """

    # Create a clean copy of the grid with only essential and relevant fields for the grid indicies

    if sRef is None:
        PE_Grid_clean=workingDS.CopyLayer(PE_Grid_calc,"PE_Grid_Clean")
    else:
        # https://pcjericks.github.io/py-gdalogr-cookbook/projection.html#reproject-a-layer
        trans = osr.CoordinateTransformation(PE_Grid_calc.GetSpatialRef(),sRef)
        oldDefn = PE_Grid_calc.GetLayerDefn()
        PE_Grid_clean=workingDS.CreateLayer("PE_Grid_clean_reproj",sRef,oldDefn.GetGeomType())
        for i in range(oldDefn.GetFieldCount()):
            PE_Grid_clean.CreateField(oldDefn.GetFieldDefn(i))

        nDefn=PE_Grid_clean.GetLayerDefn()
        for feat in PE_Grid_calc:
            geom = feat.GetGeometryRef()
            geom.Transform(trans)

            newFeat = ogr.Feature(nDefn)
            newFeat.SetGeometry(geom)
            for i in range(nDefn.GetFieldCount()):
                newFeat.SetField(i,feat.GetField(i))
            PE_Grid_clean.CreateFeature(newFeat)

    lyrDefn = PE_Grid_clean.GetLayerDefn()
    # Update fields names
    keep = {"OBJECTID", "Shape", "Shape_Length", "Shape_Area", "LG_index", "SD_index", "LD_index", "SA_index", "UD_index"}
    # as long as we are using shp files, we need to limit labels to 10 chars
    keep = {x[:10] for x in keep}

    # list comprehension to build field list using keep list to filter
    field_names_del = [lyrDefn.GetFieldDefn(i).GetName() for i in range(lyrDefn.GetFieldCount()) if lyrDefn.GetFieldDefn(i).GetName() not in keep]

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
    prsr.add_argument('workspace',type=REE_Workspace,help="The workspace directory.")
    prsr.add_argument('output_dir',type=REE_Workspace,help="Path to the output directory")
    prsr.add_argument('-W','--gridWidth',type=float,default=1000,help="Width of new grid.")
    prsr.add_argument('-H','--gridHeight',type=float,default=1000,help='Height of new grid.')
    prsr.add_argument('--prj_file', type=str, default=None, help='Spatial Reference System/Projection for resulting grid.')
    grp=prsr.add_argument_group("Input files","Override as needed, Absolute, or relative to workdir.")
    grp.add_argument('--SD_input_file',dest='IN_SD_input_file',type=str,default='SD_input_file.shp',help='Structural Domain input file.')
    grp.add_argument('--LD_input_file', dest='IN_LD_input_file',type=str, default='LD_input_file.shp', help='Lithographic Domain input file.')
    grp = prsr.add_argument_group("Optional Output files", "Optional output of intermediate files. Useful for debugging")
    grp.add_argument('--LG_SD_out_featureclass', dest='OUT_LG_SD_out_featureclass',type=str, help='Name of Joint LG_SD output.')
    grp.add_argument('--grid_LG_SD_LD',dest='OUT_grid_LG_SD_LD',type=str,help='Name of gridded LG_SD_LD output.')
    grp.add_argument('--grid_file',dest='OUT_grid_file',type=str,help='Name of base grid')
    grp.add_argument('--exported_grid_df', dest='OUT_exported_grid_df', type=str, help='Name of exported dataframe')
    grp.add_argument('--PE_Grid_calc', dest='OUT_PE_Grid_calc', type=str,help='Name of PE_calc file')

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

    PE_grid_calc=calcUniqueDomains(grid_LG_SD_LD,args.output_dir)
    cpg_print("\nStep 2 complete")

    proj = None
    if args.prj_file is not None:
        proj = osr.SpatialReference()
        with open(args.prj_file,'r') as inFile:
            proj.ImportFromESRI(inFile.readlines())

    #del outDS
    finalDS = drvr.Create(os.path.join(args.output_dir.workspace, 'PE_clean_grid.shp'), 0, 0, 0, gdal.OF_VECTOR)
    copyPE_Grid(finalDS,PE_grid_calc, proj)
    cpg_print("\nStep 3 complete")