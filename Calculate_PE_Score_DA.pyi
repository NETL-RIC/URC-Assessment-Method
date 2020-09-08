
from osgeo import gdal,ogr
import typing

def ListFeatureClasseNames(ds:gdal.Dataset,wildCard:str,first_char:int, last_char:int) ->typing.List[str]:
    ...

def ListFeatureClasses(ds:gdal.Dataset,wildCard:str) ->typing.List[ogr.Layer]:
    ...

def replaceNULL(feature_class : ogr.Layer, field : str):
    ...