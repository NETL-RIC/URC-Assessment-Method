""" Create lists for unique components and each corresponding dataset """

### CODE TESTED AND SUCCESSFUL ###

### COMMENT FOR DEVELOPMENT: RUN THIS CELL FOR EACH SESSION ###

### THIS CELL IS NEEDED IN THE FINAL SCRIPT ###


from common_utils import *
from time import process_time
import pandas as pd

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

workspace = workspace_dir + "/" + workspace_gdb

# Set ArcGIS workspace environment
arcpy.env.workspace = workspace
PE_Grid = workspace + "/" + PE_Grid_file


######################################################################################################################
def ListFeatureClasses(WildCard, FeatureDataset, fullname, first_char, last_char):
    """
    Function that creates a list of all unique REE-Coal components in an ESRI GDB Feature Dataset, for use in use in
        calculating PE score from DA and DS databases.

    Parameters
    ----------
    WildCard: <str>
        Criteria used to limit the results returned
    FeatureDataset: <str>
        Name of the feature dataset
    fullname: <str>
        Yes or no to return the full filenames.  Yes must be entered as 'y' or 'yes'.
    first_char: <str>
        Index of first character to include in the filename
    last_char: <str>
        Index of last character to include in the filename

    Returns
    -------
    <list>
        sorted, non-repeating iterable sequence of feature class names based on the WildCard criteria
    """

    feature_list = arcpy.ListFeatureClasses(WildCard, feature_dataset=FeatureDataset)  # list all feature classes

    fc_names = []  # create empty

    # extract code prefixes from all feature classes
    if fullname == 'y' or fullname == 'yes':
        for features in feature_list:
            fc_names.append(features)  # extract all characters in the filename
    else:
        for features in feature_list:
            fc_names.append(features[first_char:last_char])  # extract only a portion of the filename

    fc_names = list(set(fc_names))  # sort and filter out repeated values, convert to list from dictionary

    return sorted(fc_names)


