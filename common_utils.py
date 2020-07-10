from osgeo import gdal,ogr

def ListFieldNames(featureclass : ogr.Feature) -> list:
    """
    Lists the fields in a feature class, shapefile, or table in a specified dataset.

    Parameters
    ----------
    featureclass: <str>
        Name of feature class
    Can modify to include: wild_card, field_type in arcpy.ListFields()

    Returns
    -------
    <list>
        Field names
    """

    fDefn = featureclass.GetFieldDefnRef()
    field_names = [fDefn.GetFieldDefn(i).GetName() for i in range(fDefn.GetFieldCount())]

    return field_names



def FieldValues(lyr : ogr.Layer, field : str) -> list:
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

    unique_values = [None] * lyr.GetFeatureCount()
    fIdx = lyr.GetFeatureDefn().GetFieldIndex(field)
    for i in range(lyr.GetFeatureCount()):
        feat = lyr.GetFeature(i)
        unique_values[i] = feat.GetFieldAsDouble(field)

    return unique_values
