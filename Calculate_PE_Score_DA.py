""" Create lists for unique components and each corresponding dataset """

### CODE TESTED AND SUCCESSFUL ###

### COMMENT FOR DEVELOPMENT: RUN THIS CELL FOR EACH SESSION ###

### THIS CELL IS NEEDED IN THE FINAL SCRIPT ###


from common_utils import *
from time import process_time
import pandas as pd
import sys
import fnmatch
from osgeo import gdal, ogr, osr
cpes_print=print
# UNTESTED: SWITCH BETWEEN DA AND DS
FeatureDataset = "DA"

# Identify working files and workspace on C:\ (testing SSD vs. HDD performace) -- POWDER RIVER BASIN
workspace_dir = r"C:\Users\creasonc\REE_PE_Script_dev\11-1-19"
workspace_gdb = r"REE_EnrichmentDatabase_PRB_DA_DS.gdb"
PE_Grid_file = r"PE_Grid_calc_v9"

# Identify working files and workspace -- POWDER RIVER BASIN
# workspace_dir = r"E:/REE/PE_Score_Calc/Development/10-10-19"
# workspace_gdb = r"REE_EnrichmentDatabase_PRB_cgc.gdb"
# PE_Grid_file = r"PE_Grid_ScriptTest_20200401"

# Identify working files and workspace -- CENTRAL APP BASIN
# workspace_dir = r"E:/REE/PE_Score_Calc/Development/10-10-19"
# workspace_gdb = r"REE_EnrichmentDatabase_CAB_cgc.gdb"
# PE_Grid_file = r"PE_Grid_clean"



# Set ArcGIS workspace environment

# PE_Grid = workspace + "/" + PE_Grid_file

def printTimeStamp(rawSeconds):
    """
    Print raw seconds in nicely hour, minute, seconds format.

    Parameters
    ----------
    rawSeconds: <int> The raw seconds to print.

    """
    totMin,seconds = divmod(rawSeconds,60)
    hours,minutes = divmod(totMin,60)
    cpes_print(f"Runtime: {hours} hours, {minutes} minutes, {round(seconds,2)} seconds.")

######################################################################################################################
def ListFeatureClassNames(ds, wildCard, first_char=0, last_char=sys.maxsize):
    """
    Function that creates a list of all unique REE-Coal components in an ESRI GDB Feature Dataset, for use in use in
        calculating PE score from DA and DS databases.

    Parameters
    ----------
    ds: <gdal.Dataset>
        The dataset to query.
    wildCard: <str>
        Criteria used to limit the results returned
    first_char: <int>
        Index of first character to include in the filename
    last_char: <int>
        Index of last character to include in the filename

    Returns
    -------
    <list>
        sorted, non-repeating iterable sequence of feature class names based on the WildCard criteria
    """

    fcNames = [ds.GetLayer(i).GetName() for i in range(ds.GetLayerCount())]
    # match against wildcard
    fcNames=[x[first_char:last_char] for x in fnmatch.filter(fcNames,wildCard)]

    return sorted(set(fcNames))


######################################################################################################################
def ListFeatureClasses(ds,wildCard):
    """
    Function that creates a list of all unique REE-Coal components in an ESRI GDB Feature Dataset, for use in use in
        calculating PE score from DA and DS databases.

    Parameters
    ----------
    ds <gdal.Dataset>
        The dataset to query.
    wildCard: <str>
        Criteria used to limit the results returned

    Returns
    -------
    <list>
        sorted, non-repeating iterable sequence of feature class names based on the WildCard criteria
    """

    fcNames=ListFeatureClassNames(ds, wildCard)

    fcList = []
    for i in range(ds.GetLayerCount()):
        lyr = ds.GetLayer(i)
        if lyr.GetName() in fcNames:
            fcList.append(lyr)


    return fcList


######################################################################################################################
def replaceNULL(feature_class, field):
    """
    Replace NULL values with zeros for a field in a feature class

    Parameters
    ----------
    feature_class: <ogr.Layer>
        Layer containing the field to be modified
    field: <str>
        Name of the field to be evaluated and modified if necessary

    Returns
    -------
    None; this function only modifies the field in the feature_class
    """

    idx = feature_class.GetLayerDefn().GetFieldIndex(field)
    for feat in feature_class:
        if feat.IsFieldNull(idx):
            feat.SetField(idx,0)
    feature_class.ResetReading()


def FindUniqueComponents(gdbDS):
    """Calculate DA Step 0: find the collections to be used in subsequent steps"""
    # Create a list of all unique code prefixes for the component IDs
    unique_components = ListFeatureClassNames(gdbDS, wildCard="DA*", first_char=0, last_char=14)

    # An array comprising all components and their respective feature classes
    components_data_array = []

    # Generate a list of feature classes for each Emplacement Type, Influence Extent, AND Component ID combination
    for component_datasets in unique_components:
        #     cpes_print("component_datasets:", component_datasets, "\n")
        component_datasets = ListFeatureClasses(gdbDS, wildCard=(component_datasets + "*"))
        #     cpes_print("component_datasets:", component_datasets, "\n")
        # Append list to a single array
        components_data_array.append(component_datasets)

    return unique_components,components_data_array