######################################################################################################################
def replaceNULL(feature_class : ogr.Layer, field : str):
    """
    Replace NULL values with zeros for a field in a feature class

    Parameters
    ----------
    feature_class: <str>
        Name of feature class containing the field to be modified
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


def DAFeaturesPresent():
    """ Calculate DA step 1 of 4: Presence/absence for each feature class in the DA Feature Dataset.
        Creates a new field in PE_Grid for each feature class in the geodatabase """

    # Create a list of all unique code prefixes for the component IDs
    unique_components = ListFeatureClasses(WildCard="DA*", FeatureDataset="DA", fullname='no', first_char=0, last_char=14)

    # An array comprising all components and their respective feature classes
    components_data_array = []

    # Generate a list of feature classes for each Emplacement Type, Influence Extent, AND Component ID combination
    for component_datasets in unique_components:
        #     print("component_datasets:", component_datasets, "\n")
        component_datasets = ListFeatureClasses(WildCard=(component_datasets + "*"), FeatureDataset="DA", fullname='yes',
                                                first_char=0, last_char=8)
        #     print("component_datasets:", component_datasets, "\n")
        # Append list to a single array
        components_data_array.append(component_datasets)

    # del(component_datasets)

    # List field names
    field_names = ListFieldNames(PE_Grid)

    print("PE_Grid attributes:", field_names, "\n")


    ### CODE TESTED AND SUCCESSFUL ###

    """ THIS CELL ONLY NEEDS EXECUTED ONCE (TAKES ~6.9 HOURS TO EXECUTE WHEN USING replaceNULL (v8)) """

    ### THIS CELL IS NEEDED IN THE FINAL SCRIPT ###

    t_start = process_time()  # track processing time

    processing = {}  # dictionary for processing time

    # Iterate through features for each component, add new field with the code prefix, test for intersection with PE_Grid and features, add DA
    for component_datasets in components_data_array:
        # Test for intersect between PE_Grid cells and data features
        for feature_class in component_datasets:
            t1 = process_time()

            #        # this variable is the component code prefix (e.g., DA_Eo_LD_CID16) at the current iteration step
            #         component = unique_components[component_datasets.index(feature_class)]

            # Create new field with same name as component code prefix and feature class
            #         arcpy.AddField_management(PE_Grid, feature_class, "SHORT")
            #         print("added field for feature_class:", feature_class)

            # Select layer by location
            selection = arcpy.SelectLayerByLocation_management(in_layer=PE_Grid,
                                                               overlap_type="INTERSECT",
                                                               select_features=feature_class,
                                                               search_distance="",
                                                               selection_type="NEW_SELECTION",
                                                               invert_spatial_relationship="NOT_INVERT")
            #         print("selected layer for feature_class:", feature_class)

            # Create new layer from selection
            selection_lyr = arcpy.CopyFeatures_management(selection, feature_class + "_selected")
            #         print("copied layer for selection_lyr:", selection_lyr)

            # Delete from PE_Grid the field with same name as component code prefix and feature class
            #         arcpy.DeleteField_management(in_table=PE_Grid, drop_field=feature_class)
            #         print("deleted field for feature_class:", feature_class)

            # Set select field to 1
            calc_field = arcpy.CalculateField_management(in_table=selection_lyr,
                                                         field=feature_class,
                                                         expression="1",
                                                         expression_type="PYTHON3",
                                                         code_block="")
            #         print("calculated field for feature_class:", feature_class)

            # Join field to PE_Grid (add DA_component_featureclass field from 'selection')
            join_field = arcpy.JoinField_management(in_data=PE_Grid,
                                                    in_field="LG_index",
                                                    join_table=selection_lyr,
                                                    join_field="LG_index",
                                                    fields=feature_class)
            #         print("joined field for feature_class:", feature_class, "\n")

            # Replace Null values for the DA_featureclass field
            #         replaceNULL(PE_Grid, feature_class)

            # Delete selection layer from the geodatabase
            arcpy.Delete_management(selection_lyr)

            # print processing times for each feature class
            t2 = process_time()
            dt = t2 - t1
            processing[feature_class] = round(dt, 2)  # update the processing time dictionary
            print(feature_class, "time:", round(dt, 2), "seconds")

    #         break  # Development only
    #     break  # Development only

    t_stop = process_time()
    seconds = t_stop - t_start
    minutes = seconds / 60
    hours = minutes / 60

    print("Runtime:", round(seconds, 2), "seconds")
    print("Runtime:", round(minutes, 2), "minutes")
    print("Runtime:", round(hours, 2), "hours")

    # Print processing times to csv file
    step1_time = pd.Series(processing, name='seconds')
    step1_time.to_csv(workspace_dir + '\step1_time.csv', header=True)



def DetermineDAForComponents():
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

    # Iterate through all components, create new field (if necessary), and determine DA
    for i in range(len(unique_components)):

        #     LIMITER FOR DEVELOPMENT ONLY
        #     if i == 2:
        #         break

        # A list containing the unique component and corresponding feature datasets (that are represented as fields in PE_Grid)
        component_fields = [unique_components[i]] + components_data_array[i]

        # Create a new field for unique_component if it does not already exist
        present = 0
        for indiv_field in field_names:
            if indiv_field == unique_components[i]:
                present = present + 1
            else:
                present = present + 0
        if not present:
            # Add new field for unique_component
            arcpy.AddField_management(PE_Grid, unique_components[i], "SHORT")
            print("Added new field:", unique_components[i])
            # Assign DA value for each component
            with arcpy.da.UpdateCursor(PE_Grid, component_fields) as cursor:
                for row in cursor:
                    row[0] = 0  # Set the component field to zero to start (e.g., 'DA_Eo_LD_CID10' = 0)
                    convert = lambda x: x or '0'
                    row_strings = [convert(x) for x in row]  # Replace 'None' with '0'
                    row_ints = list(map(int, row_strings))  # Convert strings to integers
                    row[0] = max(row_ints)  # Determine if any datasets are present
                    cursor.updateRow(row)  # Update the cursor with the updated list
        else:
            print("Field already exists for:", unique_components[i])
            try:
                # The sum function will throw an error if there are any empty cells (due to this code being killed previously)
                fv = FieldValues(PE_Grid, unique_components[i])
                sum(fv)
            except:
                # If error, delete field and recalculate DA
                print("  Encountered an error with:", unique_components[i], "\n  ...trying again from scractch...")
                arcpy.DeleteField_management(in_table=PE_Grid, drop_field=unique_components[i])
                arcpy.AddField_management(PE_Grid, unique_components[i], "SHORT")
                print("  Deleted and re-added field:", unique_components[i])
                with arcpy.da.UpdateCursor(PE_Grid, component_fields) as cursor:
                    for row in cursor:
                        row[0] = 0  # Set the component field to zero to start (e.g., 'DA_Eo_LD_CID10' = 0)
                        convert = lambda x: x or '0'
                        row_strings = [convert(x) for x in row]  # Replace 'None' with '0'
                        row_ints = list(map(int, row_strings))  # Convert strings to integers
                        row[0] = max(row_ints)  # Determine if any datasets are present
                        cursor.updateRow(row)  # Update the cursor with the updated list
    #             fv = FieldValues(PE_Grid, unique_components[i])
    #             print("Sum:", sum(fv))

    # Update field names
    field_names = ListFieldNames(PE_Grid)

    # Print processing time
    t_stop = process_time()
    seconds = t_stop - t_start
    minutes = seconds / 60
    hours = minutes / 60

    print("Runtime:", round(seconds, 2), "seconds")
    print("Runtime:", round(minutes, 2), "minutes")
    print("Runtime:", round(hours, 2), "hours")

def FieldValues(table, field):
    """
    Create a list of unique values from a field in a feature class.

    Parameters
    ----------
    table: <str>
        Name of the table or feature class

    field: <str>
        Name of the field

    Returns
    -------
    unique_values: <list>
        Field values
    """
    # Create a cursor object for reading the table
    cursor = arcpy.da.SearchCursor(table, [field])  # A cursor iterates over rows in table

    # Create an empty list for unique values
    unique_values = []

    # Iterate through rows
    for row in cursor:
        unique_values.append(row[0])

    return unique_values

def DistribDAOverDomains():
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
    df_index_cols.set_index('LG_index', inplace=True)  # Set 'LG_index' as dataframe index
    df_dict_LG_domains_ALL = {"indicies": df_index_cols}  # This dict will contain all of the calculated DA fields

    # Add LG components to master DataFrame "df_dict_LG_domains_ALL"
    print("Adding LG_index components to master DataFrame...\n")
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

        print(domainType, "distribution started...")

        # Create a list of domain index values (e.g, LD1, LD2, LD3, LD4), then add to DataFrame
        domainType_index_values = FieldValues(PE_Grid, domainType + '_index')
        df_index_cols[domainType + '_index'] = domainType_index_values
        df_index_cols.fillna(value={domainType + '_index': 0}, inplace=True)
        print("created list of domain index values")

        # Update dict of lists for each domain type
        domainType_components[domainType] = [i for i in unique_components if domainType in i]

        # Create DataFrame with values for records for each domainType
        domain_cols = {'LG_index': LG_index_values}  # Include LG_index for joining
        for i in domainType_components[domainType]:
            domain_cols[i] = FieldValues(PE_Grid, i)
        df_domainType_fieldvalues = pd.DataFrame(domain_cols)
        df_domainType_fieldvalues.set_index('LG_index', inplace=True)  # Set 'LG_index' as dataframe index
        print("created dataframe with values for records")

        # Join into a new DataFrame the domainType_index and domainType_components/values columns
        df_domainType_joined = df_index_cols.join(df_domainType_fieldvalues, sort=False)

        # Group by unique domainType_index values
        df_domainType_grouped = df_domainType_joined.groupby([domainType + '_index'])

        # Determine max of DA for each domainType_index group, return in "DA_...domainType..._distributed" column
        df_domainType_max = df_domainType_grouped.max()
        for i in domainType_components[domainType]:
            df_domainType_max.rename(columns={i: (i + "_distributed")}, inplace=True)
        #     df_domainType_max.drop(['LG_index'], axis=1, inplace=True)  # LG_index is erroneously overwritten without this line

        # Join index and DA_max columns in a new DataFrame
        #     df_domainType_export = df_index_cols.merge(df_domainType_max, on = domainType + '_index')
        df_domainType_export = df_index_cols.join(df_domainType_max, on=domainType + '_index')
        #     df_domainType_all = df_domainType_joined.merge(df_domainType_max, on = domainType + '_index')

        # Combine all domain types into a list/dict of DataFrames
        #     df_domainALL = df_domainType_joined.join(df_domainType_export, on='LG_index', lsuffix='', rsuffix='_from'+domainType)
        df_dict_LG_domains_ALL[domainType] = df_domainType_export.copy()

        print(domainType, "distribution finished.\n")

    print("All domain types distributed.\n")

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

    #     print(domainType, "export started...")

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
    #         print(str(domainType + "_index"), "ArcGIS table already exists... deleting and trying again!")
    #         arcpy.Delete_management(outTable)
    #         arcpy.TableToTable_conversion(inTable, outLocation, outTable)
    #         print(str(domainType + "_index"), "DataFrame csv converted to ArcGIS table!")

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
    #             print("Unable to remove unnecessary fields from Join list... they may not exist.")
    #     print("Joining", joinTable, "to", PE_Grid)
    #     arcpy.JoinField_management(inFeatures, joinField, joinTable, joinField, fieldList)

    #     print(domainType, "exported.\n")

    # print('\nAll done.')

    # # number of cells with data in each LD domain
    # df_domainALL['LD']['LD_index'].value_counts()

    # # number of cells with data in each UD domain
    # df_domainALL['UD']['UD_index'].value_counts()


    # Print processing time
    t_stop = process_time()
    seconds = t_stop - t_start
    minutes = seconds / 60
    hours = minutes / 60

    print("Runtime:", round(seconds, 2), "seconds")
    print("Runtime:", round(minutes, 2), "minutes")
    print("Runtime:", round(hours, 2), "hours")

def CalcSumDA();
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


    # Print processing time
    t_stop = process_time()
    seconds = t_stop - t_start
    minutes = seconds / 60
    hours = minutes / 60

    print("Runtime:", round(seconds, 2), "seconds")
    print("Runtime:", round(minutes, 2), "minutes")
    print("Runtime:", round(hours, 2), "hours")
