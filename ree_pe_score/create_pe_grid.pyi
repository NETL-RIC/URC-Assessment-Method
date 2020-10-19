from typing import Optional
from osgeo import ogr,gdal,osr
from .common_utils import REE_Workspace


def IndexCalc(domainType : str, domainDS : gdal.Dataset) -> gdal.Dataset:
    ...

def indexDomainType(domainType:str,input_file:str,layerInd:int=0) -> gdal.Dataset:
    ...

def ClearPEDatasets(paths:REE_Workspace):
    ...

def buildIndices(ds : gdal.Dataset,workspace: REE_Workspace,outputs:REE_Workspace,
                 polygonWidth:float,polygonHeight:float) -> ogr.Layer:
    ...

def calcUniqueDomains(grid_LG_SD_LD : ogr.Layer,outputs : REE_Workspace) -> ogr.Layer:
    ...

def copyPE_Grid(workingDS:gdal.Dataset,PE_Grid_calc:ogr.Layer,sRef:osr.SpatialReference) -> ogr.Layer:
    ...

def RunCreatePEGrid(workspace:REE_Workspace,output_dir:REE_Workspace,gridWidth:float,gridHeight:float,prj_file:Optional[str]=None):
    ...