def DAFeaturesPresent(PE_Grid,unique_components,components_data_array,scratchDS,outputs):
    """ Calculate DA step 1 of 4: Presence/absence for each feature class in the DA Feature Dataset.
        Creates a new field in PE_Grid for each feature class in the geodatabase """



    # del(component_datasets)

    # List field names
    field_names = ListFieldNames(PE_Grid)

    cpes_print("PE_Grid attributes:", field_names, "\n")


    ### CODE TESTED AND SUCCESSFUL ###

    """ THIS CELL ONLY NEEDS EXECUTED ONCE (TAKES ~6.9 HOURS TO EXECUTE WHEN USING replaceNULL (v8)) """

    ### THIS CELL IS NEEDED IN THE FINAL SCRIPT ###

    t_start = process_time()  # track processing time

    processing = {}  # dictionary for processing time

    PE_Grid_working = scratchDS.CreateLayer(PE_Grid.GetName(),PE_Grid.GetSpatialRef(),PE_Grid.GetGeomType())
    # add existing fields
    peDefn = PE_Grid.GetLayerDefn()
    wDefn = PE_Grid_working.GetLayerDefn()
    for i in range(peDefn.GetFieldCount()):
        wDefn.AddFieldDefn(peDefn.GetFieldDefn(i))
    # add join fields
    for component_datasets in components_data_array:
        # Test for intersect between PE_Grid cells and data features
        for feature_class in component_datasets:
            field = ogr.FieldDefn(feature_class.GetName(),ogr.OFTInteger)
            field.SetDefault('0') # might not work with shp/gdb
            wDefn.AddFieldDefn(field)

    for uc in unique_components:
        if uc not in field_names:
            cpes_print("Adding field:", uc)
            fDefn=ogr.FieldDefn(uc,ogr.OFTInteger)
            fDefn.SetDefault('0')
            wDefn.AddFieldDefn(fDefn)
        else:
            cpes_print("Field exists:", uc)
    # copy features
    for feat in PE_Grid:
        newFeat=ogr.Feature(wDefn)
        oldGeom  = feat.GetGeometryRef()
        newGeom = oldGeom.Clone()
        newFeat.SetGeometry(newGeom)
        for i in range(feat.GetFieldCount()):

            name = feat.GetFieldDefnRef(i).GetName()
            newFeat.SetField(name,feat.GetField(name))
        for uc in unique_components:
            newFeat.SetField(uc,0)
        PE_Grid_working.CreateFeature(newFeat)
    PE_Grid.ResetReading()

    # Iterate through features for each component, add new field with the code prefix, test for intersection with PE_Grid and features, add DA
    for component_datasets in components_data_array:
        # Test for intersect between PE_Grid cells and data features
        for feature_class in component_datasets:
            fName = feature_class.GetName()
            t1 = process_time()

            #        # this variable is the component code prefix (e.g., DA_Eo_LD_CID16) at the current iteration step
            #         component = unique_components[component_datasets.index(feature_class)]

            # Create new field with same name as component code prefix and feature class
            #         arcpy.AddField_management(PE_Grid, feature_class, "SHORT")
            #         cpes_print("added field for feature_class:", feature_class)

            # Find intersected Geometry, mark as hit for the joined features
            for feat in GetFilteredFeatures(PE_Grid_working, feature_class):
                feat.SetField(fName,1)

            # cpes_print processing times for each feature class
            t2 = process_time()
            dt = t2 - t1
            processing[feature_class.GetName()] = round(dt, 2)  # update the processing time dictionary
            cpes_print(feature_class.GetName(), "time:", round(dt, 2), "seconds")

    #         break  # Development only
    #     break  # Development only

    t_stop = process_time()
    seconds = t_stop - t_start
    printTimeStamp(seconds)

    # cpes_print processing times to csv file
    cpes_print("Generating Time Series...")
    step1_time = pd.Series(processing, name='seconds')
    if 'step1_performance' in outputs:
        step1_time.to_csv(outputs['step1_performance'], header=True)

    cpes_print("Cleaning up...")
    return PE_Grid_working

def DetermineDAForComponents(PE_Grid,unique_components):
    """ Calculate DA step 2 of 4: Determine DA for each component (if multiple available datasets for a single component,
        DA is set to 1) """

    ### CODE TESTED AND SUCCESSFUL ###

    ### THIS CELL ONLY NEEDS EXECUTED ONCE ###

    ### THIS CELL IS NEEDED IN THE FINAL SCRIPT ###

    """ 
    NOTE: If this script is killed, it will result in an incomplete calculation of DA for a component field, resulting 
    in empty cells for that field. This is an issue since the code is not setup to overwrite DA for components.  To 
    resolve this, you need to delete the field (e.g., arcpy.DeleteField_management(in_table=PE_Grid, 
    drop_field='DA_HA_UD_CID39')) and re-run this section of code. ADDENDUM: Added 'try' statement and necessary logic 
    to address this automatically.  No action is needed by the user. 
    
    NOTE: Added code to replace None values (this action is no longer performed using replaceNULL in step 1). 
    Step 2: v8 (replaceNULL in step 1) takes 100 minutes (1.68 hours) to execute 
            v9 (None convert in step 2) takes 120 minutes          
    --> Handling the null values this way in step 2 increases runtime by 20 min, but reduces step 1 by ~3.9 hours. 
    """

    t_start = process_time()  # track processing time

    # Update field names
    field_names = ListFieldNames(PE_Grid)

    lyrDefn = PE_Grid.GetLayerDefn()
    for uc in unique_components:
        # TODO: verify that this is correct
        if uc not in field_names:
            cpes_print("Adding field:", uc)
            fDefn=ogr.FieldDefn(uc,ogr.OFTInteger)
            fDefn.SetDefault('0')
            lyrDefn.AddFieldDefn(fDefn)
        else:
            cpes_print("Field exists:", uc)

    # refresh features
    for feat in PE_Grid:
        for uc in unique_components:
            # TODO: verify that this is correct
            if uc not in field_names:
                feat.SetField(uc,0)
        PE_Grid.SetFeature(feat)

    # cpes_print processing time
    t_stop = process_time()
    seconds = t_stop - t_start
    printTimeStamp(seconds)

    return PE_Grid


