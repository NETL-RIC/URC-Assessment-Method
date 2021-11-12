
from typing import Callable,Optional
from .common_utils import REE_Workspace
from .urc_common import RasterGroup
import numpy as np


def CollectIndexRasters(inWorkspace:REE_Workspace)->RasterGroup:
    ...

def RunPEScore(gdbPath : str,inWorkspace : REE_Workspace,outWorkspace : REE_Workspace,doDA:bool=...,doDS:bool=...,rasters_only:bool=...,postProg:Optional[Callable[[int],None]]=...):
    ...

