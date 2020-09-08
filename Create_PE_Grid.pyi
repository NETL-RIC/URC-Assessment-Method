from osgeo import ogr,gdal
from common_utils import REE_Workspace


def IndexCalc(domainType : str, domain_shp : gdal.Dataset) -> gdal.Dataset:
    ...

def indexDomainType(domainType:str,input_file:str,) -> gdal.Dataset:
    ...

def ClearPEDatasets(paths:REE_Workspace):
    ...

def buildIndices(ds : gdal.Dataset,workspace: REE_Workspace,outputs:REE_Workspace,
                 polygonWidth:float,polygonHeight:float) -> ogr.Layer:
    ...

def calcUniqueDomains(inDS : gdal.Dataset,grid_LG_SD_LD : ogr.Layer,outputs : REE_Workspace) -> ogr.Layer:
    ...

def copyPE_Grid(workingDS:gdal.Dataset,PE_Grid_calc:ogr.Layer) -> ogr.Layer:
    ...