def DistribDAOverDomains(PE_Grid,unique_components):
    """ Calculate DA step 3 of 4: Distribute DA across appropriate domain areas.  Assigns presence/absesnce
        for a dataset within a geologic domain.  Also creates a dictionary of DataFrames ('df_dict_LG_domains_ALL') for
        each component spatial type (e.g., 'LD') post-spatial distribution, and a master DataFrame with all components
        (local and domains) """

    ### CODE TESTED AND SUCCESSFUL ###

    ### THIS CELL NEEDS EXECUTED EACH SESSION ###

    ### THIS CELL WILL BE NEEDED IN THE FINAL SCRIPT ###


    t_start = process_time()  # track processing time

    # Create a list of local grid index values, then create DataFrame
    LG_index_values = FieldValues(PE_Grid, 'LG_index')
    df_index_cols = pd.DataFrame(LG_index_values, columns={'LG_index'})
    df_index_cols.set_index('LG_index',inplace=True)  # Set 'LG_index' as dataframe index
    df_dict_LG_domains_ALL = {"indicies": df_index_cols}  # This dict will contain all of the calculated DA fields

    # Add LG components to master DataFrame "df_dict_LG_domains_ALL"
    cpes_print("Adding LG_index components to master DataFrame...\n")
    LG_components = [i for i in unique_components if 'LG' in i]  # List of LG components
    LG_cols = {'LG_index': LG_index_values}  # Include LG_index for joining
    for i in LG_components:
        LG_cols[i] = FieldValues(PE_Grid, i)
    df_LG_fieldvalues = pd.DataFrame(LG_cols)
    df_LG_fieldvalues.set_index('LG_index', inplace=True)  # Set 'LG_index' as dataframe index
    df_dict_LG_domains_ALL['LG'] = df_index_cols.join(df_LG_fieldvalues)

    # Determine which domain types have available datasets for the AOI
    domainTypes_ALL = ["LD", "SD", "SA", "UD"]
    domainTypes = []
    for domainType in domainTypes_ALL:
        count = [i for i in unique_components if domainType in i]
        if len(count) > 0:
            domainTypes.append(domainType)

    # Create a dict of lists for each domain type (components with domain subtext (e.g., LD) in the name)
    domainType_components = {}

    # Distribute presence across domain for each domain type
    for domainType in domainTypes:

        cpes_print(domainType, "distribution started...")

        # Create a list of domain index values (e.g, LD1, LD2, LD3, LD4), then add to DataFrame
        domainType_index_values = FieldValues(PE_Grid, domainType + '_index')
        df_index_cols[domainType + '_index'] = domainType_index_values
        df_index_cols.fillna(value={domainType + '_index': 0}, inplace=True)
        cpes_print("created list of domain index values")

        # Update dict of lists for each domain type
        domainType_components[domainType] = [i for i in unique_components if domainType in i]

        # Create DataFrame with values for records for each domainType
        domain_cols = {'LG_index': LG_index_values}  # Include LG_index for joining
        for i in domainType_components[domainType]:
            domain_cols[i] = FieldValues(PE_Grid, i)
        df_domainType_fieldvalues = pd.DataFrame(domain_cols)
        df_domainType_fieldvalues.set_index('LG_index', inplace=True)  # Set 'LG_index' as dataframe index
        cpes_print("created dataframe with values for records")

        # Join into a new DataFrame the domainType_index and domainType_components/values columns
        df_domainType_joined = df_index_cols.join(df_domainType_fieldvalues, sort=False)

        # Group by unique domainType_index values
        df_domainType_grouped = df_domainType_joined.groupby([domainType + '_index'])

        # Determine max of DA for each domainType_index group, return in "DA_...domainType..._distributed" column
        df_domainType_max = df_domainType_grouped.max()
        for i in domainType_components[domainType]:
            df_domainType_max.rename(columns={i: (i + "_distributed")}, inplace=True)
        # df_domainType_max.drop(['LG_index'], axis=1, inplace=True)  # LG_index is erroneously overwritten without this line

        # Join index and DA_max columns in a new DataFrame
        #     df_domainType_export = df_index_cols.merge(df_domainType_max, on = domainType + '_index')
        df_domainType_export = df_index_cols.join(df_domainType_max, on=domainType + '_index')
        #     df_domainType_all = df_domainType_joined.merge(df_domainType_max, on = domainType + '_index')

        # Combine all domain types into a list/dict of DataFrames
        #     df_domainALL = df_domainType_joined.join(df_domainType_export, on='LG_index', lsuffix='', rsuffix='_from'+domainType)
        df_dict_LG_domains_ALL[domainType] = df_domainType_export.copy()

        cpes_print(domainType, "distribution finished.\n")
        df_index_cols.drop( columns=[domainType + '_index'],inplace=True)

    cpes_print("All domain types distributed.\n")

    # Compile a master dataframe in 'df_dict_LG_domains_ALL' for all spatial types (local and domains)
    spatialTypes = domainTypes.copy()  # Create a list for all spatial types
    spatialTypes.insert(0, 'LG')  # Include 'LG_index' for joining
    df_dict_LG_domains_ALL['compiled'] = df_dict_LG_domains_ALL['indicies'].copy()  # This is the master dataframe
    for i in spatialTypes:
        df_dict_LG_domains_ALL['compiled'] = df_dict_LG_domains_ALL['compiled'].join(df_dict_LG_domains_ALL[i], lsuffix='',
                                                                                     rsuffix='_from' + i)

    # Create a copy of LG component columns (named "..._local") to serve as QA/QC record
    for i in LG_components:
        df_dict_LG_domains_ALL['LG'][i + "_local"] = df_dict_LG_domains_ALL['LG'][i].copy()

    ### SECTION BELOW MAY BE COMMENTED OUT IF FILES ALREADY EXIST ###

    # # Export dataframes to csv and ArcGIS tables
    # for domainType in domainTypes:

    #     cpes_print(domainType, "export started...")

    #     # Export domainType DataFrame as CSV
    #     exported_df_domainType = workspace_dir + "/" + domainType + r"_domains_exported_df.csv"
    #     df_dict_LG_domains_ALL[domainType].to_csv(exported_df_domainType, index=False)

    #     # Convert the DataFrame CSV file to ArcGIS table
    #     inTable = exported_df_domainType
    #     outLocation = workspace
    #     outTable = str(domainType + "_domain_distributed_df_table")
    #     try:
    #         arcpy.TableToTable_conversion(inTable, outLocation, outTable)
    #     except:
    #         cpes_print(str(domainType + "_index"), "ArcGIS table already exists... deleting and trying again!")
    #         arcpy.Delete_management(outTable)
    #         arcpy.TableToTable_conversion(inTable, outLocation, outTable)
    #         cpes_print(str(domainType + "_index"), "DataFrame csv converted to ArcGIS table!")

    #     # Join DataFrame table to PE_Grid
    #     inFeatures = PE_Grid
    #     joinField = "LG_index"
    #     joinTable = outTable
    #     fieldList = list(df_dict_LG_domains_ALL[domainType].columns)
    #     fieldList.remove("LG_index")  # exclude indicies from fields to join
    #     for domType in domainTypes:
    #         try:
    #             fieldList.remove(str(domType + "_index")) # exclude indicies from fields to join
    #         except:
    #             cpes_print("Unable to remove unnecessary fields from Join list... they may not exist.")
    #     cpes_print("Joining", joinTable, "to", PE_Grid)
    #     arcpy.JoinField_management(inFeatures, joinField, joinTable, joinField, fieldList)

    #     cpes_print(domainType, "exported.\n")

    # cpes_print('\nAll done.')

    # # number of cells with data in each LD domain
    # df_domainALL['LD']['LD_index'].value_counts()

    # # number of cells with data in each UD domain
    # df_domainALL['UD']['UD_index'].value_counts()


    # cpes_print processing time
    t_stop = process_time()
    seconds = t_stop - t_start
    printTimeStamp(seconds)

    return df_dict_LG_domains_ALL

