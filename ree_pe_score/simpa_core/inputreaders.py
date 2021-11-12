"""
This is a module intended for standardizing import formats.

**NOTE:** This module is presently just stubs; once we allow more than just rasters as inputs, we'll
begin utilizing this module.

"""

from __future__ import absolute_import, division, print_function, unicode_literals

import sys
from .compat2or3 import ABC
from abc import abstractmethod


class BaseInputReader(ABC):
    """
    Abstract base class for file loaders.
    """

    def __init__(self, src):
        """
        Constructor.
        Args:
            src (str): Path to source object.
        """

        self._srcStr = src

    @abstractmethod
    def load(self):
        """
        Load data from the source, as defined in a subclass.
        """
        pass

    @abstractmethod
    def populate_inputs(self, inps):
        """

        Args:
            inps (???): ???

        """
        pass


######################################################################################################################

class RasterInputReader(BaseInputReader):
    """
    Stub for class used to read in rasters.
    """
    pass


######################################################################################################################

class VectorInputReader(BaseInputReader):
    """
    Stub for class used to read in vectors.
    """
    pass

######################################################################################################################
