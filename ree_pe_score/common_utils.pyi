from osgeo import gdal,ogr,osr
from typing import Iterable, Callable,Dict,Sequence,Generator,Union,Set,Any,Optional,Tuple,List
import pandas as pd
import numpy as np

class DataPrefix(object):

    _pref : str

    def __init__(self,prefix:str): ...
    def __getitem__(self, lbl:str) -> str: ...


class REE_Workspace(object):

    workspace : str
    _entries : Dict[str,str]
    def __init__(self,workspace_dir:str,**kwargs): ...
    def __getitem__(self, item:str)->str: ...
    def __setitem__(self, key:str, value:str): ...
    def __contains__(self,item:str)->bool: ...
    def __iter__(self)->Generator[str,None,None]: ...
    def __dict__(self)->Dict[str,str]: ...
    def __len__(self) -> int: ...
    def get(self, key:str, default:Any)->Any: ...
    def DeleteFiles(self,*args,**kwargs): ...


class RasterGroup(object):

    _rasters: Dict[str,gdal.Dataset]
    _cached_ref: Optional[gdal.Dataset]

    def __init__(self, **kwargs): ...
    def __repr__(self)->str: ...
    def __getitem__(self, item:str)->gdal.Dataset: ...
    def __setitem__(self, key:str, value:Union[str,gdal.Dataset]): ...
    def __delitem__(self, key:str): ...
    def items(self)->Set[Tuple[str,gdal.Dataset]]: ...
    def add(self, id:str, path_or_ds:Union[str,gdal.Dataset]): ...
    def generateHitMap(self,keys:Optional[List[str]]=...)->np.ndarray: ...
    def generateNoDataMask(self)->np.ndarray: ...
    def _getTestRaster(self)->Optional[gdal.Dataset]: ...

    @property
    def rasterNames(self)->List[str]: ...
    @property
    def extents(self)->Tuple[float,float,float,float]: ...
    @property
    def projection(self)->str: ...
    @property
    def geoTransform(self)->Tuple[float,float,float,float,float,float]: ...
    @property
    def spatialRef(self)->osr.SpatialReference: ...
    @property
    def RasterXSize(self)->int: ...
    @property
    def RasterYSize(self)->int: ...


def ParseWorkspaceArgs(vals:Dict[str,str],workspace:REE_Workspace,outputs:REE_Workspace):
    ...

def ListFieldNames(featureclass : ogr.Layer) -> list:
    ...

def FieldValues(lyr : ogr.Layer, field : str) -> list:
    ...

def DeleteFile(path : str):
    ...

def rasterDomainIntersect(inCoords:np.ndarray, inMask:np.ndarray, srcSRef:osr.SpatialReference, joinLyr:ogr.Layer, fldName:str, nodata:int=...)->np.ndarray:
    ...

def IndexFeatures(inLyr : ogr.Layer, cellWidth : float,cellHeight : float,drivername:str=...,noData:int=...) -> (np.ndarray,gdal.Dataset):
    ...

def writeRaster(maskLyr: gdal.Dataset, data:np.ndarray, name:str, drivername:str=..., gdtype:int=..., nodata:int=...):
    ...

def Rasterize(id:str,fc_list:List[List[ogr.Layer]],inDS:gdal.Dataset,xSize:int,ySize:int,geotrans:Tuple[float,float,float,float,float,float],
              srs:osr.SpatialReference,drvrName:str=...,prefix:str=...,suffix:str=...,nodata:int=...,
              gdType:int=...)->gdal.Dataset:
    ...

def RasterDistance(id:str,inDS:gdal.Dataset, drvrName:str=..., prefix:str=..., suffix:str=...,gdType:int=...)->gdal.Dataset:
    ...

def normalizeRaster(inRast:gdal.Dataset,flip:bool=...)->Tuple[np.ndarray,float]:
    ...

def MultBandData(data1:np.ndarray,data2:np.ndarray,id:str,nd1:float,nd2:float,geotrans:Tuple[float,float,float,float,float,float],spatRef:osr.SpatialReference,drvrName:str=...)->gdal.Dataset:
    ...

def SpatialJoinCentroid(targetLyr : ogr.Layer, joinLyr : ogr.Layer, outDS : gdal.Dataset) -> ogr.Layer:
    ...

def CreateCopy(inDS : gdal.Dataset,path : str,driverName : str) -> gdal.Dataset:
    ...

def WriteIfRequested(inLayer : ogr.Layer, workspace: REE_Workspace, tag : str, drvrName : str = 'ESRI Shapefile'):
    ...

def OgrPandasJoin(inLyr : ogr.Layer, inField : str, joinDF : pd.DataFrame, joinField : str = None,copyFields : list = None):
    ...

def BuildLookups(lyr : ogr.Layer,indFields : Sequence[str])-> Dict[str,int]:
    ...

def MarkIntersectingFeatures(testLyr : ogr.Layer,filtLyr : ogr.Layer,domInds:Dict[str,int],fcInd:int,hitMatrix:np.array):
    ...

def GetFilteredFeatures(inlyr : ogr.Layer,filterLyr : ogr.Layer):
    ...

def CopyFilteredFeatures(inlyr : ogr.Layer,filterLyr : ogr.Layer,dsOrLyr : Union[gdal.Dataset,ogr.Layer]) -> ogr.Layer:
    ...

def GetFilteredUniqueValues(inlyr : ogr.Layer,filterLyr : ogr.Layer,field : Union[str,int]) -> Set[Any]:
    ...