def CalcSumDA(df_dict_LG_domains_ALL,inFeatures,outputs):
    """ Calculate DA step 4 of 4: Calculate sum(DA) for each REE emplacement type (explicit tally of components;
        not implicit score) """

    ### THIS CODE WILL BE IN FINAL SCRIPT ###

    ### TESTED AND SUCCESSFUL ###

    t_start = process_time()  # track processing time

    # Comprehensive list of all possible components, including those deemed 'not testable' and
    # 'not evalutated (duplicate)'.  This list current as of 2020-03-24.  Values copied from Google Sheet
    # "REE Enrichment Tree Related Data - Google Sheets 'Component_Codes_asof_2020-03-24'!Y2:FR2"
    componentsALL = ['DA_Fl_LD_CID01', 'DA_Fl_LD_CID02', 'DA_Fl_LD_CID03', 'DA_Fl_LD_CID04', 'DA_Fl_LD_CID05',
                     'DA_Fl_LD_CID06', 'DA_Fl_LD_CID07', 'DA_Fl_LD_CID08', 'DA_Fl_LD_CID09', 'DA_Eo_LD_CID10',
                     'DA_Fl_NE_CID11', 'DA_Fl_NE_CID12', 'DA_Fl_NE_CID13', 'DA_Eo_LG_CID14', 'DA_Eo_LG_CID15',
                     'DA_Eo_LD_CID16', 'DA_Fl_LD_CID17', 'DA_Fl_LG_CID18', 'DA_Fl_NT_CID19', 'DA_Fl_LD_CID19',
                     'DA_Eo_NT_CID20', 'DA_Fl_NT_CID20', 'DA_Eo_NT_CID21', 'DA_Eo_LD_CID21', 'DA_Eo_NE_CID21',
                     'DA_Eo_NT_CID22', 'DA_Eo_NT_CID23', 'DA_MA_LD_CID24', 'DA_MA_LD_CID25', 'DA_MA_LD_CID26',
                     'DA_MA_LD_CID27', 'DA_MA_LD_CID28', 'DA_MA_LD_CID29', 'DA_MA_LD_CID30', 'DA_MA_LD_CID31',
                     'DA_MA_LD_CID32', 'DA_MA_NE_CID33', 'DA_MA_NE_CID34', 'DA_MA_NE_CID35', 'DA_MA_NE_CID36',
                     'DA_MA_UD_CID37', 'DA_MA_UD_CID38', 'DA_MA_UD_CID39', 'DA_MA_UD_CID40', 'DA_MA_UD_CID41',
                     'DA_MA_LG_CID42', 'DA_MA_UD_CID43', 'DA_MA_NT_CID44', 'DA_HP_UD_CID45', 'DA_HP_LG_CID46',
                     'DA_MA_LG_CID47', 'DA_MA_LG_CID48', 'DA_MA_LG_CID49', 'DA_MA_LG_CID50', 'DA_MA_NT_CID51',
                     'DA_MA_LG_CID52', 'DA_MA_NT_CID53', 'DA_MA_LG_CID54', 'DA_MP_NT_CID55', 'DA_MP_LG_CID56',
                     'DA_MP_LG_CID57', 'DA_MP_NT_CID58', 'DA_MA_NT_CID59', 'DA_Fl_LD_CID10', 'DA_Fl_NT_CID21',
                     'DA_Fl_LD_CID21', 'DA_Fl_NE_CID21', 'DA_Fl_NT_CID22', 'DA_Fl_NT_CID23', 'DA_MP_LD_CID24',
                     'DA_MP_LD_CID25', 'DA_MP_LD_CID26', 'DA_MP_LD_CID27', 'DA_MP_LD_CID28', 'DA_MP_LD_CID29',
                     'DA_MP_LD_CID30', 'DA_MP_LD_CID31', 'DA_MP_LD_CID32', 'DA_MP_NE_CID33', 'DA_MP_NE_CID34',
                     'DA_MP_NE_CID35', 'DA_MP_NE_CID36', 'DA_MP_UD_CID37', 'DA_MP_UD_CID38', 'DA_MP_UD_CID39',
                     'DA_MP_UD_CID40', 'DA_MP_UD_CID41', 'DA_MP_LG_CID42', 'DA_MP_UD_CID43', 'DA_MP_NT_CID44',
                     'DA_HA_LG_CID47', 'DA_HA_LG_CID48', 'DA_HA_LG_CID49', 'DA_MP_LG_CID50', 'DA_MP_NT_CID51',
                     'DA_MP_LG_CID52', 'DA_MP_NT_CID53', 'DA_HA_LG_CID54', 'DA_HP_NT_CID55', 'DA_HP_LG_CID56',
                     'DA_HP_LG_CID57', 'DA_HP_NT_CID58', 'DA_HA_NT_CID59', 'DA_HA_LD_CID24', 'DA_HA_LD_CID25',
                     'DA_HA_LD_CID26', 'DA_HA_LD_CID27', 'DA_HA_LD_CID28', 'DA_HA_LD_CID29', 'DA_HA_LD_CID30',
                     'DA_HA_LD_CID31', 'DA_HA_LD_CID32', 'DA_HA_NE_CID33', 'DA_HA_NE_CID34', 'DA_HA_NE_CID35',
                     'DA_HA_NE_CID36', 'DA_HA_UD_CID37', 'DA_HA_UD_CID38', 'DA_HA_UD_CID39', 'DA_HA_UD_CID40',
                     'DA_HA_UD_CID41', 'DA_HA_LG_CID42', 'DA_HA_UD_CID43', 'DA_HA_UD_CID45', 'DA_HA_LG_CID50',
                     'DA_HA_NT_CID51', 'DA_HA_LG_CID52', 'DA_HA_NT_CID53', 'DA_HP_LD_CID24', 'DA_HP_LD_CID25',
                     'DA_HP_LD_CID26', 'DA_HP_LD_CID27', 'DA_HP_LD_CID28', 'DA_HP_LD_CID29', 'DA_HP_LD_CID30',
                     'DA_HP_LD_CID31', 'DA_HP_LD_CID32', 'DA_HP_NE_CID33', 'DA_HP_NE_CID34', 'DA_HP_NE_CID35',
                     'DA_HP_NE_CID36', 'DA_HP_UD_CID37', 'DA_HP_UD_CID38', 'DA_HP_UD_CID39', 'DA_HP_UD_CID40',
                     'DA_HP_UD_CID41', 'DA_HP_LG_CID42', 'DA_HP_UD_CID43', 'DA_HP_LG_CID50', 'DA_HP_NT_CID51']

    # Create dict of unique_components for each emplacement mechanism with data in the geodatabase
    mechanismTypes = ['Eo', 'Fl', 'HA', 'HP', 'MA', 'MP']
    mechanismComponents = {}
    for mechanism in mechanismTypes:
        mechanismComponents[mechanism] = [i for i in unique_components if mechanism in i]

    # Create dict of all possible components (including those that are untestable) for each emplacement mechanism
    mechanismComponentsALL = {}
    for mechanism in mechanismTypes:
        mechanismComponentsALL[mechanism] = sorted([i for i in componentsALL if mechanism in i])

    # # DEVELOPMENT ONLY: Create a list of components that are 'not testable' or 'not evaluated', set to 'False'
    # NotTestable = []
    # for k in mechanismComponentsALL.keys():
    #     I = [x for x in mechanismComponentsALL[k] if 'N' in x]
    #     for i in I:
    #         NotTestable.append(i)
    # for i in NotTestable:
    #     df_PE_calc[i] = False

    # Create a copy of the DataFrame that contains post-processed tallies.
    df_keys = df_dict_LG_domains_ALL.keys()
    df_dict_PostProcessed = {}
    for key in df_keys:
        df_dict_PostProcessed[key] = df_dict_LG_domains_ALL[key].copy()

    # Rename fields to simplified component names (e.g., remove "_distributed", etc.)
    sel = df_dict_PostProcessed['compiled'].columns  # list of fields
    rename_fields = [i for i in sel if "_distributed" in i]  # list of fields to be renamed
    for i in rename_fields:
        df_dict_PostProcessed['compiled'].rename(columns={i: (i[:14])}, inplace=True)

        # Create an 'empty' dataframe that has columns for all components and row values = 'False'
    df_PE_empty = df_dict_LG_domains_ALL['indicies'].copy()
    for component in componentsALL:
        df_PE_empty[component] = False

    # Create new DataFrame (df_PE_calc), update values from PostProcessed DataFrame
    df_PE_calc = df_PE_empty.copy()
    df_PE_calc.update(df_dict_PostProcessed['compiled'])

    ############################################################################################################

    ### Generic assignment for all cells (DA)
    df_PE_calc['DA_Eo_NT_CID20'] = True  # Accumulation of peat
    df_PE_calc['DA_Fl_NT_CID20'] = True  # Accumulation of peat

    df_PE_calc['DA_Fl_NT_CID22'] = True  # Burial of peat

    df_PE_calc['DA_Fl_NT_CID23'] = True  # Conversion of peat to coal

    df_PE_calc['DA_HA_LG_CID52'] = True  # Coal and/or related strata
    df_PE_calc['DA_HP_LG_CID52'] = True  # Coal and/or related strata
    df_PE_calc['DA_MA_LG_CID52'] = True  # Coal and/or related strata
    df_PE_calc['DA_MP_LG_CID52'] = True  # Coal and/or related strata

    ### Powder River Basin assignment for all cells (DA)
    df_PE_calc['DA_Eo_LG_CID14'] = True  # Mire downwind of volcanism (this is true for PRB)
    df_PE_calc['DA_Fl_LD_CID17'] = True  # Mire in same paleo-drainage basin
    df_PE_calc['DA_Fl_LG_CID18'] = True  # Mire downstream of REE source

    ############################################################################################################

    ### Eo relevant components.  Not testable: CID15, CID21


    ### Fl relevant components.  Not testable: CID17, CID18, CID19, CID21
    df_PE_calc['DA_Fl_NE_CID11'] = df_PE_calc[['DA_Fl_LD_CID01', 'DA_Fl_LD_CID02', 'DA_Fl_LD_CID03', 'DA_Fl_LD_CID04',
                                               'DA_Fl_LD_CID05', 'DA_Fl_LD_CID06']].max(axis=1)  # Bedrock REE deposit
    df_PE_calc['DA_Fl_NE_CID12'] = df_PE_calc[['DA_Fl_LD_CID07', 'DA_Fl_LD_CID08', 'DA_Fl_LD_CID09']].max(
        axis=1)  # Sed REE deposit
    df_PE_calc['DA_Fl_NE_CID13'] = df_PE_calc[['DA_Fl_LD_CID10', 'DA_Fl_NE_CID11', 'DA_Fl_NE_CID12']].max(
        axis=1)  # REE source

    ### HA relevant components.  Not testable: CID47, CID48, CID49, CID51, CID53, CID59
    df_PE_calc['DA_HA_NE_CID33'] = df_PE_calc[['DA_HA_UD_CID37', 'DA_HA_UD_CID38', 'DA_HA_UD_CID39',
                                               'DA_HA_UD_CID40', 'DA_HA_UD_CID41']].max(axis=1)  # Alkaline volcanic ash
    df_PE_calc['DA_HA_NE_CID34'] = df_PE_calc[['DA_HA_LD_CID24', 'DA_HA_LD_CID25', 'DA_HA_LD_CID26',
                                               'DA_HA_LD_CID27', 'DA_HA_LD_CID28', 'DA_HA_LD_CID29']].max(
        axis=1)  # Bedrock REE deposit
    df_PE_calc['DA_HA_NE_CID35'] = df_PE_calc[['DA_HA_LD_CID30', 'DA_HA_LD_CID31', 'DA_HA_LD_CID32']].max(
        axis=1)  # Sed REE deposit
    df_PE_calc['DA_HA_NE_CID36'] = df_PE_calc[['DA_HA_NE_CID33', 'DA_HA_NE_CID34', 'DA_HA_NE_CID35']].max(
        axis=1)  # REE source
    df_PE_calc['DA_HA_NE_42_43'] = df_PE_calc[['DA_HA_LG_CID42', 'DA_HA_UD_CID43']].max(axis=1)  # Conduit for fluid flow

    ### HP relevant components.  Not testable: CID47, CID48, CID49, CID51, CID53, CID55, CID58
    df_PE_calc['DA_HP_NE_CID33'] = df_PE_calc[['DA_HP_UD_CID37', 'DA_HP_UD_CID38', 'DA_HP_UD_CID39',
                                               'DA_HP_UD_CID40', 'DA_HP_UD_CID41']].max(axis=1)  # Alkaline volcanic ash
    df_PE_calc['DA_HP_NE_CID34'] = df_PE_calc[['DA_HP_LD_CID24', 'DA_HP_LD_CID25', 'DA_HP_LD_CID26',
                                               'DA_HP_LD_CID27', 'DA_HP_LD_CID28', 'DA_HP_LD_CID29']].max(
        axis=1)  # Bedrock REE deposit
    df_PE_calc['DA_HP_NE_CID35'] = df_PE_calc[['DA_HP_LD_CID30', 'DA_HP_LD_CID31', 'DA_HP_LD_CID32']].max(
        axis=1)  # Sed REE deposit
    df_PE_calc['DA_HP_NE_CID36'] = df_PE_calc[['DA_HP_NE_CID33', 'DA_HP_NE_CID34', 'DA_HP_NE_CID35']].max(
        axis=1)  # REE source
    df_PE_calc['DA_HP_NE_42_43'] = df_PE_calc[['DA_HP_LG_CID42', 'DA_HP_UD_CID43']].max(axis=1)  # Conduit for fluid flow
    df_PE_calc['DA_HP_NE_57_46'] = df_PE_calc[['DA_HP_LG_CID57', 'DA_HP_LG_CID46']].max(axis=1)  # Dissolve phosphorus

    ### MA relevant components.  Not testable:  CID44, CID47, CID48, CID49, CID51, CID53, CID59
    df_PE_calc['DA_MA_NE_CID33'] = df_PE_calc[['DA_MA_UD_CID37', 'DA_MA_UD_CID38', 'DA_MA_UD_CID39',
                                               'DA_MA_UD_CID40', 'DA_MA_UD_CID41']].max(axis=1)  # Alkaline volcanic ash
    df_PE_calc['DA_MA_NE_CID34'] = df_PE_calc[['DA_MA_LD_CID24', 'DA_MA_LD_CID25', 'DA_MA_LD_CID26',
                                               'DA_MA_LD_CID27', 'DA_MA_LD_CID28', 'DA_MA_LD_CID29']].max(
        axis=1)  # Bedrock REE deposit
    df_PE_calc['DA_MA_NE_CID35'] = df_PE_calc[['DA_MA_LD_CID30', 'DA_MA_LD_CID31', 'DA_MA_LD_CID32']].max(
        axis=1)  # Sed REE deposit
    df_PE_calc['DA_MA_NE_CID36'] = df_PE_calc[['DA_MA_NE_CID33', 'DA_MA_NE_CID34', 'DA_MA_NE_CID35']].max(
        axis=1)  # REE source
    df_PE_calc['DA_MA_NE_42_43'] = df_PE_calc[['DA_MA_LG_CID42', 'DA_MA_UD_CID43']].max(axis=1)  # Conduit for fluid flow

    ### MP relevant components.  Not testable: CID47, CID48, CID49, CID51, CID53, CID55, CID58
    df_PE_calc['DA_MP_NE_CID33'] = df_PE_calc[['DA_MP_UD_CID37', 'DA_MP_UD_CID38', 'DA_MP_UD_CID39',
                                               'DA_MP_UD_CID40', 'DA_MP_UD_CID41']].max(axis=1)  # Alkaline volcanic ash
    df_PE_calc['DA_MP_NE_CID34'] = df_PE_calc[['DA_MP_LD_CID24', 'DA_MP_LD_CID25', 'DA_MP_LD_CID26',
                                               'DA_MP_LD_CID27', 'DA_MP_LD_CID28', 'DA_MP_LD_CID29']].max(
        axis=1)  # Bedrock REE deposit
    df_PE_calc['DA_MP_NE_CID35'] = df_PE_calc[['DA_MP_LD_CID30', 'DA_MP_LD_CID31', 'DA_MP_LD_CID32']].max(
        axis=1)  # Sed REE deposit
    df_PE_calc['DA_MP_NE_CID36'] = df_PE_calc[['DA_MP_NE_CID33', 'DA_MP_NE_CID34', 'DA_MP_NE_CID35']].max(
        axis=1)  # REE source
    df_PE_calc['DA_MP_NE_42_43'] = df_PE_calc[['DA_MP_LG_CID42', 'DA_MP_UD_CID43']].max(axis=1)  # Conduit for fluid flow

    ############################################################################################################
    # DR components (NOTE: this is NOT the entire list of DR components; only those that are considered testable)
    DR_Eo = ['DA_Eo_LD_CID10', 'DA_Eo_LG_CID14', 'DA_Eo_LD_CID16', 'DA_Fl_NT_CID22', 'DA_Fl_NT_CID23']
    DR_Fl = ['DA_Fl_NE_CID13', 'DA_Fl_NT_CID20', 'DA_Fl_NT_CID22', 'DA_Fl_NT_CID23']
    DR_HA = ['DA_HA_NE_42_43', 'DA_HA_LG_CID52', 'DA_HA_NE_CID36', 'DA_HA_UD_CID45', 'DA_HA_LG_CID50', 'DA_HA_LG_CID54']
    DR_HP = ['DA_HP_NE_42_43', 'DA_HP_LG_CID52', 'DA_HP_NE_CID36', 'DA_HP_UD_CID45', 'DA_HP_LG_CID50', 'DA_HP_LG_CID56',
             'DA_HP_NE_57_46']
    DR_MA = ['DA_MA_NE_42_43', 'DA_MA_LG_CID52', 'DA_MA_NE_CID36', 'DA_MA_LG_CID50', 'DA_MA_LG_CID54']
    DR_MP = ['DA_MP_NE_42_43', 'DA_MP_LG_CID52', 'DA_MP_NE_CID36', 'DA_MP_LG_CID50', 'DA_MP_LG_CID56']

    DR_Types = [DR_Eo, DR_Fl, DR_HA, DR_HP, DR_MA, DR_MP]  # A list of required components (DR) for each mechanism type
    ############################################################################################################


    # Add sum fields to dataframe
    df_PE_calc['Eo_sum'] = df_PE_calc[DR_Eo].sum(axis=1)
    df_PE_calc['Fl_sum'] = df_PE_calc[DR_Fl].sum(axis=1)
    df_PE_calc['HA_sum'] = df_PE_calc[DR_HA].sum(axis=1)
    df_PE_calc['HP_sum'] = df_PE_calc[DR_HP].sum(axis=1)
    df_PE_calc['MA_sum'] = df_PE_calc[DR_MA].sum(axis=1)
    df_PE_calc['MP_sum'] = df_PE_calc[DR_MP].sum(axis=1)

    # # Display DA_sums
    # DAsum_cols = []
    # for mech in mechanismTypes:
    #     DAsum_cols.append(mech + '_sum')
    # df_PE_calc[DAsum_cols].describe()

    # Calculate DA_sum/DR
    DAsumDR_cols = []  # To be columns of DA_sum / DR
    for i in range(len(DR_Types)):
        col = FeatureDataset + '_' + DR_Types[i][0][3:5] + '_sum_DR'  # Assemble column heading (e.g., 'DA_Eo_sum_DR')
        df_PE_calc[col] = df_PE_calc[DR_Types[i][0][3:5] + '_sum'] / len(
            DR_Types[i])  # Divide mechanism sum by DR (e.g., Eo_sum / DR_Eo)
        DAsumDR_cols.append(col)  # Append column name to this list

    # df_PE_calc[DAsumDR_cols].describe()

    joinField = 'LG_index'
    fieldList = list(DAsumDR_cols)
    cpes_print('Joining DA Data frames to',inFeatures.GetName())
    OgrPandasJoin(inFeatures,joinField,df_PE_calc,copyFields=fieldList)

    # Print processing time
    t_stop = process_time()
    seconds = t_stop - t_start
    printTimeStamp(seconds)


