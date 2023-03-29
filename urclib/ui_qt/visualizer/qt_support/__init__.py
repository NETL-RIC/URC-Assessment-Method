# This file is part of URC Assessment Method.
#
# URC Assessment Method is free software: you can redistribute it and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# URC Assessment Method is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with URC Assessment Method. If not, see
# <https://www.gnu.org/licenses/>.

"""Package for utilizing GAIAVisualizer in Qt."""

from .qt_GaiaGLWidget import GaiaQtGLWidget
from .colorbuttons_qt import ColorButton,GradientButton,GradientSwatch
from .GradientDlg import GradientDialog
from .qt_color_utils import vecToQColor,QColorToVec,GradRecToStops,StopsToGradRec
