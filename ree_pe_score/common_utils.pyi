from osgeo import gdal,ogr,osr
from typing import Dict,Sequence,Generator,Union,Set,Any,Optional,Tuple,List
import pandas as pd
import numpy as np

class DataPrefix(object):

    prefix : str

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


def printTimeStamp(rawSeconds:Union[int,float]):
    ...

def ParseWorkspaceArgs(vals:Dict[str,str],workspace:REE_Workspace,outputs:REE_Workspace):
    ...

def ListFieldNames(featureclass : ogr.Layer) -> list:
    ...

def DeleteFile(path : str):
    ...

def rasterDomainIntersect(inCoords:np.ndarray, inMask:np.ndarray, srcSRef:osr.SpatialReference, joinLyr:ogr.Layer, fldName:str, nodata:int=...)->np.ndarray:
    ...

def IndexFeatures(inLyr : ogr.Layer, cellWidth : float,cellHeight : float,drivername:str=...,noData:int=...) -> (np.ndarray,gdal.Dataset):
    ...

def writeRaster(maskLyr: gdal.Dataset, data:np.ndarray, name:str, drivername:str=..., gdtype:int=..., nodata:int=...)->gdal.Dataset:
    ...