if __name__=='__main__':
    t_allStart = process_time()

    gdal.UseExceptions()
    from argparse import ArgumentParser

    prsr = ArgumentParser(description="Calculate the PE score.")
    prsr.add_argument('gdbPath',type=str,help="Path to the GDB file to process.")
    prsr.add_argument('workspace',type=REE_Workspace,help="The workspace directory.")
    prsr.add_argument('output_dir',type=REE_Workspace,help="Path to the output directory.")
    prsr.add_argument('--input_grid',type=str, dest='IN_PE_Grid_file',default='PE_Grid_file',help="The grid file created from 'Create_PE_Grid.py'.")
    prsr.add_argument('--final_grid', type=str, dest='OUT_final_grid',default='PE_Grid_Calc.kml', help="The name of the output file.")
    prsr.add_argument('--step1_performance_csv', type=str, dest='OUT_step1_performance',help="Optional output of step 1 processing times.")

    args = prsr.parse_args()
    ParseWorkspaceArgs(vars(args),args.workspace,args.output_dir)

    gdbDS=gdal.OpenEx(args.gdbPath,gdal.OF_VECTOR)
    PE_Grid_DS = gdal.OpenEx(args.workspace['PE_Grid_file'],gdal.OF_VECTOR)
    PE_Grid = PE_Grid_DS.GetLayer(0)

    cpes_print('Finding components...',end='')
    unique_components,components_data_array = FindUniqueComponents(gdbDS)
    cpes_print('Done')
    drvr = gdal.GetDriverByName('memory')
    scratchDS=drvr.Create('scratch',0,0,0,gdal.OF_VECTOR)

    workingLyr=DAFeaturesPresent(PE_Grid,unique_components,components_data_array,scratchDS,args.output_dir)
    cpes_print("\nStep 1 complete")

    # workingLyr=DetermineDAForComponents(workingLyr,unique_components)
    # cpes_print("\nStep 2 complete")

    df_dict_LG_domains_ALL=DistribDAOverDomains(workingLyr,unique_components)
    cpes_print("\nStep 3 complete")

    CalcSumDA(df_dict_LG_domains_ALL,workingLyr,args.output_dir)
    cpes_print("\nStep 4 complete")

    # scratchDS.FlushCache()
    WriteIfRequested(workingLyr,args.output_dir,'final_grid',drvrName='KML',printFn=cpes_print)

    cpes_print("Done.")

    t_allStop = process_time()
    seconds = t_allStop - t_allStart
    cpes_print('Total time:',end=' ')
    printTimeStamp(seconds)